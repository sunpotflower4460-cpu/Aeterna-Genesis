"""Unit tests for core/vortex.py: winding of known imprints, quantization."""

import numpy as np

from core import field, vortex


def _imprint(L, charge, center):
    x, y = field.index_grid(L)
    cx, cy = center
    return np.exp(1j * charge * np.arctan2(y - cy, x - cx))


def test_known_positive_vortex_winding():
    L = 48
    center = (24.5, 24.5)  # plaquette centre -> no node coincidence
    psi = _imprint(L, +1, center)
    cores = vortex.find_vortices(psi, refine=False)
    assert len(cores) == 1
    assert cores[0]["charge"] == +1
    assert abs(cores[0]["x"] - 24.5) < 1.0
    assert abs(cores[0]["y"] - 24.5) < 1.0


def test_known_negative_vortex_winding():
    L = 48
    center = (24.5, 24.5)
    psi = _imprint(L, -1, center)
    cores = vortex.find_vortices(psi, refine=False)
    assert len(cores) == 1
    assert cores[0]["charge"] == -1


def test_vortex_free_field_has_no_cores():
    L = 48
    x, y = field.index_grid(L)
    # smooth phase ramp, no singularity
    psi = np.exp(1j * 0.1 * x)
    cores = vortex.find_vortices(psi, refine=False)
    assert cores == []


def test_circulation_is_quantized():
    L = 48
    psi = _imprint(L, +1, (24.5, 24.5))
    assert vortex.is_circulation_quantized(psi)


def test_two_opposite_vortices():
    L = 64
    p1 = _imprint(L, +1, (24.5, 31.5))
    p2 = _imprint(L, -1, (39.5, 31.5))
    psi = p1 * p2
    cores = vortex.find_vortices(psi, refine=False)
    charges = sorted(c["charge"] for c in cores)
    assert charges == [-1, +1]
