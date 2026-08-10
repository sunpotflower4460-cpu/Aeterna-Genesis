"""Human-first reporting for Aeterna autonomous research.

The scientific record remains machine-readable and complete. This module creates a separate
reader-facing layer whose job is orientation, not data compression into unexplained jargon.

The main report always answers, in this order:
1. where are we trying to go,
2. where are we now,
3. what became possible / clearer this time,
4. what is still not achieved,
5. what will be tested next.

Raw hypothesis IDs, variable names, status codes, trial counts and regulator values stay in JSON and
technical evidence. They are intentionally absent from the first-read prose.
"""
from __future__ import annotations

import re
from typing import Any


# Terms that are useful internally but should not be required to understand the first-read report.
_FORBIDDEN_FIRST_READ = (
    "seed", "run", "trial", "burst", "amp_std", "gradient_rms", "mean_amp",
    "fingerprint", "pattern", "RLAW", "X-", "F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7",
    "Level", "Room", "priority", "confidence", "novelty", "3D", "2D", "Native", "Preset",
)
_ASCII_NUMBER = re.compile(r"[0-9]")


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _night_counts(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("counts") if isinstance(report.get("counts"), dict) else {}


def _root(report: dict[str, Any]) -> dict[str, Any]:
    return report.get("pure_genesis_r0") if isinstance(report.get("pure_genesis_r0"), dict) else {}


def _frontier(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("autonomous_frontier_expansion")
    return value if isinstance(value, dict) else {}


def _fission_reference(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("zero_to_fission_path")
    return value if isinstance(value, dict) else {}


def _has_root_research(report: dict[str, Any]) -> bool:
    root = _root(report)
    return bool(root.get("law_trials") or root.get("top_laws") or root.get("root_integrity_audit"))


def build_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build an orientation-first Japanese summary from a full technical report."""
    counts = _night_counts(report)
    root = _root(report)
    frontier = _frontier(report)
    frontier_human = frontier.get("human") if isinstance(frontier.get("human"), dict) else {}
    fission = _fission_reference(report)

    destination = str(frontier_human.get("destination") or (
        "ほとんど何も形として決めていない出発点から、違いと関係が自然に育ち、"
        "宇宙のような大きなまとまり、脳のように過去を生かして変わるまとまり、"
        "種から育つ植物のように自分を保ちながら成長するまとまりまで、形を先に与えず生まれるかを確かめることです。"
    ))

    if frontier_human.get("current_position"):
        current = str(frontier_human["current_position"])
    elif _has_root_research(report):
        current = (
            "いまは、最小の出発点から生まれた小さな違いが、関係の中で広がって長く残れるかを"
            "調べている段階です。同時に、計算の都合でそう見えるだけの変化を"
            "本当の発見と取り違えないための監査も通しています。"
        )
    else:
        current = (
            "いまは、違いが生まれて関係が続く条件を広く探している段階です。"
            "まだ生命や脳そのものを作れた段階ではありません。"
        )

    achieved: list[str] = []
    for item in frontier_human.get("advances") or []:
        if item:
            achieved.append(str(item))
    if _has_root_research(report):
        achieved.append(
            "最小の出発点から試した関係の変わり方について、見かけの成功を除く監査まで含めて比べ、"
            "次に詳しく調べる候補を絞り直しています。"
        )
        audit = root.get("root_integrity_audit") if isinstance(root.get("root_integrity_audit"), dict) else {}
        if audit:
            achieved.append(
                "計算上の名前や単なる全体の反転を、そのまま自然の新しい仕組みだと数えないように自動でチェックしています。"
            )
    if _int(counts.get("reproduced")) > 0 or "反復" in str(report.get("one_line") or ""):
        achieved.append(
            "最初の偶然や条件を変えても、似た変化がもう一度現れる例について、再現するだけでなく何に敏感かまで調べ始めています。"
        )
    if str(fission.get("deepest_label") or ""):
        achieved.append(
            "別の補助実験では、局所的な構造どうしが関係を作り、その関係が不安定になるところまで進む例も追っています。"
            "これは自然の正式な一本道ではなく、仕組みを学ぶための参考ルートです。"
        )
    if not achieved:
        achieved.append(
            "今回は大きな到達を宣言する結果はありませんでしたが、次に捨てる考えと深く追う考えを整理しました。"
        )

    gaps = [str(x) for x in (frontier_human.get("largest_gaps") or []) if x]
    if gaps:
        not_yet = [f"「{label}」までは、まだ本物の物理として確認できていません。" for label in gaps]
    else:
        not_yet = [
            "最初の小さな違いを大きくするだけでなく、新しい種類の違いそのものを自力で増やせるかはまだ途中です。",
            "空間や物理的な時間、記憶が最小の出発点から自然に生まれたとはまだ言えません。",
            "生命の器や脳が生まれたとはまだ言えません。脳や植物の形を最初から置いてもいません。",
        ]

    requests = frontier.get("instrument_requests") if isinstance(frontier.get("instrument_requests"), list) else []
    next_steps = []
    for req in requests[:5]:
        purpose = str((req or {}).get("purpose") or "")
        if purpose:
            next_steps.append(purpose + "ための新しい測り方や介入実験を作ります。")
    if not next_steps:
        next_steps = [
            "何度も現れる変化について、どの条件を変えると消えるかを一つずつ確かめます。",
            "深く進んだ候補について、何が必要で何が不要なのかを部品を外す実験で確かめます。",
            "今の測り方では確認できない能力があれば、その能力を確かめる新しい測定器から作ります。",
        ]

    return {
        "version": 2,
        "purpose": "destination_progress_orientation",
        "destination": destination,
        "current_position": current,
        "achieved_this_time": achieved[:6],
        "not_achieved_yet": not_yet[:6],
        "next_questions": next_steps[:5],
        "reading_note": (
            "細かい実験回数、内部の識別名、数値、計算設定は証拠として機械向け記録に残しています。"
            "ここでは、たくさん試した結果として目的地へ何が近づき、何がまだ足りないかを優先して伝えます。"
        ),
        "technical_details_preserved_elsewhere": True,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    """Render the first-read report without requiring internal vocabulary."""
    lines = [
        "# 自動研究レポート",
        "",
        "## 要するに、目的地はどこか",
        str(summary.get("destination") or ""),
        "",
        "## 現在地はどこか",
        str(summary.get("current_position") or ""),
        "",
        "## 今回できたこと",
    ]
    for item in summary.get("achieved_this_time") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## まだできていないこと"])
    for item in summary.get("not_achieved_yet") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## 次に確かめること"])
    for item in summary.get("next_questions") or []:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "---",
        str(summary.get("reading_note") or ""),
        "",
    ])
    return "\n".join(lines)


def first_read_violations(text: str) -> list[str]:
    """Return jargon/readability violations for CI and tests."""
    violations = [term for term in _FORBIDDEN_FIRST_READ if term.lower() in text.lower()]
    if _ASCII_NUMBER.search(text):
        violations.append("ASCII_NUMBER")
    return sorted(set(violations))
