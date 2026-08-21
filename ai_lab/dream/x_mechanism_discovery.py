"""Persistent mechanism dissection for mature recurrent anonymous X-patterns.

Recurrence and mechanism are different questions.  Once an X-pattern is mature, this lane stops treating
another raw occurrence as the main scientific gain and asks why the detector fires inside the simulator.
It adds scale-normalized diagnostics and controlled start-side interventions with paired fresh-seed
controls.  Historical X fingerprints are never changed, so old X identities remain comparable.

Intervened runs are exploratory mechanism evidence, not strict-zero evidence.  No target X, morphology,
vortex, location, event time or desired result is seeded.  A repeatable intervention effect is at most a
simulator sensitivity/mechanism candidate; it is not a new physical law or a causal claim about nature.
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

# Baselines are always present.  The non-baseline interventions rotate across bursts, so a bounded
# production budget eventually covers every listed factor instead of permanently starving the tail.
_INTERVENTIONS = (
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

_SUPPORTED = {
    "SUPPORTED_SIMULATOR_EXPLANATION",
    "SUPPORTED_SIMULATOR_SENSITIVITY_CANDIDATE",
}


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


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
            counts[str(pid)] = max(counts.get(str(pid), 0), int(row.get("observations", 0) or 0))
    return counts


def _runs_since_pattern(ledger: dict[str, Any], pattern_id: str) -> int:
    history = [row for row in (ledger.get("history") or []) if isinstance(row, dict)]
    positions = [i for i, row in enumerate(history) if str(row.get("pattern_id")) == pattern_id]
    if not positions:
        return len(history) + 1
    return max(0, len(history) - 1 - positions[-1])


def _select_focus() -> tuple[str, dict[str, Any], int] | None:
    """Prefer unresolved mature X, but periodically revisit supported explanations for falsification."""
    unknown = _read(_UNKNOWN, {"patterns": {}})
    ledger = _read(_LEDGER, {"patterns": {}, "history": []})
    observations = _observation_counts()
    candidates: list[tuple[tuple[int, int, int, int, str], str, dict[str, Any], int]] = []
    for pid, row in (unknown.get("patterns") or {}).items():
        if not isinstance(row, dict):
            continue
        focus = row.get("search_focus") or {}
        if not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        exact = row.get("exact") or {}
        local = row.get("local") or {}
        recurrent_hits = int(exact.get("hit", 0) or 0) + int(local.get("hit", 0) or 0)
        obs = max(
            int(observations.get(str(pid), 0) or 0),
            int(exact.get("n", 0) or 0),
            recurrent_hits,
        )
        if obs <= 0 and recurrent_hits < 2:
            continue
        entry = ((ledger.get("patterns") or {}).get(str(pid)) or {})
        mech_status = str(entry.get("status") or "UNRESOLVED")
        supported = mech_status in _SUPPORTED
        holdout_due = bool(supported and _runs_since_pattern(ledger, str(pid)) >= 6)
        unresolved = not supported
        source_status = str(row.get("status") or "")
        mature_broad = bool(source_status == "REPEATED_NONSPECIFIC" and obs >= 100)
        # Holdout-due supported claims receive the strongest pressure; otherwise unresolved questions
        # lead, with mature broad patterns ahead of mere count growth.
        tier = 2 if holdout_due else (1 if unresolved else 0)
        key = (tier, int(mature_broad and unresolved), obs, recurrent_hits, str(pid))
        candidates.append((key, str(pid), row, obs))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, pid, row, obs = candidates[0]
    return pid, row, obs


def _rotating_interventions(entry: dict[str, Any], count: int) -> list[tuple[str, float, str]]:
    if count <= 0:
        return []
    cursor = int(entry.get("intervention_cursor", 0) or 0) % len(_INTERVENTIONS)
    return [_INTERVENTIONS[(cursor + i) % len(_INTERVENTIONS)] for i in range(count)]


def _specs(
    *,
    pattern_id: str,
    focus: dict[str, Any],
    burst_id: str,
    budget: int,
    entry: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build paired-control probes.

    Two fresh IC seeds are generated for the burst.  Every intervention reuses one of those IC seeds,
    which reduces seed-to-seed confounding when comparing the intervention with its control.  Fresh means
    fresh relative to prior bursts, not a deliberately different seed for control and intervention.
    """
    family = str(focus.get("family") or "")
    if not family or budget <= 0:
        return []
    base = _clip_knobs(focus.get("knobs") or {})
    n_baseline = min(2, max(1, int(budget)))
    baseline_seeds = [_seed(burst_id, pattern_id, "paired-control", i) for i in range(n_baseline)]
    rows: list[dict[str, Any]] = []
    for i, seed in enumerate(baseline_seeds):
        rows.append({
            "family": family,
            "knobs": dict(base),
            "seed": seed,
            "quick": True,
            "intervention": f"baseline-{i}",
            "intervened_knob": None,
            "factor": 1.0,
            "paired_control_seed": seed,
            "target_pattern_seeded": False,
            "target_shape_seeded": False,
        })
    remaining = max(0, int(budget) - len(rows))
    for i, (knob, factor, label) in enumerate(_rotating_interventions(entry or {}, remaining)):
        varied = dict(base)
        varied[knob] = varied[knob] * float(factor)
        varied = _clip_knobs(varied)
        paired_seed = baseline_seeds[i % len(baseline_seeds)]
        rows.append({
            "family": family,
            "knobs": varied,
            "seed": paired_seed,
            "quick": True,
            "intervention": label,
            "intervened_knob": knob,
            "factor": float(factor),
            "paired_control_seed": paired_seed,
            "target_pattern_seeded": False,
            "target_shape_seeded": False,
        })
    return rows


def _safe_log_ratio(after: float, before: float) -> float:
    floor = 1e-15
    return float(math.log(max(float(after), floor) / max(float(before), floor)))


def _classify_event(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    event_time: float,
    quench_duration: float,
    known_context: list[str] | None = None,
) -> dict[str, Any]:
    """Shadow-diagnose ``amp_std:+L`` after dividing out the overall amplitude scale."""
    mean_before = max(float(before.get("mean_amp", 0.0)), 1e-15)
    mean_after = max(float(after.get("mean_amp", 0.0)), 1e-15)
    std_before = max(float(before.get("amp_std", 0.0)), 1e-15)
    std_after = max(float(after.get("amp_std", 0.0)), 1e-15)
    cv_before = std_before / mean_before
    cv_after = std_after / mean_after
    mean_log_gain = _safe_log_ratio(mean_after, mean_before)
    std_log_gain = _safe_log_ratio(std_after, std_before)
    cv_log_gain = _safe_log_ratio(cv_after, cv_before)
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
        "known_context": list(known_context or []),
    }


def _target_event_metrics(
    probe: dict[str, Any], pattern_id: str, *, max_episodes: int = 5
) -> tuple[list[dict[str, Any]], list[str]]:
    episodes = open_ended.detect_episodes(probe, max_episodes=max(1, int(max_episodes)))
    snaps = list(probe.get("snapshots") or [])
    metrics: list[dict[str, Any]] = []
    qd = float((probe.get("knobs") or {}).get("quench_duration", 0.0))
    for episode in episodes:
        if str(episode.get("pattern_id")) != str(pattern_id):
            continue
        t = float(episode.get("physical_time", 0.0))
        idx = next((i for i, snap in enumerate(snaps) if abs(float(snap.get("physical_time", -1.0)) - t) <= 1e-9), None)
        if idx is None or idx <= 0:
            continue
        metrics.append(_classify_event(
            snaps[idx - 1],
            snaps[idx],
            event_time=t,
            quench_duration=qd,
            known_context=list(episode.get("known_context") or []),
        ))
    other = [str(ep.get("pattern_id")) for ep in episodes if str(ep.get("pattern_id")) != str(pattern_id)]
    return metrics, other


def _mean_or_none(total: float, n: int) -> float | None:
    return None if n <= 0 else float(total) / float(n)


def _paired_sensitivity(entry: dict[str, Any]) -> dict[str, Any] | None:
    effects: list[dict[str, Any]] = []
    for label, stat in (entry.get("intervention_stats") or {}).items():
        if label == "baseline":
            continue
        paired_n = int(stat.get("paired_n", 0) or 0)
        if paired_n < 4:
            continue
        delta = float(stat.get("paired_hit_delta_sum", 0.0) or 0.0) / paired_n
        effects.append({
            "intervention": label,
            "knob": stat.get("knob"),
            "factor": stat.get("factor"),
            "paired_n": paired_n,
            "paired_hit_rate_delta": round(delta, 4),
        })
    effects.sort(key=lambda row: abs(float(row["paired_hit_rate_delta"])), reverse=True)
    if effects and abs(float(effects[0]["paired_hit_rate_delta"])) >= 0.25:
        return effects[0]
    return None


def _recent_scale_share(entry: dict[str, Any], n: int = 12) -> tuple[int, float]:
    recent = list(entry.get("recent_events") or [])[-max(1, int(n)):]
    if not recent:
        return 0, 0.0
    scale = sum(str(row.get("explanation_class")) == "AMPLITUDE_SCALE_TRACKING" for row in recent)
    return len(recent), scale / len(recent)


def _derive_status(
    entry: dict[str, Any], *, prior_status: str = "UNRESOLVED"
) -> tuple[str, str, dict[str, Any] | None]:
    counts = entry.get("event_classes") or {}
    events = int(entry.get("target_events", 0) or 0)
    seeds = int(entry.get("unique_fresh_seed_groups", 0) or 0)
    scale = int(counts.get("AMPLITUDE_SCALE_TRACKING", 0) or 0)
    hetero = int(counts.get("RELATIVE_HETEROGENEITY_GROWTH", 0) or 0)
    scale_share = 0.0 if events <= 0 else scale / events
    hetero_share = 0.0 if events <= 0 else hetero / events
    mean_cv = _mean_or_none(float(entry.get("sum_amp_cv_log_gain", 0.0) or 0.0), events)
    sensitivity = _paired_sensitivity(entry)

    recent_n, recent_scale = _recent_scale_share(entry)
    if prior_status in _SUPPORTED and recent_n >= 8 and recent_scale < 0.50:
        return (
            "WEAKENED_SIMULATOR_EXPLANATION",
            "以前支持された説明に対し、最近のholdoutでは同じ特徴が十分残っていません。失敗を消さず、説明を再び未解決側へ戻します。",
            sensitivity,
        )

    if events >= 20 and seeds >= 10 and scale_share >= 0.80 and mean_cv is not None and abs(mean_cv) <= math.log(1.10):
        status = "SUPPORTED_SIMULATOR_EXPLANATION"
        plain = "amp_std増加の大半は平均振幅の増加に追随し、尺度で割ったamp_cvはほぼ増えていません。空間的不均一化より、シミュレータの全体振幅成長を検出器が拾う説明が強い候補です。"
    elif events >= 10 and seeds >= 6 and scale_share >= 0.70:
        status = "AMPLITUDE_SCALE_EFFECT_CANDIDATE"
        plain = "amp_std増加の多くが平均振幅増加と一緒に起き、amp_cvは比較的安定しています。単純な振幅スケール効果かをpaired controlで反証中です。"
    elif events >= 10 and seeds >= 6 and hetero_share >= 0.65:
        status = "RELATIVE_HETEROGENEITY_CANDIDATE"
        plain = "平均振幅で割ってもamp_cvが増える例が多く、単なる全体増幅だけでは説明しにくい候補です。"
    else:
        status = "UNRESOLVED"
        plain = "振幅スケール成長、相対的不均一化、複数機構の混在をまだ十分に切り分けられていません。"

    if sensitivity is not None and status == "SUPPORTED_SIMULATOR_EXPLANATION":
        status = "SUPPORTED_SIMULATOR_SENSITIVITY_CANDIDATE"
        plain += (
            f" paired-controlでは {sensitivity['intervention']} が出現率を動かす感度候補です。"
            "これはモデル内の候補であり、自然界の因果法則という意味ではありません。"
        )
    return status, plain, sensitivity


def _update_entry(
    entry: dict[str, Any],
    *,
    pattern_id: str,
    observations: int,
    burst_id: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    prior_status = str(entry.get("status") or "UNRESOLVED")
    entry.setdefault("pattern_id", pattern_id)
    entry["latest_observations"] = max(int(entry.get("latest_observations", 0) or 0), int(observations))
    entry["bursts"] = int(entry.get("bursts", 0) or 0) + 1
    entry["experiments"] = int(entry.get("experiments", 0) or 0) + len(rows)

    seed_groups = set(int(seed) for seed in (entry.get("fresh_seed_groups") or []))
    baseline_by_seed = {
        int(row["seed"]): bool(row.get("same_pattern_seen"))
        for row in rows
        if row.get("intervened_knob") is None
    }
    seed_groups.update(baseline_by_seed)
    stats = entry.setdefault("intervention_stats", {})
    baseline = stats.setdefault("baseline", {"n": 0, "hit": 0})
    for hit in baseline_by_seed.values():
        baseline["n"] = int(baseline.get("n", 0) or 0) + 1
        baseline["hit"] = int(baseline.get("hit", 0) or 0) + int(hit)

    classes = entry.setdefault("event_classes", {})
    phases = entry.setdefault("quench_phase_counts", {})
    recent = list(entry.get("recent_events") or [])
    for row in rows:
        if row.get("intervened_knob") is not None:
            label = str(row.get("intervention"))
            stat = stats.setdefault(label, {
                "knob": row.get("intervened_knob"),
                "factor": row.get("factor"),
                "n": 0,
                "hit": 0,
                "paired_n": 0,
                "paired_hit_delta_sum": 0.0,
            })
            hit = bool(row.get("same_pattern_seen"))
            stat["n"] = int(stat.get("n", 0) or 0) + 1
            stat["hit"] = int(stat.get("hit", 0) or 0) + int(hit)
            seed = int(row["seed"])
            if seed in baseline_by_seed:
                stat["paired_n"] = int(stat.get("paired_n", 0) or 0) + 1
                stat["paired_hit_delta_sum"] = float(stat.get("paired_hit_delta_sum", 0.0) or 0.0) + float(int(hit) - int(baseline_by_seed[seed]))
        for event in row.get("target_event_metrics") or []:
            name = str(event.get("explanation_class") or "MIXED_OR_UNRESOLVED")
            classes[name] = int(classes.get(name, 0) or 0) + 1
            phase = str(event.get("quench_phase") or "UNKNOWN")
            phases[phase] = int(phases.get(phase, 0) or 0) + 1
            entry["target_events"] = int(entry.get("target_events", 0) or 0) + 1
            entry["sum_amp_cv_log_gain"] = float(entry.get("sum_amp_cv_log_gain", 0.0) or 0.0) + float(event.get("amp_cv_log_gain", 0.0) or 0.0)
            entry["defect_change_events"] = int(entry.get("defect_change_events", 0) or 0) + int(bool(event.get("defect_count_changed")))
            recent.append({
                "burst_id": burst_id,
                "seed": row["seed"],
                "intervention": row["intervention"],
                **event,
            })

    entry["fresh_seed_groups"] = sorted(seed_groups)[-256:]
    entry["unique_fresh_seed_groups"] = len(seed_groups)
    entry["recent_events"] = recent[-64:]
    nonbaseline_count = max(0, len(rows) - len(baseline_by_seed))
    entry["intervention_cursor"] = (int(entry.get("intervention_cursor", 0) or 0) + nonbaseline_count) % len(_INTERVENTIONS)
    status, plain, sensitivity = _derive_status(entry, prior_status=prior_status)
    entry["status"] = status
    entry["leading_explanation"] = plain
    entry["leading_sensitivity_candidate"] = sensitivity
    entry["last_burst"] = burst_id
    entry["counts_as_strict_zero_evidence"] = False
    entry["fundamental_physical_law_claim"] = False
    entry["causal_claim_about_nature"] = False
    entry["historical_x_identity_changed"] = False
    return entry


def _next_question(entry: dict[str, Any]) -> str:
    status = str(entry.get("status") or "UNRESOLVED")
    sensitivity = entry.get("leading_sensitivity_candidate") or {}
    if status == "WEAKENED_SIMULATOR_EXPLANATION":
        return "holdoutで弱まった理由を残し、以前の支持を固定観念にせず、別説明と介入方向を再比較する。"
    if status == "UNRESOLVED":
        return "paired fresh-seed controlsと回転する一因子介入を続け、amp_std増加がamp_cv増加を伴うかを切り分ける。"
    if status == "AMPLITUDE_SCALE_EFFECT_CANDIDATE":
        return "平均振幅で正規化したときXの特徴が消えるかを別seed・別介入で反証し、単純な増幅を未知構造と誤認していないか確認する。"
    if status == "RELATIVE_HETEROGENEITY_CANDIDATE":
        return "相対的不均一化を壊す介入を優先し、diffusion・quench・初期相関長のどれが必要かを分離する。"
    if sensitivity:
        return f"{sensitivity.get('intervention')} のpaired効果を将来のholdout seedで再検証し、感度の向きと大きさが残るか壊しに行く。"
    return "支持された説明を定期holdoutで壊しに行きつつ、別の未解決Xにも機構探索を回す。"


def run_mechanism_discovery(
    *,
    burst_id: str,
    budget: int = 8,
    persist: bool = True,
    max_episodes: int = 5,
) -> dict[str, Any]:
    selected = _select_focus()
    if budget <= 0 or selected is None:
        out = {
            "version": 2,
            "mode": "persistent-x-mechanism-dissection",
            "burst_id": burst_id,
            "ran": False,
            "experiments": 0,
            "reason": "no-mature-recurrent-x-focus-or-budget",
            "policy": {
                "observation_count_is_not_goal": True,
                "counts_as_strict_zero_evidence": False,
                "target_pattern_seeded": False,
            },
        }
        if persist:
            _write(_REPORT, out)
        return out

    pattern_id, source_row, observations = selected
    focus = source_row.get("search_focus") or {}
    ledger = _read(_LEDGER, {"version": 2, "patterns": {}, "history": []})
    entry = (ledger.setdefault("patterns", {})).setdefault(pattern_id, {})
    specs = _specs(
        pattern_id=pattern_id,
        focus=focus,
        burst_id=burst_id,
        budget=budget,
        entry=entry,
    )
    results: list[dict[str, Any]] = []
    for spec in specs:
        probe = open_ended._probe(spec)
        metrics, other = _target_event_metrics(probe, pattern_id, max_episodes=max_episodes)
        results.append({
            "seed": int(spec["seed"]),
            "paired_control_seed": int(spec["paired_control_seed"]),
            "intervention": spec["intervention"],
            "intervened_knob": spec["intervened_knob"],
            "factor": spec["factor"],
            "same_pattern_seen": bool(metrics),
            "target_event_metrics": metrics,
            "other_pattern_ids": other,
            "zero_purity": probe.get("zero_purity"),
        })

    _update_entry(
        entry,
        pattern_id=pattern_id,
        observations=observations,
        burst_id=burst_id,
        rows=results,
    )
    next_question = _next_question(entry)
    entry["next_question"] = next_question
    target_events_this_burst = sum(len(row.get("target_event_metrics") or []) for row in results)
    out = {
        "version": 2,
        "mode": "persistent-x-mechanism-dissection",
        "burst_id": burst_id,
        "ran": True,
        "pattern_id": pattern_id,
        "source_recurrence_status": source_row.get("status"),
        "observations_seen": observations,
        "experiments": len(results),
        "target_events_this_burst": target_events_this_burst,
        "cumulative": {
            "bursts": entry.get("bursts"),
            "experiments": entry.get("experiments"),
            "target_events": entry.get("target_events", 0),
            "unique_fresh_seed_groups": entry.get("unique_fresh_seed_groups", 0),
            "event_classes": entry.get("event_classes") or {},
            "quench_phase_counts": entry.get("quench_phase_counts") or {},
            "intervention_stats": entry.get("intervention_stats") or {},
            "defect_change_events": entry.get("defect_change_events", 0),
        },
        "status": entry.get("status"),
        "leading_explanation": entry.get("leading_explanation"),
        "leading_sensitivity_candidate": entry.get("leading_sensitivity_candidate"),
        "next_question": next_question,
        "results": results,
        "policy": {
            "observation_count_is_not_goal": True,
            "after_mature_recurrence_prioritize_why": True,
            "periodic_supported_explanation_holdout": True,
            "paired_control_seed_design": True,
            "intervention_directions_rotate_across_bursts": True,
            "historical_x_fingerprint_schema_unchanged": True,
            "intervened_runs_are_exploratory": True,
            "counts_as_strict_zero_evidence": False,
            "target_pattern_seeded": False,
            "target_shape_seeded": False,
            "event_location_or_time_seeded": False,
            "new_physical_law_claim": False,
            "simulator_sensitivity_is_nature_causality_claim": False,
            "room_or_official_level_change_allowed": False,
        },
    }
    if persist:
        ledger["version"] = 2
        ledger["latest"] = {
            "burst_id": burst_id,
            "pattern_id": pattern_id,
            "status": entry.get("status"),
            "leading_explanation": entry.get("leading_explanation"),
            "leading_sensitivity_candidate": entry.get("leading_sensitivity_candidate"),
            "next_question": next_question,
            "counts_as_strict_zero_evidence": False,
        }
        history = list(ledger.get("history") or [])
        history.append({
            "burst_id": burst_id,
            "pattern_id": pattern_id,
            "observations_seen": observations,
            "experiments": len(results),
            "target_events": target_events_this_burst,
            "status": entry.get("status"),
            "sensitivity": entry.get("leading_sensitivity_candidate"),
        })
        ledger["history"] = history[-256:]
        ledger["policy"] = {
            "source_x_identity_is_immutable": True,
            "negative_and_weakened_results_are_preserved": True,
            "counts_as_strict_zero_evidence": False,
            "new_physical_law_claim": False,
        }
        _write(_LEDGER, ledger)
        _write(_REPORT, out)
    return out
