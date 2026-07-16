"""Tests for e059 (H021 campaign, PR-C, role V): 3D vortex-line tracer validated on the seeded
ring (e003's setup, unchanged). Not a claim about emergence -- an instrument-validation experiment.
"""
from experiments.e059_vortex_line_tracer_validation.vortex_line_tracer_validation import run, evaluate


def test_quick_run_produces_comparable_frames():
    r = run(quick=True)
    assert r["run_valid"] is True
    assert r["n_samples"] > 0
    assert r["n_both_instruments"] > 0


def test_early_clean_window_agreement_is_close():
    # the first few samples (right after imaginary-time relaxation, before sound accumulates) must
    # show close radius agreement between the new tracer and the existing e003 meridional tracker
    r = run(quick=True)
    both = [f for f in r["frames"] if f["new_matched_loop"] is not None and f["old_tracker"] is not None]
    assert len(both) >= 2
    first = both[0]
    diff0 = abs(first["new_matched_loop"]["effective_radius"] - first["old_tracker"]["radius"])
    assert diff0 < 0.25 * r["params"]["R"]


def test_no_overloaded_cubes_ever():
    # multi-line ambiguity (>2 pierced faces per cube) should not occur for this single-ring setup
    r = run(quick=True)
    assert all(f["new_n_overloaded"] == 0 for f in r["frames"])


def test_evaluate_returns_checks_dict():
    r = run(quick=True)
    passed, checks = evaluate(r, quick=True)
    assert isinstance(passed, bool)
    assert "enough_frames_to_compare" in checks
    assert "radius_agrees_majority_of_frames" in checks
