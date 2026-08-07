"""Adaptive Dream v5: v4 discovery/follow-ups + relation-fission F-path + Deep-Time verification."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lab.dream import adaptive_loop as v3
from ai_lab.dream import adaptive_v4 as v4
from ai_lab.dream import deep_time
from ai_lab.dream import fission_path_followups
from ai_lab.dream.report import write_report


def _path_summary(report: dict[str, Any]) -> dict[str, Any]:
    adaptive = report.get("adaptive_research") or {}
    tri = adaptive.get("triangle_hypothesis") or {}
    return tri.get("zero_to_fission_path") or adaptive.get("zero_to_fission_path") or {}


def _deep_time_text(deep: dict[str, Any]) -> str:
    results = deep.get("results") or []
    if not results:
        return "今回は長時間観察へ進めるF4以上の候補が無いか、既に予定した時間幅まで確認済みでした。"
    bits = []
    for r in results:
        rung = r.get("requested_horizon_multiplier")
        code = r.get("F_code") or f"F{r.get('F_depth', -1)}"
        if r.get("network_fission_candidate"):
            outcome = "関係網の持続的な分離候補まで観測"
        elif r.get("balance_collapse_seen"):
            outcome = "三角形のバランス崩れを観測"
        else:
            outcome = "まだバランス崩れは未観測"
        bits.append(f"{rung:g}τまで同じt=0軌道を延長して {code}、{outcome}")
    return "。".join(bits) + "。途中の三角形を新しい初期条件として置き直してはいません。"


def _enrich_easy_report(
    paths: dict[str, str], path: dict[str, Any], follow: dict[str, Any], deep: dict[str, Any],
) -> None:
    latest = Path(paths["latest"])
    if not latest.exists():
        return
    try:
        easy = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        return

    depth = int(path.get("deepest_contiguous_stage", -1))
    code = path.get("deepest_code") or (f"F{depth}" if depth >= 0 else None)
    selected = int(follow.get("selected_leads", 0))
    trials = int(follow.get("trials_2d", 0))
    repeated = sum(
        1 for x in (follow.get("leads") or [])
        if x.get("status") in {"REPEATED_PATH", "REPEATED_NONSPECIFIC"}
    )
    weakened = int(follow.get("weakened", 0))
    if selected:
        follow_text = (
            f"関係分離のF-pathで深く進んだ候補を {selected} 方向選び、追加で {trials} 通りを追試しました。"
            f" 同じF段階まで再び進む傾向が確認できた候補は {repeated} 件、弱まった候補は {weakened} 件です。"
        )
    else:
        follow_text = "今回はF4以上の関係分離F-path候補がまだ無かったので、専用の条件追試は行いませんでした。"
    deep_text = _deep_time_text(deep)

    easy["zero_to_fission_path"] = path  # compatibility key retained; content declares relation-fission-F
    easy["zero_to_fission_followup"] = follow_text
    easy["zero_to_fission_followup_summary"] = follow
    easy["deep_time_followup"] = deep_text
    easy["deep_time_followup_summary"] = deep
    if depth >= 0:
        easy["zero_to_fission_status"] = (
            f"同じrunで {code}（{path.get('deepest_label')}）まで連続到達。"
            " F段階は公式Emergence Levelとは別です。"
        )
    else:
        easy["zero_to_fission_status"] = "厳しい0スタート条件で連続到達したF-pathは今回は未確認。"

    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))

    md = "\n".join([
        "# やさしい実験レポート", "",
        f"**ひとことで：** {easy.get('one_line', '')}", "",
        "## 今回なにをした？", str(easy.get("what_we_did", "")), "",
        "## なにが分かった？", str(easy.get("what_we_found", "")), "",
        "## 関係分離F-pathはどこまで進んだ？", str(easy.get("zero_to_fission_status", "")), "",
        "## その深い道は条件を変えて追試した？", follow_text, "",
        "## 同じ世界をもっと長く見た？", deep_text, "",
        "## 三角形のバランスが崩れると？", str(easy.get("balance_break_question", "")), "",
        "## 気になった一般候補は追いかけた？", str(easy.get("promising_followup", "")), "",
        "## 3つの渦の三角形は？", str(easy.get("triangle_question", "")), "",
        "## 次は？", str(easy.get("what_next", "")), "",
        f"> {easy.get('important_note', '')}", "",
    ])
    Path(paths["markdown"]).write_text(md)
    latest.with_suffix(".md").write_text(md)


def run_adaptive_v5(
    *, fission_path_trials_2d: int = 24, fission_path_max_leads: int = 2,
    deep_time_max_leads: int = 1, **kwargs: Any,
) -> dict[str, Any]:
    base = v4.run_adaptive_v4(**kwargs)
    report = base["report"]
    path = _path_summary(report)
    master_seed = int((report.get("search") or {}).get("master_seed") or 0)
    workers = int(kwargs.get("workers", 4))
    follow = fission_path_followups.load_register_and_follow(
        burst_id=str(report["burst_id"]),
        master_seed=master_seed,
        workers=max(1, workers),
        path_summary=path,
        trials_2d=max(0, int(fission_path_trials_2d)),
        max_leads=max(0, int(fission_path_max_leads)),
    )
    deep = deep_time.register_and_run(
        burst_id=str(report["burst_id"]),
        path_summary=path,
        max_leads=max(0, int(deep_time_max_leads)),
        quick=bool(kwargs.get("quick", True)),
    )

    report["zero_to_fission_path"] = path
    report["zero_to_fission_followup"] = follow
    report["deep_time_followup"] = deep
    report.setdefault("adaptive_research", {})["zero_to_fission_path"] = path
    report["adaptive_research"]["deep_time_followup"] = deep
    counts = report.setdefault("counts", {})
    counts["fission_path_followup_2d_trials"] = int(follow.get("trials_2d", 0))
    counts["fission_path_geometry_replays"] = int(follow.get("geometry_replays", 0))
    counts["deep_time_runs"] = len(deep.get("results") or [])
    counts["experiments"] = int(counts.get("experiments", 0)) + int(follow.get("trials_2d", 0)) + int(counts["deep_time_runs"])
    report.setdefault("honesty", {})["zero_to_fission_path_is_official_level"] = False
    report["honesty"]["relation_fission_F_path_is_official_level"] = False
    report["honesty"]["zero_to_fission_followup_replaces_broad_exploration"] = False
    report["honesty"]["triangle_or_division_seeded_by_path_lane"] = False
    report["honesty"]["deep_time_replays_from_time_zero"] = True
    report["honesty"]["deep_time_midrun_shape_seeded"] = False

    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy_report(base["easy_paths"], path, follow, deep)
    return base


def build_parser():
    ap = v4.build_parser()
    ap.description = "Aeterna Adaptive Dream v5 — discovery + leads + relation-fission F-path + Deep Time"
    ap.add_argument("--fission-path-trials-2d", type=int, default=24)
    ap.add_argument("--fission-path-max-leads", type=int, default=2)
    ap.add_argument("--deep-time-max-leads", type=int, default=1)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    result = run_adaptive_v5(
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
    )
    r = result["report"]
    path = r.get("zero_to_fission_path") or {}
    pf = r.get("zero_to_fission_followup") or {}
    deep = r.get("deep_time_followup") or {}
    print(f"=== Aeterna Adaptive Dream v5: {r['burst_id']} ===")
    print(f"  broad: 2D={r['counts'].get('mass_2d_trials', 0)} 3D={r['counts'].get('native_3d_trials', 0)}")
    print(f"  relation-fission deepest={path.get('deepest_code')} {path.get('deepest_label')}")
    print(f"  path follow-up: leads={pf.get('selected_leads', 0)} 2D={pf.get('trials_2d', 0)}")
    print(f"  deep-time: selected={deep.get('selected_leads', 0)} runs={len(deep.get('results') or [])}")
    print(f"  easy-report: {result['easy_paths']['markdown']}")
    print("  NOTE: F0..F7 is observation guidance only; no triangle/division is seeded and official Levels are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
