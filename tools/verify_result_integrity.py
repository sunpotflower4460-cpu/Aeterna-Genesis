#!/usr/bin/env python3
"""Historical-artifact integrity guard (research-continuity gap G4). role: governance/tooling.

WHY: committed result JSONs and recorded Room fields are the repo's MEMORY of what was measured. Today CI only
checks they *exist* and *schema-validate* -- an observer/measure change could silently rewrite the NUMBERS in a
past result in place and CI would stay green. This guard records a sha256 of every committed historical artifact
in `tools/result_integrity.json` and fails if any listed artifact's content changed, so a rewrite of the past
must be a DELIBERATE, reviewed `--update` (a visible diff), never silent. It does NOT change any result.

Covered (git-tracked only, deterministic): experiments/*/results/*.json and every rooms/official/**/*.json
(emergence / checksum / manifest / summary / convergence / field.json ...).

Usage:
    python tools/verify_result_integrity.py            # verify; exit 1 on any changed/missing listed artifact
    python tools/verify_result_integrity.py --update   # regenerate the manifest (do this only on an intended change)
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "tools", "result_integrity.json")
PATTERNS = ["experiments/*/results/*.json", "rooms/official/**/*.json"]


def _tracked_files():
    """git-tracked artifacts matching PATTERNS (sorted, deterministic; manifest excluded)."""
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "--"] + PATTERNS,
                         capture_output=True, text=True, check=True).stdout.split("\n")
    files = sorted(p for p in out if p and p != "tools/result_integrity.json")
    return files


def _sha256(relpath):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, relpath), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build():
    return {relpath: _sha256(relpath) for relpath in _tracked_files()}


def main(argv=None):
    ap = argparse.ArgumentParser(description="verify committed result artifacts are byte-unchanged (G4)")
    ap.add_argument("--update", action="store_true", help="regenerate the manifest (intended change only)")
    args = ap.parse_args(argv)

    current = build()
    if args.update:
        with open(MANIFEST, "w") as f:
            json.dump({"note": "sha256 of committed historical result artifacts; a mismatch means a past "
                               "result was rewritten. Update ONLY on an intended, reviewed change.",
                       "patterns": PATTERNS, "count": len(current), "hashes": current}, f, indent=2, sort_keys=True)
            f.write("\n")
        print("wrote %s (%d artifacts)" % (os.path.relpath(MANIFEST, ROOT), len(current)))
        return 0

    if not os.path.exists(MANIFEST):
        print("RESULT-INTEGRITY: no manifest yet; run --update to create it.")
        return 1
    stored = json.load(open(MANIFEST))["hashes"]
    changed = sorted(p for p in stored if p not in current or current[p] != stored[p])
    missing = sorted(p for p in stored if p not in current)
    unlisted = sorted(p for p in current if p not in stored)
    for p in changed:
        print("  [CHANGED] %s" % p + (" (MISSING)" if p in missing else ""))
    for p in unlisted:
        print("  [unlisted-new] %s (run --update to record it)" % p)   # warn only: new results are expected
    ok = not changed
    print("RESULT-INTEGRITY: %s (%d tracked, %d changed, %d unlisted-new)"
          % ("GREEN" if ok else "RED", len(current), len(changed), len(unlisted)))
    if not ok:
        print("  -> a past result artifact changed. If intended, run: python tools/verify_result_integrity.py --update")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
