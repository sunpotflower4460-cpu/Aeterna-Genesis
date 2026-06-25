"""Regression test for e003 (3D GPE vortex ring) and the 3D core helpers."""

import importlib.util
import json
import os

import numpy as np

from core import field, measure, vortex
from core.fft import k_squared_3d

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e003_gpe_vortex_ring")


def _load_run():
    path = os.path.abspath(os.path.join(_DIR, "run.py"))
    spec = importlib.util.spec_from_file_location("e003_run", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_3d_step_conserves_norm_and_energy():
    # The conservative 3D split-step must preserve norm and energy.
    L, g, mu = 24, 1.0, 1.0
    k2 = k_squared_3d(L)
    psi = (np.sqrt(mu) * np.exp(1j * field.vortex_ring_phase(L, 6.0))).astype(complex)
    norm0 = measure.norm(psi)
    for _ in range(30):                       # brief imaginary relax
        psi = field.step_imag_3d(psi, 0.0, k2, g, mu, 0.05)
        psi *= np.sqrt(norm0 / np.sum(np.abs(psi) ** 2))
    n0, e0 = measure.norm(psi), measure.energy_3d(psi, 0.0, g)
    for _ in range(50):
        psi = field.step_real_3d(psi, 0.0, k2, g, mu, 0.1)
    assert abs(measure.norm(psi) - n0) / n0 < 1e-9
    assert abs(measure.energy_3d(psi, 0.0, g) - e0) / abs(e0) < 1e-3


def test_ring_cross_section_recovers_radius_and_axis():
    # An imprinted ring pierces the y=cy slice as a +-1 pair; the tracker must
    # recover its radius and axial position.
    L, R = 48, 10.0
    c = (L - 1) / 2.0
    psi = np.exp(1j * field.vortex_ring_phase(L, R))
    jy = int(round(c))
    tr = vortex.track_ring_cross_section(
        psi[:, jy, :], c, (c + R, c), (c - R, c), (3, L - 4))
    assert tr is not None
    assert abs(tr["radius"] - R) < 1.5
    assert abs(tr["axial"] - c) < 1.5


def test_ring_cross_section_rejects_same_side_cores():
    # Two cross-section cores on the SAME side of the axis must be rejected
    # (a meaningless radius), so the caller ends the clean window.
    L, c = 48, 23.5

    def _imprint2d(L, q, cx, cy):
        x = np.arange(L)[:, None]
        y = np.arange(L)[None, :]
        return np.exp(1j * q * np.arctan2(y - cy, x - cx))

    # +1 and -1 cores both at x = c + 8 (same side of the axis at x=c)
    psi2d = _imprint2d(L, +1, c + 8, 20.0) * _imprint2d(L, -1, c + 8, 28.0)
    tr = vortex.track_ring_cross_section(
        psi2d, c, (c + 8, 20.0), (c + 8, 28.0), (2, L - 3))
    assert tr is None


def test_e003_quick_ring_propagates():
    run = _load_run()
    result = run.simulate(quick=True)
    assert result["propagation_distance"] > 2.0       # ring translates
    assert result["propagation_monotonic"]
    assert result["radius_spread"] < 0.3 * result["radius_mean"]
    assert result["circulation_quantized"]
    assert result["energy_drift"] < 1e-3
    assert result["norm_drift"] < 1e-6


def test_e003_committed_result_in_range():
    path = os.path.abspath(os.path.join(_DIR, "result.json"))
    if not os.path.exists(path):
        return
    with open(path) as f:
        result = json.load(f)
    run = _load_run()
    passed, checks = run.evaluate(result)
    assert passed, checks
