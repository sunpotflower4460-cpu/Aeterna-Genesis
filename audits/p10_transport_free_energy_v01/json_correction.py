"""One-time, format-only correction of results/summary.json (correction FMT-1, v0.1.1).

Problem: the scored summary.json contains the bare token NaN (not valid JSON) at headline.T10_rk4_order.
Fix: replace that non-finite value by null and record the reason in a separate field. No other value
changes. This script refuses to change anything else, and it verifies that every other field is equal
to the scored original before writing.

Preserved, not overwritten:
  results/corrections/summary.pre-json-fix.json   byte copy of the scored summary.json (pre-change SHA-256 recorded)
  results/numerical_results.csv                   scored CSV, not rewritten
  results/manifest.json, results/test_results.json  scored records, not rewritten
Written:
  results/summary.json                            corrected format
  results/corrections/CORRECTIONS.json            correction log with SHA-256 before and after

Idempotent: if summary.json already parses as strict JSON, nothing is changed.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import strict_json as SJ  # noqa: E402

RES = os.path.join(HERE, "results")
CORR = os.path.join(RES, "corrections")
SUMMARY = os.path.join(RES, "summary.json")
PRE_COPY = os.path.join(CORR, "summary.pre-json-fix.json")
LOG = os.path.join(CORR, "CORRECTIONS.json")
SCORED_HEAD = "08309554c84e5aaade625947d0d4bc3bfc519ac7"   # commit that holds the scored results


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def git_show_sha(commit, relpath):
    out = subprocess.run(["git", "show", f"{commit}:{relpath}"], cwd=REPO, capture_output=True)
    return sha256_bytes(out.stdout) if out.returncode == 0 else None


def same(a, b):
    """Deep equality where None stands for the nulled value and everything else must match exactly."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main():
    raw = open(SUMMARY, "rb").read()
    try:
        SJ.strict_loads(raw.decode("utf-8"))
        print("summary.json is already strict JSON; nothing to do")
        return
    except ValueError:
        pass

    os.makedirs(CORR, exist_ok=True)
    if not os.path.exists(PRE_COPY):
        shutil.copyfile(SUMMARY, PRE_COPY)
    pre_sha = sha256_bytes(open(PRE_COPY, "rb").read())
    if pre_sha != sha256_bytes(raw):
        raise SystemExit("summary.json changed after the preserved copy was made; stop and inspect")

    original = json.loads(raw.decode("utf-8"))          # Python accepts NaN here, only for reading the scored file
    corrected = SJ.finalize_summary(original)

    # every field other than the nulled one and the new reason fields must be identical to the scored value
    checked = {k: v for k, v in corrected.items() if k != "json_null_fields"}
    orig_checked = dict(original)
    assert same({k: v for k, v in checked.items() if k != "headline"},
                {k: v for k, v in orig_checked.items() if k != "headline"}), "non-headline field changed"
    h_new = dict(checked["headline"])
    h_old = dict(orig_checked["headline"])
    assert h_new.keys() == h_old.keys()
    for k in h_old:
        if k == "T10_rk4_order":
            assert h_old[k] != h_old[k] and h_new[k] is None, "expected exactly this NaN to become null"
        else:
            assert same(h_new[k], h_old[k]), f"headline field changed: {k}"
    nulled_paths = [e["path"] for e in corrected["json_null_fields"]]
    assert nulled_paths == ["headline.T10_rk4_order"], nulled_paths

    text = SJ.dumps(corrected, ensure_ascii=False, indent=2) + "\n"
    SJ.strict_loads(text)                                # must be standard JSON before we write it
    with open(SUMMARY, "w", encoding="utf-8") as fh:
        fh.write(text)
    post_sha = sha256_bytes(text.encode("utf-8"))

    other = {}
    for name in ("numerical_results.csv", "manifest.json", "test_results.json"):
        path = os.path.join(RES, name)
        other[name] = {"sha256_now": sha256_bytes(open(path, "rb").read()),
                       "sha256_at_scored_commit": git_show_sha(SCORED_HEAD, f"audits/p10_transport_free_energy_v01/results/{name}")}
    log = {
        "file": "audits/p10_transport_free_energy_v01/results/summary.json",
        "corrections": [{
            "id": "FMT-1",
            "kind": "format only (non-standard JSON -> standard JSON)",
            "change": "headline.T10_rk4_order: NaN -> null; reason recorded in json_null_fields[0].reason",
            "numeric_or_verdict_change": False,
            "verified_equal_fields": "all other fields of the scored summary are equal to the original",
            "pre_change_sha256": pre_sha,
            "pre_change_copy": "audits/p10_transport_free_energy_v01/results/corrections/summary.pre-json-fix.json",
            "post_change_sha256": post_sha,
        }],
        "scored_outputs_not_rewritten": other,
        "code_changes_after_scored_run": {
            "run_audit.py": {"sha256_at_scored_commit": git_show_sha(SCORED_HEAD, "audits/p10_transport_free_energy_v01/run_audit.py"),
                             "sha256_now": sha256_bytes(open(os.path.join(HERE, "run_audit.py"), "rb").read()),
                             "why": "JSON writes now use strict_json (format only). Scored run was not repeated."},
        },
        "note": "manifest.json code hashes describe the code that produced the scored run; they were not regenerated.",
    }
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write(SJ.dumps(log, ensure_ascii=False, indent=2) + "\n")
    print("corrected summary.json")
    print("pre :", pre_sha)
    print("post:", post_sha)


if __name__ == "__main__":
    main()
