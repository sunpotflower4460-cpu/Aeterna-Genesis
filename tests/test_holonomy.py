"""Unit tests for core.holonomy (winding read on a CCW loop)."""

import numpy as np

from core.holonomy import winding_around, ring_winding, circulation


def _phase_of_cores(N, cores):
    """Superposed vortex phase: sum_c charge * atan2(Y-cy, X-cx) on an NxN grid."""
    x = np.arange(N)
    X, Y = np.meshgrid(x, x, indexing="ij")
    ph = np.zeros((N, N))
    for cx, cy, c in cores:
        ph += c * np.arctan2(Y - cy, X - cx)
    return ph


def test_single_positive_vortex_winds_plus_one_radius_invariant():
    N = 121
    c = N // 2
    ph = _phase_of_cores(N, [(c, c, +1)])
    for R in (12, 20, 30, 40):
        w = winding_around(ph, c, c, R)
        assert abs(w - 1.0) < 1e-6, (R, w)


def test_negative_vortex_winds_minus_one():
    N = 121
    c = N // 2
    ph = _phase_of_cores(N, [(c, c, -1)])
    for R in (12, 20, 30):
        assert abs(winding_around(ph, c, c, R) + 1.0) < 1e-6


def test_loop_enclosing_no_core_reads_zero():
    N = 121
    ph = _phase_of_cores(N, [(30, 30, +1)])       # core in the lower-left
    w = winding_around(ph, 90, 90, 12)            # loop far away, encloses nothing
    assert abs(w) < 1e-6


def test_ring_winding_from_complex_field_matches_phase():
    N = 121
    c = N // 2
    ph = _phase_of_cores(N, [(c, c, +1)])
    psi = np.exp(1j * ph)
    assert abs(ring_winding(psi, c, c, 20) - 1.0) < 1e-6


def test_ccw_convention_not_flipped():
    """A +1 vortex must read +1 (a clockwise loop would give -1)."""
    N = 121
    c = N // 2
    ph = _phase_of_cores(N, [(c, c, +1)])
    assert winding_around(ph, c, c, 20) > 0.5


def test_circulation_sign_follows_charge():
    N = 121
    c = N // 2
    amp = np.ones((N, N))
    psi_pos = amp * np.exp(1j * _phase_of_cores(N, [(c, c, +1)]))
    psi_neg = amp * np.exp(1j * _phase_of_cores(N, [(c, c, -1)]))
    cp = circulation(psi_pos, c, c, 20)
    cn = circulation(psi_neg, c, c, 20)
    assert cp > 0 and cn < 0
