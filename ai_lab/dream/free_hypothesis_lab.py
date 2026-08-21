"""Free Hypothesis Lab: deliberately adventurous experiments kept outside strict-zero evidence.

This lane exists to discover *ideas*, not to prove Pure Genesis.  It is allowed to ask provocative
questions such as "what if energy is injected as a shell?", "what if the available region is circular?"
or "what if the environment is periodically driven?".  Those interventions may be useful precisely
because they are not neutral.  Their provenance is therefore explicit and they can never promote a
Room, assign an official Level, or count as strict-zero evidence.

What may flow back to the strict lane is an *abstract hypothesis* (energy scale, confinement, curvature,
time-scale separation, etc.).  The scaffolded geometry/outcome itself may not be copied back as proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from genesis.diagnostics import measures
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_EASY = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_DEEP = _REPO / "ai_lab" / "discoveries" / "deep_time_fission.json"
_DIRECTIONS = _REPO / "ai_lab" / "discoveries" / "ai_scientist_directions.json"
_LEDGER = _REPO / "ai_lab" / "discoveries" / "free_hypothesis_lab.json"
_REPORT_JSON = _REPO / "ai_lab" / "reports" / "easy" / "free_hypothesis_latest.json"
_REPORT_MD = _REPO / "ai_lab" / "reports" / "easy" / "free_hypothesis_latest.md"


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    title: str
    question: str
    rationale: str
    experiment_type: str
    provenance_class: str
    parameters: dict[str, Any]
    abstract_factor: str
    strict_transfer_question: str
    source: str = "evidence-aware-auto"


_LIBRARY: dict[str, dict[str, Any]] = {
    "uniform_energy_boost": {
        "title": "0全体へ一様に追加エネルギーを与える",
        "provenance_class": "DRIVEN_EXPLORATORY",
        "parameters": {"factor": 3.0},
        "abstract_factor": "energy_density_scale",
        "strict_transfer_question": "形を与えず初期揺らぎのエネルギー尺度だけを変えると同じ変化境界が現れるか",
    },
    "central_energy_pulse": {
        "title": "0の中心へ局所エネルギーを一度だけ入れる",
        "provenance_class": "GEOMETRY_SCAFFOLDED_EXPLORATORY",
        "parameters": {"radius": 0.22, "factor": 5.0},
        "abstract_factor": "localized_energy_concentration",
        "strict_transfer_question": "中心位置を指定せずランダムな局所エネルギー集中でも同じ機構が現れるか",
    },
    "annular_energy_shell": {
        "title": "0へリング状のエネルギー殻を入れる",
        "provenance_class": "GEOMETRY_SCAFFOLDED_EXPLORATORY",
        "parameters": {"radius": 0.50, "width": 0.09, "factor": 4.0},
        "abstract_factor": "curved_energy_interface",
        "strict_transfer_question": "リング形状を置かず、曲率を持つ界面が自発形成した場合にも同じ変化が起きるか",
    },
    "circular_confinement": {
        "title": "0が存在できる場所を円形に制限する",
        "provenance_class": "GEOMETRY_SCAFFOLDED_EXPLORATORY",
        "parameters": {"radius": 0.82},
        "abstract_factor": "confinement_and_boundary_curvature",
        "strict_transfer_question": "円を置かず、境界曲率や有限サイズだけが変化境界を支配するかをランダム境界ensembleで確認する",
    },
    "elliptic_confinement": {
        "title": "円ではなく楕円形の0領域にする",
        "provenance_class": "GEOMETRY_SCAFFOLDED_EXPLORATORY",
        "parameters": {"axis_x": 0.86, "axis_y": 0.58},
        "abstract_factor": "boundary_anisotropy",
        "strict_transfer_question": "特定形状を置かず、異方的な有限サイズ制約だけでも同じ差が残るか",
    },
    "periodic_global_drive": {
        "title": "環境エネルギーを周期的に揺らす",
        "provenance_class": "DRIVEN_EXPLORATORY",
        "parameters": {"amplitude": 0.45, "period": 7.0},
        "abstract_factor": "temporal_forcing_and_timescale_resonance",
        "strict_transfer_question": "外部周期を置かず、内部時定数の比だけで同様の周期・分岐が自発するか",
    },
    "single_random_energy_kick": {
        "title": "途中で一度だけランダムな場所へエネルギーを入れる",
        "provenance_class": "DRIVEN_EXPLORATORY",
        "parameters": {"time_fraction": 0.45, "radius": 0.16, "factor": 4.0},
        "abstract_factor": "response_to_local_perturbation",
        "strict_transfer_question": "外部キックなしでも内部揺らぎへの応答・修復・分岐の同じ統計が現れるか",
    },
    "radial_quench": {
        "title": "中心と外側でquench速度を変える",
        "provenance_class": "SPATIALLY_DRIVEN_EXPLORATORY",
        "parameters": {"contrast": 0.55},
        "abstract_factor": "spatial_quench_gradient",
        "strict_transfer_question": "空間パターンを指定せず、局所時定数の不均一だけで同様の組織化が起こるか",
    },
    "slow_quench": {
        "title": "非常にゆっくり環境を変える",
        "provenance_class": "DRIVEN_EXPLORATORY",
        "parameters": {"duration_factor": 2.5},
        "abstract_factor": "quench_timescale",
        "strict_transfer_question": "strictな一様開始のままquench時定数だけを変えた時にも同じ遷移が残るか",
    },
    "fast_quench": {
        "title": "急激に環境を変える",
        "provenance_class": "DRIVEN_EXPLORATORY",
        "parameters": {"duration_factor": 0.35},
        "abstract_factor": "quench_timescale",
        "strict_transfer_question": "strictな一様開始のまま急冷速度だけで未知遷移の頻度が変わるか",
    },
}


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _seed(*parts: Any) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16) % 1_000_000_000


def _top_unknown_focus() -> dict[str, Any]:
    doc = _read(_UNKNOWN, {"patterns": {}})
    rows = []
    for pid, raw in (doc.get("patterns") or {}).items():
        if not isinstance(raw, dict):
            continue
        focus = raw.get("search_focus") or {}
        if not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        exact = raw.get("exact") or {}
        contrast = raw.get("contrast") or {}
        en = int(exact.get("n", 0) or 0)
        er = 0.0 if en <= 0 else int(exact.get("hit", 0) or 0) / en
        cn = int(contrast.get("n", 0) or 0)
        cr = 0.0 if cn <= 0 else int(contrast.get("hit", 0) or 0) / cn
        bonus = 2.0 if raw.get("status") == "REPEATED_SPECIFIC_CANDIDATE" else 0.0
        rows.append((bonus + er - cr, pid, focus))
    if not rows:
        return {"pattern_id": None, "family": "white", "knobs": {}}
    rows.sort(reverse=True, key=lambda x: (x[0], x[1]))
    _, pid, focus = rows[0]
    return {"pattern_id": pid, "family": focus.get("family"), "knobs": dict(focus.get("knobs") or {})}


def _evidence_context() -> dict[str, Any]:
    easy = _read(_EASY, {})
    deep = _read(_DEEP, {})
    return {
        "top_unknown": _top_unknown_focus(),
        "pairs": int(easy.get("persistent_pair_seen", 0) or 0),
        "triads": int(easy.get("triad_local_energy_measured", 0) or 0),
        "energy_precedes_geometry": int(easy.get("energy_asymmetry_peak_preceded_geometry_collapse", 0) or 0),
        "triangle_split": int(easy.get("triangle_then_split", 0) or 0),
        "nontriangle_split": int(easy.get("nontriangle_then_split", 0) or 0),
        "deep_leads": len(deep.get("leads") or []),
    }


def _direction_hypotheses() -> list[Hypothesis]:
    doc = _read(_DIRECTIONS, {"directions": []})
    out: list[Hypothesis] = []
    for row in doc.get("directions") or []:
        if not isinstance(row, dict) or row.get("enabled") is False:
            continue
        kind = str(row.get("experiment_type") or "")
        if kind not in _LIBRARY:
            continue
        base = _LIBRARY[kind]
        params = dict(base["parameters"])
        params.update(row.get("parameters") or {})
        out.append(Hypothesis(
            hypothesis_id=str(row.get("id") or f"direction-{kind}"),
            title=str(row.get("title") or base["title"]),
            question=str(row.get("question") or base["title"]),
            rationale=str(row.get("rationale") or "AI Scientist direction note"),
            experiment_type=kind,
            provenance_class=str(base["provenance_class"]),
            parameters=params,
            abstract_factor=str(base["abstract_factor"]),
            strict_transfer_question=str(base["strict_transfer_question"]),
            source=str(row.get("author") or "ai-scientist-direction"),
        ))
    return out


def propose_hypotheses(*, max_hypotheses: int = 6) -> list[Hypothesis]:
    """Evidence-aware proposal policy. Ranking is planning-only and cannot change scientific truth."""
    ctx = _evidence_context()
    requested = _direction_hypotheses()
    order: list[tuple[str, str]] = []

    # Energy timing is unresolved/inconsistent -> aggressively perturb energy layouts, but only in sandbox.
    if ctx["triads"] > 0:
        order += [
            ("uniform_energy_boost", "局所エネルギー配置と関係崩壊の対応が一定しないため、まず総量と局在を分離する"),
            ("annular_energy_shell", "エネルギー総量ではなく曲率を持つ界面が関係形成へ効くかを見る"),
            ("single_random_energy_kick", "静的配置ではなく摂動への応答性そのものを調べる"),
        ]
    # Triangle has repeatedly failed to be uniquely special -> compare confinement/anisotropy rather than triangle shape.
    if ctx["triangle_split"] <= ctx["nontriangle_split"] or ctx["nontriangle_split"] > 0:
        order += [
            ("circular_confinement", "三角形そのものより全体の閉じ込め・境界曲率が効く可能性を試す"),
            ("elliptic_confinement", "円で差が出ても円固有なのか異方性/有限サイズなのかを分解する"),
        ]
    if ctx["deep_leads"] > 0:
        order += [
            ("periodic_global_drive", "長時間でのみ進む候補があるため、内部時定数と外部時定数の相互作用を探索する"),
            ("slow_quench", "時間を与えること自体が重要か、quench速度が重要かを切り分ける"),
            ("fast_quench", "slow対照として急冷側も同時に置く"),
        ]
    if ctx["top_unknown"].get("pattern_id"):
        order += [
            ("radial_quench", "条件依存Xがあるため、同じ平均条件でも空間的不均一で遷移がどう変わるかを見る"),
            ("central_energy_pulse", "局所集中が名無し遷移の引き金になるかを大胆に探索する"),
        ]

    seen = {h.experiment_type for h in requested}
    out = list(requested)
    for kind, rationale in order:
        if kind in seen:
            continue
        seen.add(kind)
        base = _LIBRARY[kind]
        out.append(Hypothesis(
            hypothesis_id=f"auto-{kind}",
            title=base["title"],
            question=base["title"] + "と、そこから生じる関係・欠陥・分岐はどう変わるか？",
            rationale=rationale,
            experiment_type=kind,
            provenance_class=base["provenance_class"],
            parameters=dict(base["parameters"]),
            abstract_factor=base["abstract_factor"],
            strict_transfer_question=base["strict_transfer_question"],
        ))
        if len(out) >= max(0, int(max_hypotheses)):
            break
    return out[: max(0, int(max_hypotheses))]


def _coords(shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    axis = np.linspace(-1.0, 1.0, shape[0])
    x, y = np.meshgrid(axis, axis, indexing="ij")
    return x, y, np.sqrt(x * x + y * y)


def _apply_initial_intervention(psi: np.ndarray, h: Hypothesis, rng: np.random.Generator) -> np.ndarray:
    x, y, r = _coords(psi.shape)
    p = h.parameters
    kind = h.experiment_type
    if kind == "uniform_energy_boost":
        return psi * float(p.get("factor", 3.0))
    if kind == "central_energy_pulse":
        radius = max(float(p.get("radius", 0.22)), 1e-3)
        envelope = np.exp(-(r / radius) ** 2)
        theta = rng.uniform(0.0, 2 * np.pi)
        return psi + float(p.get("factor", 5.0)) * np.std(psi) * envelope * np.exp(1j * theta)
    if kind == "annular_energy_shell":
        radius = float(p.get("radius", 0.50)); width = max(float(p.get("width", 0.09)), 1e-3)
        shell = np.exp(-((r - radius) / width) ** 2)
        theta = rng.uniform(0.0, 2 * np.pi)
        return psi + float(p.get("factor", 4.0)) * np.std(psi) * shell * np.exp(1j * theta)
    return psi


def _mask_for(h: Hypothesis, shape: tuple[int, int]) -> np.ndarray | None:
    x, y, r = _coords(shape)
    if h.experiment_type == "circular_confinement":
        return r <= float(h.parameters.get("radius", 0.82))
    if h.experiment_type == "elliptic_confinement":
        ax = max(float(h.parameters.get("axis_x", 0.86)), 1e-3)
        ay = max(float(h.parameters.get("axis_y", 0.58)), 1e-3)
        return (x / ax) ** 2 + (y / ay) ** 2 <= 1.0
    return None


def _eps_field(t: float, p: dict[str, float], h: Hypothesis, shape: tuple[int, int]) -> float | np.ndarray:
    base = gl.eps_of_t(t, p)
    if h.experiment_type == "periodic_global_drive":
        amp = float(h.parameters.get("amplitude", 0.45))
        period = max(float(h.parameters.get("period", 7.0)), 1e-3)
        return base + amp * math.sin(2.0 * math.pi * t / period)
    if h.experiment_type == "radial_quench":
        _, _, r = _coords(shape)
        contrast = float(h.parameters.get("contrast", 0.55))
        return base + contrast * np.tanh((0.55 - r) / 0.18)
    return base


def _custom_step(psi: np.ndarray, t: float, p: dict[str, float], h: Hypothesis) -> np.ndarray:
    eps = _eps_field(t, p, h, psi.shape)
    return psi + p["dt"] * (eps * psi - (np.abs(psi) ** 2) * psi + p["Du"] * gl.laplacian(psi))


def _run_one(h: Hypothesis, *, seed: int, quick: bool, base_family: str, base_knobs: dict[str, Any]) -> dict[str, Any]:
    edge, steps, nsnap = (40, 120, 16) if quick else (72, 360, 36)
    shape = (edge, edge)
    knobs = {
        "noise_amplitude": float(base_knobs.get("noise_amplitude", 1.0e-2)),
        "correlation_length": float(base_knobs.get("correlation_length", 1.0)),
        "diffusion_ratio": float(base_knobs.get("diffusion_ratio", 1.0)),
        "drive_strength": float(base_knobs.get("drive_strength", 1.0)),
        "quench_duration": float(base_knobs.get("quench_duration", 8.0)),
    }
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    if h.experiment_type == "slow_quench":
        p["quench_duration"] *= float(h.parameters.get("duration_factor", 2.5))
    elif h.experiment_type == "fast_quench":
        p["quench_duration"] *= float(h.parameters.get("duration_factor", 0.35))
    base_dt = p["dt"]
    nsub = lab._cfl_substeps(p["Du"], base_dt)
    p["dt"] = base_dt / nsub
    total = steps * nsub
    rng = np.random.default_rng(seed)
    # Free lab may start from scaffolded families. Provenance prevents this evidence from becoming strict.
    family = base_family if base_family in lab.IC_FAMILIES else "white"
    psi = lab.make_ic(family, shape, p["noise_amplitude"], rng, corr_len=knobs["correlation_length"])
    psi = _apply_initial_intervention(psi, h, rng)
    mask = _mask_for(h, shape)
    if mask is not None:
        psi = np.where(mask, psi, 0.0)
    kick_time = int(total * float(h.parameters.get("time_fraction", 0.45)))
    kick_done = False
    traj: list[dict[str, Any]] = []
    snap = max(1, total // nsnap)
    finite = True
    for i in range(total):
        t = i * p["dt"]
        psi = _custom_step(psi, t, p, h)
        if h.experiment_type == "single_random_energy_kick" and not kick_done and i >= kick_time:
            x, y, _ = _coords(shape)
            cx, cy = rng.uniform(-0.5, 0.5, 2)
            rr = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            radius = max(float(h.parameters.get("radius", 0.16)), 1e-3)
            theta = rng.uniform(0.0, 2 * np.pi)
            psi = psi + float(h.parameters.get("factor", 4.0)) * p["noise_amplitude"] * np.exp(-(rr / radius) ** 2) * np.exp(1j * theta)
            kick_done = True
        if mask is not None:
            psi = np.where(mask, psi, 0.0)
        if not np.all(np.isfinite(psi)):
            finite = False
            break
        if i % snap == 0 or i == total - 1:
            _, prom = measures.structure_factor_peak(psi)
            traj.append({
                "mean_amp": measures.mean_amplitude(psi),
                "sk_prom": prom,
                "defects": measures.winding_defect_count(psi),
            })
    if not finite or not traj:
        return {"finite": False, "seed": seed, "reason": "numerical_instability"}
    level, _, measured = measures.assess_level(traj)
    complexity = lab.spectral_complexity(psi)
    energy = gl.free_energy(psi, p)
    checksum = hashlib.sha256(np.ascontiguousarray(psi.view(np.float64)).tobytes()).hexdigest()[:16]
    return {
        "finite": True,
        "seed": seed,
        "raw_reference_level": int(level),
        "reference_score": lab.score_run(level, measured, complexity),
        "final_mean_amplitude": float(measures.mean_amplitude(psi)),
        "final_defect_count": int(measures.winding_defect_count(psi)),
        "final_structure_prominence": float(measures.structure_factor_peak(psi)[1]),
        "final_quench_independent_energy": float(energy),
        "spectral_complexity": float(complexity),
        "checksum": checksum,
        "measured_by": measured,
    }


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    vals = [float(r[key]) for r in rows if r.get("finite") and r.get(key) is not None and math.isfinite(float(r[key]))]
    return None if not vals else sum(vals) / len(vals)


def _summarize(h: Hypothesis, rows: list[dict[str, Any]], control: list[dict[str, Any]]) -> dict[str, Any]:
    metrics = ["raw_reference_level", "reference_score", "final_mean_amplitude", "final_defect_count",
               "final_structure_prominence", "final_quench_independent_energy", "spectral_complexity"]
    summary = {k: _mean(rows, k) for k in metrics}
    baseline = {k: _mean(control, k) for k in metrics}
    delta = {
        k: None if summary[k] is None or baseline[k] is None else round(float(summary[k]) - float(baseline[k]), 6)
        for k in metrics
    }
    magnitude = sum(abs(float(delta[k] or 0.0)) for k in ("raw_reference_level", "reference_score", "final_defect_count", "spectral_complexity"))
    return {
        **asdict(h),
        "runs": rows,
        "finite_runs": sum(bool(r.get("finite")) for r in rows),
        "mean_metrics": summary,
        "control_mean_metrics": baseline,
        "delta_vs_unmodified_control": delta,
        "orientation_priority_only": round(magnitude, 6),
        "counts_as_strict_zero_evidence": False,
        "may_change_room_or_official_level": False,
        "may_seed_new_strict_target": False,
        "interpretation": "探索用の介入実験。差が出ても、その介入自体が自然創発したとは主張しない。抽象的な機構仮説だけをstrict側で再検証する。",
    }


def run(*, max_hypotheses: int = 6, replicates: int = 3, seed: int = 0, quick: bool = True, persist: bool = True) -> dict[str, Any]:
    hypotheses = propose_hypotheses(max_hypotheses=max_hypotheses)
    ctx = _evidence_context()
    top = ctx["top_unknown"]
    family = str(top.get("family") or "white")
    knobs = dict(top.get("knobs") or {})

    control_h = Hypothesis(
        hypothesis_id="control-unmodified",
        title="同じ探索条件を介入なしで再実行",
        question="自由仮説の差は、単なるseed差ではないか？",
        rationale="全ての自由仮説にfresh-seed controlを置く",
        experiment_type="control",
        provenance_class="CONTROL_MATCHED_TO_FREE_LAB",
        parameters={},
        abstract_factor="none",
        strict_transfer_question="none",
    )
    control = [_run_one(control_h, seed=_seed(seed, "control", i), quick=quick, base_family=family, base_knobs=knobs)
               for i in range(max(1, int(replicates)))]
    summaries = []
    for h in hypotheses:
        rows = [_run_one(h, seed=_seed(seed, h.hypothesis_id, i), quick=quick, base_family=family, base_knobs=knobs)
                for i in range(max(1, int(replicates)))]
        summaries.append(_summarize(h, rows, control))
    summaries.sort(key=lambda x: float(x.get("orientation_priority_only") or 0.0), reverse=True)

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "version": 1,
        "mode": "free-hypothesis-exploratory-sandbox",
        "generated_at": now,
        "source_evidence_context": ctx,
        "matched_control_runs": control,
        "hypotheses": summaries,
        "top_hypothesis_for_next_question": summaries[0] if summaries else None,
        "strict_bridge": {
            "rule": "transfer abstract mechanism questions only; never transfer scaffolded morphology as evidence",
            "strict_zero_evidence_incremented": False,
            "room_promotion_allowed": False,
            "official_level_change_allowed": False,
            "free_hypothesis_failure_is_kept": True,
        },
        "honesty": {
            "free_lab_is_pure_genesis": False,
            "geometry_scaffold_is_emergent_geometry": False,
            "external_energy_is_self_generated_energy": False,
            "reference_level_is_official_level": False,
            "interesting_difference_is_causal_proof": False,
        },
    }
    if persist:
        old = _read(_LEDGER, {"version": 1, "runs": []})
        old.setdefault("runs", []).append({
            "generated_at": now,
            "source_pattern": top.get("pattern_id"),
            "top": None if not summaries else {
                "hypothesis_id": summaries[0]["hypothesis_id"],
                "experiment_type": summaries[0]["experiment_type"],
                "orientation_priority_only": summaries[0]["orientation_priority_only"],
                "abstract_factor": summaries[0]["abstract_factor"],
                "strict_transfer_question": summaries[0]["strict_transfer_question"],
            },
        })
        old["runs"] = old["runs"][-200:]
        _write(_LEDGER, old)
        _write(_REPORT_JSON, report)
        _REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Free Hypothesis Lab — latest",
            "",
            "これは **Pure/strict evidence ではありません**。大胆な介入から、strict側で試す次の問いを発見する sandbox です。",
            "",
        ]
        for i, row in enumerate(summaries, 1):
            lines += [
                f"## {i}. {row['title']}",
                f"- provenance: `{row['provenance_class']}`",
                f"- rationale: {row['rationale']}",
                f"- orientation priority: {row['orientation_priority_only']}",
                f"- strictへ戻す問い: {row['strict_transfer_question']}",
                f"- strict evidenceに数える: **NO**",
                "",
            ]
        _REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the separated Free Hypothesis exploratory laboratory")
    ap.add_argument("--max-hypotheses", type=int, default=6)
    ap.add_argument("--replicates", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    report = run(
        max_hypotheses=max(0, a.max_hypotheses),
        replicates=max(1, a.replicates),
        seed=a.seed,
        quick=a.quick,
        persist=not a.no_record,
    )
    top = report.get("top_hypothesis_for_next_question") or {}
    print(f"Free Hypothesis Lab: hypotheses={len(report.get('hypotheses') or [])} top={top.get('experiment_type')}")
    print("NOTE: free-lab results never count as strict-zero evidence or official Levels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
