"""Adaptive Dream v6: open-ended emergence discovery above the existing v5 research lanes.

v6 keeps every existing broad-search, Native-3D, promising-lead, F-path and Deep-Time lane, but
changes the epistemic centre of gravity: the F-path is one known reference route, not the route.
A small additive lane searches for recurrent, initially unlabeled state transitions and a Question
Critic periodically challenges the framing of the research question itself.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive
from ai_lab.dream import adaptive_loop as v3
from ai_lab.dream import adaptive_v5 as v5
from ai_lab.dream import deep_time_v2
from ai_lab.dream import open_ended
from ai_lab.dream import question_critic
from ai_lab.dream.report import write_report


def _question_text(critic: dict[str, Any], *, limit: int = 2) -> str:
    questions = critic.get("questions") or []
    if not questions:
        return "今回は問い方そのものを変える強い理由はまだありませんでした。"
    bits = [str(q.get("question")) for q in questions[:max(1, limit)] if q.get("question")]
    return " / ".join(bits)


def _enrich_easy_report(
    paths: dict[str, str], *, open_summary: dict[str, Any], critic: dict[str, Any], report: dict[str, Any],
) -> None:
    latest = Path(paths["latest"])
    if not latest.exists():
        return
    try:
        easy = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        return

    old_headline = str(easy.get("one_line", ""))
    highlight = str(open_summary.get("highlight", ""))
    if highlight:
        easy["one_line_before_open_ended"] = old_headline
        easy["one_line"] = highlight
    easy["unexpected_discovery"] = highlight
    easy["open_ended_emergence"] = open_summary
    easy["question_critic"] = critic
    easy["question_critic_summary"] = _question_text(critic)
    easy["known_route_context"] = (
        "F0〜F7は残していますが、自然の正解順序ではなく『人間が先に考えた参照ルートの1本』として扱います。"
        "別の枝・ループ・長期安定・合流・未知遷移も同じ価値で探します。"
    )
    easy["what_next"] = (
        "F-pathだけを先へ進めるのではなく、繰り返して現れる名前のない変化を別seed・別条件で確かめます。"
        " 同時に、既存のF-path・三角形・Native 3Dの反証実験も小さな独立レーンとして続けます。"
    )

    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))

    md = "\n".join([
        "# やさしい実験レポート", "",
        f"**ひとことで：** {easy.get('one_line', '')}", "",
        "## 今回いちばん予想外だったこと", str(easy.get("unexpected_discovery", "")), "",
        "## 今まで名前を付けていない変化は繰り返した？",
        (
            f"今回 {open_summary.get('probes', 0)} runをスコア上位だけに偏らず観測し、"
            f"変化点候補 {open_summary.get('episodes', 0)} 件、新しいfingerprint {open_summary.get('new_patterns', 0)} 件。"
            f"複数条件で反復した未整理patternは {open_summary.get('recurrent_unlabeled_patterns', 0)} 件です。"
        ), "",
        "## そもそも問い方が狭くない？", str(easy.get("question_critic_summary", "")), "",
        "## 今回なにをした？", str(easy.get("what_we_did", "")), "",
        "## F-pathはどう扱う？", str(easy.get("known_route_context", "")), "",
        "## 参照F-pathの現在地", str(easy.get("zero_to_fission_status", "")), "",
        "## 同じ世界をもっと長く見た？", str(easy.get("deep_time_followup", "")), "",
        "## 三角形の仮説は？", str(easy.get("triangle_question", "")), "",
        "## 一般の有望候補は追試した？", str(easy.get("promising_followup", "")), "",
        "## 次は？", str(easy.get("what_next", "")), "",
        f"> {easy.get('important_note', '')}", "",
    ])
    Path(paths["markdown"]).write_text(md)
    latest.with_suffix(".md").write_text(md)


def run_adaptive_v6(
    *, open_ended_probes: int = 24, open_ended_max_episodes: int = 3, **kwargs: Any,
) -> dict[str, Any]:
    # Capture the same broad mass search for a stratified observational sample; do not change it.
    open_ended.install_mass_capture(adaptive)
    # Upgrade only the Deep-Time interpretation/audit layer; v5's other research lanes stay intact.
    previous_deep = v5.deep_time
    v5.deep_time = deep_time_v2
    try:
        base = v5.run_adaptive_v5(**kwargs)
    finally:
        v5.deep_time = previous_deep

    report = base["report"]
    mass_results = open_ended.consume_captured_mass()
    master_seed = int((report.get("search") or {}).get("master_seed") or 0)
    workers = int(kwargs.get("workers", 4))
    opened = open_ended.run_open_ended(
        burst_id=str(report["burst_id"]),
        mass_results=mass_results,
        seed=master_seed,
        quick=bool(kwargs.get("quick", True)),
        probes=max(0, int(open_ended_probes)),
        workers=max(1, workers),
        max_episodes_per_probe=max(0, int(open_ended_max_episodes)),
    )
    ar = report.get("adaptive_research") or {}
    critic = question_critic.run_question_critic(
        burst_id=str(report["burst_id"]),
        report=report,
        open_summary=opened,
        director_refreshed=bool(ar.get("director_refreshed")),
    )

    report["open_ended_emergence"] = opened
    report["question_critic"] = critic
    report["known_route_policy"] = {
        "relation_fission_F": "one-known-reference-route",
        "director_focus_overridden_by_F_frontier": False,
        "unknown_routes_are_first_class_after_recurrence": True,
        "cycles_merges_stability_and_self_transitions_are_not_failures": True,
    }
    counts = report.setdefault("counts", {})
    counts["open_ended_probes"] = int(opened.get("probes", 0))
    counts["open_ended_change_episodes"] = int(opened.get("episodes", 0))
    counts["experiments"] = int(counts.get("experiments", 0)) + int(opened.get("probes", 0))
    report.setdefault("honesty", {})["F_path_is_the_assumed_natural_route"] = False
    report["honesty"]["open_ended_pattern_is_new_physics_claim"] = False
    report["honesty"]["question_critic_changes_truth_gate"] = False
    report["honesty"]["open_ended_lane_replaces_broad_exploration"] = False

    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy_report(base["easy_paths"], open_summary=opened, critic=critic, report=report)
    return base


def build_parser():
    ap = v5.build_parser()
    ap.description = "Aeterna Adaptive Dream v6 — open-ended emergence + known reference routes"
    ap.add_argument("--open-ended-probes", type=int, default=24)
    ap.add_argument("--open-ended-max-episodes", type=int, default=3)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    result = run_adaptive_v6(
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
    )
    r = result["report"]
    opened = r.get("open_ended_emergence") or {}
    path = r.get("zero_to_fission_path") or {}
    print(f"=== Aeterna Adaptive Dream v6: {r['burst_id']} ===")
    print(f"  broad: 2D={r['counts'].get('mass_2d_trials', 0)} 3D={r['counts'].get('native_3d_trials', 0)}")
    print(f"  open-ended: probes={opened.get('probes', 0)} episodes={opened.get('episodes', 0)} recurrent-unlabeled={opened.get('recurrent_unlabeled_patterns', 0)}")
    print(f"  known F reference: deepest={path.get('deepest_code')} (not the assumed natural route)")
    deep = r.get("deep_time_followup") or {}
    print(f"  prefix-audited deep-time runs={len(deep.get('results') or [])} quarantined={deep.get('quarantined_prefix_mismatches', 0)}")
    print(f"  easy-report: {result['easy_paths']['markdown']}")
    print("  NOTE: X-patterns and Question Critic are research guidance only; official science gates are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
