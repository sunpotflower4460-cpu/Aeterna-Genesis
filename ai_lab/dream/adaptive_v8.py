"""Adaptive Dream v8: Pure Genesis R0 north-star integration.

v8 keeps every v7 experiment and scientific gate intact, then adds a separate root-level automatic
experimenter whose only physical starting hypothesis is R0 (distinguishability + relation + change).
The root layer cannot seed space, geometry, dimension, frequency, phase, vortex, life, neuron or brain.
It also annotates the shared hypothesis graph with R0 relevance so the *next* v7 portfolio favors
observation-first questions without weakening unexplored/breaker/random floors.

The autonomous frontier expander sits above those layers.  It treats the destination as fixed while
allowing methods and hypotheses to change: recurrent unknown transitions trigger mechanism tests,
deep F-reference candidates trigger start-side intervention studies, root laws trigger ablations, and
missing destination capabilities trigger requests for new measurement instruments.  None of those
planning actions can weaken scientific integrity or turn scaffolded experiments into Pure Genesis proof.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive
from ai_lab.dream import adaptive_loop as v3
from ai_lab.dream import adaptive_v7 as v7
from ai_lab.dream import dry_run
from ai_lab.dream import frontier_expander
from ai_lab.dream import human_report
from ai_lab.dream import hypothesis_evolution
from ai_lab.dream import portfolio_director
from ai_lab.dream import pure_genesis
from ai_lab.dream import root_integrity
from ai_lab.dream import why_gate
from ai_lab.dream.report import write_report

_REPO = Path(__file__).resolve().parents[2]
_PORTFOLIO = _REPO / "ai_lab" / "discoveries" / "hypothesis_portfolio.json"


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _root_seed(value: Any, *, burst_id: str) -> int:
    """Resolve the root-search sampling seed without turning it into a physical parameter.

    Production historically leaves ``--seed`` unspecified (None).  In that case derive a deterministic
    regulator seed from the burst id so successive bursts vary anonymous pair/sign sampling while a
    rerun of the same burst remains reproducible.
    """
    if value is not None:
        return int(value)
    digest = hashlib.sha256(str(burst_id).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def _refresh_final_observatory(enabled: bool) -> str | None:
    """Copy the *final* v8 report to the Observatory after all v8 enrichments are complete.

    Lower layers refresh the app before Pure Genesis, Root Integrity and human_summary are appended.
    v8 therefore deliberately performs one final presentation-only sync.  This never changes physics.
    """
    if not enabled:
        return None
    return v3._refresh_observatory()


def _root_summary(root: dict[str, Any]) -> dict[str, Any]:
    top = []
    for row in (root.get("top_laws") or [])[:5]:
        top.append({
            "id": row.get("id"),
            "operators": row.get("operators") or [],
            "coefficients": row.get("coefficients") or {},
            "axiom_cost": row.get("axiom_cost"),
            "status": row.get("status"),
            "planning_confidence": row.get("planning_confidence"),
            "priority": row.get("priority"),
            "raw_priority_before_root_integrity": row.get("raw_priority_before_root_integrity"),
            "regulator_robustness": row.get("regulator_robustness"),
            "observations": row.get("observations") or {},
            "root_integrity_flags": (row.get("root_integrity") or {}).get("flags") or [],
        })
    return {
        "version": root.get("version"),
        "mode": root.get("mode"),
        "root": root.get("root") or {},
        "research_question": root.get("research_question"),
        "law_trials": root.get("law_trials"),
        "sizes": root.get("sizes") or [],
        "steps": root.get("steps"),
        "top_laws": top,
        "why_gate": root.get("why_gate") or {},
        "root_integrity_audit": root.get("root_integrity_audit") or {},
        "observed_not_seeded": root.get("observed_not_seeded") or [],
        "not_claimed": root.get("not_claimed") or [],
        "brain_from_zero": root.get("brain_from_zero") or {},
        "honesty": root.get("honesty") or {},
        "full_root_report": "ai_lab/reports/easy/root_latest.json",
    }


def _enrich_easy(
    paths: dict[str, str], *, root_summary: dict[str, Any], frontier_summary: dict[str, Any],
) -> None:
    latest = Path(paths.get("latest") or "")
    if not latest.exists():
        return
    try:
        easy = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        return
    easy["pure_genesis_r0"] = root_summary
    easy["autonomous_frontier_expansion"] = frontier_summary
    easy["research_north_star"] = {
        "root_id": why_gate.ROOT_ID,
        "statement": why_gate.ROOT_STATEMENT,
        "reason": why_gate.ROOT_REASON,
        "all_new_root_physical_givens_require_why_chain": True,
        "brain_is_not_seeded_target": True,
        "root_integrity_uses_permutation_quotient": True,
        "destination_fixed_methods_adaptive": True,
        "scaffolded_parallel_experiments_may_inform_but_not_prove_pure_genesis": True,
        "note": "宇宙・生命・脳を別レシピとして置かず、R0から関係がどこまで階層化・再帰・成長・適応できるかを調べます。",
    }
    easy["human_summary"] = human_report.build_summary(easy)
    human_md = human_report.render_markdown(easy["human_summary"])

    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    latest.with_suffix(".md").write_text(human_md)
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    if paths.get("markdown"):
        Path(paths["markdown"]).write_text(human_md)


def run_adaptive_v8(
    *, root_law_trials: int = 24, root_sizes: tuple[int, ...] = (8, 12, 16),
    root_steps: int = 48, frontier_experiments: int = 24, **kwargs: Any,
) -> dict[str, Any]:
    base = v7.run_adaptive_v7(**kwargs)
    report = base["report"]
    burst_id = str(report.get("burst_id") or "unknown")
    persist = bool(kwargs.get("record", True))
    seed = _root_seed(kwargs.get("seed"), burst_id=burst_id)

    root = pure_genesis.run_root_research(
        burst_id=burst_id,
        law_trials=max(0, int(root_law_trials)),
        sizes=tuple(max(3, int(n)) for n in root_sizes) or (8,),
        steps=max(8, int(root_steps)),
        seed=seed,
        persist=persist,
    )
    # A raw relation-matrix result is not yet a physical result. Remove latent-label closure,
    # global-sign aliases and step-period overinterpretation before research priority is persisted.
    root = root_integrity.audit_report(root, persist=persist)
    root_summary = _root_summary(root)

    # The frontier expander reacts to the evidence that actually exists in this burst.  It is not an
    # F6->F7 script: absent F evidence simply donates budget to recurrent-X or root mechanism questions.
    frontier = frontier_expander.run_frontier_expansion(
        report=report,
        root_report=root,
        burst_id=burst_id,
        max_experiments=max(0, int(frontier_experiments)),
        persist=persist,
    )

    # Align existing research questions to R0 and inject the new falsifiable mechanism questions.
    # This is planning only. It cannot change measurements, official Levels, Rooms, or anti-bias floors.
    graph = hypothesis_evolution.load_graph()
    why_gate.annotate_graph(graph)
    frontier_expander.inject_planning_hypotheses(graph, frontier, burst_id=burst_id)
    why_gate.annotate_graph(graph)
    if persist:
        hypothesis_evolution._save(hypothesis_evolution._GRAPH, graph)

    portfolio = portfolio_director.build_portfolio(graph, hypothesis_budget=adaptive.HYPOTHESIS_MAX)
    if persist:
        _write(_PORTFOLIO, {**portfolio, "last_burst": burst_id})

    report["pure_genesis_r0"] = root_summary
    report["autonomous_frontier_expansion"] = frontier
    report["research_north_star"] = {
        "root_id": why_gate.ROOT_ID,
        "statement": why_gate.ROOT_STATEMENT,
        "reason": why_gate.ROOT_REASON,
        "destination": "R0から結果形状を与えず、宇宙・脳・種からの成長に必要な機能が自発的に成立するところまで進む。",
        "policy": "新しい物理的前提はR0へのWhy Chainを説明できない限りPure Genesisへ入れない。",
        "methods_and_hypotheses_may_change_freely": True,
        "destination_fixed_methods_adaptive": True,
        "scaffolded_parallel_experiments_allowed": True,
        "scaffolded_parallel_experiments_count_as_pure_genesis_proof": False,
        "root_integrity_uses_permutation_quotient": True,
        "changes_scientific_gate": False,
        "changes_official_level": False,
        "brain_is_seeded_target": False,
    }
    report["hypothesis_portfolio_v7"] = portfolio
    if isinstance(report.get("goal_mission_v7"), dict):
        report["goal_mission_v7"]["role_under_v8"] = "downstream_reference_mission_not_research_north_star"
    report.setdefault("honesty", {})["pure_genesis_R0_is_final_metaphysical_truth"] = False
    report["honesty"]["pure_genesis_adds_unexplained_physical_givens"] = False
    report["honesty"]["pure_genesis_numerical_regulators_are_physical_claims"] = False
    report["honesty"]["brain_from_zero_claimed_achieved"] = False
    report["honesty"]["root_sampling_seed_is_physical_parameter"] = False
    report["honesty"]["latent_relation_slot_labels_are_physical_entities"] = False
    report["honesty"]["raw_slot_graph_cycles_are_emergent_geometry"] = False
    report["honesty"]["human_report_changes_scientific_evidence"] = False
    report["honesty"]["frontier_expansion_changes_truth_gate"] = False
    report["honesty"]["frontier_expansion_seeds_target_outcome"] = False
    report["honesty"]["scaffolded_analogy_counts_as_pure_genesis_proof"] = False

    # Reader-facing prose is generated only after all scientific/root/frontier audits. It never
    # replaces technical JSON; it adds an orientation layer on top of the same evidence.
    report["human_summary"] = human_report.build_summary(report)

    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy(base["easy_paths"], root_summary=root_summary, frontier_summary=frontier)

    # v7/lower layers may have refreshed app/public/data before the v8-only fields above existed.
    # Re-copy only after the final human report is on disk so the Observatory and Markdown agree.
    final_refresh_error = _refresh_final_observatory(bool(kwargs.get("refresh_app", True)))
    if final_refresh_error:
        report["observatory_final_sync_warning"] = final_refresh_error
        Path(base["paths"]["latest"]).write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return base


def _parse_sizes(raw: str) -> tuple[int, ...]:
    rows = []
    for part in str(raw).split(","):
        part = part.strip()
        if part:
            rows.append(max(3, int(part)))
    return tuple(rows) or (8, 12, 16)


def build_parser():
    ap = v7.build_parser()
    ap.description = "Aeterna Adaptive Dream v8 — Pure Genesis R0 + autonomous frontier expansion"
    ap.add_argument("--root-law-trials", type=int, default=24)
    ap.add_argument("--root-sizes", default="8,12,16", help="comma-separated finite-size regulators")
    ap.add_argument("--root-steps", type=int, default=48)
    ap.add_argument("--frontier-experiments", type=int, default=24,
                    help="bounded extra mechanism/intervention budget chosen adaptively from current evidence")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    if a.no_record:
        dry_run.activate()
    result = run_adaptive_v8(
        trials=max(0, a.trials), native3d_trials=max(0, a.native3d_trials), workers=max(1, a.workers),
        repro_top=max(0, a.repro_top), repro_seeds=max(1, a.repro_seeds),
        compare_native3d_top=max(0, a.compare_native3d_top), geometry_top=max(0, a.geometry_top),
        geometry_broad=max(0, a.geometry_broad), native_variants=max(0, a.native_variants),
        max_jobs=max(0, a.max_jobs), seed=a.seed, quick=a.quick,
        record=not a.no_record, refresh_app=(not a.no_refresh_app and not a.no_record),
        followup_trials_2d=max(0, a.followup_trials_2d), followup_trials_3d=max(0, a.followup_trials_3d),
        followup_max_leads=max(0, a.followup_max_leads),
        fission_path_trials_2d=max(0, a.fission_path_trials_2d),
        fission_path_max_leads=max(0, a.fission_path_max_leads),
        deep_time_max_leads=max(0, a.deep_time_max_leads),
        open_ended_probes=max(0, a.open_ended_probes),
        open_ended_max_episodes=max(0, a.open_ended_max_episodes),
        unknown_followup_max_patterns=max(0, a.unknown_followup_max_patterns),
        max_synthesized_hypotheses=max(0, a.max_synthesized_hypotheses),
        root_law_trials=max(0, a.root_law_trials), root_sizes=_parse_sizes(a.root_sizes),
        root_steps=max(8, a.root_steps), frontier_experiments=max(0, a.frontier_experiments),
    )
    r = result["report"]
    root = r.get("pure_genesis_r0") or {}
    port = r.get("hypothesis_portfolio_v7") or {}
    frontier = r.get("autonomous_frontier_expansion") or {}
    critic = (root.get("root_integrity_audit") or {}).get("critic_questions") or []
    print(f"=== Aeterna Adaptive Dream v8: {r['burst_id']} ===")
    print(f"  R0: {why_gate.ROOT_STATEMENT}")
    print(f"  Pure Genesis laws={root.get('law_trials', 0)} top={len(root.get('top_laws') or [])}")
    print(f"  Why Gate accepted={int((root.get('why_gate') or {}).get('accepted', 0))} unexplained physical givens=0")
    print(f"  Root Integrity critic questions={len(critic)} permutation-quotient=True")
    print(f"  frontier mechanism experiments={int((frontier.get('budget') or {}).get('executed', 0))}")
    print(f"  shared portfolio active={len(port.get('active') or [])} runnable={port.get('runnable_focuses', 0)}")
    print("  NOTE: destination is fixed, methods are adaptive; target shapes/outcomes are never seeded as Pure Genesis evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
