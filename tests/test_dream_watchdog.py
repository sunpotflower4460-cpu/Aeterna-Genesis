from datetime import datetime, timedelta, timezone
import json

from ai_lab.dream.watchdog import should_run_backup


def _write(tmp_path, generated_at):
    p = tmp_path / "latest.json"
    p.write_text(json.dumps({"generated_at": generated_at}))
    return p


def test_backup_skips_when_latest_report_is_fresh(tmp_path):
    now = datetime(2026, 8, 7, 13, 47, tzinfo=timezone.utc)
    p = _write(tmp_path, (now - timedelta(minutes=25)).isoformat())
    run, reason = should_run_backup(p, now=now, max_age_minutes=70)
    assert run is False
    assert "fresh" in reason


def test_backup_runs_when_latest_report_is_stale(tmp_path):
    now = datetime(2026, 8, 7, 13, 47, tzinfo=timezone.utc)
    p = _write(tmp_path, (now - timedelta(minutes=71)).isoformat())
    run, reason = should_run_backup(p, now=now, max_age_minutes=70)
    assert run is True
    assert "stale" in reason


def test_backup_fails_open_on_missing_or_broken_report(tmp_path):
    missing = tmp_path / "missing.json"
    assert should_run_backup(missing)[0] is True

    broken = tmp_path / "broken.json"
    broken.write_text("not-json")
    assert should_run_backup(broken)[0] is True


def test_backup_fails_open_on_implausible_future_timestamp(tmp_path):
    now = datetime(2026, 8, 7, 13, 47, tzinfo=timezone.utc)
    p = _write(tmp_path, (now + timedelta(minutes=10)).isoformat())
    run, reason = should_run_backup(p, now=now, max_age_minutes=70)
    assert run is True
    assert "future" in reason
