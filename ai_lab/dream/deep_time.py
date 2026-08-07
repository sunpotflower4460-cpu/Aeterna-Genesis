"""Bounded Deep-Time follow-up for relation-fission F-path frontier runs.

A short run that reaches F4 but not F5 is ambiguous: the relation may be truly stable, or the
observation may simply end too early.  This lane deterministically replays the SAME t=0 law/start
(family, knobs, seed) and keeps evolving that uninterrupted trajectory to a predeclared 4/16/64 tau
horizon.  It never starts from a hand-built triangle or from an extracted mid-run state.

Replay-from-t0 is used instead of serializing a shaped F4 state, preserving the causal claim.  The
underlying numerical trajectory is deterministic for a fixed implementation; reproducibility across
platforms remains a later integrity audit, not an assumption.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ai_lab import lab
from ai_lab.dream import fission_path
from ai_lab.dream import strict_geometry as strict
from genesis.diagnostics import geometry_events as geom
from genesis.diagnostics import measures
from genesis.models import ginzburg_landau as gl

_REPO = Path(__file__).resolve().parents[2]
_LEDGER = _REPO / "ai_lab" / "discoveries" / "deep_time_fission.json"
_LADDER = (4.0, 16.0, 64.0)


def _candidate_key(candidate: dict[str, Any]) -> str:
    raw = json.dumps({
        "family": candidate.get("family"),
        "knobs": candidate.get("knobs") or {},
        "seed": candidate.get("seed"),
    }, sort_keys=True, separators=(",", ":"))
    return "deep-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def next_effective_rung(*, tau_ref: float, base_physical_time: float, last_rung: float = 0.0) -> float | None:
    """Return the next ladder rung that actually extends beyond the ordinary observation window."""
    for rung in _LADDER:
        if rung <= last_rung + 1e-12:
            continue
        if rung * tau_ref <= base_physical_time * 1.05:
            continue
        return rung
    return None


def _load() -> dict[str, Any]:
    if _LEDGER.exists():
        try:
            return json.loads(_LEDGER.read_text())
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "version": 1,
        "note": "Deep-Time F-path evidence only; no official Level or body/cell division claim.",
        "leads": [],
    }


def _save(doc: dict[str, Any]) -> None:
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER.write_text(json.dumps(doc, indent=2, ensure_ascii=False))


def run_candidate(candidate: dict[str, Any], *, horizon_multiplier: float, quick: bool = True) -> dict[str, Any]:
    """Replay one frontier candidate from t=0 and continue it to a longer physical horizon."""
    edge, base_steps, nsnap = lab.STEPS_2D[bool(quick)]
    shape = (edge, edge)
    knobs = dict(candidate.get("knobs") or {})
    p = lab._apply_knobs(dict(gl.DEFAULTS), knobs)
    base_dt = float(p["dt"])
    nsub = lab._cfl_substeps(float(p["Du"]), base_dt, ndim=2)
    p["dt"] = base_dt / nsub
    tau_ref = max(float(knobs.get("quench_duration", p.get("quench_duration", 8.0))), 1e-9)
    base_physical_time = base_steps * base_dt
    target_physical_time = max(base_physical_time, float(horizon_multiplier) * tau_ref)
    macro_steps = int(math.ceil(target_physical_time / base_dt))
    total = macro_steps * nsub

    rng = np.random.default_rng(int(candidate["seed"]))
    psi = lab.make_ic(
        str(candidate["family"]), shape, float(p["noise_amplitude"]), rng,
        corr_len=float(knobs.get("correlation_length", 1.0)),
    )
    # Preserve approximately the same temporal sampling resolution as the ordinary geometry probe,
    # rather than keeping a fixed number of snapshots over a much longer run.
    base_total = base_steps * nsub
    snap_every = max(1, base_total // max(10, nsnap * 2))
    snapshots: list[dict[str, Any]] = []
    traj: list[dict[str, Any]] = []
    finite = True
    for t in range(total):
        psi = gl.step(psi, t * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            finite = False
            break
        if t % snap_every != 0 and t != total - 1:
            continue
        points = geom.vortex_points_2d(psi)
        _, prom = measures.structure_factor_peak(psi)
        defects = measures.winding_defect_count(psi)
        snapshots.append({
            "step": t,
            "points": points,
            "triad": geom.best_mutual_triad(points, shape),
            "triangle": geom.best_triangle(points, shape),
            "control": geom.best_control_triad(points, shape),
        })
        traj.append({"mean_amp": measures.mean_amplitude(psi), "sk_prom": prom, "defects": defects})

    reached_level = 0
    if traj:
        reached_level, _, _ = measures.assess_level(traj)
    relation_found = strict._persistent_anchor(snapshots, kind="relation", shape=shape)
    tri_found = strict._persistent_anchor(snapshots, kind="triangle", shape=shape)
    transition = (
        strict._triangle_transition_after(snapshots, int(tri_found[0]), tri_found[1], shape)
        if tri_found else {
            "balance_collapse_seen": False,
            "balance_collapse_step": None,
            "pre_split_instability_candidate": False,
            "persistent_split_seen": False,
            "persistent_split_step": None,
            "network_fission_candidate": False,
            "network_fission_is_biological_cell_division": False,
        }
    )
    probe = {
        "family": candidate["family"],
        "knobs": knobs,
        "seed": candidate["seed"],
        "reached_level": reached_level,
        "persistent_relation_seen": relation_found is not None,
        "triangle_seen": tri_found is not None,
        **transition,
    }
    path = fission_path.assess_probe(probe)
    return {
        "finite": finite,
        "candidate_key": _candidate_key(candidate),
        "family": candidate["family"],
        "seed": candidate["seed"],
        "tau_ref": tau_ref,
        "base_physical_time": base_physical_time,
        "requested_horizon_multiplier": float(horizon_multiplier),
        "target_physical_time": target_physical_time,
        "observed_physical_time": (len(range(total)) * p["dt"]) if finite else None,
        "replayed_from_time_zero": True,
        "midrun_shape_seeded": False,
        "reached_level_for_path_measurement": reached_level,
        "F_depth": int(path.get("depth", -1)),
        "F_code": path.get("depth_code"),
        "triangle_seen": bool(tri_found),
        "balance_collapse_seen": bool(transition.get("balance_collapse_seen")),
        "pre_split_instability_candidate": bool(transition.get("pre_split_instability_candidate")),
        "network_fission_candidate": bool(transition.get("network_fission_candidate")),
        "network_fission_is_biological_cell_division": False,
        "snapshot_count": len(snapshots),
    }


def register_and_run(
    *, burst_id: str, path_summary: dict[str, Any], max_leads: int = 1, quick: bool = True,
) -> dict[str, Any]:
    doc = _load()
    leads = doc.setdefault("leads", [])
    for candidate in path_summary.get("frontier_candidates") or []:
        if int(candidate.get("depth", -1)) < 4:
            continue
        key = _candidate_key(candidate)
        old = next((x for x in leads if x.get("lead_id") == key), None)
        if old is None:
            leads.append({
                "lead_id": key,
                "family": candidate.get("family"),
                "knobs": candidate.get("knobs") or {},
                "seed": candidate.get("seed"),
                "first_burst": burst_id,
                "last_seen_burst": burst_id,
                "baseline_F_depth": int(candidate.get("depth", 4)),
                "last_rung": 0.0,
                "status": "OPEN",
                "history": [],
            })
        else:
            old["last_seen_burst"] = burst_id
            old["baseline_F_depth"] = max(int(old.get("baseline_F_depth", 4)), int(candidate.get("depth", 4)))

    active = [x for x in leads if x.get("status") not in {"F7_OBSERVED", "STABLE_THROUGH_64TAU", "NUMERICALLY_UNSTABLE"}]
    active.sort(key=lambda x: (int(x.get("baseline_F_depth", 4)), -float(x.get("last_rung", 0.0))), reverse=True)
    selected = active[:max(0, int(max_leads))]
    summaries = []
    for lead in selected:
        tau = max(float((lead.get("knobs") or {}).get("quench_duration", 8.0)), 1e-9)
        base_steps = lab.STEPS_2D[bool(quick)][1]
        base_time = base_steps * float(gl.DEFAULTS["dt"])
        rung = next_effective_rung(tau_ref=tau, base_physical_time=base_time, last_rung=float(lead.get("last_rung", 0.0)))
        if rung is None:
            lead["status"] = "STABLE_THROUGH_64TAU"
            continue
        result = run_candidate(lead, horizon_multiplier=rung, quick=quick)
        lead["last_rung"] = rung
        lead["last_burst"] = burst_id
        lead.setdefault("history", []).append({
            "burst_id": burst_id,
            "rung": rung,
            "finite": result["finite"],
            "F_depth": result["F_depth"],
            "balance_collapse_seen": result["balance_collapse_seen"],
            "pre_split_instability_candidate": result["pre_split_instability_candidate"],
            "network_fission_candidate": result["network_fission_candidate"],
        })
        lead["history"] = lead["history"][-12:]
        if not result["finite"]:
            lead["status"] = "NUMERICALLY_UNSTABLE"
        elif result["F_depth"] >= 7:
            lead["status"] = "F7_OBSERVED"
        elif rung >= 64.0 and result["F_depth"] < 5:
            lead["status"] = "STABLE_THROUGH_64TAU"
        elif result["F_depth"] >= 5:
            lead["status"] = "TRANSITION_SEEN_VERIFYING"
        else:
            lead["status"] = "VERIFYING"
        summaries.append({"lead_id": lead["lead_id"], "status": lead["status"], **result})

    doc["last_burst"] = burst_id
    _save(doc)
    return {
        "registered_leads": len(leads),
        "selected_leads": len(selected),
        "results": summaries,
        "ladder_tau": list(_LADDER),
        "replay_is_uninterrupted_from_t0": True,
        "midrun_triangle_seeded": False,
        "official_level_effect": False,
        "body_or_cell_division_claim": False,
    }
