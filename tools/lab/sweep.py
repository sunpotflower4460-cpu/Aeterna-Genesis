"""「まとめて試す」: run many variants of one white from t=0 without drawing them, judge each against the goal.

    variants = product(seeds, values of each varied knob)          at most MAX_VARIANTS per call
    each     = Universe(white, seed, knobs) advanced frame by frame, measured every frame (same as the hub),
               judged with goals.check_criterion on the same series the live lab would have

Every variant is a plain recipe (white + seed + initial knobs, no events), so the one a person wants to watch
can be put in a tank and will run exactly the same way from t=0 (and its sha256 is kept for replay).
Variants run in separate processes (numpy work is CPU-bound); `stop()` cancels what has not started.
Nothing here decides what a result means: it only ranks by how many of the chosen criteria were met.
"""
from __future__ import annotations

import concurrent.futures as cf
import itertools
import multiprocessing as mp
import os
from typing import Any, Callable

from tools.lab import goals as goalmod
from tools.lab import whites
from tools.lab.universe import Universe

MAX_VARIANTS = 24
MAX_FRAMES = 300


def plan(white_id: str, base: dict[str, float], vary: dict[str, list[float]], seeds: list[int]) -> list[dict[str, Any]]:
    """All combinations, each checked against the registry (start knobs allowed: every variant starts at t=0)."""
    w = whites.get(white_id)
    names = list(vary)
    out = []
    for seed in seeds or [0]:
        for combo in itertools.product(*[vary[n] for n in names]) if names else [()]:
            knobs = w.check_knobs({**base, **dict(zip(names, combo))}, allow_start=True)
            out.append({"white": white_id, "seed": int(seed), "knobs": knobs})
    if len(out) > MAX_VARIANTS:
        raise ValueError(f"組み合わせが {len(out)} 通りあります（1 回 {MAX_VARIANTS} 通りまで）。値か seed を減らしてください")
    if not out:
        raise ValueError("試す組み合わせがありません")
    return out


def run_variant(v: dict[str, Any], frames: int, criteria: list[dict[str, Any]]) -> dict[str, Any]:
    """One variant from t=0: measured every frame, judged on its own series. Top level (picklable)."""
    u = Universe(v["white"], v["seed"], v["knobs"])
    spf = u.white.steps_per_frame
    samples = [{"t": u.t, "metrics": u.metrics()}]
    diverged = False
    for _ in range(frames):
        u.advance(spf)
        if not u.finite():                 # numerical blow-up is not physics
            diverged = True
            break
        samples.append({"t": u.t, "metrics": u.metrics()})
    series = goalmod.derived_series(samples)
    rows = [goalmod.check_criterion(series, c) for c in criteria]
    met = sum(r["met"] for r in rows)
    closeness = sum(min(1.0, r["longest"] / r["hold"]) if r["hold"] else float(r["met"]) for r in rows)
    first, last = samples[0]["metrics"], samples[-1]["metrics"]
    return {**v, "frames": len(samples) - 1, "steps": u.step_index, "t": u.t, "diverged": diverged,
            "sha256": None if diverged else u.sha256(), "criteria": rows, "met": met,
            "all_met": bool(rows) and met == len(rows), "score": round(met + 0.5 * closeness, 4),
            "first": {k: _r(x) for k, x in first.items()}, "last": {k: _r(x) for k, x in last.items()}}


def _r(x: Any) -> Any:
    return round(float(x), 4) if isinstance(x, (int, float)) and x == x else None


def run(variants: list[dict[str, Any]], frames: int, criteria: list[dict[str, Any]], workers: int | None = None,
        should_stop: Callable[[], bool] = lambda: False) -> list[dict[str, Any]]:
    """Run all variants (in parallel processes when workers > 1) and return them best first."""
    if not 1 <= frames <= MAX_FRAMES:
        raise ValueError(f"frames は 1〜{MAX_FRAMES} です")
    workers = max(1, min(workers or max(1, (os.cpu_count() or 2) - 1), len(variants)))
    results: list[dict[str, Any]] = []
    if workers == 1:
        for v in variants:
            if should_stop():
                break
            results.append(run_variant(v, frames, criteria))
    else:
        with cf.ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as pool:
            futs = [pool.submit(run_variant, v, frames, criteria) for v in variants]
            for f in cf.as_completed(futs):
                if should_stop():
                    for g in futs:
                        g.cancel()
                    break
                results.append(f.result())
    return rank(results)


def rank(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(results, key=lambda r: (r["diverged"], -r["score"], r["seed"], sorted(r["knobs"].items())))


def label(r: dict[str, Any], base: dict[str, float] | None = None) -> str:
    """'θ=30, Dw=40 / seed 2' -- only what differs from the white's defaults (or from `base`)."""
    w = whites.get(r["white"])
    ref = {**w.default_knobs(), **(base or {})}
    diff = [f"{k}={v:g}" for k, v in r["knobs"].items() if ref.get(k) != v]
    return (", ".join(diff) or "既定のつまみ") + f" / seed {r['seed']}"
