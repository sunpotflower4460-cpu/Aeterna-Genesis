"""Adaptive Dream v7: hypothesis evolution + mission-aware research portfolio.

v7 wraps v6 rather than replacing it.  Existing open-ended discovery, X-pattern verification,
F-reference, Deep-Time, local-energy and anti-bias lanes remain intact.  v7 adds a hypothesis graph,
evidence cards, bounded automatic branching, deterministic hypothesis synthesis and a portfolio plan.
Scientific truth gates are unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive
from ai_lab.dream import adaptive_loop as v3
from ai_lab.dream import adaptive_v6 as v6
from ai_lab.dream import evidence_cards
from ai_lab.dream import goal_engine
from ai_lab.dream import hypothesis_evolution
from ai_lab.dream import hypothesis_synthesizer
from ai_lab.dream import portfolio_director
from ai_lab.dream.report import write_report

_REPO = Path(__file__).resolve().parents[2]
_UNKNOWN = _REPO / "ai_lab" / "discoveries" / "unknown_followups.json"
_PORTFOLIO = _REPO / "ai_lab" / "discoveries" / "hypothesis_portfolio.json"
_GOAL_PROGRESS = _REPO / "ai_lab" / "discoveries" / "goal_progress.json"


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False))


def _enrich_easy(paths: dict[str, str], *, report: dict[str, Any]) -> None:
    latest = Path(paths.get("latest") or "")
    if not latest.exists():
        return
    try:
        easy = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        return
    evo = report.get("hypothesis_evolution_v7") or {}
    goal = report.get("goal_mission_v7") or {}
    portfolio = report.get("hypothesis_portfolio_v7") or {}
    easy["hypothesis_evolution_v7"] = {
        "nodes": evo.get("nodes"),
        "changes": evo.get("changes"),
        "automatic_branches": evo.get("automatic_branches"),
        "new_proposals": evo.get("new_proposals"),
        "note": "仮説の強弱・枝分かれは次の研究配分を決めるためのもの。科学的真実や公式Levelを変更しません。",
    }
    easy["goal_mission_v7"] = goal
    easy["hypothesis_portfolio_v7"] = {
        "active": portfolio.get("active"),
        "anti_bias": portfolio.get("anti_bias"),
    }
    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))


def run_adaptive_v7(*, max_synthesized_hypotheses: int = 3, **kwargs: Any) -> dict[str, Any]:
    base = v6.run_adaptive_v6(**kwargs)
    report = base["report"]
    burst_id = str(report.get("burst_id") or "unknown")
    persist = bool(kwargs.get("record", True))

    legacy = adaptive.load_hypotheses()
    unknown = _read(_UNKNOWN, {"version": 1, "patterns": {}})
    cards = evidence_cards.build_cards(report=report, legacy_hypotheses=legacy, unknown_followups=unknown)
    evolved = hypothesis_evolution.evolve(
        legacy=legacy,
        unknown=unknown,
        cards=cards,
        burst_id=burst_id,
        persist=persist,
    )
    graph = evolved["graph"]

    proposals = hypothesis_synthesizer.propose_from_unknown(
        unknown,
        burst_id=burst_id,
        max_proposals=max(0, int(max_synthesized_hypotheses)),
    )
    hypothesis_synthesizer.insert_proposals(graph, proposals, burst_id=burst_id)
    if persist:
        hypothesis_evolution._save(hypothesis_evolution._GRAPH, graph)

    portfolio = portfolio_director.build_portfolio(graph, hypothesis_budget=adaptive.HYPOTHESIS_MAX)
    if persist:
        _write(_PORTFOLIO, {**portfolio, "last_burst": burst_id})

    contract = goal_engine.load_contract()
    goal = goal_engine.evaluate(report, contract)
    if persist:
        _write(_GOAL_PROGRESS, {**goal, "last_burst": burst_id})

    automatic_branches = [
        n.get("id") for n in (graph.get("nodes") or {}).values()
        if n.get("origin") == "automatic-branch" and n.get("created_burst") == burst_id
    ]
    report["hypothesis_evolution_v7"] = {
        "version": 1,
        "mode": "planning-layer",
        "nodes": len(graph.get("nodes") or {}),
        "edges": len(graph.get("edges") or []),
        "changes": evolved.get("changes") or [],
        "automatic_branches": automatic_branches,
        "new_proposals": [p.get("id") for p in proposals],
        "evidence_cards": len(cards),
        "quarantined_evidence_has_zero_weight": True,
        "changes_scientific_gate": False,
        "changes_official_level": False,
        "writes_official_rooms": False,
    }
    report["hypothesis_portfolio_v7"] = portfolio
    report["goal_mission_v7"] = goal
    report.setdefault("honesty", {})["hypothesis_graph_confidence_is_scientific_truth_probability"] = False
    report["honesty"]["goal_mission_seeds_target_morphology"] = False
    report["honesty"]["F7_alone_counts_as_biological_cell_division"] = False
    report["honesty"]["hypothesis_synthesizer_can_change_scientific_gate"] = False

    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy(base["easy_paths"], report=report)
    return base


def build_parser():
    ap = v6.build_parser()
    ap.description = "Aeterna Adaptive Dream v7 — hypothesis evolution + mission-aware portfolio"
    ap.add_argument("--max-synthesized-hypotheses", type=int, default=3)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    result = run_adaptive_v7(
        trials=max(0, a.trials), native3d_trials=max(0, a.native3d_trials), workers=max(1, a.workers),
        repro_top=max(0, a.repro_top), repro_seeds=max(1, a.repro_seeds),
        compare_native3d_top=max(0, a.compare_native3d_top), geometry_top=max(0, a.geometry_top),
        geometry_broad=max(0, a.geometry_broad), native_variants=max(0, a.native_variants),
        max_jobs=max(0, a.max_jobs), seed=a.seed, quick=a.quick,
        record=not a.no_record, refresh_app=not a.no_refresh_app,
        followup_trials_2d=max(0, a.followup_trials_2d), followup_trials_3d=max(0, a.followup_trials_3d),
        followup_max_leads=max(0, a.followup_max_leads),
        fission_path_trials_2d=max(0, a.fission_path_trials_2d),
        fission_path_max_leads=max(0, a.fission_path_max_leads),
        deep_time_max_leads=max(0, a.deep_time_max_leads),
        open_ended_probes=max(0, a.open_ended_probes),
        open_ended_max_episodes=max(0, a.open_ended_max_episodes),
        unknown_followup_max_patterns=max(0, a.unknown_followup_max_patterns),
        max_synthesized_hypotheses=max(0, a.max_synthesized_hypotheses),
    )
    r = result["report"]
    evo = r.get("hypothesis_evolution_v7") or {}
    goal = r.get("goal_mission_v7") or {}
    port = r.get("hypothesis_portfolio_v7") or {}
    print(f"=== Aeterna Adaptive Dream v7: {r['burst_id']} ===")
    print(f"  graph: nodes={evo.get('nodes', 0)} edges={evo.get('edges', 0)} branches={len(evo.get('automatic_branches') or [])}")
    print(f"  synthesized proposals={len(evo.get('new_proposals') or [])} evidence cards={evo.get('evidence_cards', 0)}")
    print(f"  mission progress={goal.get('required_satisfied', 0)}/{goal.get('required_total', 0)} reached={goal.get('goal_reached', False)}")
    print(f"  portfolio active hypotheses={len(port.get('active') or [])}; hypothesis lane cap={port.get('hypothesis_budget_cap')}")
    print("  NOTE: v7 evolves research questions only; physics, scientific gates, official Levels and Rooms are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
