"""Adaptive mass discovery and epistemic planning for Dream Loop v2.

Scientific truth stays in the existing deterministic runners/diagnostics.  This module only
chooses where to search next, compresses mundane results into a Coverage Atlas, and forces
counter-hypothesis/random exploration so the Research Director cannot monopolize the budget
with its current favourite idea.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from ai_lab import lab
from genesis.runners import runner

_REPO = Path(__file__).resolve().parents[2]
_COVERAGE = _REPO / "ai_lab" / "discoveries" / "coverage_atlas.json"
_HYPOTHESES = _REPO / "ai_lab" / "discoveries" / "hypothesis_ledger.json"
_DECISIONS = _REPO / "ai_lab" / "discoveries" / "research_decisions.json"
_NATIVE3D = _REPO / "ai_lab" / "discoveries" / "native3d_discoveries.json"
JST = ZoneInfo("Asia/Tokyo")

LANE_FLOORS = {"unexplored": 0.20, "breaker": 0.10, "random": 0.10}
HYPOTHESIS_MAX = 0.35
DEFAULT_ALLOCATION = {
    "unexplored": 0.35,
    "boundary": 0.20,
    "hypothesis": 0.20,
    "breaker": 0.15,
    "random": 0.10,
}
_PRIMES = (2, 3, 5, 7, 11)

# A region is saturated by sampling count only -- never by reached Level, score, status, or outcome.
SATURATION_TRIALS = 200
# Large deterministic stride so coverage spill lands in a genuinely different Halton location.
_RESAMPLE_STRIDE = 7919
# Focus-following lanes may still concentrate, but no more than this share of a burst in saturated cells.
SATURATED_FOCUS_SHARE = 0.15
_FOCUS_LANES = ("hypothesis", "boundary", "breaker")


def _load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    os.replace(tmp, path)


def cycle_slot(now: datetime) -> str:
    hour = now.astimezone(JST).hour
    return min(((3, "A"), (9, "B"), (15, "C"), (21, "D")), key=lambda x: min((hour-x[0]) % 24, (x[0]-hour) % 24))[1]


def _vdc(index: int, base: int) -> float:
    n, denom, out = max(1, int(index)), 1.0, 0.0
    while n:
        n, rem = divmod(n, base)
        denom *= base
        out += rem / denom
    return out


def _halton(index: int) -> list[float]:
    return [_vdc(index + 1, p) for p in _PRIMES]


def _lin(u: float, lo: float, hi: float) -> float:
    return lo + (hi - lo) * min(1.0, max(0.0, u))


def _log(u: float, lo: float, hi: float) -> float:
    return 10 ** _lin(u, math.log10(lo), math.log10(hi))


def _space() -> dict[str, Any]:
    return lab._load_search_space()


def _knobs(unit: list[float]) -> dict[str, float]:
    ss = _space(); ir, pr = ss["initial_state"], ss["physical_parameters"]
    return {
        "noise_amplitude": _log(unit[0], float(ir["noise_amplitude"]["min"]), float(ir["noise_amplitude"]["max"])),
        "correlation_length": _lin(unit[1], float(ir["correlation_length"]["min"]), float(ir["correlation_length"]["max"])),
        "diffusion_ratio": _log(unit[2], float(pr["diffusion_ratio"]["min"]), float(pr["diffusion_ratio"]["max"])),
        "drive_strength": _lin(unit[3], float(pr["drive_strength"]["min"]), float(pr["drive_strength"]["max"])),
        "quench_duration": _lin(unit[4], 4.0, 20.0),
    }


def _unit_from_knobs(k: dict[str, Any]) -> list[float]:
    ss = _space(); ir, pr = ss["initial_state"], ss["physical_parameters"]
    def ln(x, lo, hi):
        x = min(hi, max(lo, float(x))); return (math.log10(x)-math.log10(lo))/(math.log10(hi)-math.log10(lo))
    def li(x, lo, hi):
        x = min(hi, max(lo, float(x))); return (x-lo)/(hi-lo)
    return [
        ln(k.get("noise_amplitude", 1e-3), float(ir["noise_amplitude"]["min"]), float(ir["noise_amplitude"]["max"])),
        li(k.get("correlation_length", 1.0), float(ir["correlation_length"]["min"]), float(ir["correlation_length"]["max"])),
        ln(k.get("diffusion_ratio", 1.0), float(pr["diffusion_ratio"]["min"]), float(pr["diffusion_ratio"]["max"])),
        li(k.get("drive_strength", 1.0), float(pr["drive_strength"]["min"]), float(pr["drive_strength"]["max"])),
        li(k.get("quench_duration", 8.0), 4.0, 20.0),
    ]


def _seed(index: int, salt: str) -> int:
    return int(hashlib.sha256(f"{salt}|{index}".encode()).hexdigest()[:12], 16) % 1_000_000


def focus_from_report(report: dict[str, Any] | None) -> dict[str, Any] | None:
    facts = ((report or {}).get("headline") or {}).get("facts") or {}
    knobs = facts.get("knobs") or facts.get("overrides")
    if not isinstance(knobs, dict) or not knobs:
        return None
    return {"family": facts.get("family") or "white", "knobs": knobs, "source_event_id": ((report or {}).get("headline") or {}).get("event_id")}


def load_hypotheses() -> dict[str, Any]:
    return _load(_HYPOTHESES, {"version": 1, "hypotheses": [{
        "id": "dimension-specific-emergence",
        "statement": "Some start conditions can emerge more strongly when started directly in 3D than in 2D.",
        "counter_statement": "Any apparent 3D advantage disappears under paired comparisons or fresh seeds.",
        "falsification_condition": "Repeated paired trials show no positive 3D-minus-2D Level difference.",
        "status": "TESTING", "support": 0, "contradiction": 0, "support_cycles": [], "confidence": 0.5,
    }]})


def update_hypotheses(doc: dict[str, Any], *, burst_id: str, native_summary: dict[str, Any]) -> dict[str, Any]:
    positive = int(native_summary.get("dimension_emergence", 0)); paired = int(native_summary.get("paired_compared", 0))
    for h in doc.get("hypotheses", []):
        if h.get("id") != "dimension-specific-emergence": continue
        if positive:
            h["support"] = int(h.get("support", 0)) + positive
            cycles = set(h.get("support_cycles") or []); cycles.add(burst_id); h["support_cycles"] = sorted(cycles)
        h["contradiction"] = int(h.get("contradiction", 0)) + max(0, paired-positive)
        s, c = int(h.get("support", 0)), int(h.get("contradiction", 0))
        cap = 0.65 if len(h.get("support_cycles") or []) < 2 else 0.85
        h["confidence"] = round(min(cap, max(0.15, (s+1)/(s+c+2))), 4)
        h["status"] = "UNCERTAIN" if s >= 2 and c >= 2 else ("SUPPORTED" if s >= 2 else ("WEAKENED" if c >= 3 and s == 0 else "TESTING"))
    doc["last_updated_burst"] = burst_id; _save(_HYPOTHESES, doc); return doc


def _normalize(raw: dict[str, float]) -> dict[str, float]:
    a = dict(DEFAULT_ALLOCATION); a.update(raw)
    for k, floor in LANE_FLOORS.items(): a[k] = max(floor, float(a[k]))
    a["hypothesis"] = min(HYPOTHESIS_MAX, float(a["hypothesis"]))
    total = sum(max(0.0, x) for x in a.values()) or 1.0; a = {k: max(0.0, v)/total for k, v in a.items()}
    for k, floor in LANE_FLOORS.items(): a[k] = max(floor, a[k])
    a["hypothesis"] = min(HYPOTHESIS_MAX, a["hypothesis"])
    excess = sum(a.values()) - 1.0
    for k in ("boundary", "hypothesis", "unexplored"):
        reducible = max(0.0, a[k]-LANE_FLOORS.get(k, 0.0)); take = min(max(excess, 0.0), reducible); a[k] -= take; excess -= take
    if excess < 0: a["boundary"] += -excess
    total = sum(a.values()); return {k: round(v/total, 6) for k, v in a.items()}


def build_research_decision(*, previous_report: dict[str, Any] | None, hypotheses: dict[str, Any], cycle: str, burst_id: str, trials_2d: int, trials_3d: int) -> dict[str, Any]:
    current = next(iter(hypotheses.get("hypotheses") or []), None); belief = float((current or {}).get("confidence", 0.5))
    raw = dict(DEFAULT_ALLOCATION); counts = (previous_report or {}).get("counts") or {}
    if int(counts.get("new_behavior", 0)) + int(counts.get("reproduced", 0)) == 0:
        raw.update({"unexplored": raw["unexplored"]+0.05, "breaker": raw["breaker"]+0.05, "hypothesis": raw["hypothesis"]-0.05, "boundary": raw["boundary"]-0.05})
    if belief >= 0.65:
        raw.update({"breaker": raw["breaker"]+0.10, "random": raw["random"]+0.05, "hypothesis": raw["hypothesis"]-0.10, "boundary": raw["boundary"]-0.05})
    headline = (previous_report or {}).get("headline")
    observation = "No previous burst: start broad." if not headline else f"Previous: {headline.get('title')} — {headline.get('plain')}"
    return {
        "decision_version": 2, "burst_id": burst_id, "cycle": cycle, "observation": observation,
        "uncertainty": "A headline can overrepresent one rare event; counter-hypothesis and random lanes stay mandatory.",
        "current_hypothesis": current,
        "alternative_hypotheses": [
            {"id": "null", "statement": "The pattern is seed/sampling noise.", "test": "Fresh seeds and off-focus conditions."},
            {"id": "dimension-alternative", "statement": "The effect is dimension-specific.", "test": "Direct 3D first, paired 2D only afterwards."},
            {"id": "parameter-confound", "statement": "A correlated knob explains the apparent effect.", "test": "Boundary/complement search."},
        ],
        "focus": focus_from_report(previous_report),
        "next_plan": {"mass_2d_trials": int(trials_2d), "native_3d_trials": int(trials_3d), "allocation": _normalize(raw)},
        "anti_bias": {"hypothesis_budget_cap": HYPOTHESIS_MAX, "minimum_unexplored_fraction": 0.20, "minimum_assumption_breaker_fraction": 0.10, "minimum_random_fraction": 0.10, "stronger_belief_increases_challenge_budget": True, "single_cycle_confidence_cap": 0.65, "multi_cycle_confidence_cap": 0.85, "counter_hypothesis_required": True, "2d_failure_never_blocks_native_3d": True, "director_can_change_success_thresholds": False, "director_can_write_official_rooms": False},
    }


def _focus_trial(focus: dict[str, Any], index: int, width: float, invert: bool) -> tuple[str, dict[str, float], int]:
    rng = random.Random(_seed(index, f"focus-{width}-{invert}")); center = _unit_from_knobs(focus.get("knobs") or {})
    unit = [min(1.0, max(0.0, (1.0-c if invert else c) + rng.uniform(-width, width))) for c in center]
    family = focus.get("family") or "white"
    if invert:
        try: pos = lab.IC_FAMILIES.index(family)
        except ValueError: pos = 0
        family = lab.IC_FAMILIES[(pos+1) % len(lab.IC_FAMILIES)]
    return family, _knobs(unit), _seed(index, "focus-seed")


def plan_region_key(family: str, knobs: dict[str, float], dimension: str = "2d") -> str:
    """Coverage-atlas region of a not-yet-run trial; family + knobs are sufficient."""
    return _region({"family": family, "knobs": knobs}, dimension)


def saturated_regions(
    atlas: dict[str, Any], *, min_trials: int = SATURATION_TRIALS, dimension: str = "2d"
) -> set[str]:
    """Return over-sampled cells using sample count only, never a measured physical outcome."""
    return {
        key
        for key, cell in (atlas.get("regions") or {}).items()
        if cell.get("dimension") == dimension and int(cell.get("tested") or 0) >= int(min_trials)
    }


def _halton_trial(idx: int, master_seed: int, offset: int = 0) -> tuple[str, dict[str, float], int]:
    base = idx + master_seed + offset
    return lab.IC_FAMILIES[base % len(lab.IC_FAMILIES)], _knobs(_halton(base)), _seed(base, "halton")


def _cap_saturated_focus(
    plan: list[dict[str, Any]], *, saturated: set[str], n: int, master_seed: int
) -> list[dict[str, Any]]:
    """Cap focus-lane re-drilling of saturated cells without reading outcomes.

    Focus lanes are allowed to concentrate. Only overflow beyond the burst-wide cap becomes
    coverage sampling. The random floor is never redirected.
    """
    budget = max(1, int(n * SATURATED_FOCUS_SHARE))
    spent = 0
    out: list[dict[str, Any]] = []
    for row in plan:
        if row["lane"] in _FOCUS_LANES and plan_region_key(row["family"], row["knobs"]) in saturated:
            spent += 1
            if spent > budget:
                idx = int(row["trial_index"])
                family, knobs, seed = _halton_trial(idx, master_seed, _RESAMPLE_STRIDE)
                for attempt in range(2, 10):
                    if plan_region_key(family, knobs) not in saturated:
                        break
                    family, knobs, seed = _halton_trial(idx, master_seed, attempt * _RESAMPLE_STRIDE)
                out.append({
                    "family": family, "knobs": knobs, "seed": seed, "lane": "unexplored",
                    "trial_index": idx, "spilled_from_saturated_focus": row["lane"],
                })
                continue
        out.append(row)
    return out


def make_trial_plan(
    *, start_index: int, n: int, allocation: dict[str, float], focus: dict[str, Any] | None,
    master_seed: int, saturated: set[str] | None = None, max_resample: int = 8,
) -> list[dict[str, Any]]:
    lanes = list(DEFAULT_ALLOCATION)
    counts = {k: int(n * float(allocation.get(k, 0))) for k in lanes}
    counts["unexplored"] += n - sum(counts.values())
    out, idx = [], int(start_index)
    for lane in lanes:
        for _ in range(max(0, counts[lane])):
            resampled = 0
            if lane == "hypothesis" and focus:
                family, knobs, seed = _focus_trial(focus, idx, 0.10, False)
            elif lane == "boundary" and focus:
                family, knobs, seed = _focus_trial(focus, idx, 0.28, False)
            elif lane == "breaker" and focus:
                family, knobs, seed = _focus_trial(focus, idx, 0.20, True)
            elif lane == "random":
                rng = random.Random(_seed(idx + master_seed, "random"))
                family = lab.IC_FAMILIES[rng.randrange(len(lab.IC_FAMILIES))]
                knobs = _knobs([rng.random() for _ in range(5)])
                seed = rng.randrange(1_000_000)
            else:
                family, knobs, seed = _halton_trial(idx, master_seed)
                if saturated and lane == "unexplored":
                    for attempt in range(1, max(0, int(max_resample)) + 1):
                        if plan_region_key(family, knobs) not in saturated:
                            break
                        family, knobs, seed = _halton_trial(idx, master_seed, attempt * _RESAMPLE_STRIDE)
                        resampled = attempt
            row = {"family": family, "knobs": knobs, "seed": seed, "lane": lane, "trial_index": idx}
            if resampled:
                row["resampled_from_saturated"] = resampled
            out.append(row)
            idx += 1
    if saturated:
        out = _cap_saturated_focus(out, saturated=saturated, n=n, master_seed=master_seed)
    random.Random(master_seed ^ start_index ^ n).shuffle(out)
    return out


def _screen2d(tr: dict[str, Any]) -> dict[str, Any]:
    r = lab._screen_ic(tr["family"], tr["knobs"], int(tr["seed"]), quick=bool(tr["quick"])); return {**tr, **r}


def run_mass_2d(
    *, start_index: int, n: int, workers: int, allocation: dict[str, float], focus: dict[str, Any] | None,
    master_seed: int, quick: bool, saturated: set[str] | None = None,
) -> dict[str, Any]:
    plan = make_trial_plan(start_index=start_index, n=n, allocation=allocation, focus=focus,
                           master_seed=master_seed, saturated=saturated)
    payload = [{**x, "quick": bool(quick)} for x in plan]
    if workers <= 1:
        results = [_screen2d(x) for x in payload]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(_screen2d, payload, chunksize=max(1, len(payload)//(workers*8))))
    results.sort(key=lab._score_key, reverse=True)
    return {"results": results, "n": len(results), "next_index": start_index+len(payload),
            "redirected_from_saturated": sum(1 for x in plan if x.get("resampled_from_saturated")),
            "spilled_from_saturated_focus": sum(1 for x in plan if x.get("spilled_from_saturated_focus"))}


def _native3d(tr: dict[str, Any]) -> dict[str, Any]:
    g = copy.deepcopy(runner._DEMO_GENESIS); g["dimension"] = 3; g["seed"] = int(tr["seed"]); g["initial_state"] = dict(g["initial_state"]); g["protocol"] = {"quench": dict(g["protocol"]["quench"])}
    g["initial_state"]["noise_amplitude"] = float(tr["knobs"]["noise_amplitude"]); g["protocol"]["quench"]["duration"] = float(tr["knobs"]["quench_duration"])
    r = runner.run(g, mode="local-3d", quick=bool(tr["quick"])); m, e = r["manifest"], r["emergence"]; mb = e.get("measured_by") or {}; level = int(m["summary"].get("reached_level") or 0)
    score = level + min(math.log10(max(1.0, float(mb.get("mean_amplitude_growth") or 1.0)))/6.0, 1.0)*0.25 + min(float(mb.get("structure_factor_prominence") or 0.0)/10.0, 1.0)*0.20
    return {"trial_index": tr["trial_index"], "family": "uniform_plus_noise", "knobs": tr["knobs"], "seed": tr["seed"], "status": "native_3d_screened", "dimension": 3, "reached_level": level, "score": round(score,4), "measured_by": mb, "checksum": m["checksum"]["final_field_sha256"][:16]}


def run_native_3d(*, start_index: int, n: int, workers: int, master_seed: int, quick: bool) -> dict[str, Any]:
    ss = _space(); nr = ss["initial_state"]["noise_amplitude"]; payload = []
    for i in range(max(0,n)):
        idx = start_index+i; u = _halton(idx+master_seed); payload.append({"trial_index": idx, "knobs": {"noise_amplitude": _log(u[0], float(nr["min"]), float(nr["max"])), "quench_duration": _lin(u[1], 4.0, 20.0)}, "seed": _seed(idx+master_seed, "native3d"), "quick": bool(quick)})
    if workers <= 1: results = [_native3d(x) for x in payload]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool: results = list(pool.map(_native3d, payload, chunksize=max(1, len(payload)//(workers*8))))
    results.sort(key=lambda x: (x["reached_level"], x["score"]), reverse=True); return {"results": results, "n": len(results), "next_index": start_index+len(payload)}


def _paired2d(rec: dict[str, Any]) -> dict[str, Any]:
    g = copy.deepcopy(runner._DEMO_GENESIS); g["seed"] = int(rec["seed"]); g["initial_state"] = dict(g["initial_state"]); g["protocol"] = {"quench": dict(g["protocol"]["quench"])}; g["initial_state"]["noise_amplitude"] = rec["knobs"]["noise_amplitude"]; g["protocol"]["quench"]["duration"] = rec["knobs"]["quench_duration"]
    r = runner.run(g, mode="2d-screen", quick=True); l2 = int(r["manifest"]["summary"].get("reached_level") or 0); return {**rec, "paired_2d_level": l2, "dimension_delta": int(rec.get("reached_level") or 0)-l2}


def compare_native3d_top(results: list[dict[str, Any]], *, top: int, workers: int) -> list[dict[str, Any]]:
    selected = results[:max(0, top)]
    if workers <= 1: return [_paired2d(x) for x in selected]
    with ProcessPoolExecutor(max_workers=workers) as pool: return list(pool.map(_paired2d, selected))


def native3d_events(compared: list[dict[str, Any]], *, parent_level: int) -> list[dict[str, Any]]:
    out = []
    for r in compared:
        level, delta = int(r.get("reached_level") or 0), int(r.get("dimension_delta") or 0)
        if level < parent_level and delta <= 0: continue
        key = f"native3d|{r['trial_index']}|seed={r['seed']}"; dim = delta > 0
        out.append({"event_id": "evt-"+hashlib.sha256(f"NEW_BEHAVIOR|{key}".encode()).hexdigest()[:16], "kind": "NEW_BEHAVIOR", "source": "native-3d-discovery", "source_key": key, "title": "3Dから直接始めたときだけ深くなる挙動候補" if dim else "2Dを入口にせず3Dから直接見つかった候補", "plain": f"同条件で3Dは L{level}、後追い2D比較は L{r.get('paired_2d_level')} でした。" if dim else f"2D選別なしのNative 3D探索から L{level} を検出しました。", "why": "3Dは2D結果で選別していません。後追い2D比較は次元差の理解だけに使います。", "facts": {"dimension":3, "native_3d":True, "dimension_emergence":dim, "reached_level":level, "paired_2d_level":r.get("paired_2d_level"), "dimension_delta":delta, "knobs":r.get("knobs") or {}, "family":r.get("family"), "seed":r.get("seed"), "trial_index":r.get("trial_index"), "measured_by":r.get("measured_by") or {}, "checksum":r.get("checksum")}, "scientific_status": "native_3d_dimension_candidate" if dim else "native_3d_screened", "visual_interest":"high", "room_id":None, "parent_room":"room-g001-a", "view_preset_id":None})
    return out


def load_coverage() -> dict[str, Any]:
    return _load(_COVERAGE, {"version":1, "note":"Mundane/negative trials are aggregated by coarse region; no per-failure files.", "regions":{}, "totals":{"2d":0,"native_3d":0}})


def _bin(x: float, edges: list[float]) -> int:
    for i,e in enumerate(edges):
        if x <= e: return i
    return len(edges)


def _region(r: dict[str, Any], dim: str) -> str:
    k=r.get("knobs") or {}; return "|".join([dim, str(r.get("family") or "unknown"), f"n{_bin(math.log10(max(float(k.get('noise_amplitude',1e-3)),1e-12)),[-4.5,-4,-3.5,-3,-2.5])}", f"c{_bin(float(k.get('correlation_length',1)),[3,6,9])}", f"d{_bin(math.log10(max(float(k.get('diffusion_ratio',1)),1e-12)),[-.5,0,.5])}", f"r{_bin(float(k.get('drive_strength',1)),[1.5,2.5,3.5,4.5])}", f"q{_bin(float(k.get('quench_duration',8)),[6,10,14,18])}"])


def update_coverage(atlas: dict[str, Any], *, records: list[dict[str, Any]], dimension: str, burst_id: str) -> dict[str, Any]:
    regions=atlas.setdefault("regions",{}); totals=atlas.setdefault("totals",{}); totals[dimension]=int(totals.get(dimension,0))+len(records)
    for r in records:
        key=_region(r,dimension); c=regions.setdefault(key,{"dimension":dimension,"family":r.get("family"),"tested":0,"stable":0,"interesting":0,"best_level":None,"best_score":None,"last_burst":None}); c["tested"]+=1
        if r.get("status")!="unstable" and r.get("reached_level") is not None:
            c["stable"]+=1; level=int(r.get("reached_level") or 0); c["best_level"]=level if c["best_level"] is None else max(int(c["best_level"]),level); score=r.get("score"); c["best_score"]=score if c["best_score"] is None else max(float(c["best_score"]),float(score or 0)); c["interesting"] += int(level>=2)
        c["last_burst"]=burst_id
    atlas["last_burst"]=burst_id; return atlas


def save_coverage(atlas: dict[str, Any]) -> None: _save(_COVERAGE, atlas)


def coverage_progress(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {"regions_before":len(before.get("regions") or {}), "regions_after":len(after.get("regions") or {}), "new_regions":max(0,len(after.get("regions") or {})-len(before.get("regions") or {})), "total_2d_trials":int((after.get("totals") or {}).get("2d",0)), "total_native_3d_trials":int((after.get("totals") or {}).get("native_3d",0))}


def native_summary(results: list[dict[str, Any]], compared: list[dict[str, Any]]) -> dict[str, Any]:
    return {"trials":len(results), "best_level":max([int(r.get("reached_level") or 0) for r in results] or [0]), "paired_compared":len(compared), "dimension_emergence":sum(int(r.get("dimension_delta") or 0)>0 for r in compared), "same_or_weaker_than_2d":sum(int(r.get("dimension_delta") or 0)<=0 for r in compared)}


def record_native3d(events: list[dict[str, Any]], *, burst_id: str) -> None:
    doc=_load(_NATIVE3D,{"version":1,"note":"Only noteworthy direct-3D observations; mundane trials are in Coverage Atlas.","discoveries":[]}); by={e.get("event_id"):e for e in doc.get("discoveries",[]) if e.get("event_id")}
    for e in events: by[e["event_id"]]={**e,"burst_id":burst_id}
    doc["discoveries"]=sorted(by.values(),key=lambda e:(e.get("burst_id",""),e.get("event_id","")))[-500:]; doc["last_burst"]=burst_id; _save(_NATIVE3D,doc)


def progress_certificate(*, coverage: dict[str, Any], events: list[dict[str, Any]], native: dict[str, Any]) -> dict[str, Any]:
    reasons=[]
    if int(coverage.get("new_regions",0))>0: reasons.append(f"探索済み領域が {coverage['new_regions']} region 増えた")
    if any(e.get("kind")=="NEW_BEHAVIOR" for e in events): reasons.append("新しいBehavior候補を観測した")
    if any(e.get("kind")=="REPRODUCED" for e in events): reasons.append("別seedで再現した")
    if int(native.get("dimension_emergence",0))>0: reasons.append("2Dより3Dで深くなる次元差候補を観測した")
    if int(native.get("paired_compared",0))>0: reasons.append("Native 3D候補を後追い2D比較し次元仮説を更新した")
    return {"status":"ADVANCED" if reasons else "STALLED", "reasons":reasons or ["新情報を追加できなかった"], "stall_recovery_next":None if reasons else "Increase unexplored/random/breaker budgets and reduce hypothesis exploitation."}


def save_decision(decision: dict[str, Any], keep: int = 200) -> None:
    doc=_load(_DECISIONS,{"version":1,"decisions":[]}); by={d.get("burst_id"):d for d in doc.get("decisions",[]) if d.get("burst_id")}; by[decision["burst_id"]]=decision; doc["decisions"]=sorted(by.values(),key=lambda d:d.get("generated_at",d.get("burst_id","")))[-keep:]; doc["last_burst"]=decision["burst_id"]; _save(_DECISIONS,doc)
