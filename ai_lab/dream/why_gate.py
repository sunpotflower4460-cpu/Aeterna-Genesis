"""Pure Genesis R0 Why Gate.

The gate is a research-governance layer, not a physics gate.  It prevents new *physical givens*
from entering root-directed experiments without an explicit derivation from the current minimal root
assumption. Numerical regulators are allowed only when they are clearly labeled as computation rather
than physics and are varied in robustness checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ROOT_ID = "R0"
ROOT_STATEMENT = "何かと何かが区別可能になり、その関係が変わりうる"
ROOT_REASON = (
    "区別・関係・変化が一切なければ前後を区別できず、何らかの宇宙が『生まれる』出来事自体を定義できない。"
)

# These may be OBSERVED downstream, but they may not be supplied as unexplained root-level physical inputs.
FORBIDDEN_ROOT_GIVENS = {
    "space", "geometry", "dimension", "frequency", "phase", "wavelength", "torus", "vortex",
    "charge", "particle", "field", "energy_landscape", "boundary", "inside", "outside", "cell",
    "life", "dna", "gene", "inheritance", "neuron", "brain", "memory", "prediction", "consciousness",
    "target_shape", "target_morphology", "division_location", "division_time",
}

# Operators are not declared fundamental.  They are candidate constructions that use only information
# already available from R0.  A candidate law may use them, and the experiment then asks whether the
# construction explains more with fewer assumptions.
DERIVED_OPERATORS: dict[str, dict[str, Any]] = {
    "relation_self": {
        "why_chain": [ROOT_ID, "relation", "current relation can be compared with its next value"],
        "uses": ["relation"],
    },
    "relation_composition_2": {
        "why_chain": [ROOT_ID, "relation", "two relations sharing an intermediate distinction can be composed"],
        "uses": ["relation"],
    },
    "relation_contrast": {
        "why_chain": [ROOT_ID, "distinguishability", "relations can be compared, so a relation can differ from the undifferentiated relation average"],
        "uses": ["relation", "distinguishability"],
    },
    "relation_trend": {
        "why_chain": [ROOT_ID, "change", "successive relation changes can be compared without adding a new state variable"],
        "uses": ["relation", "change"],
    },
}

NUMERICAL_REGULATORS = {
    "finite_size", "step_count", "floating_precision", "gauge_normalization", "sampling_seed",
    "root_event_pair", "root_event_sign", "operator_coefficient_grid",
}


@dataclass(frozen=True)
class GateResult:
    accepted: bool
    reasons: tuple[str, ...]
    unexplained_physical_givens: tuple[str, ...]
    target_encoded: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "unexplained_physical_givens": list(self.unexplained_physical_givens),
            "target_encoded": self.target_encoded,
        }


def validate_proposal(proposal: dict[str, Any]) -> GateResult:
    """Reject unexplained physical givens and target-encoded root experiments.

    Expected proposal shape is deliberately simple::
      {"why_chain": ["R0", ...], "operators": [...], "givens": [{"name": ..., "kind": ...}],
       "target_encoded": false}

    ``kind`` must be one of root_axiom / derived / numerical_regulator / imposed_environment.
    ``imposed_environment`` is not accepted for Pure Genesis root experiments (it may still exist in
    other Aeterna worlds with an honest claim_excludes label).
    """
    reasons: list[str] = []
    unexplained: list[str] = []
    target = bool(proposal.get("target_encoded", False))
    chain = proposal.get("why_chain") or []
    if not isinstance(chain, list) or not chain or str(chain[0]) != ROOT_ID:
        reasons.append("why_chain_must_start_at_R0")

    for op in proposal.get("operators") or []:
        if str(op) not in DERIVED_OPERATORS:
            unexplained.append(f"operator:{op}")

    for raw in proposal.get("givens") or []:
        if isinstance(raw, str):
            raw = {"name": raw, "kind": "physical"}
        name = str(raw.get("name") or "")
        kind = str(raw.get("kind") or "")
        lname = name.lower()
        if kind == "root_axiom":
            if name not in {"distinguishability", "relation", "change"}:
                unexplained.append(name or "unnamed_root_axiom")
        elif kind == "derived":
            if not raw.get("why_chain"):
                unexplained.append(name or "unnamed_derived")
        elif kind == "numerical_regulator":
            if name not in NUMERICAL_REGULATORS:
                unexplained.append(f"numerical:{name}")
        else:
            # In the root experiment, an environment/physical ingredient cannot be merely declared.
            unexplained.append(name or "unnamed_physical_given")
        if lname in FORBIDDEN_ROOT_GIVENS and kind not in {"derived"}:
            target = True
            reasons.append(f"forbidden_root_given:{name}")

    if target:
        reasons.append("target_encoded_or_downstream_concept_was_supplied")
    if unexplained:
        reasons.append("unexplained_physical_given")
    return GateResult(not reasons, tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(unexplained)), target)


def root_alignment(node: dict[str, Any]) -> dict[str, Any]:
    """Annotate a planning hypothesis with R0 relevance without deciding scientific truth."""
    origin = str(node.get("origin") or "")
    statement = str(node.get("statement") or "").lower()
    if origin == "pure-genesis-root-law":
        score, cls = 1.0, "DIRECT_R0"
    elif origin in {"open-ended-x-pattern", "automatic-hypothesis"} or "x-pattern" in statement:
        score, cls = 0.90, "OBSERVATION_FIRST"
    elif origin == "automatic-branch":
        score, cls = 0.82, "OBSERVATION_DERIVED"
    elif origin == "human-reference-hypothesis":
        score, cls = 0.52, "DOWNSTREAM_REFERENCE"
    else:
        score, cls = 0.65, "UNCLASSIFIED_DERIVED"
    return {
        "root_id": ROOT_ID,
        "root_relevance": score,
        "root_alignment_class": cls,
        "root_alignment_is_truth_claim": False,
    }


def annotate_graph(graph: dict[str, Any]) -> dict[str, Any]:
    for node in (graph.get("nodes") or {}).values():
        node.update(root_alignment(node))
    graph.setdefault("policy", {})["requires_why_chain_for_new_root_physical_givens"] = True
    graph["policy"]["root_alignment_changes_scientific_gate"] = False
    return graph
