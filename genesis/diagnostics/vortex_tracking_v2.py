#!/usr/bin/env python3
"""Vortex tracking v2 -- global (Hungarian) per-charge assignment tracker, periodic-aware, with per-step
track confidence and best-effort event classification (annihilation / merge / creation / tracking loss).

Motivation (external review, 2026-07-16): the v1 tracker (genesis.diagnostics.level3_motion.link_frames)
is GREEDY -- it processes active tracks in a fixed order and each one grabs the nearest same-charge core
one at a time. In a dense defect field, this can swap two tracks' identities when core A is nearest to
track 1 (which is fine) but a DIFFERENT core B, nearest to track 2, is actually closer to track 1's true
continuation than the greedy order let it see. Global (Hungarian / minimum-cost bipartite matching, via
scipy.optimize.linear_sum_assignment) assigns ALL active tracks of a charge against ALL same-charge cores
SIMULTANEOUSLY by minimizing total squared periodic displacement -- the standard fix in multi-object
tracking. Optionally biases the match toward each track's velocity-predicted position (linear extrapolation
from its last step), which further stabilizes assignment for genuinely moving pairs (exactly the case this
campaign cares about).

v1 (level3_motion.py) is UNCHANGED and remains the historical instrument behind e052-e057's committed
results (no_touch discipline: this is an ADDITIVE, alternative instrument, not a replacement -- same
pattern as LT-1/2/3 relative to measures.py). This module exists to CHECK v1's findings with an
independent method, not to silently supersede them.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment


def _wrap_delta(d, L):
    """Shortest signed displacement on a periodic line of length L."""
    return d - L * np.round(d / L)


def _predicted_position(track, L, velocity_predict):
    pts = track["points"]
    if not velocity_predict or len(pts) < 2:
        return track["last"]
    (_, x0, y0), (_, x1, y1) = pts[-2], pts[-1]
    vx = _wrap_delta(x1 - x0, L)
    vy = _wrap_delta(y1 - y0, L)
    return (x1 + vx) % L, (y1 + vy) % L


def link_frames_v2(frames, L, max_step, velocity_predict=True):
    """Global (Hungarian) per-charge assignment tracker.

    frames: list of per-timestep vortex core lists [{'x','y','charge'}, ...] (core.vortex.find_vortices
    output). Returns a list of tracks: {'charge', 'points': [(t,x,y),...], 'confidence': [...],
    'start_event', 'end_event'}. confidence[i] in (0,1] is 1/(1+matched_distance) for the i-th point
    (excluding the first); lower means a less certain assignment (large jump / sparse field).
    """
    tracks = []
    active = {1: [], -1: []}

    for t, cores in enumerate(frames):
        for charge in (1, -1):
            cand = [c for c in cores if c["charge"] == charge]
            act = active[charge]
            if act and cand:
                pred = [_predicted_position(tracks[i], L, velocity_predict) for i in act]
                cost = np.empty((len(act), len(cand)))
                for i, (px, py) in enumerate(pred):
                    for j, c in enumerate(cand):
                        dx = _wrap_delta(c["x"] - px, L)
                        dy = _wrap_delta(c["y"] - py, L)
                        cost[i, j] = dx * dx + dy * dy
                row_ind, col_ind = linear_sum_assignment(cost)
                matched_rows, matched_cols = set(), set()
                new_active = []
                for ri, ci in zip(row_ind, col_ind):
                    d2 = cost[ri, ci]
                    if d2 <= max_step ** 2:
                        ti = act[ri]
                        c = cand[ci]
                        tracks[ti]["points"].append((t, c["x"], c["y"]))
                        tracks[ti]["last"] = (c["x"], c["y"])
                        tracks[ti]["confidence"].append(1.0 / (1.0 + np.sqrt(d2)))
                        matched_rows.add(ri)
                        matched_cols.add(ci)
                        new_active.append(ti)
                for i, ti in enumerate(act):
                    if i not in matched_rows:
                        tracks[ti]["end_event"] = (t, "unmatched")
                for j, c in enumerate(cand):
                    if j not in matched_cols:
                        tracks.append({"charge": charge, "points": [(t, c["x"], c["y"])],
                                        "last": (c["x"], c["y"]), "confidence": [1.0],
                                        "start_event": (t, "appeared"), "end_event": None})
                        new_active.append(len(tracks) - 1)
                active[charge] = new_active
            elif cand and not act:
                new_active = []
                for c in cand:
                    tracks.append({"charge": charge, "points": [(t, c["x"], c["y"])],
                                    "last": (c["x"], c["y"]), "confidence": [1.0],
                                    "start_event": (t, "appeared"), "end_event": None})
                    new_active.append(len(tracks) - 1)
                active[charge] = new_active
            elif act and not cand:
                for ti in act:
                    tracks[ti]["end_event"] = (t, "unmatched")
                active[charge] = []
    for charge in (1, -1):
        for ti in active[charge]:
            if tracks[ti]["end_event"] is None:
                tracks[ti]["end_event"] = (len(frames) - 1, "window_end")
    return tracks


def classify_events(tracks, L, proximity=4.0):
    """Best-effort labeling of each track's end event: 'annihilation' if an opposite-charge track ends
    within `proximity` at the SAME frame (topological charge conservation makes this the natural read),
    'merge' if a same-charge track ends near another track that continues, 'window_end' if the observation
    window simply stopped (informational only -- NOT a physics claim, a labeling convenience for
    survival-analysis censoring: window_end durations are right-censored, others are observed events)."""
    ends_by_frame = {}
    for idx, tr in enumerate(tracks):
        if tr["end_event"] is None:
            continue
        f, reason = tr["end_event"]
        if reason == "window_end":
            continue
        ends_by_frame.setdefault(f, []).append(idx)

    labels = {}
    for f, idxs in ends_by_frame.items():
        for idx in idxs:
            tr = tracks[idx]
            _, x, y = tr["points"][-1]
            best = None
            for other in idxs:
                if other == idx:
                    continue
                otr = tracks[other]
                _, ox, oy = otr["points"][-1]
                dx = _wrap_delta(ox - x, L); dy = _wrap_delta(oy - y, L)
                d = np.hypot(dx, dy)
                if d <= proximity and (best is None or d < best[1]):
                    best = (other, d)
            if best is not None:
                other_charge = tracks[best[0]]["charge"]
                labels[idx] = "annihilation" if other_charge != tr["charge"] else "merge_candidate"
            else:
                labels[idx] = "unclassified_loss"
    for idx, tr in enumerate(tracks):
        if tr["end_event"] is not None and tr["end_event"][1] == "window_end":
            labels[idx] = "window_end"
    return labels
