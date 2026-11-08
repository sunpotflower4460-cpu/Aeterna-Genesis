"""Protection of the scored results (v0.1.2).

The scored results under results/ must never be overwritten. run_audit.py refuses:
  * a run without --out (default),
  * an --out inside the scored results/ directory (also through a symlink),
  * an existing file, or an existing non-empty directory, as --out.
These tests check the refusal rules (no audit is run; refusals happen before any write) and that the
protected artifacts keep their recorded SHA-256 values, and that no unlisted file appears in results/.
"""
import hashlib
import json
import os
import subprocess
import sys

import pytest

import _setup  # noqa: F401
import run_audit as RA

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(HERE, "results")
PROTECTED = os.path.join(RES, "corrections", "PROTECTED_ARTIFACTS.json")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _protected():
    return json.load(open(PROTECTED, encoding="utf-8"))["artifacts"]


# ---------------------------------------------------------------- refusal rules
def test_default_run_without_out_is_refused():
    with pytest.raises(RA.OutputRefused, match="--out"):
        RA.resolve_output_dir(None)


def test_scored_results_directory_is_refused():
    with pytest.raises(RA.OutputRefused, match="protected"):
        RA.resolve_output_dir(RES)


def test_directory_inside_scored_results_is_refused(tmp_path):
    with pytest.raises(RA.OutputRefused, match="protected"):
        RA.resolve_output_dir(os.path.join(RES, "figures"))


def test_symlink_into_scored_results_is_refused(tmp_path):
    link = tmp_path / "link"
    try:
        os.symlink(RES, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    with pytest.raises(RA.OutputRefused, match="protected"):
        RA.resolve_output_dir(str(link))


def test_audit_directory_containing_results_is_refused():
    # HERE is not empty (it holds results/), so it is refused by the non-empty rule
    with pytest.raises(RA.OutputRefused):
        RA.resolve_output_dir(HERE)


def test_existing_file_is_refused(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(RA.OutputRefused, match="file"):
        RA.resolve_output_dir(str(f))


def test_existing_nonempty_directory_is_refused(tmp_path):
    (tmp_path / "old.csv").write_text("x")
    with pytest.raises(RA.OutputRefused, match="non-empty"):
        RA.resolve_output_dir(str(tmp_path))
    assert (tmp_path / "old.csv").read_text() == "x"      # untouched


def test_new_directory_is_created(tmp_path):
    new = tmp_path / "run_new"
    out = RA.resolve_output_dir(str(new))
    assert os.path.isdir(out) and not os.listdir(out)


def test_existing_empty_directory_is_accepted(tmp_path):
    out = RA.resolve_output_dir(str(tmp_path))
    assert out == os.path.realpath(str(tmp_path))


# ---------------------------------------------------------------- CLI refusal (before any work)
def _cli(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, "run_audit.py"), *args],
                          capture_output=True, text=True, cwd=HERE, timeout=120)


def test_cli_default_run_exits_2_and_writes_nothing():
    before = {p: _sha(os.path.join(HERE, p)) for p in _protected()}
    r = _cli()
    assert r.returncode == 2 and "REFUSED" in r.stderr
    assert {p: _sha(os.path.join(HERE, p)) for p in _protected()} == before


def test_cli_out_pointing_at_scored_results_exits_2_and_writes_nothing():
    before = {p: _sha(os.path.join(HERE, p)) for p in _protected()}
    r = _cli("--out", RES)
    assert r.returncode == 2 and "REFUSED" in r.stderr
    assert {p: _sha(os.path.join(HERE, p)) for p in _protected()} == before


# ---------------------------------------------------------------- protected artifacts unchanged
def test_protected_artifacts_keep_their_recorded_sha256():
    for rel, info in _protected().items():
        path = os.path.join(HERE, rel)
        assert os.path.exists(path), rel
        assert _sha(path) == info["sha256"], f"protected artifact changed: {rel}"
        assert os.path.getsize(path) == info["bytes"], rel


def test_no_unlisted_file_appears_in_scored_results():
    listed = set(_protected()) | {os.path.relpath(PROTECTED, HERE)}
    present = set()
    for root, _, names in os.walk(RES):
        for n in names:
            present.add(os.path.relpath(os.path.join(root, n), HERE))
    assert present == listed, f"unexpected files: {sorted(present - listed)}; missing: {sorted(listed - present)}"


def test_csv_summary_and_manifest_match_correction_log():
    log = json.load(open(os.path.join(RES, "corrections", "CORRECTIONS.json"), encoding="utf-8"))
    for name, info in log["scored_outputs_not_rewritten"].items():
        assert _sha(os.path.join(RES, name)) == info["sha256_now"] == info["sha256_at_scored_commit"], name
