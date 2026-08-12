"""Strict Nothing Genesis (NØ) meta-control.

This module deliberately does *less* than Pure Genesis R0.

NØ is the question: if the physical side is given literally nothing, can a computation honestly report
that something physically emerged?  The strict arm therefore supplies no entities, slots, state space,
initial state, relation, transition rule, time/order, randomness, probability measure, possibility set,
geometry, energy, or observer.  It does not perform a hidden random draw and it does not call a zero
array "nothing".

That makes NØ a null/control experiment rather than a dynamical simulation.  With no transition
semantics there is no physical step to execute.  If this arm ever reports an object/event anyway, that
is treated as an implementation leak or an added assumption, never as ex-nihilo emergence.

The surrounding *meta* audit may enumerate many candidate "first givens" to map the boundary between
strict nothing and runnable models.  Those candidates are explicitly outside NØ and can never count as
"from nothing" evidence.  In particular, "all things can happen" would itself require at least a
possibility/admissibility structure (and a measure or rule if one outcome is sampled), so it is recorded
as a boundary hypothesis but is not smuggled into the strict arm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

_REPO = Path(__file__).resolve().parents[2]
_REPORT = _REPO / "ai_lab" / "reports" / "easy" / "nothing_latest.json"
_EASY_LATEST = _REPO / "ai_lab" / "reports" / "easy" / "latest.json"

# Candidate assumptions are audited only at the meta level.  None is injected into strict NØ.
FIRST_GIVEN_CANDIDATES: tuple[str, ...] = (
    "carrier_or_existence_domain",
    "entity_multiplicity",
    "identity",
    "distinguishability",
    "relation",
    "state_space",
    "initial_state",
    "change_possibility",
    "transition_rule_or_law",
    "ordering_or_time",
    "randomness",
    "probability_measure",
    "possibility_space_or_admissibility",
    "geometry_or_dimension",
    "energy_or_conservation_structure",
    "physical_observer_or_measurement_rule",
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _latest_burst_id() -> str:
    latest = _read(_EASY_LATEST, {})
    return str(latest.get("burst_id") or "unknown-burst")


def strict_nothing_control() -> dict[str, Any]:
    """Return the one strict NØ physical case.

    ``None`` and empty lists below are reporting symbols used by the meta-program.  They are not a
    physical zero field, vacuum, empty set of particles, latent canvas, or initialized state.
    """
    physical_layer = {
        "physical_givens": [],
        "entities_seeded": False,
        "entity_count_defined": False,
        "slots_defined": False,
        "identity_defined": False,
        "distinguishability_defined": False,
        "relations_defined": False,
        "state_space_defined": False,
        "initial_state_defined": False,
        "zero_field_defined": False,
        "vacuum_state_defined": False,
        "change_possibility_defined": False,
        "transition_rule_defined": False,
        "law_defined": False,
        "time_defined": False,
        "update_step_defined": False,
        "randomness_defined": False,
        "random_seed_defined": False,
        "probability_measure_defined": False,
        "possibility_space_defined": False,
        "geometry_defined": False,
        "dimension_defined": False,
        "energy_defined": False,
        "physical_observer_defined": False,
    }
    result = {
        "physical_transition_executed": False,
        "physical_event_defined": False,
        "something_observed": False,
        "outcome": "NO_PHYSICAL_DYNAMICS_DEFINED",
        "nothing_to_something_claim": False,
        "interpretation": (
            "何も物理前提を与えない場合、計算上の『次』そのものを定義できない。"
            "これは『無から何かは絶対に生まれない』という形而上学的証明ではなく、"
            "追加前提なしには計算実験として判定不能だという境界結果。"
        ),
    }
    return {
        "id": "NØ",
        "name": "strict-nothing",
        "strict_nothing": True,
        "physical_layer": physical_layer,
        "result": result,
        "meta_scaffolding": {
            "code_and_hardware_exist": True,
            "reporting_symbols_exist": True,
            "count_as_physical_givens": False,
            "note": "計算機・Python・JSONは観測装置側の足場であり、NØ内部の物理として数えない。",
        },
    }


def _iter_nonempty_subsets(names: tuple[str, ...]) -> Iterable[tuple[str, ...]]:
    n = len(names)
    for mask in range(1, 1 << n):
        yield tuple(names[i] for i in range(n) if mask & (1 << i))


def audit_first_given_boundary(names: tuple[str, ...] = FIRST_GIVEN_CANDIDATES) -> dict[str, Any]:
    """Exhaustively map candidate added-assumption combinations without running them as NØ physics."""
    if len(names) > 20:
        raise ValueError("boundary audit is intentionally capped at 20 named assumptions")
    digest = hashlib.sha256()
    by_size = {str(i): 0 for i in range(1, len(names) + 1)}
    singletons: list[list[str]] = []
    pair_examples: list[list[str]] = []
    total = 0
    for subset in _iter_nonempty_subsets(names):
        total += 1
        by_size[str(len(subset))] += 1
        digest.update(("|".join(subset) + "\n").encode("utf-8"))
        if len(subset) == 1:
            singletons.append(list(subset))
        elif len(subset) == 2 and len(pair_examples) < 32:
            pair_examples.append(list(subset))
    return {
        "mode": "meta-assumption-boundary-audit",
        "candidate_first_givens": list(names),
        "candidate_count": len(names),
        "nonempty_combinations_exhaustively_audited": total,
        "expected_nonempty_combinations": (1 << len(names)) - 1,
        "combinations_by_size": by_size,
        "canonical_enumeration_sha256": digest.hexdigest(),
        "single_assumption_frontier": singletons,
        "pair_examples": pair_examples,
        "every_nonempty_combination_is_strict_nothing": False,
        "every_nonempty_combination_counts_as_from_nothing_evidence": False,
        "purpose": "何かが出たように見えた時、どの『最初の与え物』を密輸したかを追跡するための境界地図。",
    }


def possibility_zero_boundary() -> dict[str, Any]:
    return {
        "id": "N0-P",
        "label": "全てが起きうる0",
        "strict_nothing": False,
        "instantiated_in_strict_arm": False,
        "why_not_identical_to_nothing": [
            "『起きうる』と言うには、少なくとも可能/不可能を区別する意味が要る。",
            "具体的な候補集合を置けば possibility_space が追加前提になる。",
            "その中から何かを選ぶなら、選択規則・確率測度・乱数などが追加前提になる。",
        ],
        "policy": (
            "N0-Pは境界仮説として記録するだけで、strict NØには可能性集合・乱数・法則を入れない。"
            "将来N0-Pを実装する場合も『無から』ではなく『可能性構造を1つ与えた最小モデル』と明記する。"
        ),
    }


def run_nothing_research(*, burst_id: str | None = None, persist: bool = True,
                         boundary_names: tuple[str, ...] = FIRST_GIVEN_CANDIDATES) -> dict[str, Any]:
    """Run the strict null control plus exhaustive meta-boundary audit.

    There is intentionally only one strict physical trial. Repeating it with seeds, sizes, clocks,
    fields or random draws would add structure and would therefore be a different experiment.
    Breadth comes from auditing all named first-given combinations *outside* the strict arm.
    """
    strict = strict_nothing_control()
    if strict["physical_layer"]["physical_givens"]:
        raise RuntimeError("NØ contamination: physical givens are not empty")
    if strict["result"]["something_observed"]:
        raise RuntimeError("NØ contamination: something appeared without a traceable added assumption")

    report = {
        "version": 1,
        "mode": "strict-nothing-genesis-meta-control",
        "burst_id": str(burst_id or _latest_burst_id()),
        "research_question": "本当に何も物理的に与えないとき、何かが生まれたと計算実験で言えるか。",
        "strict_trial_count": 1,
        "why_not_repeat_strict_trial_with_many_seeds": (
            "seed・試行回数・サイズ・時間・乱数をNØ内部に入れた瞬間、それは『何もない』ではなくなるため。"
        ),
        "strict_nothing": strict,
        "all_things_possible_zero": possibility_zero_boundary(),
        "first_given_boundary": audit_first_given_boundary(boundary_names),
        "comparison_to_R0": {
            "R0_is_downstream_of_NØ": True,
            "R0_adds": ["distinguishability", "relation", "change_possibility"],
            "R0_results_count_as_strict_nothing_results": False,
        },
        "claim_limits": {
            "proves_metaphysical_nothing_cannot_create_something": False,
            "proves_metaphysical_nothing_can_create_something": False,
            "computational_boundary_identified": True,
            "if_future_strict_arm_reports_something": "treat_as_hidden_assumption_or_software_bug_until_traced",
        },
    }
    if persist:
        _write(_REPORT, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Aeterna strict Nothing Genesis (NØ) control")
    ap.add_argument("--burst-id", default=None, help="defaults to ai_lab/reports/easy/latest.json burst_id")
    ap.add_argument("--no-record", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    r = run_nothing_research(burst_id=a.burst_id, persist=not a.no_record)
    b = r["first_given_boundary"]
    print(f"=== Nothing Genesis NØ: {r['burst_id']} ===")
    print("  strict physical givens=0; transition defined=False; something observed=False")
    print(f"  meta boundary combinations audited={b['nonempty_combinations_exhaustively_audited']}")
    print("  N0-P ('all things can happen') is boundary-only, not injected into strict nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
