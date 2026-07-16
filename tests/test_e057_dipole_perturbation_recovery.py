"""e057 H021-campaign Level-4 perturbation-recovery tests (role E-candidate/F -- mixed, honest result).

Recovery outcomes are legitimately stochastic (a random perturbation angle each seed), so tests check
structural correctness (candidate discovery, matched-control symmetry, coordinate-convention sanity) rather
than asserting a specific recovery outcome.
"""
import numpy as np

from experiments.e057_dipole_perturbation_recovery.dipole_perturbation_recovery import (
    run, run_one_seed, CONFIG_QUICK, L_FIXED, PERTURB_RADIUS,
)


def test_quick_run_is_valid():
    r = run(CONFIG_QUICK)
    assert r["run_valid"] is True
    assert r["n_seeds"] == CONFIG_QUICK["n_seeds"]


def test_candidate_found_and_control_recovers_by_construction():
    # the control branch replays the SAME unperturbed physics the pair was already surviving in --
    # it should recover (this is the baseline, not the test itself)
    row = run_one_seed(CONFIG_QUICK["seed_start"])
    assert row["found_candidate"] is True
    assert row["pre_bound_duration"] >= 20   # >= PRE_BOUND_MIN by construction
    assert row["control_recovered"] is True


def test_perturbation_mask_uses_correct_xy_convention():
    # regression test for the row/col (x/y) axis-swap bug found during development: a mask built from
    # a coordinate pair must be centered where core.vortex's (x=row, y=col) convention says it is.
    row_idx, col_idx = np.meshgrid(np.arange(L_FIXED), np.arange(L_FIXED), indexing="ij")
    cx, cy = 10.0, 70.0   # deliberately asymmetric (x far from y) to catch a swap
    dx = np.minimum(np.abs(row_idx - cx), L_FIXED - np.abs(row_idx - cx))
    dy = np.minimum(np.abs(col_idx - cy), L_FIXED - np.abs(col_idx - cy))
    mask = (dx * dx + dy * dy) <= PERTURB_RADIUS ** 2
    ys, xs = np.where(mask)
    # the masked region's centroid must sit near (cx, cy) in (row, col) = (x, y) order
    assert abs(float(np.mean(ys)) - cx) < 2.0
    assert abs(float(np.mean(xs)) - cy) < 2.0


def test_result_reports_both_branches_per_seed():
    r = run(CONFIG_QUICK)
    for row in r["per_seed"]:
        if row["found_candidate"]:
            assert "control_recovered" in row and "perturbed_recovered" in row
            assert isinstance(row["control_recovered"], bool)
            assert isinstance(row["perturbed_recovered"], bool)
