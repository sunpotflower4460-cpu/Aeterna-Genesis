#!/usr/bin/env python3
"""Level-3 (spontaneous motion) observer -- NOT a measures.py extension, a separate diagnostic (same pattern
as LT-1/LT-2/LT-3: add observers, not physics; genesis/diagnostics/measures.py stays untouched/no_touch).

EMERGENCE_LEVELS.md Level 3 asks: does a localized structure show spontaneous motion -- COM velocity != 0 AND
circulation != 0 -- that was NOT put into the initial condition? For point vortices in a 2D condensate, an
isolated opposite-charge pair is known to translate (e002, PLACED). This module answers the harder, unasked
question for a SINGLE CONTINUOUS run from an undifferentiated t=0 IC: do vortices that self-form during a
Kibble-Zurek quench ever pair up and translate coherently, distinguishable from generic jitter/numerical
noise -- i.e. is the motion GENUINE dipole propulsion, not an artifact?

Two independent, self-calibrating floors (from the SAME run's data, no separate simulation needed):
  (a) an ANALYTIC random-walk straightness floor: an n-step random walk has expected net/path ~ 1/sqrt(n),
      so a directed (non-random) trajectory must clear a safety multiple of that.
  (b) an EMPIRICAL step-size floor: the median per-step displacement magnitude across ALL tracked vortices
      in the run (not a specific pairing) -- "how far does a typical single defect move per frame from
      phase noise/interactions". A genuine coherent pair must move faster than a safety multiple of this.
A naive alternative -- comparing a candidate pair's speed against OTHER (mismatched) opposite-charge
pairings as a "shuffle null" -- was tried and rejected: if either member of the true pair also appears in a
mismatched pairing, that mismatched pair partially inherits the real signal (its COM is a literal average
including the moving point), inflating the "null" and making the test conservative in a data-dependent,
uncontrolled way. The median single-track step size is a population statistic over potentially many tracks,
so one mover does not dominate it the way it dominates a small-N pairwise shuffle.

Input is a per-frame list of vortex cores from core.vortex.find_vortices: [{'x','y','charge'}, ...].
"""
import numpy as np


def _wrap_delta(d, L):
    """Shortest signed displacement on a periodic line of length L."""
    return d - L * np.round(d / L)


def link_frames(frames, L, max_step):
    """Greedy nearest-neighbor, charge-matched, periodic-aware tracker.

    frames: list (per timestep) of lists of {'x','y','charge'} (core.vortex.find_vortices output).
    Returns a list of tracks: {'charge': int, 'points': [(t, x, y), ...]} (one-to-one per frame; a track ends
    when no same-charge core lies within max_step of its last position, and a fresh track starts for it).
    """
    tracks = []
    active = []
    for t, cores in enumerate(frames):
        used = set()
        new_active = []
        for ti in active:
            tr = tracks[ti]
            lx, ly = tr["last"]
            best, bestd = None, None
            for ci, c in enumerate(cores):
                if ci in used or c["charge"] != tr["charge"]:
                    continue
                dx = _wrap_delta(c["x"] - lx, L)
                dy = _wrap_delta(c["y"] - ly, L)
                d2 = dx * dx + dy * dy
                if bestd is None or d2 < bestd:
                    bestd, best = d2, ci
            if best is not None and bestd <= max_step ** 2:
                c = cores[best]
                used.add(best)
                tr["points"].append((t, c["x"], c["y"]))
                tr["last"] = (c["x"], c["y"])
                new_active.append(ti)
        active = new_active
        for ci, c in enumerate(cores):
            if ci in used:
                continue
            tracks.append({"charge": c["charge"], "points": [(t, c["x"], c["y"])], "last": (c["x"], c["y"])})
            active.append(len(tracks) - 1)
    return tracks


def track_step_sizes(tracks, L):
    """Per-step displacement magnitude for EVERY track (all charges, all tracks) -- the empirical
    population floor for 'how far a typical single defect moves per frame'."""
    sizes = []
    for tr in tracks:
        pts = tr["points"]
        for i in range(len(pts) - 1):
            _, x0, y0 = pts[i]
            _, x1, y1 = pts[i + 1]
            dx = _wrap_delta(x1 - x0, L)
            dy = _wrap_delta(y1 - y0, L)
            sizes.append(float(np.hypot(dx, dy)))
    return np.array(sizes)


def _unwrap_pair_positions(pa, pb, L):
    """Given two point sequences over the SAME frame indices, return (com_xy[T,2], sep_xy[T,2]) with `b`
    unwrapped relative to `a` each frame (periodic-aware midpoint; valid while separation stays < L/2)."""
    com, sep = [], []
    for (ta, xa, ya), (tb, xb, yb) in zip(pa, pb):
        assert ta == tb
        dx = _wrap_delta(xb - xa, L)
        dy = _wrap_delta(yb - ya, L)
        com.append((xa + 0.5 * dx, ya + 0.5 * dy))
        sep.append((dx, dy))
    return np.array(com), np.array(sep)


def _straightness_speed(com_xy):
    """net displacement / path length (1.0=straight line, ->0 for a random walk), and mean speed per frame
    step (no drift subtraction -- see module docstring for why)."""
    if len(com_xy) < 2:
        return 0.0, 0.0
    steps = np.diff(com_xy, axis=0)
    path = float(np.sum(np.linalg.norm(steps, axis=1)))
    net = float(np.linalg.norm(np.sum(steps, axis=0)))
    straightness = net / path if path > 1e-12 else 0.0
    speed = net / (len(com_xy) - 1)
    return straightness, speed


def box_centroid_drift(frames, L):
    """Per-step drift (dx,dy) of the unweighted centroid of ALL defects present in consecutive frames --
    an informational numerical/global-advection sanity check reported once per run (should be ~0 for a
    periodic box with no imposed flow); NOT used to correct individual pair speeds."""
    centroids = []
    for cores in frames:
        if not cores:
            centroids.append(None)
            continue
        xs = np.array([c["x"] for c in cores]); ys = np.array([c["y"] for c in cores])
        centroids.append((float(xs.mean()), float(ys.mean())))
    drifts = []
    for a, b in zip(centroids[:-1], centroids[1:]):
        if a is None or b is None:
            drifts.append((0.0, 0.0))
        else:
            drifts.append((_wrap_delta(b[0] - a[0], L), _wrap_delta(b[1] - a[1], L)))
    return np.array(drifts) if drifts else np.zeros((0, 2))


def dipole_events(tracks, L, persist_min, sep_max, straight_min):
    """Find opposite-charge track pairs that are MUTUAL NEAREST NEIGHBORS (in mean separation over their
    frame overlap) for >= persist_min consecutive overlapping frames with mean separation <= sep_max --
    the geometric signature of a bound dipole, not an incidental crossing.

    Returns (candidates, other_pair_speeds): candidates is a list of dicts with straightness/speed/persist/
    mean_sep for genuine mutual-nearest pairs; other_pair_speeds is the speed of every other opposite-charge
    overlapping pairing, reported for CONTEXT only (see module docstring for why it is not the load-bearing
    null -- level3_verdict uses track_step_sizes + an analytic random-walk floor instead).
    """
    pos_tracks = [t for t in tracks if t["charge"] > 0]
    neg_tracks = [t for t in tracks if t["charge"] < 0]

    def overlap(ta, tb):
        fa = {p[0] for p in ta["points"]}
        fb = {p[0] for p in tb["points"]}
        return sorted(fa & fb)

    def window_metrics(ta, tb, common):
        if len(common) < persist_min:
            return None
        pa = [p for p in ta["points"] if p[0] in common]
        pb = [p for p in tb["points"] if p[0] in common]
        com, sep = _unwrap_pair_positions(pa, pb, L)
        mean_sep = float(np.mean(np.linalg.norm(sep, axis=1)))
        straightness, speed = _straightness_speed(com)
        return dict(persist=len(common), mean_sep=mean_sep, straightness=straightness, speed=speed)

    all_pairs = []
    for ta in pos_tracks:
        for tb in neg_tracks:
            m = window_metrics(ta, tb, overlap(ta, tb))
            if m is not None:
                all_pairs.append((ta, tb, m))

    candidates, other_speeds = [], []
    for ta, tb, m in all_pairs:
        ta_best = min((mm["mean_sep"] for (a2, b2, mm) in all_pairs if a2 is ta), default=None)
        tb_best = min((mm["mean_sep"] for (a2, b2, mm) in all_pairs if b2 is tb), default=None)
        is_mutual = (ta_best is not None and abs(m["mean_sep"] - ta_best) < 1e-9 and
                     tb_best is not None and abs(m["mean_sep"] - tb_best) < 1e-9)
        if is_mutual and m["mean_sep"] <= sep_max and m["persist"] >= persist_min and m["straightness"] >= straight_min:
            candidates.append(m)
        else:
            other_speeds.append(m["speed"])
    return candidates, other_speeds


def mutual_neighbor_durations(tracks, L, sep_max):
    """For EVERY mutual-nearest-neighbor opposite-charge pairing (same geometric test as dipole_events, but
    WITHOUT the persist_min/straightness gates), return its raw persist duration (frames) and mean_sep.

    This is the building block for a survival-TIME distribution (Level-4 direction: is there a long-lived
    bound compound, not just a pair that clears a fixed threshold?) -- dipole_events answers "did >=
    persist_min frames of coherent motion occur"; this answers "how long did a bound pair exist at all,
    including short-lived ones", which dipole_events' persist_min cutoff would otherwise discard."""
    pos_tracks = [t for t in tracks if t["charge"] > 0]
    neg_tracks = [t for t in tracks if t["charge"] < 0]

    def overlap(ta, tb):
        fa = {p[0] for p in ta["points"]}
        fb = {p[0] for p in tb["points"]}
        return sorted(fa & fb)

    all_pairs = []
    for ta in pos_tracks:
        for tb in neg_tracks:
            common = overlap(ta, tb)
            if not common:
                continue
            pa = [p for p in ta["points"] if p[0] in common]
            pb = [p for p in tb["points"] if p[0] in common]
            _com, sep = _unwrap_pair_positions(pa, pb, L)
            mean_sep = float(np.mean(np.linalg.norm(sep, axis=1)))
            all_pairs.append((ta, tb, dict(persist=len(common), mean_sep=mean_sep)))

    durations = []
    for ta, tb, m in all_pairs:
        ta_best = min((mm["mean_sep"] for (a2, b2, mm) in all_pairs if a2 is ta), default=None)
        tb_best = min((mm["mean_sep"] for (a2, b2, mm) in all_pairs if b2 is tb), default=None)
        is_mutual = (ta_best is not None and abs(m["mean_sep"] - ta_best) < 1e-9 and
                     tb_best is not None and abs(m["mean_sep"] - tb_best) < 1e-9)
        if is_mutual and m["mean_sep"] <= sep_max:
            durations.append(m["persist"])
    return durations


def level3_verdict(candidates, step_sizes, persist_min, speed_margin=3.0, straight_margin=2.0, min_steps=8):
    """Honest classification against the two self-calibrating floors (see module docstring).

    rw_floor = 1/sqrt(persist_min): the expected straightness of an n-step random walk (n=persist_min).
    step_floor = median(step_sizes): typical single-defect per-frame jitter over the WHOLE run's tracks.
    A candidate passes only if straightness clears straight_margin*rw_floor AND speed clears
    speed_margin*step_floor. With too few tracked steps to trust step_floor, report unresolved (not passed).
    """
    rw_floor = 1.0 / np.sqrt(max(persist_min, 1))
    straight_required = max(straight_margin * rw_floor, 0.3)
    if len(step_sizes) < min_steps:
        return dict(level3_reached=False, verdict="unresolved_insufficient_track_data", best=None,
                     step_floor=None, straight_required=round(straight_required, 4),
                     speed_required=None, n_candidates=len(candidates))
    step_floor = float(np.median(step_sizes))
    speed_required = speed_margin * max(step_floor, 1e-9)
    if not candidates:
        return dict(level3_reached=False, verdict="no_dipole_event", best=None,
                     step_floor=round(step_floor, 6), straight_required=round(straight_required, 4),
                     speed_required=round(speed_required, 6), n_candidates=0)
    best = max(candidates, key=lambda c: c["speed"])
    passes = best["speed"] > speed_required and best["straightness"] > straight_required
    return dict(level3_reached=bool(passes),
                 verdict="level3_dipole_candidate" if passes else "not_separated_from_jitter_floor",
                 best=best, step_floor=round(step_floor, 6),
                 straight_required=round(straight_required, 4), speed_required=round(speed_required, 6),
                 n_candidates=len(candidates))
