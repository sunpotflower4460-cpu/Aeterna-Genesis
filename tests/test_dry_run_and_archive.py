from __future__ import annotations

import json
from ai_lab.dream import dry_run, ledger_archive


def test_dry_run_redirects_and_prefers_scratch(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    target = repo / "ai_lab" / "discoveries" / "ledger.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"v":"real"}')
    monkeypatch.setattr(dry_run, "_REPO", repo)
    scratch = dry_run.activate("unit")
    try:
        assert json.loads(target.read_text())["v"] == "real"
        target.write_text('{"v":"dry"}')
        assert json.loads(target.read_text())["v"] == "dry"
    finally:
        dry_run.deactivate()
    assert json.loads(target.read_text())["v"] == "real"
    assert (scratch / "ai_lab" / "discoveries" / "ledger.json").exists()


def test_dry_run_is_inert_until_activated(tmp_path):
    assert not dry_run.is_active()
    p = tmp_path / "plain.json"
    p.write_text("{}")
    assert p.read_text() == "{}"


def test_archive_preserves_all_and_seals_parts(tmp_path):
    hot = tmp_path / "event_ledger.json"
    archive = ledger_archive.archive_dir_for(hot)
    doc = {"events": [{"event_id": f"evt-{i:03d}"} for i in range(8)]}
    ledger_archive.roll(doc, list_key="events", id_key="event_id", keep=3, archive_dir=archive, name="events", burst_id="b1")
    first = sorted(archive.glob("*.json"))[0]
    sealed = first.read_bytes()
    doc["events"].extend({"event_id": f"evt-{i:03d}"} for i in range(8, 14))
    ledger_archive.roll(doc, list_key="events", id_key="event_id", keep=3, archive_dir=archive, name="events", burst_id="b2")
    hot.write_text(json.dumps(doc))
    assert first.read_bytes() == sealed
    assert len(doc["events"]) == 3
    assert len(ledger_archive.load_all(hot, list_key="events")) == 14


def test_archived_ids_stay_out_of_hot_window(tmp_path):
    hot = tmp_path / "event_ledger.json"
    doc = {"events": [{"event_id": f"evt-{i:03d}"} for i in range(6)]}
    ledger_archive.roll(doc, list_key="events", id_key="event_id", keep=2, archive_dir=ledger_archive.archive_dir_for(hot), name="events")
    cold = ledger_archive.archived_ids(doc)
    assert cold
    assert all(e["event_id"] not in cold for e in doc["events"])
