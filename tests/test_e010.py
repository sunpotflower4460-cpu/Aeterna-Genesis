"""Regression test for e010 (KZ coherence length: spacing/xi const, 2 sigma = b)."""

import importlib.util
import os

import numpy as np

from core import measure

_DIR = os.path.join(os.path.dirname(__file__), "..", "experiments",
                    "e010_kz_coherence")


def _load(name):
    path = os.path.abspath(os.path.join(_DIR, name))
    spec = importlib.util.spec_from_file_location("e010_" + name[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_coherence_length_of_known_gaussian():
    # A field with a single smooth Gaussian bump has a finite, positive 1/e
    # coherence length well below the box size (sanity of the ruler).
    L = 64
    x = np.arange(L) - L / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    psi = np.exp(-(X ** 2 + Y ** 2) / (2 * 6.0 ** 2)).astype(complex)
    xi = measure.coherence_length(psi)
    assert 0.0 < xi < L / 2


def test_coherence_length_flat_field_is_zero():
    psi = np.ones((32, 32), complex)        # no fluctuation -> degenerate
    assert measure.coherence_length(psi) == 0.0


def test_e010_quick_mechanism_and_consistency():
    run = _load("run.py")
    result = run.simulate(quick=True)
    # KZ mechanism: defect spacing is a constant multiple of xi
    assert result["spacing_over_xi_cv"] < 0.15
    # internal consistency: b = 2 sigma (same exponent governs N and xi)
    assert result["internal_consistency_rel"] < 0.25
    # negative power law on a genuine condensate
    assert result["defect_exponent_b"] > 0.1
    assert result["rho_median_min"] > 0.6


def test_e010_z_ordering():
    rob = _load("robustness.py")
    z = rob.substrate_z_test(quick=True)
    # smaller dynamical exponent z -> larger KZ exponent b (KZ-consistent)
    assert z["NLKG_z1"]["b"] > z["GPE_z2"]["b"]
    assert z["ordering_b_z1_gt_z2"]


def test_e010_committed_result_sane():
    path = os.path.abspath(os.path.join(_DIR, "result.json"))
    if not os.path.exists(path):
        return
    import json
    with open(path) as f:
        data = json.load(f)
    r = data["result"]
    assert r["spacing_over_xi_cv"] < 0.15
    assert r["internal_consistency_rel"] < 0.25
