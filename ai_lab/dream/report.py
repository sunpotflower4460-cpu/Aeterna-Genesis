"""Night Report generation for the Aeterna Dream Loop."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from ai_lab.dream import human_report

_PRIORITY = {
    "PROMOTION_READY": 100,
    "STAGE_PROMOTED": 95,
    "REPRODUCED": 85,
    "NEW_BEHAVIOR": 80,
    "DIMENSION_FAILURE": 70,
    "RARE_EVENT": 65,
    "NEW_REGION": 50,
    "NEGATIVE_RESULT": 35,
    "NUMERICAL_WARNING": 20,
}

_LABEL = {
    "PROMOTION_READY": "昇格候補",
    "STAGE_PROMOTED": "段階通過",
    "REPRODUCED": "再現成功",
    "NEW_BEHAVIOR": "新規候補",
    "DIMENSION_FAILURE": "3D移行失敗",
    "RARE_EVENT": "希少挙動",
    "NEW_REGION": "新規領域",
    "NEGATIVE_RESULT": "負の結果",
    "NUMERICAL_WARNING": "数値警告",
}


def _sort_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        events,
        key=lambda e: (
            _PRIORITY.get(e.get("kind"), 0),
            float((e.get("facts") or {}).get("novelty") or 0.0),
        ),
        reverse=True,
    )


def _belongs_to_burst(
    event: dict[str, Any],
    burst_id: str,
    executed_job_ids: set[str] | None = None,
) -> bool:
    """Keep a Night Report about work that actually happened during this burst.

    Search events are constructed in-memory during the current burst. Genesis Orchestrator events come
    from an append-only ledger that can contain historical campaigns. When the worker's executed job IDs
    are available, they are the authoritative boundary: this also correctly includes a carried-over job
    from yesterday if it was actually executed tonight. The campaign-id check is a defensive fallback for
    direct callers/tests that do not provide worker results.
    """
    if event.get("source") != "genesis-orchestrator":
        return True
    if executed_job_ids is not None:
        return str(event.get("source_key") or "") in executed_job_ids
    return (event.get("facts") or {}).get("campaign_id") == burst_id


def build_report(
    events: list[dict[str, Any]],
    *,
    burst_id: str,
    expanded_trials: int,
    native_jobs: int,
    generated_at: str | None = None,
    executed_job_ids: set[str] | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    current_events = [
        event for event in events
        if _belongs_to_burst(event, burst_id, executed_job_ids=executed_job_ids)
    ]
    ranked = _sort_events(current_events)
    counts: dict[str, int] = {
        "experiments": int(expanded_trials) + int(native_jobs),
        "expanded_trials": int(expanded_trials),
        "native_jobs": int(native_jobs),
        "new_behavior": 0,
        "reproduced": 0,
        "promotion_ready": 0,
        "stage_promoted": 0,
        "dimension_failure": 0,
        "negative_result": 0,
        "rare_event": 0,
        "numerical_warning": 0,
        "new_region": 0,
    }
    map_key = {
        "NEW_BEHAVIOR": "new_behavior",
        "REPRODUCED": "reproduced",
        "PROMOTION_READY": "promotion_ready",
        "STAGE_PROMOTED": "stage_promoted",
        "DIMENSION_FAILURE": "dimension_failure",
        "NEGATIVE_RESULT": "negative_result",
        "RARE_EVENT": "rare_event",
        "NUMERICAL_WARNING": "numerical_warning",
        "NEW_REGION": "new_region",
    }
    for event in current_events:
        key = map_key.get(event.get("kind"))
        if key:
            counts[key] += 1

    headline = ranked[0] if ranked else None
    return {
        "report_version": 1,
        "burst_id": burst_id,
        "generated_at": generated_at,
        "counts": counts,
        "headline_event_id": headline.get("event_id") if headline else None,
        "headline": headline,
        "events": ranked,
        "honesty": {
            "event_explanations_rule_based": True,
            "llm_required": False,
            "novelty_is_success_gate": False,
            "view_presets_change_physics": False,
            "dream_loop_can_write_official_rooms": False,
        },
    }


def _facts_line(event: dict[str, Any]) -> str:
    f = event.get("facts") or {}
    bits: list[str] = []
    if f.get("reached_level") is not None:
        bits.append(f"L{f['reached_level']}")
    if f.get("novelty") is not None:
        bits.append(f"novelty {float(f['novelty']):.2f}")
    repro = f.get("reproduction") or {}
    if repro:
        bits.append(f"再現 {repro.get('matched', 0)}/{repro.get('tested', 0)}")
    if f.get("stage"):
        bits.append(str(f["stage"]))
    if f.get("seed") is not None:
        bits.append(f"seed {f['seed']}")
    return " / ".join(bits)


def render_technical_markdown(report: dict[str, Any]) -> str:
    """Render the old detail-heavy report for audit/debug use, not as the first-read document."""
    c = report["counts"]
    lines = [
        "# 🌙 Genesis Night Report",
        "",
        f"Burst: `{report['burst_id']}`  ",
        f"Generated: `{report['generated_at']}`",
        "",
        "## 実験記録",
        "",
        f"- 実験・ジョブ: **{c['experiments']}**",
        f"- 新規候補: **{c['new_behavior']}**",
        f"- 再現成功: **{c['reproduced']}**",
        f"- 昇格候補: **{c['promotion_ready']}**",
        f"- 段階通過: **{c['stage_promoted']}**",
        f"- 3D移行失敗: **{c['dimension_failure']}**",
        f"- 負の結果: **{c['negative_result']}**",
        f"- 数値警告: **{c['numerical_warning']}**",
        "",
    ]
    if report.get("headline"):
        h = report["headline"]
        lines.extend([
            "## 今回もっとも注目すべきこと",
            "",
            f"**{h['title']}**",
            "",
            h["plain"],
            "",
            f"> なぜ見る価値がある？ {h['why']}",
            "",
        ])
    lines.extend(["## 出来事", ""])
    if not report["events"]:
        lines.append("今回のburstでは特筆イベントはありませんでした。結果そのものは探索履歴へ保存されます。")
    for event in report["events"]:
        label = _LABEL.get(event.get("kind"), event.get("kind", "EVENT"))
        lines.extend([
            f"### {label} — {event['title']}",
            "",
            event["plain"],
            "",
            f"- 状態: `{event.get('scientific_status')}`",
            f"- 見る価値: `{event.get('visual_interest')}`",
        ])
        facts_line = _facts_line(event)
        if facts_line:
            lines.append(f"- 測定メモ: {facts_line}")
        if event.get("room_id"):
            lines.append(f"- Room: `{event['room_id']}`")
        if event.get("view_preset_id"):
            lines.append(f"- View Preset: `{event['view_preset_id']}`")
        lines.extend(["", f"> {event['why']}", ""])
    lines.extend([
        "---",
        "Novelty / visual interest はランキングと観察補助であり、物理的成功判定ではありません。",
        "Dream Loop は `rooms/official/` を書き換えません。",
        "",
    ])
    return "\n".join(lines)


def render_markdown(report: dict[str, Any]) -> str:
    """Render the default human-facing report.

    Once a human summary exists, the default Markdown is intentionally orientation-first.  Detailed IDs,
    counts and raw measurements remain in summary/events JSON and in technical-report.md.
    """
    summary = report.get("human_summary")
    if isinstance(summary, dict):
        return human_report.render_markdown(summary)
    return render_technical_markdown(report)


def write_report(root: str, report: dict[str, Any], *, stamp: str) -> dict[str, str]:
    base = os.path.join(root, "ai_lab", "reports", "nightly")
    out = os.path.join(base, stamp)
    os.makedirs(out, exist_ok=True)
    summary_path = os.path.join(out, "summary.json")
    events_path = os.path.join(out, "events.json")
    md_path = os.path.join(out, "report.md")
    technical_md_path = os.path.join(out, "technical-report.md")
    with open(summary_path, "w") as f:
        json.dump({k: v for k, v in report.items() if k != "events"}, f, indent=2, ensure_ascii=False)
    with open(events_path, "w") as f:
        json.dump(report["events"], f, indent=2, ensure_ascii=False)
    with open(md_path, "w") as f:
        f.write(render_markdown(report))
    if isinstance(report.get("human_summary"), dict):
        with open(technical_md_path, "w") as f:
            f.write(render_technical_markdown(report))
    latest_path = os.path.join(base, "latest.json")
    with open(latest_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return {
        "dir": out,
        "summary": summary_path,
        "events": events_path,
        "markdown": md_path,
        "technical_markdown": technical_md_path,
        "latest": latest_path,
    }
