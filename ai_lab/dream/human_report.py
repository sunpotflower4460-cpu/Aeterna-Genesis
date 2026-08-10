"""Human-first reporting for Aeterna autonomous research.

The scientific record remains machine-readable and complete.  This module creates a separate
reader-facing layer whose job is orientation, not data compression into unexplained jargon.

The main report always answers, in this order:
1. where are we trying to go,
2. where are we now,
3. what became possible / clearer this time,
4. what is still not achieved,
5. what will be tested next.

Raw hypothesis IDs, variable names, status codes, trial counts and regulator values stay in JSON and
technical evidence.  They are intentionally absent from the first-read prose.
"""
from __future__ import annotations

import re
from typing import Any


# Terms that are useful internally but should not be required to understand the first-read report.
# This is intentionally conservative: technical detail is preserved elsewhere rather than deleted.
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


def _fission_reference(report: dict[str, Any]) -> dict[str, Any]:
    value = report.get("zero_to_fission_path")
    return value if isinstance(value, dict) else {}


def _has_root_research(report: dict[str, Any]) -> bool:
    root = _root(report)
    return bool(root.get("law_trials") or root.get("top_laws") or root.get("root_integrity_audit"))


def build_summary(report: dict[str, Any]) -> dict[str, Any]:
    """Build an orientation-first Japanese summary from a full technical report.

    The wording is deliberately qualitative.  Exact counts and IDs remain available in the source report,
    while this summary answers the research-navigation questions a first-time reader actually needs.
    """
    counts = _night_counts(report)
    root = _root(report)
    fission = _fission_reference(report)

    destination = (
        "ほとんど何も形として決めていない出発点から、違いと関係が自然に育ち、"
        "まとまりが自分を保ったり、過去を生かしたり、先を見越して変わったりする働きまで"
        "生まれるかを確かめることです。最終的には、脳の形を先に与えず、脳に必要な働きが"
        "この流れの先に自然に現れるかを調べます。"
    )

    if _has_root_research(report):
        current = (
            "いまは、最小の出発点から生まれた小さな違いが、関係の中で広がって長く残れるかを"
            "調べている段階です。同時に、計算の都合でそう見えるだけの周期や閉じた形を"
            "本当の発見と取り違えないための監査も通しています。"
        )
    else:
        current = (
            "いまは、すでに決められた世界の中で、違いが生まれて関係が続く条件を広く探している段階です。"
            "まだ生命や脳そのものを作れた段階ではありません。"
        )

    achieved: list[str] = []
    if _has_root_research(report):
        achieved.append(
            "最小の出発点から試した関係の変わり方を、見かけの成功を除く監査まで含めて比較し、"
            "次に詳しく追う候補を絞り直せました。"
        )
        audit = root.get("root_integrity_audit") if isinstance(root.get("root_integrity_audit"), dict) else {}
        if audit:
            achieved.append(
                "全体が反転しているだけの変化や、計算用のつながりをそのまま発見と数える問題を"
                "自動で見抜き、研究の評価から外せるようになっています。"
            )
    if _int(counts.get("reproduced")) > 0 or "反復" in str(report.get("one_line") or ""):
        achieved.append(
            "条件や最初の偶然を変えても、似た変化がもう一度現れる例があることを確認できました。"
        )
    deepest = str(fission.get("deepest_label") or "")
    if deepest:
        # This is explicitly a downstream reference lane, not the north-star progress meter.
        achieved.append(
            "別の下流実験では、局所的な構造どうしが関係を作り、一時的に安定した並びになるところまでは"
            "観測されています。ただし、これは目的地までの正式な段階表ではありません。"
        )
    if not achieved:
        achieved.append(
            "今回は大きな到達を宣言する結果はありませんでしたが、調べていない条件を広げ、"
            "次に捨てるべき考えと残すべき考えを整理できました。"
        )

    not_yet = [
        "最初の小さな違いを増幅するだけでなく、新しい種類の違いそのものを自力で生み出したとはまだ言えません。",
        "空間や物理的な時間、記憶が、最小の出発点から自然に生まれたとはまだ言えません。",
        "生命の器や脳が生まれたとはまだ言えません。脳を作るための部品も最初から置いていません。",
    ]

    next_steps = [
        "いま見えている変化が、最初の小さな違いを単に大きくしているだけなのか、それとも新しい区別を生んでいるのかを確かめます。",
        "過去との差を使う仕組みが、まだ説明していない記憶をこっそり持ち込んでいないかを、使わない場合と比べます。",
        "計算用の名前やつながりを全部取り除いたあとにも、新しい閉じた関係が本当に残るかを確かめます。",
    ]

    return {
        "version": 1,
        "purpose": "first_read_orientation",
        "destination": destination,
        "current_position": current,
        "achieved_this_time": achieved,
        "not_achieved_yet": not_yet,
        "next_questions": next_steps,
        "reading_note": (
            "細かい実験回数、内部の識別名、数値、計算設定は、証拠として機械向け記録に残しています。"
            "この報告では、まず研究の意味と現在地が分かることを優先しています。"
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
    """Return jargon/readability violations for CI and tests.

    Japanese prose may naturally contain punctuation and symbols, but the orientation layer should not
    force a first-time reader to decode raw IDs or unexplained numerical readouts.
    """
    violations = [term for term in _FORBIDDEN_FIRST_READ if term.lower() in text.lower()]
    if _ASCII_NUMBER.search(text):
        violations.append("ASCII_NUMBER")
    return sorted(set(violations))
