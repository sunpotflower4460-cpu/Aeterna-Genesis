import json
import subprocess

import pytest

from tools import study_record as study


@pytest.fixture
def registered(tmp_path):
    plan = tmp_path / "PLAN.json"
    solver = tmp_path / "solver.py"
    solver.write_text("rate = 0\n")
    fields = ("question", "prior_access", "independent_unit", "inputs", "measurement", "alternatives", "stopping")
    plan.write_text(json.dumps({**{k: k for k in fields}, "version": 1, "tracked_inputs": ["solver.py"],
                                "cases": {"zero": {}, "other": {}}}))
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], text=True).strip()
    git("init", "-q")
    git("add", "PLAN.json", "solver.py")
    git("-c", "user.email=audit@example.invalid", "-c", "user.name=Audit", "-c", "commit.gpgsign=false",
        "commit", "-qm", "registered")
    output = tmp_path / "evidence"
    output.mkdir()
    raw = output / "zero.json"
    raw.write_text('{"displacement": 0}\n')
    record = output / "record.json"
    record.write_text(json.dumps({"registration_commit": git("rev-parse", "HEAD"), "cases": {
        "zero": [{"status": "failed", "reason": "interrupted before measurement"},
                 {"status": "completed", "artifacts": {"zero.json": study.sha256(raw)}}],
        "other": [{"status": "not_run", "reason": "budget exhausted"}]}}))
    return plan, record


def test_denominator_and_prior_attempts_survive(registered):
    plan, record = registered
    assert study.check_record(plan, record) == {
        "planned_cases": 2, "attempts_by_status": {"failed": 1, "completed": 1, "not_run": 1}, "verified_files": 1}
    data = study.read_object(record)
    del data["cases"]["other"]
    record.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="differ"):
        study.check_record(plan, record)


@pytest.mark.parametrize("changed", ["PLAN.json", "solver.py", "evidence/zero.json"])
def test_changed_plan_input_or_evidence_is_detected(registered, changed):
    plan, record = registered
    with (plan.parent / changed).open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="changed since registration|SHA-256 mismatch"):
        study.check_record(plan, record)


def test_duplicate_case_keys_and_missing_reasons_are_rejected(registered):
    plan, record = registered
    data = study.read_object(record)
    data["cases"]["other"] = [{"status": "stopped"}]
    record.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="why"):
        study.check_record(plan, record)
    record.write_text('{"cases":{"zero":[],"zero":[]}}')
    with pytest.raises(ValueError, match="duplicate JSON key"):
        study.check_record(plan, record)
