"""Regressions for hourly Dream continuity and first-read report grammar.

These cover three failures that were observed in production evidence rather than in unit tests:
run_number restarting at 0001 after a cache miss, the state file living in a gitignored path, and
noun-phrase capability labels producing an ungrammatical "not yet achieved" sentence.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_lab.dream import human_report, loop
from ai_lab.dream.adaptive_loop import _run_number_from_report

_REPO = Path(__file__).resolve().parents[1]


def test_state_file_is_tracked_by_git() -> None:
    """The counter/cursor state must not be gitignored: a cache miss would restart the search."""
    rel = loop._STATE.relative_to(_REPO).as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", rel], cwd=_REPO, check=False,
    ).returncode == 0
    assert not ignored, f"{rel} is gitignored; run_number and search cursors cannot survive"


def test_load_state_falls_back_to_legacy_runtime_copy(tmp_path, monkeypatch) -> None:
    legacy = tmp_path / "runtime" / "dream" / "state.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(json.dumps({"state_version": 3, "run_number": 22, "mass_2d_cursor": 900}))
    monkeypatch.setattr(loop, "_STATE", tmp_path / "ai_lab" / "discoveries" / "dream_state.json")
    monkeypatch.setattr(loop, "_LEGACY_STATE", legacy)

    state = loop.load_state()
    assert state["run_number"] == 22
    assert state["mass_2d_cursor"] == 900


def test_run_number_recovers_from_last_report(tmp_path) -> None:
    """A lost state must not restart burst ids; the last committed report is the floor."""
    report = tmp_path / "latest.json"
    report.write_text(json.dumps({"burst_id": "dream-20260810-0022"}))
    assert _run_number_from_report(report) == 22

    report.write_text(json.dumps({"burst_id": "not-a-burst"}))
    assert _run_number_from_report(report) == 0
    assert _run_number_from_report(tmp_path / "missing.json") == 0


def test_noun_phrase_gap_labels_stay_grammatical() -> None:
    """Capability labels are a mix of verb and noun phrases; both must read as Japanese."""
    summary = human_report.build_summary({
        "autonomous_frontier_expansion": {
            "human": {"largest_gaps": ["ラベルを消しても残る閉じた関係", "まとまりが個体として自分を保つ"]},
        },
    })
    not_yet = summary["not_achieved_yet"]
    assert any("「ラベルを消しても残る閉じた関係」までは" in line for line in not_yet)
    assert not any("関係ところまでは" in line for line in not_yet)
    assert human_report.first_read_violations(human_report.render_markdown(summary)) == []
