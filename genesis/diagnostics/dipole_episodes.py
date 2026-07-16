#!/usr/bin/env python3
"""Per-frame dipole episode detector (Observer v2).

Motivation (external review, 2026-07-16): v1's genesis.diagnostics.level3_motion.mutual_neighbor_durations
judges a +/- pairing by AVERAGE properties over its ENTIRE frame-overlap window (mean separation, one
straightness number over the whole span). Two real weaknesses follow:
  1. If the mutual-nearest-neighbor partner effectively changes partway through (a different opposite-
     charge vortex becomes closer), v1's whole-track-overlap design can still report one long "duration" --
     it never re-checks per frame.
  2. It never tests the two clearest PHYSICAL signatures of a genuine translating dipole: (a) the pair's
     COM velocity should be roughly PERPENDICULAR to the separation vector (this is what "translate, don't
     co-rotate" means for a point-vortex pair -- a same-charge co-rotating pair would NOT show this), and
     (b) the separation should not be changing rapidly (screens out incidental crossings).

This module re-derives dipole "episodes" FRAME BY FRAME: at each frame, find the instantaneous mutual-
nearest opposite-charge partner within a separation bound. A continuous run of frames where the SAME
(positive track, negative track) pair stays within that bound is one episode; a partner change (or the
partner leaving the bound) ENDS the episode immediately (never silently extends it, unlike v1). Kinematic
quality signatures of a genuine translating dipole -- COM velocity roughly PERPENDICULAR to the separation
vector, and a stable (not rapidly changing) separation -- are reported as WHOLE-EPISODE summary statistics
(straightness = net displacement / path length over the full episode, mean_sep_rate), not as hard per-frame
tests: an earlier version of this module enforced them frame-to-frame and found that single-step COM
displacement is noisy enough (core-refinement jitter, discretization) to fragment a genuinely translating
dipole into many spurious 1-2 frame episodes. The episode's COM trajectory is unwrapped across periodic-
boundary crossings before computing net displacement / straightness -- v1 computed a periodic-aware
MIDPOINT per frame but never unwrapped the resulting trajectory across frames, so a box-edge crossing could
show up as a spurious large jump.

v1 (level3_motion.py) is UNCHANGED. This is a complementary, independent instrument (no_touch discipline).
"""
import numpy as np

from genesis.diagnostics.level3_motion import _wrap_delta


def _unwrap_com_trajectory(points, L):
    """Unwrap a 2D trajectory across periodic boundaries into a continuous (non-periodic) path."""
    points = np.asarray(points, dtype=float)
    unwrapped = [points[0]]
    for i in range(1, len(points)):
        px, py = unwrapped[-1]
        cx, cy = points[i]
        dx = _wrap_delta(cx - (px % L), L)
        dy = _wrap_delta(cy - (py % L), L)
        unwrapped.append((px + dx, py + dy))
    return np.array(unwrapped)


def detect_episodes(tracks, L, sep_max=8.0, max_sep_rate=2.0, straight_min=0.5, min_len=1):
    """Per-frame dipole episode detection.

    tracks: output of vortex_tracking_v2.link_frames_v2 (or level3_motion.link_frames -- either track
    format works, only 'charge' and 'points' are used).
    sep_max: geometric bound on separation to count as "bound" (hard, per-frame episode-continuation test,
    together with partner identity -- see the note above the main loop for why kinematics are NOT also a
    hard per-frame test).
    max_sep_rate / straight_min: whole-episode kinematic diagnostics (mean frame-to-frame separation
    change; net-displacement/path-length straightness over the full unwrapped trajectory). Reported as
    `kinematics_ok` per episode for callers to filter on; translating dipoles are expected to show high
    straightness (COM moves in roughly one direction) and a stable separation.
    Returns a list of episode dicts: pos_track/neg_track indices, start/end frame, duration, mean_sep,
    mean_sep_rate, net_displacement, path_length, straightness, kinematics_ok.
    """
    pos_tracks = {i: t for i, t in enumerate(tracks) if t["charge"] > 0}
    neg_tracks = {i: t for i, t in enumerate(tracks) if t["charge"] < 0}
    by_frame = {}
    for idx, t in list(pos_tracks.items()) + list(neg_tracks.items()):
        for (f, x, y) in t["points"]:
            by_frame.setdefault(f, {})[idx] = (x, y)
    all_frames = sorted(by_frame.keys())

    # Per frame, find ALL reciprocal (mutual) nearest-neighbor +/- pairs, not just the single globally
    # closest one (external review, 2026-07-16: a single `best` pair per frame silently drops every OTHER
    # simultaneous bound dipole, undercounting episodes -- e.g. two independent pairs nucleate in the same
    # box, only the closer one was ever counted). A positive track's nearest negative partner (within
    # sep_max) and that negative track's nearest positive partner must point back at each other; each track
    # can appear in at most one such pair per frame (it has only one "nearest"), so this is a proper
    # (non-overlapping) matching, just no longer capped at one pair per frame.
    frame_pairs = {}
    for f in all_frames:
        pres = by_frame[f]
        p_here = [i for i in pres if i in pos_tracks]
        n_here = [i for i in pres if i in neg_tracks]

        def _nearest(src, dst):
            out = {}
            for si in src:
                sx, sy = pres[si]
                best = None
                for di in dst:
                    dxp, dyp = pres[di]
                    dx = _wrap_delta(dxp - sx, L)
                    dy = _wrap_delta(dyp - sy, L)
                    d = float(np.hypot(dx, dy))
                    if best is None or d < best[1]:
                        best = (di, d)
                if best is not None and best[1] <= sep_max:
                    out[si] = best
            return out

        pos_nearest = _nearest(p_here, n_here)
        neg_nearest = _nearest(n_here, p_here)
        frame_pairs[f] = [(pi, ni, d) for pi, (ni, d) in pos_nearest.items()
                           if ni in neg_nearest and neg_nearest[ni][0] == pi]

    # Episode continuation is governed ONLY by (a) partner identity (same pos/neg track pair) and
    # (b) the separation bound -- both checked every frame. This is the real fix for v1's partner-exchange
    # bug (a partner change always starts a new episode). Per-frame kinematic checks (velocity
    # perpendicular to separation, separation rate-of-change) were tried as HARD per-step episode-ending
    # conditions in an earlier version of this module and rejected: single-step COM displacement is noisy
    # enough (sub-pixel refinement jitter, discretization) that even a genuinely translating dipole often
    # fails a strict frame-to-frame perpendicularity test, fragmenting one real episode into many spurious
    # 1-2 frame ones. Kinematic quality is instead reported as a WHOLE-EPISODE summary (straightness over
    # the full unwrapped trajectory, exactly the quantity that is robust to single-step noise) so callers
    # can filter on it themselves (e.g. straightness > 0.5) without contaminating the episode boundaries.
    # Multiple pairs can be concurrently "open" (different simultaneous dipoles), tracked by (pi, ni) key.
    episodes = []
    open_eps = {}
    for f in all_frames:
        pairs_here = {(pi, ni): sep for (pi, ni, sep) in frame_pairs[f]}
        for key in list(open_eps.keys()):
            if key not in pairs_here:
                episodes.append(open_eps.pop(key))
        for (pi, ni), sep in pairs_here.items():
            px, py = by_frame[f][pi]
            nx, ny = by_frame[f][ni]
            dx = _wrap_delta(nx - px, L)
            dy = _wrap_delta(ny - py, L)
            comx, comy = px + 0.5 * dx, py + 0.5 * dy
            if (pi, ni) in open_eps:
                cur = open_eps[(pi, ni)]
                cur["frames"].append(f)
                cur["seps"].append(sep)
                cur["com"].append((comx, comy))
            else:
                open_eps[(pi, ni)] = dict(pair=(pi, ni), frames=[f], seps=[sep], com=[(comx, comy)])
    episodes.extend(open_eps.values())

    out = []
    for ep in episodes:
        if len(ep["frames"]) < min_len:
            continue
        com_unwrapped = _unwrap_com_trajectory(ep["com"], L)
        net = com_unwrapped[-1] - com_unwrapped[0]
        net_disp = float(np.hypot(*net))
        steps = np.diff(com_unwrapped, axis=0) if len(com_unwrapped) > 1 else np.zeros((0, 2))
        path = float(np.sum(np.linalg.norm(steps, axis=1))) if len(steps) else 0.0
        straightness = net_disp / path if path > 1e-12 else 0.0
        seps = np.asarray(ep["seps"])
        sep_rate_mean = float(np.mean(np.abs(np.diff(seps)))) if len(seps) > 1 else 0.0
        out.append(dict(pos_track=ep["pair"][0], neg_track=ep["pair"][1],
                         start_frame=ep["frames"][0], end_frame=ep["frames"][-1],
                         duration=len(ep["frames"]), mean_sep=round(float(np.mean(seps)), 4),
                         mean_sep_rate=round(sep_rate_mean, 4),
                         net_displacement=round(net_disp, 4), path_length=round(path, 4),
                         straightness=round(straightness, 4),
                         kinematics_ok=bool(sep_rate_mean <= max_sep_rate and straightness >= straight_min)))
    return out
