"""e048 P07/F1 basin-decision calibration tests (role V, physics-free — placed known basins)."""
import numpy as np

from experiments.e048_field_slow_field_calib.field_slow_field_calib import (
    basin_ref, assign_basin, run, CONFIG_QUICK)
from genesis.diagnostics.winding_reliability import winding_reliability as wr


def test_basins_are_separable_by_winding_reliability():
    L = 32
    for w in (0, 1, 2):
        r = wr(basin_ref(L, w), axis=0)
        assert r["dominant_winding"] == w and r["dominant_fraction"] > 0.99 and r["invalid_fraction"] == 0.0


def test_clean_states_assign_to_own_basin_with_margin():
    L = 32
    refs = [basin_ref(L, k) for k in (0, 1, 2)]
    for k in (0, 1, 2):
        basin, margin, _ = assign_basin(refs[k], refs)
        assert basin == k and margin > 1e-6


def test_morph_is_flagged_ambiguous():
    L = 32
    refs = [basin_ref(L, k) for k in (0, 1, 2)]
    morph = refs[0].copy(); morph[L // 2:, :] = refs[1][L // 2:, :]
    _b, m_margin, _ = assign_basin(morph, refs)
    clean_margin = min(assign_basin(refs[0], refs)[1], assign_basin(refs[1], refs)[1])
    assert m_margin < 0.5 * clean_margin


def test_gauge_invariance_of_basin_assignment():
    L = 32
    refs = [basin_ref(L, k) for k in (0, 1, 2)]
    b0, _, _ = assign_basin(refs[1], refs)
    b1, _, _ = assign_basin(np.exp(1j * 1.1) * refs[1], refs)     # global phase must not change the basin
    assert b0 == b1 == 1


def test_full_calibration_is_green():
    r = run(CONFIG_QUICK)
    assert r["all_ok"], [k for k, v in r["checks"].items() if not v]
    s = r["scales"]
    assert s["d_identical"] < s["d_same_basin"] < s["d_different_basin"]
    assert r["calibrated_bands"]["copy_band"] < r["calibrated_bands"]["detachment_band"]
