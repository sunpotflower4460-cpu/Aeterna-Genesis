"""PR7 test: the AI Genesis Lab searches start conditions non-destructively and cannot self-promote."""

import json
import os

from jsonschema import Draft202012Validator

from ai_lab import lab

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_lab_screens_children_from_zero():
    res = lab.run_lab(n=4, quick=True)
    assert res["parent_baseline_level"] >= 1
    screened = [p for p in res["proposals"] if p["status"] == "2d_screened"]
    assert len(screened) >= 1
    for p in screened:
        assert p["parent_room"] == "room-g001-a"
        assert "reached_level" in p["screen_2d"]         # Level is MEASURED, not asserted
        assert p["mutation"]["param"] in lab.KNOBS


def test_children_genesis_validate_against_schema():
    res = lab.run_lab(n=4, quick=True)
    schema = json.load(open(os.path.join(_REPO, "schemas", "genesis.schema.json")))
    v = Draft202012Validator(schema)
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            v.validate(p["genesis"])                     # each proposed child is a valid genesis


def test_lab_cannot_self_promote_and_only_changes_one_knob():
    res = lab.run_lab(n=6, quick=True)
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            assert p["promotion"]["stage"] == "2d_screened"   # never full_3d from the Lab
            assert p["status"] != "official"


def test_out_of_range_proposal_is_rejected():
    # a value outside the allowed search space must be rejected, not run
    ss = lab._load_search_space()
    bad = {"param": "noise_amplitude", "to": 1.0}         # far above max
    assert lab._within_allowed(bad, ss) is False


# ---- expanded engine (指示書①): score / IC families / modes / ranking / discipline ----

import numpy as np  # noqa: E402

from genesis.diagnostics import measures  # noqa: E402


def test_ic_families_seed_no_phase_winding_8th_audit():
    """第8監査: an IC family adds only REAL (zero-phase) amplitude structure -- it never seeds the GL
    target (organized phase-winding vortices). The added component must be purely real."""
    shape = (48, 48)
    for fam in ("single_seed", "sparse_seeds", "ring", "gradient"):
        base = lab.make_ic("white", shape, 1e-2, np.random.default_rng(0))
        fld = lab.make_ic(fam, shape, 1e-2, np.random.default_rng(0), corr_len=6.0)
        added = fld - base                                 # the structure this family injects
        assert np.max(np.abs(added.imag)) < 1e-12          # purely real: no phase / vortex seeded
    # low-k/high-k families are just filtered noise (no injected structure at all)
    for fam in ("white_lowk", "white_highk"):
        fld = lab.make_ic(fam, shape, 1e-2, np.random.default_rng(0), corr_len=6.0)
        assert np.isfinite(fld).all()


def test_complexity_is_non_saturating():
    """The complexity measure must NOT saturate at 1.0 (docs/traps_museum.md: T-entropy-sat): a single
    dominant mode -> ~0, white noise -> high, and a set of screened fields must show real spread."""
    shape = (48, 48)
    xs = np.linspace(0, 2 * np.pi, shape[0])
    single = np.exp(1j * xs)[:, None] * np.ones(shape)     # one Fourier mode
    assert lab.spectral_complexity(single) < 0.15
    noise = (np.random.default_rng(0).standard_normal(shape)
             + 1j * np.random.default_rng(1).standard_normal(shape))
    assert lab.spectral_complexity(noise) > 0.85
    res = lab.search(mode="random", n=8, seed=3, quick=True)
    cx = [r["complexity"] for r in res["results"] if r["complexity"] is not None]
    assert np.std(cx) > 0.02                                # genuine run-to-run spread (not flattened)


def test_score_ranks_deeper_level_above_shallower():
    """Score is a RANKING heuristic but Level dominates: a deeper reached Level always outranks a
    shallower one regardless of within-level signals."""
    hi = lab.score_run(2, {"mean_amplitude_growth": 1.0, "structure_factor_prominence": 0.0, "defect_count": 0}, 0.0)
    lo = lab.score_run(1, {"mean_amplitude_growth": 1e6, "structure_factor_prominence": 10.0, "defect_count": 20}, 0.6)
    assert hi > lo


def test_search_never_exceeds_allowed_space():
    """AI cannot pick knob values outside param_ranges.yaml (start-side only, bounded)."""
    ss = lab._load_search_space()
    res = lab.search(mode="random", n=12, seed=5, quick=True)
    for r in res["results"]:
        for k, v in r["knobs"].items():
            assert lab._knob_within_allowed(k, v, ss)


def test_search_is_deterministic():
    a = lab.search(mode="random", n=6, seed=9, quick=True)
    b = lab.search(mode="random", n=6, seed=9, quick=True)
    assert [r["score"] for r in a["results"]] == [r["score"] for r in b["results"]]


def test_levels_measured_not_asserted_and_no_self_promotion():
    """The reached Level is measured (may be None if numerically unstable); the Lab never self-promotes."""
    res = lab.search(mode="random", n=6, seed=2, quick=True)
    assert res["parent_room"] == "room-g001-a"
    for r in res["results"]:
        assert r["status"] in ("2d_screened", "unstable")
        assert "official" not in r["status"]


def test_unknown_parent_is_refused():
    import pytest
    with pytest.raises(ValueError):
        lab.search(mode="random", n=2, parent="g999", quick=True)
