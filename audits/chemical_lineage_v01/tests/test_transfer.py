"""T05–T08: transfer mass balance, fresh independence, donor exchange, units-only reconstitution."""
import numpy as np

import _setup  # noqa: F401
import controls as C
import species as SP
import transfer_protocol as P


def test_T05_transfer_mass_balance_and_fresh_material():
    parent = C.seed_state(4)
    f = 0.1
    start, led = P.start_of_generation(parent, f, "L1")
    assert np.allclose(SP.element_totals(start), 1.0, atol=1e-14)
    assert np.allclose(led["transferred_units"], f * SP.element_totals(parent), atol=1e-14)
    assert np.allclose(led["fresh_units"], (1 - f) * np.ones(3), atol=1e-14)
    assert np.allclose(led["start_units"], 1.0, atol=1e-14)


def test_T06_fresh_control_is_independent_of_any_parent():
    parent_a = C.seed_state(1)
    parent_b = np.array([0.2, 0.2, 0.2, 0.3, 0.3, 0.3])   # any other state with other totals is still fine
    s_a, _ = P.start_of_generation(None, 0.0, "L0")
    s_b, _ = P.start_of_generation(parent_b, 0.0, "L0")
    assert np.array_equal(s_a, s_b)


def test_T06_units_only_counterfactual_equals_fresh_start_by_construction():
    parent = C.seed_state(2)
    s_lr, _ = P.start_of_generation(parent, 0.1, "LR")
    s_l0, _ = P.start_of_generation(None, 0.0, "L0")
    assert np.allclose(s_lr, s_l0, atol=1e-14)


def test_T07_donor_exchange_uses_the_donor_state_exactly():
    donor = C.seed_state(7)
    parent = C.seed_state(3)
    f = 0.1
    start, _ = P.start_of_generation(parent, f, "LS", donor_end=donor)
    expected = f * donor + P.fresh_material(f)
    assert np.array_equal(start, expected)


def test_T08_reconstitution_keeps_units_and_removes_complexes():
    state = C.seed_state(5)
    m = P.reconstitute(state)
    assert np.allclose(SP.element_totals(m), SP.element_totals(state), atol=1e-14)
    assert np.all(m[SP.IDX["XY"]:] == 0.0)
