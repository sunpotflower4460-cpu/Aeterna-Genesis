"""Standard-JSON validity of every audit output (FMT-1), and integrity of the correction log.

Strict means: json.loads with parse_constant rejecting NaN, Infinity and -Infinity. The only exempt file is the
preserved byte copy of the scored summary.json, which is non-standard by design. Its SHA-256 is checked against
the value recorded in results/corrections/CORRECTIONS.json, so it cannot be silently edited.
"""
import glob
import hashlib
import json
import math
import os

import pytest

import _setup  # noqa: F401
import strict_json as SJ

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES = os.path.join(HERE, "results")
PRESERVED = os.path.join("results", "corrections", "summary.pre-json-fix.json")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _log():
    return json.load(open(os.path.join(RES, "corrections", "CORRECTIONS.json"), encoding="utf-8"))


def test_every_result_json_is_standard_json():
    for f in sorted(glob.glob(os.path.join(RES, "**", "*.json"), recursive=True)):
        rel = os.path.relpath(f, HERE)
        if rel == PRESERVED:
            continue
        SJ.strict_loads(open(f, encoding="utf-8").read())   # raises on NaN / Infinity


def test_preserved_original_is_exactly_the_recorded_pre_change_file():
    entry = _log()["corrections"][0]
    assert _sha(os.path.join(HERE, PRESERVED)) == entry["pre_change_sha256"]
    with pytest.raises(ValueError):                          # it really is the non-standard original
        SJ.strict_loads(open(os.path.join(HERE, PRESERVED), encoding="utf-8").read())


def test_corrected_summary_matches_recorded_post_change_sha():
    entry = _log()["corrections"][0]
    assert _sha(os.path.join(RES, "summary.json")) == entry["post_change_sha256"]


def test_scored_csv_manifest_and_test_results_untouched_since_scored_commit():
    recorded = _log()["scored_outputs_not_rewritten"]
    for name, info in recorded.items():
        assert _sha(os.path.join(RES, name)) == info["sha256_now"] == info["sha256_at_scored_commit"], name


def test_sanitize_nulls_nonfinite_values_and_reports_paths():
    obj = {"a": 1.0, "b": {"c": float("nan"), "d": [float("inf"), 2.0]}, "e": "x"}
    clean, nulled = SJ.sanitize(obj)
    assert clean == {"a": 1.0, "b": {"c": None, "d": [None, 2.0]}, "e": "x"}
    assert [p for p, _ in nulled] == ["b.c", "b.d[0]"]


def test_dumps_refuses_nonfinite_numbers():
    with pytest.raises(ValueError):
        SJ.dumps({"x": float("nan")})
    assert SJ.strict_loads(SJ.dumps({"x": None})) == {"x": None}


def test_summary_nonfinite_field_is_null_with_reason():
    summary = json.load(open(os.path.join(RES, "summary.json"), encoding="utf-8"))
    order = summary["headline"]["T10_rk4_order"]
    fields = {e["path"]: e for e in summary["json_null_fields"]}
    assert order is None
    assert "headline.T10_rk4_order" in fields
    assert "INCONCLUSIVE" in fields["headline.T10_rk4_order"]["reason"]
    assert fields["headline.T10_rk4_order"]["original"] == "nan"


def test_finalize_summary_gives_standard_json_for_a_fresh_nan():
    raw = {"headline": {"order": float("nan"), "ok": 1.5}, "overall": "INCONCLUSIVE"}
    out = SJ.finalize_summary(raw)
    text = SJ.dumps(out)
    back = SJ.strict_loads(text)
    assert back["headline"]["order"] is None and back["headline"]["ok"] == 1.5
    assert back["json_null_fields"][0]["path"] == "headline.order"
    assert not math.isnan(back["headline"]["ok"])
