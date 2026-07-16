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
nearest opposite-charge partner and test separation bound + rate-of-change bound + velocity-perpendicular-
to-separation. A continuous run of frames where the SAME (positive track, negative track) pair satisfies
all three is one episode; a partner change or a failed test ENDS the episode immediately (never silently
extends it). The episode's COM trajectory is unwrapped across periodic-boundary crossings before computing
net displacement / straightness -- v1 computed a periodic-aware MIDPOINT per frame but never unwrapped the
resulting trajectory across frames, so a box-edge crossing could show up as a spurious large jump.

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


def detect_episodes(tracks, L, sep_max=8.0, max_sep_rate=2.0, perp_cos_tol=0.5, min_len=1):
    """Per-frame dipole episode detection.

    tracks: output of vortex_tracking_v2.link_frames_v2 (or level3_motion.link_frames -- either track
    format works, only 'charge' and 'points' are used).
    sep_max: geometric bound on separation to count as "bound".
    max_sep_rate: separation must not change by more than this per frame (screens incidental crossings).
    perp_cos_tol: |cos(angle between COM velocity and separation vector)| must be <= this (translating
    dipoles move PERPENDICULAR to their separation; co-rotating or radially approaching pairs do not).
    Returns a list of episode dicts: pos_track/neg_track indices, start/end frame, duration, mean_sep,
    net_displacement, path_length, straightness (all computed on the UNWRAPPED COM trajectory).
    """
    pos_tracks = {i: t for i, t in enumerate(tracks) if t["charge"] > 0}
    neg_tracks = {i: t for i, t in enumerate(tracks) if t["charge"] < 0}
    by_frame = {}
    for idx, t in list(pos_tracks.items()) + list(neg_tracks.items()):
        for (f, x, y) in t["points"]:
            by_frame.setdefault(f, {})[idx] = (x, y)
    all_frames = sorted(by_frame.keys())

    frame_partner = {}
    for f in all_frames:
        pres = by_frame[f]
        p_here = [i for i in pres if i in pos_tracks]
        n_here = [i for i in pres if i in neg_tracks]
        best = None
        for pi in p_here:
            px, py = pres[pi]
            for ni in n_here:
                nx, ny = pres[ni]
                dx = _wrap_delta(nx - px, L)
                dy = _wrap_delta(ny - py, L)
                d = float(np.hypot(dx, dy))
                if best is None or d < best[2]:
                    best = (pi, ni, d)
        frame_partner[f] = best if (best and best[2] <= sep_max) else None

    episodes = []
    cur = None
    prev_sep = None
    prev_com = None
    for f in all_frames:
        partner = frame_partner[f]
        if partner is None:
            if cur is not None:
                episodes.append(cur)
                cur = None
            prev_sep = None
            prev_com = None
            continue
        pi, ni, sep = partner
        px, py = by_frame[f][pi]
        nx, ny = by_frame[f][ni]
        dx = _wrap_delta(nx - px, L)
        dy = _wrap_delta(ny - py, L)
        comx, comy = px + 0.5 * dx, py + 0.5 * dy

        same_pair = cur is not None and cur["pair"] == (pi, ni)
        if not same_pair:
            if cur is not None:
                episodes.append(cur)
            cur = dict(pair=(pi, ni), frames=[f], seps=[sep], com=[(comx, comy)])
            prev_sep, prev_com = sep, (comx, comy)
            continue

        sep_rate = abs(sep - prev_sep)
        ok_rate = sep_rate <= max_sep_rate
        pcx, pcy = prev_com
        vcx = _wrap_delta(comx - pcx, L)
        vcy = _wrap_delta(comy - pcy, L)
        speed = float(np.hypot(vcx, vcy))
        if speed > 1e-9 and sep > 1e-9:
            cos_ang = abs((vcx * dx + vcy * dy) / (speed * sep))
        else:
            cos_ang = 0.0
        ok_perp = cos_ang <= perp_cos_tol

        if ok_rate and ok_perp:
            cur["frames"].append(f)
            cur["seps"].append(sep)
            cur["com"].append((comx, comy))
            prev_sep, prev_com = sep, (comx, comy)
        else:
            episodes.append(cur)
            cur = dict(pair=(pi, ni), frames=[f], seps=[sep], com=[(comx, comy)])
            prev_sep, prev_com = sep, (comx, comy)
    if cur is not None:
        episodes.append(cur)

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
        out.append(dict(pos_track=ep["pair"][0], neg_track=ep["pair"][1],
                         start_frame=ep["frames"][0], end_frame=ep["frames"][-1],
                         duration=len(ep["frames"]), mean_sep=round(float(np.mean(ep["seps"])), 4),
                         net_displacement=round(net_disp, 4), path_length=round(path, 4),
                         straightness=round(straightness, 4)))
    return out
