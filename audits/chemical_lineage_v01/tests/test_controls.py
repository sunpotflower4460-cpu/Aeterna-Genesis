"""T04, T09–T10, T12–T13: controls, determinism, seed independence, and no false inheritance from carryover."""
import numpy as np

import _setup  # noqa: F401
import controls as C
import run_audit as RA
import solver as S
import thermodynamics as TH


def test_T04_passive_arm_has_zero_reaction_rates():
    """LN: each generation starts from the protocol transfer and does not change during the generation."""
    f = 0.1
    ends = C.run_arm("LN", 2, 2.0, f, 3)
    fresh = np.array([0.9, 0.9, 0.9, 0, 0, 0.0])
    for s in range(2):
        for g in range(1, 4):
            start = f * ends[s, g - 1] + fresh
            assert np.allclose(ends[s, g], start, atol=1e-12)


def test_T09_same_inputs_give_bitwise_identical_runs():
    a = C.run_arm("L1", 3, 2.0, 0.1, 4)
    b = C.run_arm("L1", 3, 2.0, 0.1, 4)
    assert np.array_equal(a, b)


def test_T10_different_seeds_give_different_initial_states_and_series_differ():
    s0, s1 = C.seed_state(0), C.seed_state(1)
    assert not np.allclose(s0, s1)
    a = C.run_arm("L1", 3, 2.0, 0.1, 2)
    assert not np.allclose(a[0, 1], a[1, 1])


def test_T12_generation_correlation_alone_is_not_inheritance():
    """A purely passive dilution produces a parent-related series over generations but must not be classified
    as parent-specific persistence beyond dilution (it decays as f^g)."""
    f, n_series, n_gen = 0.1, 12, 6
    rng = np.random.default_rng(0)
    d0 = np.abs(rng.normal(0.3, 0.05, size=n_series))
    rows = []
    for g in range(n_gen + 1):
        for s in range(n_series):
            rows.append({"tau": 2.0, "f": f, "gen": g, "series": s, "disp_L1": d0[s] * f ** g,
                         "passive_expectation": d0[s] * f ** g, "offset_L1_LS": 0.0, "offset_L1_LR": 0.0})
    pr = {"delta_abs": 0.01, "delta_noise_floor_abs": 1e-6, "bootstrap_resamples": 2000, "bootstrap_seed": 0}
    v = RA.verdicts_for(rows, 2.0, f, pr, n_gen)
    assert v["C_parent_specific_persistence_to_g5_present"] is False
    assert v["Q2_excess_over_passive_at_g1"] == "NOT_DISTINGUISHABLE_FROM_PASSIVE"


def test_T13_exact_passive_dilution_matches_f_power_g():
    """With zero reaction constants, the difference between two lineages decays exactly as f^g."""
    f = 0.1
    a = C.seed_state(0)
    b = C.seed_state(1)
    xa, xb = a.copy(), b.copy()
    d0 = 0.5 * np.sum(np.abs(xa - xb))
    for g in range(1, 5):
        xa = f * xa + (1 - f) * np.array([1, 1, 1, 0, 0, 0.0])
        xb = f * xb + (1 - f) * np.array([1, 1, 1, 0, 0, 0.0])
        assert abs(0.5 * np.sum(np.abs(xa - xb)) - (f ** g) * d0) < 1e-14


def test_T04_zero_rate_constants_stop_reactions():
    kf, kr = 0.0 * TH.forward_reverse_rates()[0], 0.0 * TH.forward_reverse_rates()[1]
    c = np.array([0.8, 0.9, 1.0, 0.2, 0.3, 0.1])
    assert np.array_equal(S.end_state(c, 5.0, kf, kr), c)
