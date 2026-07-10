#!/usr/bin/env python3
"""8th-audit CI guard (LAW.md §6/§7): scan every experiment's YAML header and enforce the role rules.

Each experiment `.py` may carry a YAML block (between `---` fences or as loose `key: value` lines in the
docstring) with `id / role / claim_tier / target_encoded`. This tool enforces:

  RULE 1 (8th audit): if `target_encoded: true`, the role MUST be one of S / F / Q -- NEVER E or V.
                      (A conclusion embedded in the gate/IC cannot be called an emergence or a validation.)
  RULE 2: `role` must be one of E / V / S / N / F / Q.

It prints a registry table (id, role, claim_tier, target_encoded) and exits non-zero on any violation, so CI
mechanically prevents a target_encoded result from wearing a GREEN (E/V) badge. Experiments with no YAML
header are listed as `role: -` (not yet classified) and do NOT fail the build.
"""

import os
import re
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_EXP = os.path.join(_ROOT, "experiments")
_VALID_ROLES = {"E", "V", "S", "N", "F", "Q"}
_GREEN_ROLES = {"E", "V"}


def _parse_header(text):
    """Pull id/role/claim_tier/target_encoded from a YAML-ish header (fenced or loose) if present."""
    fields = {}
    for key in ("id", "role", "claim_tier", "target_encoded"):
        m = re.search(r"^\s*%s:\s*([^\n#]+)" % key, text, re.MULTILINE)
        if m:
            fields[key] = m.group(1).strip().strip('"').strip("'")
    return fields


def scan():
    rows, violations = [], []
    for d in sorted(os.listdir(_EXP)):
        dpath = os.path.join(_EXP, d)
        if not os.path.isdir(dpath) or not d.startswith("e"):
            continue
        for fn in sorted(os.listdir(dpath)):
            if not fn.endswith(".py") or fn == "__init__.py" or fn == "robustness.py":
                continue
            with open(os.path.join(dpath, fn)) as f:
                head = f.read(4000)                       # header lives at the top
            hdr = _parse_header(head)
            if "role" not in hdr:
                continue
            role = hdr.get("role", "-")
            te = hdr.get("target_encoded", "false").lower() == "true"
            rid = hdr.get("id", "%s/%s" % (d, fn))
            rows.append((rid, role, hdr.get("claim_tier", "-"), te))
            if role not in _VALID_ROLES:
                violations.append("%s: invalid role '%s' (must be E/V/S/N/F/Q)" % (rid, role))
            if te and role in _GREEN_ROLES:
                violations.append("%s: target_encoded=true but role=%s (E/V forbidden -> must be S/F/Q)"
                                  % (rid, role))
    return rows, violations


def main():
    rows, violations = scan()
    print("=== role registry (id | role | claim_tier | target_encoded) ===")
    for rid, role, tier, te in rows:
        print("  %-16s | %-2s | %-12s | target_encoded=%s" % (rid, role, tier, te))
    counts = {}
    for _, role, _, _ in rows:
        counts[role] = counts.get(role, 0) + 1
    print("  counts:", ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    if violations:
        print("\n=== 8th-audit VIOLATIONS ===")
        for v in violations:
            print("  [FAIL] %s" % v)
        return 1
    print("\n8th-audit OK: no target_encoded result claims an E/V (GREEN) role.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
