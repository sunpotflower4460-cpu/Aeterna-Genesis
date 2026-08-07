"""Multi-World Dream shadow director.

The production Dream Loop is currently g001-heavy.  This module runs beside it and samples several
physically different Worlds without influencing promotions, official Levels, hypothesis confidence or
broad-search allocation.  It is the first safe step toward a true cross-law research director.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from genesis.worlds.integrity import audit_plan
from genesis.worlds.probes import probe_world
from genesis.worlds.registry import list_worlds
from genesis.worlds.time_horizon import HorizonPlan, default_tau_ref
from genesis.worlds.zero_registry import list_zeros

DEFAULT_SHADOW_PAIRS = (
    ("g001-tdgl", "Z-A"),
    ("g001-tdgl", "Z-B"),
    ("g003-model-h", "Z-A"),
    ("o3-vector", "Z-A"),
    ("q2-nematic", "Z-A"),
)


def _event_index(observations: list[dict[str, Any]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for obs in observations:
        for event in obs.get("events") or []:
            out.setdefault(str(event), []).append(f"{obs['world_id']}@{obs['zero_id']}")
    return {k: sorted(v) for k, v in sorted(out.items())}


def build_shadow_report(*, seed: int = 0, quick: bool = True, pairs=None) -> dict[str, Any]:
    pairs = tuple(pairs or DEFAULT_SHADOW_PAIRS)
    observations: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for i, (world_id, zero_id) in enumerate(pairs):
        try:
            observations.append(probe_world(world_id, zero_id=zero_id, seed=seed + i * 1009, quick=quick))
        except Exception as exc:  # shadow lane must report adapter failures instead of affecting main research
            errors.append({"world_id": world_id, "zero_id": zero_id, "error": f"{type(exc).__name__}: {exc}"})

    horizons = {}
    for world_id, _ in pairs:
        if world_id in horizons:
            continue
        tau = default_tau_ref(world_id)
        horizons[world_id] = {
            "tau_ref": tau,
            "multipliers": [1.0, 4.0, 16.0, 64.0],
            "physical_times": list(HorizonPlan(tau).physical_times()),
        }

    worlds = [w.to_dict() for w in list_worlds()]
    zeros = [z.to_dict() for z in list_zeros()]
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "shadow",
        "purpose": "Cross-law observation without changing official science gates or the g001 discovery budget.",
        "pairs": [{"world_id": w, "zero_id": z} for w, z in pairs],
        "observations": observations,
        "errors": errors,
        "cross_world_event_index": _event_index(observations),
        "world_registry": worlds,
        "zero_registry": zeros,
        "deep_time_policy": horizons,
        "physics_integrity_audit_plan": audit_plan(solver_alternative_available=False),
        "director_policy": {
            "promotion_effect": False,
            "official_level_effect": False,
            "hypothesis_confidence_effect": False,
            "reduces_existing_broad_exploration": False,
            "single_success_score_across_worlds": False,
            "future_budget_floors": {
                "unexplored_world_zero_pairs": 0.40,
                "frontier": 0.20,
                "breaker_null": 0.15,
                "numerical_integrity": 0.15,
                "deep_time": 0.10,
            },
        },
        "interpretation_guard": (
            "Different laws expose different observables. Shared event labels are candidate fingerprints only; "
            "they are not evidence of identical physics or universality until independent audits pass."
        ),
    }


def write_shadow_report(report: dict[str, Any], output: str) -> str:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna Multi-World Dream shadow observer")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--output", default="ai_lab/reports/multiworld/latest.json")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    report = build_shadow_report(seed=a.seed, quick=a.quick)
    out = write_shadow_report(report, a.output)
    print("=== Multi-World Genesis shadow ===")
    print(f"  probes={len(report['observations'])} errors={len(report['errors'])}")
    for obs in report["observations"]:
        print(f"  {obs['world_id']} {obs['zero_id']}: finite={obs['finite']} events={','.join(obs.get('events') or ['none'])}")
    print(f"  report={out}")
    print("  NOTE: shadow mode cannot promote, change official Levels, or alter hypothesis confidence.")
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
