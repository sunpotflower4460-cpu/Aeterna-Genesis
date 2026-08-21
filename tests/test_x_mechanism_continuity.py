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
    assert candidate["handoff_bucket"] == "unknown-x"
    assert candidate["question_or_lesson"] == "Break the paired sensitivity on holdout seeds."
