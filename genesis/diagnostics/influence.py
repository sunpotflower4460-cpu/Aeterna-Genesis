"""How far, and how fast, does a tiny poke at one point reach? (twin universes; any white, 2D or 3D)

    twin A = the universe as it is, twin B = the same universe with a tiny poke at one point
    run both with the same law; |A − B| is the influence of the poke

For each sample time: the radius inside which the influence exceeds `rel` × (its maximum at that time) -- the
front -- and the fraction of the box where it exceeds an ABSOLUTE floor `floor` (anything the poke changed at all,
beyond round-off). With a finite signal speed c, the influence stays inside r ≤ c·t (+ stencil margin); with
diffusion, or with a solver that uses global (FFT) operators, it is nonzero everywhere after one step.

Lattice note: an explicit nearest-neighbour stencil can move a signal at most one cell per step (for the wave
white 1/dt = 5 cells per time unit), so `reach` (any change above `floor`) may show a far, tiny numerical fringe
ahead of c·t; the physically meaningful `front` (relative to the maximum) is what obeys c.

This is a measuring instrument; it neither knows nor prefers what the result should be. The poke is PUT IN
(its size and place are reported), and the twins are copies, so nothing is changed in the universe measured.
"""
from __future__ import annotations

import copy
from typing import Any, Callable

import numpy as np


def _radii(shape: tuple[int, ...], point: tuple[int, ...]) -> np.ndarray:
    grids = np.meshgrid(*[np.arange(n) for n in shape], indexing="ij")
    return np.sqrt(sum(np.minimum(abs(g - c), n - abs(g - c)) ** 2 for g, c, n in zip(grids, point, shape)))


def twin_influence(state: dict[str, np.ndarray], advance: Callable[[dict[str, np.ndarray], int], dict[str, np.ndarray]],
                   key: str, point: tuple[int, ...], amp: float, samples: int, steps_per_sample: int, dt: float,
                   rel: float = 1e-3, floor: float = 1e-12) -> dict[str, Any]:
    """`advance(state, n)` returns the state n steps later (must not modify its input in place)."""
    a = {k: np.array(v, copy=True) for k, v in state.items()}
    b = copy.deepcopy(a)
    b[key] = b[key].copy()
    b[key][point] = b[key][point] + amp
    shape = a[key].shape
    r = _radii(shape, point)
    rows = []
    for s in range(1, samples + 1):
        a, b = advance(a, steps_per_sample), advance(b, steps_per_sample)
        diff = np.zeros(shape)
        for k in a:
            if np.shape(a[k]) == shape:
                diff = np.maximum(diff, np.abs(np.asarray(b[k]) - np.asarray(a[k])))
        t = s * steps_per_sample * dt
        top = float(diff.max())
        front = float(r[diff > rel * top].max()) if top > 0 else 0.0
        reach = float(r[diff > floor].max()) if (diff > floor).any() else 0.0
        rows.append({"t": round(t, 4), "front": round(front, 3), "reach": round(reach, 3),
                     "touched": round(float((diff > floor).mean()), 5), "max_diff": top})
    far = float(r.max())
    return {"point": list(point), "amp": amp, "rel": rel, "floor": floor, "box_max_r": round(far, 2), "rows": rows,
            "front_speed": _speed(rows), "reach_speed": _speed(rows, "reach"), "alpha": _alpha(rows),
            "speed_ratio": _speed_ratio(rows), "lin_over_sqrt": _lin_over_sqrt(rows)}


def _lin_over_sqrt(rows: list[dict[str, Any]], col: str = "front") -> float | None:
    """Residual of front = a + b·t divided by the residual of front = a + b·sqrt(t) (both least squares).
    < 1: the front moves at a steady speed; > 1: it slows like sqrt(t). Measured on this repo's whites:
    waves 0.27–1.15, diffusive whites 2.1–21 (tools/influence_compare.py)."""
    pts = [(x["t"], x[col]) for x in rows if 0 < x[col]]
    if len(pts) < 4:
        return None
    t, y = np.array(pts).T
    sse = []
    for X in (t, np.sqrt(t)):
        A = np.vstack([np.ones_like(X), X]).T
        c, *_ = np.linalg.lstsq(A, y, rcond=None)
        sse.append(float(((A @ c - y) ** 2).sum()))
    return round(sse[0] / max(sse[1], 1e-12), 3)


def _speed_ratio(rows: list[dict[str, Any]], col: str = "front") -> float | None:
    """Slope of the front over the second half of the samples divided by the slope over the first half:
    about 1 when the front moves at a steady speed (waves), about 0.4–0.7 when it slows like sqrt(t) (diffusion)."""
    pts = [(x["t"], x[col]) for x in rows if 0 < x[col]]
    if len(pts) < 6:
        return None
    h = len(pts) // 2
    early, late = np.array(pts[:h]).T, np.array(pts[h:]).T
    s1, s2 = np.polyfit(*early, 1)[0], np.polyfit(*late, 1)[0]
    return round(float(s2 / s1), 3) if s1 > 0 else None


def _alpha(rows: list[dict[str, Any]], col: str = "front") -> float | None:
    """Exponent of front ∝ t^α (log–log slope) while the front is inside half the box: 1 for a finite signal
    speed, about 0.5 for diffusion, about 0 when it is everywhere from the first sample on."""
    far = max(x[col] for x in rows) if rows else 0
    pts = [(x["t"], x[col]) for x in rows if 0 < x[col]]
    if len(pts) < 3 or far <= 0:
        return None
    t, y = np.log(np.array(pts)).T
    return round(float(np.polyfit(t, y, 1)[0]), 3)


def _speed(rows: list[dict[str, Any]], col: str = "front") -> float | None:
    """Least-squares slope of the column against t (cells per time unit), before it saturates at the box."""
    pts = [(x["t"], x[col]) for x in rows if 0 < x[col]]
    if len(pts) < 3:
        return None
    t, y = np.array(pts).T
    return round(float(np.polyfit(t, y, 1)[0]), 4)


KIND_WORDS = {"steady": "一定の速さで広がる（光のように有限の速さ）", "slowing": "だんだん遅く広がる（拡散のように）",
              "nonlocal": "1 ステップで隣より遠くまで届く（全体を一度に計算する近道＝FFT など。局所ではない）",
              "unclear": "はっきりしない"}


def kind(res: dict[str, Any], steps_first_sample: int) -> str:
    """nonlocal | steady | slowing | unclear.

    nonlocal: in the first sample the front is farther than a nearest-neighbour stencil can carry anything
    (one cell per step), i.e. the solver uses a global operator (FFT). Wider local stencils would need a larger
    bound; all lab whites that are local use nearest-neighbour stencils.
    steady / slowing: the front fits a + b·t better than a + b·sqrt(t) (lin_over_sqrt < 1.5) / clearly worse (> 2).
    (The late/early speed ratio is reported too, but it is noisy in hot, nonlinear states.)"""
    rows = res["rows"]
    if not rows:
        return "unclear"
    if rows[0]["front"] > steps_first_sample + 1:
        return "nonlocal"
    q = res.get("lin_over_sqrt")
    if q is None:
        return "unclear"
    if q < 1.5:
        return "steady"
    if q > 2.0:
        return "slowing"
    return "unclear"
