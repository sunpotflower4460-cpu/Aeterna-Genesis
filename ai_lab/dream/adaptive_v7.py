"""Adaptive Dream v7: hypothesis evolution + mission-aware research portfolio.

v7 wraps v6 rather than replacing it. Existing open-ended discovery, X-pattern verification,
F-reference, Deep-Time, local-energy and anti-bias lanes remain intact. v7 adds a hypothesis graph,
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
_LANES = ("unexplored", "boundary", "hypothesis", "breaker", "random")
_LAST_ROUTING: dict[str, Any] = {}


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


def _lane_counts(n: int, allocation: dict[str, Any]) -> dict[str, int]:
    """Mirror the existing mass-lane integer allocation exactly."""
    total = max(0, int(n))
    counts = {k: int(total * max(0.0, float(allocation.get(k, 0.0)))) for k in _LANES}
    # Existing Adaptive Dream assigns integer remainder to broad unexplored coverage.
    counts["unexplored"] += total - sum(counts.values())
    return counts


def _runnable_items(portfolio: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for item in portfolio.get("active") or []:
        focus = item.get("search_focus")
        if not isinstance(focus, dict) or not focus.get("family") or not isinstance(focus.get("knobs"), dict):
            continue
        out.append(item)
    return out


def _weighted_counts(n: int, items: list[dict[str, Any]], *, weight_key: str) -> list[tuple[dict[str, Any], int]]:
    """Deterministically divide an integer budget without losing or creating trials."""
    total_n = max(0, int(n))
    if total_n == 0 or not items:
        return []
    weighted = []
    for item in items:
        w = max(0.0, float(item.get(weight_key, 0.0)))
        weighted.append((item, w))
    denom = sum(w for _, w in weighted)
    if denom <= 0:
        weighted = [(item, 1.0) for item, _ in weighted]
        denom = float(len(weighted))
    raw = [(item, total_n * w / denom) for item, w in weighted]
    counts = [int(x) for _, x in raw]
    remainder = total_n - sum(counts)
    order = sorted(
        range(len(raw)),
        key=lambda i: (raw[i][1] - counts[i], str(raw[i][0].get("hypothesis_id") or "")),
        reverse=True,
    )
    for i in order[:remainder]:
        counts[i] += 1
    return [(raw[i][0], counts[i]) for i in range(len(raw)) if counts[i] > 0]


def build_portfolio_route_plan(
    *, n: int, allocation: dict[str, Any], ordinary_focus: dict[str, Any] | None,
    portfolio: dict[str, Any],
) -> dict[str, Any]:
    """Build a next-burst plan while preserving every existing global lane count.

    Only hypothesis and breaker lanes are subdivided across runnable hypothesis focuses. Broad lanes
    keep exactly the counts chosen by the existing Research Director.
    """
    counts = _lane_counts(n, allocation)
    runnable = _runnable_items(portfolio)
    blocks: list[dict[str, Any]] = []

    def add(lane: str, count: int, focus: dict[str, Any] | None, *, hid: str | None = None, role: str = "ordinary"):
        if count <= 0:
            return
        blocks.append({
            "lane": lane,
            "n": int(count),
            "focus": focus,
            "hypothesis_id": hid,
            "role": role,
        })

    add("unexplored", counts["unexplored"], None)
    add("boundary", counts["boundary"], ordinary_focus)
    add("random", counts["random"], None)

    if runnable:
        exploit = _weighted_counts(counts["hypothesis"], runnable, weight_key="hypothesis_budget_share")
        for item, count in exploit:
            add("hypothesis", count, item.get("search_focus"), hid=str(item.get("hypothesis_id")), role="exploit")

        # Challenge budget is still the existing breaker lane. Stronger beliefs only decide which
        # hypothesis the breaker tries to falsify; they cannot increase or shrink the global lane.
        challenge_items = [
            {**item, "_challenge_weight": max(1e-9, float(item.get("challenge_pressure", 0.0))) * max(1e-9, float(item.get("hypothesis_budget_share", 0.0)))}
            for item in runnable
        ]
        challenge = _weighted_counts(counts["breaker"], challenge_items, weight_key="_challenge_weight")
        for item, count in challenge:
            add("breaker", count, item.get("search_focus"), hid=str(item.get("hypothesis_id")), role="challenge")
    else:
        add("hypothesis", counts["hypothesis"], ordinary_focus)
        add("breaker", counts["breaker"], ordinary_focus)

    # Defensive accounting: any future lane schema oddity falls back to broad unexplored trials.
    planned = sum(int(x["n"]) for x in blocks)
    if planned < max(0, int(n)):
        add("unexplored", max(0, int(n)) - planned, None, role="accounting-fallback")
    return {
        "version": 1,
        "enabled": bool(runnable),
        "requested_trials": max(0, int(n)),
        "lane_counts": counts,
        "runnable_hypotheses": len(runnable),
        "blocks": blocks,
        "global_lane_counts_changed": False,
        "target_outcome_seeded": False,
    }


def install_portfolio_routing(adaptive_module: Any) -> None:
    """Route the next mass burst through the *previous* persisted portfolio.

    This wrapper is installed before v6 installs its passive open-ended capture, so open-ended analysis
    still sees the complete combined mass population.
    """
    current = adaptive_module.run_mass_2d
    if getattr(current, "_v7_portfolio_routing", False):
        return
    original = current

    def wrapped(*, start_index: int, n: int, workers: int, allocation: dict[str, float],
                focus: dict[str, Any] | None, master_seed: int, quick: bool, **extra: Any):
        previous_portfolio = _read(_PORTFOLIO, {"version": 1, "active": []})
        route = build_portfolio_route_plan(
            n=n, allocation=allocation, ordinary_focus=focus, portfolio=previous_portfolio,
        )
        global _LAST_ROUTING
        if not route["enabled"]:
            result = original(
                start_index=start_index, n=n, workers=workers, allocation=allocation, focus=focus,
                master_seed=master_seed, quick=quick, **extra,
            )
            _LAST_ROUTING = {
                **route,
                "executed_trials": int(result.get("n", 0)),
                "fallback_to_v6_single_focus": True,
            }
            return result

        combined: list[dict[str, Any]] = []
        redirected = 0
        spilled = 0
        cursor = int(start_index)
        executed_blocks = []
        for block in route["blocks"]:
            count = int(block["n"])
            lane = str(block["lane"])
            if count <= 0:
                continue
            sub = original(
                start_index=cursor,
                n=count,
                workers=workers,
                allocation={lane: 1.0},
                focus=block.get("focus"),
                master_seed=master_seed,
                quick=quick,
                **extra,
            )
            redirected += int(sub.get("redirected_from_saturated", 0))
            spilled += int(sub.get("spilled_from_saturated_focus", 0))
            rows = list(sub.get("results") or [])
            for row in rows:
                row["portfolio_hypothesis_id"] = block.get("hypothesis_id")
                row["portfolio_role"] = block.get("role")
            combined.extend(rows)
            executed_blocks.append({
                "lane": lane,
                "n": len(rows),
                "hypothesis_id": block.get("hypothesis_id"),
                "role": block.get("role"),
            })
            cursor += count

        combined.sort(key=adaptive_module.lab._score_key, reverse=True)
        _LAST_ROUTING = {
            **route,
            "executed_trials": len(combined),
            "executed_blocks": executed_blocks,
            "fallback_to_v6_single_focus": False,
        }
        return {"results": combined, "n": len(combined), "next_index": int(start_index) + max(0, int(n)),
                "redirected_from_saturated": redirected, "spilled_from_saturated_focus": spilled}

    wrapped._v7_portfolio_routing = True
    wrapped._v7_original = original
    adaptive_module.run_mass_2d = wrapped


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
        "portfolio_routing_enabled": evo.get("portfolio_routing_enabled"),
        "note": "仮説の強弱・枝分かれは次の研究配分を決めるためのもの。科学的真実や公式Levelを変更しません。",
    }
    easy["goal_mission_v7"] = goal
    easy["hypothesis_portfolio_v7"] = {
        "active": portfolio.get("active"),
        "anti_bias": portfolio.get("anti_bias"),
        "runnable_focuses": portfolio.get("runnable_focuses"),
    }
    easy["portfolio_routing_v7"] = report.get("portfolio_routing_v7") or {}
    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))


def run_adaptive_v7(*, max_synthesized_hypotheses: int = 3, **kwargs: Any) -> dict[str, Any]:
    # The previous burst's portfolio steers this burst. Current evidence builds the next portfolio.
    install_portfolio_routing(adaptive)
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
    routing = dict(_LAST_ROUTING)
    report["hypothesis_evolution_v7"] = {
        "version": 2,
        "mode": "planning-and-routing-layer",
        "nodes": len(graph.get("nodes") or {}),
        "edges": len(graph.get("edges") or []),
        "changes": evolved.get("changes") or [],
        "automatic_branches": automatic_branches,
        "new_proposals": [p.get("id") for p in proposals],
        "evidence_cards": len(cards),
        "runnable_focuses": int(portfolio.get("runnable_focuses", 0)),
        "portfolio_routing_enabled": bool(routing.get("enabled")),
        "quarantined_evidence_has_zero_weight": True,
        "changes_scientific_gate": False,
        "changes_official_level": False,
        "writes_official_rooms": False,
    }
    report["hypothesis_portfolio_v7"] = portfolio
    report["portfolio_routing_v7"] = routing
    report["goal_mission_v7"] = goal
    report.setdefault("honesty", {})["hypothesis_graph_confidence_is_scientific_truth_probability"] = False
    report["honesty"]["goal_mission_seeds_target_morphology"] = False
    report["honesty"]["F7_alone_counts_as_biological_cell_division"] = False
    report["honesty"]["hypothesis_synthesizer_can_change_scientific_gate"] = False
    report["honesty"]["portfolio_routing_changes_global_lane_floors"] = False
    report["honesty"]["portfolio_routing_seeds_target_outcome"] = False

    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy(base["easy_paths"], report=report)
    return base


def build_parser():
    ap = v6.build_parser()
    ap.description = "Aeterna Adaptive Dream v7 — hypothesis evolution + mission-aware portfolio routing"
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
    route = r.get("portfolio_routing_v7") or {}
    print(f"=== Aeterna Adaptive Dream v7: {r['burst_id']} ===")
    print(f"  graph: nodes={evo.get('nodes', 0)} edges={evo.get('edges', 0)} branches={len(evo.get('automatic_branches') or [])}")
    print(f"  synthesized proposals={len(evo.get('new_proposals') or [])} evidence cards={evo.get('evidence_cards', 0)}")
    print(f"  mission progress={goal.get('required_satisfied', 0)}/{goal.get('required_total', 0)} reached={goal.get('goal_reached', False)}")
    print(f"  portfolio active={len(port.get('active') or [])} runnable={port.get('runnable_focuses', 0)} cap={port.get('hypothesis_budget_cap')}")
    print(f"  previous-portfolio routing enabled={route.get('enabled', False)} executed={route.get('executed_trials', 0)}")
    print("  NOTE: v7 evolves research questions and bounded search focus only; physics, scientific gates, official Levels and Rooms are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
