"""Adaptive Dream v4: v3 hourly discovery + bounded Promising Lead follow-ups.

The broad search remains exactly where it was.  After each hourly burst, concrete promising results
are registered as Leads and receive extra verification trials.  This gives Aeterna the behaviour:
"that looked interesting -> test it repeatedly and from several angles" without letting one idea
consume the exploration budget.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ai_lab import lab
from ai_lab.dream import adaptive_loop as v3
from ai_lab.dream import followups
from ai_lab.dream.report import write_report


def _current_mass_memory() -> list[dict[str, Any]]:
    doc = lab.load_ledger()
    items = [x for x in (doc.get("search_discoveries") or []) if x.get("score") is not None]
    items.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)
    return items[:48]


def _inputs_from_report(report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ordinary: list[dict[str, Any]] = []
    paired3d: list[dict[str, Any]] = []
    geometry: list[dict[str, Any]] = []
    for e in report.get("events") or []:
        source = e.get("source")
        facts = e.get("facts") or {}
        if source == "geometry-probe" and facts.get("fission_like_after_triangle"):
            geometry.append({
                "family": facts.get("family"), "knobs": facts.get("knobs") or {}, "seed": facts.get("seed"),
                "trial_index": facts.get("trial_index"), "fission_like_after_triangle": True,
                "triangle_seen": True,
            })
            continue
        if source == "native-3d-discovery":
            paired3d.append({
                "family": facts.get("family"), "knobs": facts.get("knobs") or {}, "seed": facts.get("seed"),
                "reached_level": facts.get("reached_level"), "paired_2d_level": facts.get("paired_2d_level"),
                "dimension_delta": facts.get("dimension_delta"),
            })
            # A direct-3D L2 observation is still a useful ordinary lead even without a positive delta.
            ordinary.append(e)
            continue
        ordinary.append(e)
    return ordinary, paired3d, geometry


def _enrich_easy_report(paths: dict[str, str], follow: dict[str, Any]) -> None:
    latest = Path(paths["latest"])
    if not latest.exists():
        return
    try:
        easy = json.loads(latest.read_text())
    except (OSError, json.JSONDecodeError):
        return
    nlead = int(follow.get("selected_leads", 0))
    t2 = int(follow.get("trials_2d", 0))
    t3 = int(follow.get("trials_3d", 0))
    stronger = int(follow.get("strengthened", 0))
    weaker = int(follow.get("weakened", 0))
    if nlead:
        text = (
            f"気になった結果を {nlead} 方向選び、追加で平面 {t2} 通り・立体 {t3} 通りを追試しました。"
            f" 何度試しても残りそうだと一段強くなった候補は {stronger} 件、逆に弱そうだと分かった候補は {weaker} 件です。"
        )
    else:
        text = "今回は追加で追いかける条件がまだありませんでした。面白い候補が出たら自動で追試を始めます。"
    easy["promising_followup"] = text
    easy["followup_summary"] = follow
    if nlead:
        easy["what_next"] = (
            "面白そうな候補は記録だけで終わらせず、同じ条件のやり直し・少し条件を変えた確認・逆の条件との比較を続けます。"
            " それとは別に、まだ知らない場所を探す実験も止めません。"
        )
    latest.write_text(json.dumps(easy, indent=2, ensure_ascii=False))

    # Keep the timestamped JSON in sync too.
    if paths.get("json"):
        Path(paths["json"]).write_text(json.dumps(easy, indent=2, ensure_ascii=False))
    md = "\n".join([
        "# やさしい実験レポート", "",
        f"**ひとことで：** {easy.get('one_line', '')}", "",
        "## 今回なにをした？", str(easy.get("what_we_did", "")), "",
        "## なにが分かった？", str(easy.get("what_we_found", "")), "",
        "## 気になった結果は、ちゃんと追いかけた？", text, "",
        "## 3つの渦の三角形は？", str(easy.get("triangle_question", "")), "",
        "## 次は？", str(easy.get("what_next", "")), "",
        f"> {easy.get('important_note', '')}", "",
    ])
    Path(paths["markdown"]).write_text(md)
    latest.with_suffix(".md").write_text(md)


def run_adaptive_v4(
    *, followup_trials_2d: int = 256, followup_trials_3d: int = 32, followup_max_leads: int = 4,
    **kwargs: Any,
) -> dict[str, Any]:
    base = v3.run_adaptive_burst(**kwargs)
    report = base["report"]
    ordinary, paired3d, geometry = _inputs_from_report(report)
    master_seed = int((report.get("search") or {}).get("master_seed") or 0)
    workers = int(kwargs.get("workers", 4))
    follow = followups.load_register_and_follow(
        burst_id=str(report["burst_id"]), master_seed=master_seed, workers=max(1, workers),
        events=ordinary, mass_results=_current_mass_memory(), paired3d=paired3d, geometry_probes=geometry,
        trials_2d=max(0, followup_trials_2d), trials_3d=max(0, followup_trials_3d),
        max_leads=max(0, followup_max_leads),
    )
    report["promising_lead_followup"] = follow
    counts = report.setdefault("counts", {})
    counts["followup_2d_trials"] = int(follow.get("trials_2d", 0))
    counts["followup_3d_trials"] = int(follow.get("trials_3d", 0))
    counts["followup_selected_leads"] = int(follow.get("selected_leads", 0))
    counts["experiments"] = int(counts.get("experiments", 0)) + int(follow.get("trials_2d", 0)) + int(follow.get("trials_3d", 0))
    report.setdefault("honesty", {})["followup_changes_scientific_gate"] = False
    report["honesty"]["followup_replaces_broad_exploration"] = False

    # v3 has already written the report. Rewrite the same timestamp with the additive follow-up summary.
    generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    stamp = generated.strftime("%Y-%m-%dT%H-%M-%SZ")
    base["paths"] = write_report(str(v3._REPO), report, stamp=stamp)
    _enrich_easy_report(base["easy_paths"], follow)
    return base


def build_parser() -> argparse.ArgumentParser:
    ap = v3.build_parser()
    ap.description = "Aeterna Adaptive Dream v4 — hourly discovery + automatic promising-lead verification"
    ap.add_argument("--followup-trials-2d", type=int, default=256)
    ap.add_argument("--followup-trials-3d", type=int, default=32)
    ap.add_argument("--followup-max-leads", type=int, default=4)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    result = run_adaptive_v4(
        trials=max(0, a.trials), native3d_trials=max(0, a.native3d_trials), workers=max(1, a.workers),
        repro_top=max(0, a.repro_top), repro_seeds=max(1, a.repro_seeds),
        compare_native3d_top=max(0, a.compare_native3d_top), geometry_top=max(0, a.geometry_top),
        geometry_broad=max(0, a.geometry_broad), native_variants=max(0, a.native_variants),
        max_jobs=max(0, a.max_jobs), seed=a.seed, quick=a.quick,
        record=not a.no_record, refresh_app=not a.no_refresh_app,
        followup_trials_2d=max(0, a.followup_trials_2d), followup_trials_3d=max(0, a.followup_trials_3d),
        followup_max_leads=max(0, a.followup_max_leads),
    )
    r = result["report"]
    f = r["promising_lead_followup"]
    print(f"=== Aeterna Adaptive Dream v4: {r['burst_id']} ===")
    print(f"  broad: 2D={r['counts'].get('mass_2d_trials', 0)} 3D={r['counts'].get('native_3d_trials', 0)}")
    print(f"  follow-up: leads={f['selected_leads']} 2D={f['trials_2d']} 3D={f['trials_3d']}")
    print(f"  strengthened={f['strengthened']} weakened={f['weakened']}")
    print(f"  easy-report: {result['easy_paths']['markdown']}")
    print("  NOTE: follow-up status is research guidance only; truth gates and broad exploration are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
