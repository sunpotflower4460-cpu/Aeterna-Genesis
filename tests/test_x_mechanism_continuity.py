from __future__ import annotations

import json
from pathlib import Path

from ai_lab.dream import research_continuity_entrypoint as continuity


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_x_mechanism_ledger_becomes_actionable_non_strict_handoff(monkeypatch, tmp_path: Path) -> None:
    ledger = _write(tmp_path / "x.json", {
        "patterns": {
            "X-a": {
                "latest_observations": 500,
                "target_events": 20,
                "unique_fresh_seed_groups": 10,
                "status": "SUPPORTED_SIMULATOR_SENSITIVITY_CANDIDATE",
                "leading_explanation": "scale-normalized explanation",
                "leading_sensitivity_candidate": {
                    "intervention": "drive-weaker",
                    "paired_n": 6,
                    "paired_hit_rate_delta": -0.5,
                },
                "next_question": "Break the paired sensitivity on holdout seeds.",
            }
        }
    })
    easy = _write(tmp_path / "easy.json", {"burst_id": "dream-test"})
    monkeypatch.setattr(continuity, "_X_MECHANISMS", ledger)
    monkeypatch.setattr(continuity.base, "_EASY", easy)

    lessons = continuity._x_mechanism_lessons()
    assert len(lessons) == 1
    lesson = lessons[0]
    assert lesson["kind"] == "x_mechanism_dissection"
    assert lesson["importance"] == "carry"
    assert lesson["snapshot"]["counts_as_strict_zero_evidence"] is False
    assert lesson["snapshot"]["causal_claim_about_nature"] is False

    candidate = continuity._candidate_rows(lessons, {"directions": []})[0]
    assert candidate["handoff_bucket"] == "x-mechanism"
    assert candidate["question_or_lesson"] == "Break the paired sensitivity on holdout seeds."


def test_x_mechanism_has_separate_reserved_capacity_from_raw_x() -> None:
    raw_x = [
        {
            "key": f"x:raw-{i}",
            "lane": "strict/open-ended-followup",
            "kind": "unknown_transition",
            "priority": 90,
            "importance": "carry",
            "snapshot": {
                "pattern_id": f"raw-{i}",
                "status": "REPEATED_SPECIFIC_CANDIDATE",
                "exact": {"hit": 10, "n": 12},
                "nearby": {"hit": 2, "n": 12},
                "contrast": {"hit": 0, "n": 12},
            },
            "source": "test",
        }
        for i in range(12)
    ]
    mechanisms = [
        {
            "key": f"x-mechanism:m-{i}",
            "lane": "x-mechanism-exploratory",
            "kind": "x_mechanism_dissection",
            "priority": 68,
            "importance": "carry",
            "snapshot": {
                "pattern_id": f"m-{i}",
                "status": "UNRESOLVED",
                "next_question": f"mechanism question {i}",
                "counts_as_strict_zero_evidence": False,
            },
            "source": "test",
        }
        for i in range(5)
    ]
    rows = continuity.diverse_carry_forward(raw_x + mechanisms, {"directions": []}, limit=20)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["handoff_bucket"]] = counts.get(row["handoff_bucket"], 0) + 1
    assert counts["unknown-x"] == continuity._BUCKET_CAPS["unknown-x"]
    assert counts["x-mechanism"] >= continuity._BUCKET_MINIMUMS["x-mechanism"]
    assert counts["x-mechanism"] <= continuity._BUCKET_CAPS["x-mechanism"]
