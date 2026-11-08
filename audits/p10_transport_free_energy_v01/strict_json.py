"""Strict JSON output helpers for the P10 transport audit (v0.1.1).

Python's json module writes NaN and Infinity by default, which is not valid JSON (RFC 8259).
This module makes every JSON output of the audit standard JSON:

* `sanitize` replaces each non-finite float by null and reports its path and a reason,
* `finalize_summary` applies that to the audit summary and records the nulled fields in
  `json_null_fields`, so the reason is visible next to the value (not hidden),
* `dumps` uses `allow_nan=False`, so any non-finite value that slips past `sanitize` raises
  instead of producing invalid JSON.

Only the output format changes. Numerical values and verdicts are not touched here.
"""
import json
import math

DEFAULT_REASON = "non-finite value (NaN or Infinity) is not valid JSON; written as null"

# Reasons for specific non-finite fields, keyed by dotted path inside the summary.
REASONS = {
    "headline.T10_rk4_order": (
        "T10c order cannot be measured: both RK4 errors (dt=2e-5 and 1e-5, L1 vs BDF reference rtol 1e-11) "
        "are <= 1e-9, the reference-error floor (AMD-1). Verdict T10c = INCONCLUSIVE, unchanged."
    ),
}


def _is_nonfinite(x):
    return isinstance(x, float) and (math.isnan(x) or math.isinf(x))


def sanitize(obj, path=""):
    """Return (clean, nulled) where non-finite floats are replaced by None.

    `nulled` is a list of (dotted_path, original_repr) for every replaced value.
    """
    nulled = []

    def walk(o, p):
        if isinstance(o, dict):
            return {k: walk(v, f"{p}.{k}" if p else str(k)) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [walk(v, f"{p}[{i}]") for i, v in enumerate(o)]
        if _is_nonfinite(o):
            nulled.append((p, repr(o)))
            return None
        return o

    return walk(obj, path), nulled


def finalize_summary(summary):
    """Null every non-finite value in the summary and list the nulled paths with reasons."""
    clean, nulled = sanitize(summary)
    if nulled:
        clean["json_null_fields"] = [
            {"path": p, "original": orig, "reason": REASONS.get(p, DEFAULT_REASON)} for p, orig in nulled
        ]
    return clean


def dumps(obj, **kw):
    """Standard JSON. Raises ValueError if a non-finite number is present."""
    return json.dumps(obj, allow_nan=False, **kw)


def strict_loads(text):
    """Parse JSON and reject NaN / Infinity / -Infinity tokens (a strict validator)."""

    def reject(token):
        raise ValueError(f"non-standard JSON constant: {token}")

    return json.loads(text, parse_constant=reject)
