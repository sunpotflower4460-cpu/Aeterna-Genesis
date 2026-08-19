"""Persistent mechanism discovery for mature recurrent X-patterns.

This lane answers a different question from recurrence verification.  Once an unlabeled transition is
clearly recurrent, repeatedly counting it is no longer the main objective.  The lane asks *why the
fingerprint is being produced inside the simulator* and keeps testing candidate explanations across
fresh seeds and controlled start-side interventions.

The first target is deliberately conservative: distinguish a genuine increase in *relative spatial
heterogeneity* from the simpler possibility that ``amp_std`` rises mainly because the whole order-
parameter amplitude is growing after the TDGL quench.  The existing X identity is left untouched; the
scale-normalized diagnostics are a shadow analysis so historical X ids remain comparable.

No target pattern, morphology, vortex, location or event time is seeded.  A supported result is only a
simulator-level mechanism/explanation candidate.  It is not a new physical law or a claim about nature.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ai_lab.dream import open_ended

_REPO = Path(__file__).resolve().parents[2]
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_EMERGENCE = _REPO / "ai_lab" / "reports" / "emergence" / "latest.json"
_LEDGER = _REPO / "ai_lab" / "discoveries" / "x_mechanisms.json"
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "x_mechanism_latest.json"

_KNOB_RANGES = {
    "noise_amplitude": (1e-6, 0.02),
    "correlation_length": (1.0, 12.0),
    "diffusion_ratio": (0.1, 8.0),
    "drive_strength": (0.1, 5.0),
    "quench_duration": (4.0, 20.0),
}

# Ordered so even a small production budget tests the most direct TDGL mechanism controls first.
_INTERVENTIONS = (
    (None, 1.0, "fresh-seed-baseline"),
    (None, 1.0, "fresh-seed-baseline"),
    ("drive_strength", 0.55, "drive-weaker"),
    ("drive_strength", 1.55, "drive-stronger"),
    ("diffusion_ratio", 0.55, "diffusion-weaker"),
    ("diffusion_ratio", 1.65, "diffusion-stronger"),
    ("quench_duration", 0.60, "quench-faster"),
    ("quench_duration", 1.60, "quench-slower"),
    ("noise_amplitude", 0.35, "noise-lower"),
    ("noise_amplitude", 2.40, "noise-higher"),
    ("correlation_length", 0.65, "correlation-shorter"),
    ("correlation_length", 1.55, "correlation-longer"),
)


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _seed(*parts: Any) -> int:
    raw = "|".join(str(x) for x in parts).encode("utf-8")
    return int(hashlib.sha256(raw).hexdigest()[:12], 16) % 1_000_000_000 + 1


def _clip_knobs(knobs: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, (lo, hi) in _KNOB_RANGES.items():
        default = math.sqrt(lo * hi) if lo > 0 else (lo + hi) / 2.0
        out[name] = max(lo, min(hi, float(knobs.get(name, default))))
    return out


def _observation_counts() -> dict[str, int]:
    report = _read(_EMERGENCE, {})
    counts: dict[str, int] = {}
    for row in report.get("top_recurrent") or []:
        pid = row.get("pattern_id")
        if pid:
            counts[str(pid)] = max(counts.get(str(pid), 0), int(row.get("observations", 0)))
    return counts


def _mechanism_status(ledger: dict[str, Any], pattern_id: str) -> str:
    return str(((ledger.get("patterns") or {}).get(pattern_id) or {}).get("status") or "UNRESOLVED")


def _select_focus() -> tuple[str, dict[str, Any], int] | None:
    """Prefer mature broad X-patterns until their mechanism is resolved enough for holdout testing.

    This specifically prevents a huge nonspecific background transition from being ignored forever just
    because a smaller condition-specific X has a higher discovery priority.  Once a mature pattern has
    a supported simulator explanation, unresolved recurrent patterns can take the active slot.
    """
    unknown = _read(_UNKNOWN, {"patterns": {}})
    ledger = _read(_LEDGER, {"patterns": {}})
    observations = _observation_counts()
    candidates: list[tuple[tuple[int, int, int, str], str, dict[str, Any], int]] = []
    supported = {"SUPPORTED_SIMULATOR_EXPLANATION", "SUPPORTED_SIMULATOR_MECHANISM_CANDIDATE"}
    for pid, row in (unknown.get("patterns") or {}).items():
        focus = row.get("search_focus") or {}
        if not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        obs = int(observations.get(str(pid), 0))
        exact = row.get("exact") or {}
        local = row.get("local") or {}
        recurrent_hits = int(exact.get("hit", 0)) + int(local.get("hit", 0))
        if obs <= 0 and recurrent_hits < 2:
            continue
        status = str(row.get("status") or "")
        mech_status = _mechanism_status(ledger, str(pid))
        unresolved = int(mech_status not in supported)
        mature_broad = int(status == "REPEATED_NONSPECIFIC" and obs >= 100 and unresolved)
        # unresolved first, then mature broad background transitions, then the actual accumulated
        # observation count.  This keeps X-b991... under causal dissection instead of count-chasing.
        key = (unresolved, mature_broad, obs * 1000 + recurrent_hits, str(pid))
        candidates.append((key, str(pid), row, obs))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    _, pid, row, obs = candidates[0]
    return pid, row, obs


def _specs(*, pattern_id: str, focus: dict[str, Any], burst_id: str, budget: int) -> list[dict[str, Any]]:
    family = str(focus.get("family") or "")
    if not family or budget <= 0:
        return []
    base = _clip_knobs(focus.get("knobs") or {})
    rows: list[dict[str, Any]] = []
    for i, (knob, factor, label) in enumerate(_INTERVENTIONS[: max(0, int(budget))]):
        varied = dict(base)
        if knob is not None:
            varied[knob] = varied[knob] * float(factor)
            varied = _clip_knobs(varied)
        rows.append({
            "family": family,
            "knobs": varied,
            "seed": _seed(burst_id, pattern_id, label, i),
            "quick": True,
            "intervention": label,
            "intervened_knob": knob,
            "factor": float(factor),
            "target_pattern_seeded": False,
            "target_shape_seeded": False,
        })
    return rows


def _safe_log_ratio(after: float, before: float) -> float:
    floor = 1e-15
    return float(math.log(max(float(after), floor) / max(float(before), floor)))


def _classify_event(before: dict[str, Any], after: dict[str, Any], *, event_time: float,
                    quench_duration: float, known_context: list[str] | None = None) -> dict[str, Any]:
    """Classify what ``amp_std:+L`` means after removing the trivial amplitude scale.

    ``amp_cv = amp_std / mean_amp`` is deliberately *not* added to the historical X fingerprint.  It is
    a mechanism diagnostic only, so changing this code never re-labels old X observations.
    """
    mean_before = max(float(before.get("mean_amp", 0.0)), 1e-15)
    mean_after = max(float(after.get("mean_amp", 0.0)), 1e-15)
    std_before = max(float(before.get("amp_std", 0.0)), 1e-15)
    std_after = max(float(after.get("amp_std", 0.0)), 1e-15)
    cv_before = std_before / mean_before
    cv_after = std_after / mean_after
    mean_log_gain = _safe_log_ratio(mean_after, mean_before)
    std_log_gain = _safe_log_ratio(std_after, std_before)
    cv_log_gain = _safe_log_ratio(cv_after, cv_before)

    # 12% in log-space is intentionally modest: it separates simple multiplicative field growth from
    # an actual change in relative spatial contrast without pretending this heuristic is a truth gate.
    cv_tol = math.log(1.12)
    if std_log_gain > 0.0 and mean_log_gain > 0.0 and abs(cv_log_gain) <= cv_tol:
        explanation = "AMPLITUDE_SCALE_TRACKING"
    elif std_log_gain > 0.0 and cv_log_gain > cv_tol:
        explanation = "RELATIVE_HETEROGENEITY_GROWTH"
    elif std_log_gain > 0.0 and cv_log_gain < -cv_tol:
        explanation = "ABSOLUTE_GROWTH_WITH_RELATIVE_HOMOGENIZATION"
    else:
        explanation = "MIXED_OR_UNRESOLVED"

    qd = max(float(quench_duration), 1e-12)
    phase = "DURING_QUENCH" if float(event_time) <= qd * 1.05 else "POST_QUENCH"
    defect_before = float(before.get("defect_count", 0.0))
    defect_after = float(after.get("defect_count", 0.0))
    context = list(known_context or [])
    return {
        "explanation_class": explanation,
        "event_time": round(float(event_time), 8),
        "quench_phase": phase,
        "mean_amp_log_gain": round(mean_log_gain, 6),
        "amp_std_log_gain": round(std_log_gain, 6),
        "amp_cv_before": round(cv_before, 8),
        "amp_cv_after": round(cv_after, 8),
        "amp_cv_log_gain": round(cv_log_gain, 6),
        "high_amp_fraction_delta": round(float(after.get("high_amp_fraction", 0.0)) - float(before.get("high_amp_fraction", 0.0)), 6),
        "spectral_k_rms_delta": round(float(after.get("spectral_k_rms", 0.0)) - float(before.get("spectral_k_rms", 0.0)), 6),
        "spectral_entropy_delta": round(float(after.get("spectral_entropy", 0.0)) - float(before.get("spectral_entropy", 0.0)), 6),
        "gradient_rms_log_gain": round(_safe_log_ratio(float(after.get("gradient_rms", 0.0)) + 1e-15, float(before.get("gradient_rms", 0.0)) + 1e-15), 6),
        "defect_count_before": defect_before,
        "defect_count_after": defect_after,
        "defect_count_changed": bool(abs(defect_after - defect_before) >= 0.5),
        "known_context": context,
    }


def _target_event_metrics(probe: dict[str, Any], pattern_id: str, *, max_episodes: int = 5) -> tuple[list[dict[str, Any]], list[str]]:
    episodes = open_ended.detect_episodes(probe, max_episodes=max(1, int(max_episodes)))
    snaps = list(probe.get("snapshots") or [])
    metrics: list[dict[str, Any]] = []
    qd = float((probe.get("knobs") or {}).get("quench_duration", 0.0))
    for episode in episodes:
        if str(episode.get("pattern_id")) != str(pattern_id):
            continue
        t = float(episode.get("physical_time", 0.0))
        idx = next((i for i, s in enumerate(snaps) if abs(float(s.get("physical_time", -1.0)) - t) <= 1e-9), None)
        if idx is None or idx <= 0:
            continue
        metrics.append(_classify_event(
            snaps[idx - 1], snaps[idx], event_time=t, quench_duration=qd,
            known_context=list(episode.get("known_context") or []),
        ))
    other = [str(e.get("pattern_id")) for e in episodes if str(e.get("pattern_id")) != str(pattern_id)]
    return metrics, other


def _bucket(entry: dict[str, Any], name: str) -> dict[str, int]:
    stats = entry.setdefault("intervention_stats", {})
    return stats.setdefault(name, {"n": 0, "hit": 0})


def _mean_or_none(total: float, n: int) -> float | None:
    return None if n <= 0 else float(total) / float(n)


def _derive_status(entry: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    counts = entry.get("event_classes") or {}
    events = int(entry.get("target_events", 0))
    seeds = int(entry.get("unique_fresh_seeds", 0))
    scale = int(counts.get("AMPLITUDE_SCALE_TRACKING", 0))
    hetero = int(counts.get("RELATIVE_HETEROGENEITY_GROWTH", 0))
    scale_share = 0.0 if events <= 0 else scale / events
    hetero_share = 0.0 if events <= 0 else hetero / events
    mean_cv = _mean_or_none(float(entry.get("sum_amp_cv_log_gain", 0.0)), events)

    baseline = (entry.get("intervention_stats") or {}).get("baseline") or {"n": 0, "hit": 0}
    base_rate = None if int(baseline.get("n", 0)) <= 0 else int(baseline.get("hit", 0)) / int(baseline.get("n", 0))
    effects = []
    for knob, stat in (entry.get("intervention_stats") or {}).items():
        if knob == "baseline" or int(stat.get("n", 0)) <= 0 or base_rate is None:
            continue
        rate = int(stat.get("hit", 0)) / int(stat.get("n", 0))
        effects.append({"knob": knob, "n": int(stat.get("n", 0)), "hit_rate": round(rate, 4), "delta_from_baseline": round(rate - base_rate, 4)})
    effects.sort(key=lambda x: abs(float(x["delta_from_baseline"])), reverse=True)
    driver = None
    if effects and int(baseline.get("n", 0)) >= 4 and effects[0]["n"] >= 4 and abs(float(effects[0]["delta_from_baseline"])) >= 0.25:
        driver = effects[0]

    if events >= 20 and seeds >= 10 and scale_share >= 0.80 and mean_cv is not None and abs(mean_cv) <= math.log(1.10):
        status = "SUPPORTED_SIMULATOR_EXPLANATION"
        plain = "amp_std の増加の大半は平均振幅の増加に追随し、尺度で割った amp_cv はほぼ増えていません。『空間的不均一化』より、TDGL の振幅成長をX検出器が拾っている説明が強い候補です。"
    elif events >= 10 and seeds >= 6 and scale_share >= 0.70:
        status = "AMPLITUDE_SCALE_EFFECT_CANDIDATE"
        plain = "amp_std 増加の多くが平均振幅の増加と一緒に起き、amp_cv は比較的安定しています。単純な振幅スケール成長かどうかをfresh seedと介入で反証中です。"
    elif events >= 10 and seeds >= 6 and hetero_share >= 0.65:
        status = "RELATIVE_HETEROGENEITY_CANDIDATE"
        plain = "平均振幅で割っても amp_cv が増える例が多く、単なる全体振幅の成長だけでは説明しにくい候補です。空間構造・拡散・quenchとの関係を介入で切り分けます。"
    else:
        status = "UNRESOLVED"
        plain = "まだ単純な振幅スケール成長、相対的な空間不均一化、複数機構の混在を十分に切り分けられていません。"

    if driver is not None and status == "SUPPORTED_SIMULATOR_EXPLANATION":
        status = "SUPPORTED_SIMULATOR_MECHANISM_CANDIDATE"
        plain += f" さらに start-side 介入では {driver['knob']} が出現率を最も動かす候補になっています。これはシミュレータ内の因果候補であり、自然界の基本法則という意味ではありません。"
    return status, plain, driver


def _update_entry(entry: dict[str, Any], *, pattern_id: str, observations: int, burst_id: str,
                  rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry.setdefault("pattern_id", pattern_id)
    entry["latest_observations"] = max(int(entry.get("latest_observations", 0)), int(observations))
    entry["bursts"] = int(entry.get("bursts", 0)) + 1
    entry["experiments"] = int(entry.get("experiments", 0)) + len(rows)
    seeds = set(int(x) for x in (entry.get("fresh_seeds") or []))
    classes = entry.setdefault("event_classes", {})
    phases = entry.setdefault("quench_phase_counts", {})
    recent = list(entry.get("recent_events") or [])
    for row in rows:
        seeds.add(int(row["seed"]))
        key = "baseline" if row.get("intervened_knob") is None else str(row.get("intervened_knob"))
        stat = _bucket(entry, key)
        stat["n"] = int(stat.get("n", 0)) + 1
        stat["hit"] = int(stat.get("hit", 0)) + int(bool(row.get("same_pattern_seen")))
        for event in row.get("target_event_metrics") or []:
            name = str(event.get("explanation_class") or "MIXED_OR_UNRESOLVED")
            classes[name] = int(classes.get(name, 0)) + 1
            phase = str(event.get("quench_phase") or "UNKNOWN")
            phases[phase] = int(phases.get(phase, 0)) + 1
            entry["target_events"] = int(entry.get("target_events", 0)) + 1
            entry["sum_amp_cv_log_gain"] = float(entry.get("sum_amp_cv_log_gain", 0.0)) + float(event.get("amp_cv_log_gain", 0.0))
            entry["defect_change_events"] = int(entry.get("defect_change_events", 0)) + int(bool(event.get("defect_count_changed")))
            recent.append({"burst_id": burst_id, "seed": row["seed"], "intervention": row["intervention"], **event})
    entry["fresh_seeds"] = sorted(seeds)[-128:]
    entry["unique_fresh_seeds"] = len(seeds)
    entry["recent_events"] = recent[-64:]
    status, plain, driver = _derive_status(entry)
    entry["status"] = status
    entry["leading_explanation"] = plain
    entry["leading_driver_candidate"] = driver
    entry["last_burst"] = burst_id
    entry["fundamental_physical_law_claim"] = False
    entry["causal_claim_about_nature"] = False
    entry["historical_x_identity_changed"] = False
    return entry


def _next_question(entry: dict[str, Any]) -> str:
    status = str(entry.get("status") or "UNRESOLVED")
    driver = entry.get("leading_driver_candidate") or {}
    if status == "UNRESOLVED":
        return "fresh seed と drive / diffusion / quench の一因子介入を続け、amp_std の増加が amp_cv の増加を伴うかを切り分ける。"
    if status == "AMPLITUDE_SCALE_EFFECT_CANDIDATE":
        return "平均振幅で正規化したときXの特徴が消えるかを別seed・別介入で反証し、単純な増幅を未知構造と誤認していないか確認する。"
    if status == "RELATIVE_HETEROGENEITY_CANDIDATE":
        return "相対的不均一化を壊す介入を優先し、diffusion・quench・初期相関長のどれが必要かを分離する。"
    if driver:
        return f"{driver.get('knob')} の介入効果をholdout seedで再検証し、他のknobを同時に変えずに順位が残るか反証する。"
    return "支持された説明をholdout seedで定期的に壊しに行きつつ、次に大きい未解決Xへ機構探索を移す。"


def run_mechanism_discovery(*, burst_id: str, budget: int = 8, persist: bool = True,
                            max_episodes: int = 5) -> dict[str, Any]:
    selected = _select_focus()
    if budget <= 0 or selected is None:
        out = {
            "version": 1, "burst_id": burst_id, "ran": False, "experiments": 0,
            "reason": "no-mature-recurrent-x-focus-or-budget",
            "policy": {"observation_count_is_not_goal": True, "mechanism_dissection_continues_automatically": True},
        }
        if persist:
            _write(_REPORT, out)
        return out

    pattern_id, row, observations = selected
    focus = row.get("search_focus") or {}
    specs = _specs(pattern_id=pattern_id, focus=focus, burst_id=burst_id, budget=budget)
    results: list[dict[str, Any]] = []
    for spec in specs:
        probe = open_ended._probe(spec)
        metrics, other = _target_event_metrics(probe, pattern_id, max_episodes=max_episodes)
        results.append({
            "seed": int(spec["seed"]),
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "same_pattern_seen": bool(metrics),
            "target_event_metrics": metrics,
            "other_pattern_ids": other,
            "zero_purity": probe.get("zero_purity"),
        })

    ledger = _read(_LEDGER, {"version": 1, "patterns": {}, "history": []})
    entry = (ledger.setdefault("patterns", {})).setdefault(pattern_id, {})
    _update_entry(entry, pattern_id=pattern_id, observations=observations, burst_id=burst_id, rows=results)
    next_question = _next_question(entry)
    target_events_this_burst = sum(len(r.get("target_event_metrics") or []) for r in results)
    out = {
        "version": 1,
        "mode": "persistent-x-mechanism-dissection",
        "burst_id": burst_id,
        "ran": True,
        "pattern_id": pattern_id,
        "source_recurrence_status": row.get("status"),
        "observations_seen": observations,
        "experiments": len(results),
        "target_events_this_burst": target_events_this_burst,
        "cumulative": {
            "bursts": entry.get("bursts"),
            "experiments": entry.get("experiments"),
            "target_events": entry.get("target_events", 0),
            "unique_fresh_seeds": entry.get("unique_fresh_seeds", 0),
            "event_classes": entry.get("event_classes") or {},
            "quench_phase_counts": entry.get("quench_phase_counts") or {},
            "intervention_stats": entry.get("intervention_stats") or {},
            "defect_change_events": entry.get("defect_change_events", 0),
        },
        "status": entry.get("status"),
        "leading_explanation": entry.get("leading_explanation"),
        "leading_driver_candidate": entry.get("leading_driver_candidate"),
        "next_question": next_question,
        "results": results,
        "policy": {
            "observation_count_is_not_goal": True,
            "after_mature_recurrence_prioritize_why": True,
            "mechanism_dissection_continues_automatically": True,
            "supported_candidates_receive_holdout_falsification": True,
            "historical_x_fingerprint_schema_unchanged": True,
            "target_pattern_seeded": False,
            "target_shape_seeded": False,
            "event_location_or_time_seeded": False,
            "new_physical_law_claim": False,
            "simulator_mechanism_is_nature_causality_claim": False,
        },
    }
    if persist:
        ledger["latest"] = {
            "burst_id": burst_id, "pattern_id": pattern_id, "status": entry.get("status"),
            "leading_explanation": entry.get("leading_explanation"), "next_question": next_question,
        }
        history = list(ledger.get("history") or [])
        history.append({
            "burst_id": burst_id, "pattern_id": pattern_id, "observations_seen": observations,
            "experiments": len(results), "target_events": target_events_this_burst,
            "status": entry.get("status"), "driver": entry.get("leading_driver_candidate"),
        })
        ledger["history"] = history[-128:]
        _write(_LEDGER, ledger)
        _write(_REPORT, out)
    return out
