"""P3 archive: every archived file is recorded, gone from the tree, and (with history) restorable."""

import gzip
import json
import os
import subprocess

import pytest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_MANIFEST = os.path.join(_REPO, "archive", "MANIFEST.jsonl.gz")

pytestmark = pytest.mark.skipif(not os.path.exists(_MANIFEST), reason="no archive manifest in this checkout")


def _manifest():
    with gzip.open(_MANIFEST, "rt", encoding="utf-8") as fh:
        header = json.loads(fh.readline())
        return header, [json.loads(line) for line in fh]


def _git(*args):
    return subprocess.run(["git", *args], cwd=_REPO, capture_output=True, text=True)


def test_header_matches_entries():
    header, entries = _manifest()
    assert header["files"] == len(entries) > 0
    assert header["bytes"] == sum(e["size"] for e in entries)
    assert all(len(e["blob"]) == 40 and e["reason"] for e in entries)


def test_archived_paths_are_not_tracked_anymore():
    _, entries = _manifest()
    tracked = set(_git("ls-files", "-z", "rooms/candidates", "ai_lab/reports", "app/public", "app/generated")
                  .stdout.split("\0"))
    assert not tracked & {e["path"] for e in entries}


def test_keep_full_rooms_stay_in_the_tree():
    with open(os.path.join(_REPO, "audit", "candidates.jsonl"), encoding="utf-8") as fh:
        keep = [json.loads(line)["room_id"] for line in fh if '"keep-full"' in line]
    assert keep and all(os.path.isfile(os.path.join(_REPO, "rooms", "candidates", r, "room.yaml")) for r in keep)


def test_sampled_entries_resolve_at_source_commit():
    header, entries = _manifest()
    commit = header["source_commit"]
    if _git("cat-file", "-e", commit + "^{commit}").returncode:
        pytest.skip("source commit not in local history (shallow clone); run `python tools/archive.py verify`")
    step = max(1, len(entries) // 20)
    for e in entries[::step][:20]:
        assert _git("rev-parse", f"{commit}:{e['path']}").stdout.strip() == e["blob"]
