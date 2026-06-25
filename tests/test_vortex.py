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


def test_track_two_vortices_separates_and_signs():
    # Two same-sign cores imprinted at known spots; local tracking must return
    # both, correctly signed, near their true positions (not swapped/merged).
    L = 128
    c1, c2 = (50.5, 63.5), (78.5, 63.5)
    psi = _imprint(L, +1, c1) * _imprint(L, +1, c2)
    res = vortex.track_two_vortices(psi, [c1, c2], [+1, +1], window=8)
    assert all(r is not None for r in res)
    assert res[0]["charge"] == +1 and res[1]["charge"] == +1
    assert abs(res[0]["x"] - 50.5) < 2 and abs(res[1]["x"] - 78.5) < 2


def test_track_two_vortices_opposite_signs_not_confused():
    # +1 and -1 close together: each search must lock onto its OWN sign.
    L = 128
    cp, cm = (56.5, 63.5), (72.5, 63.5)
    psi = _imprint(L, +1, cp) * _imprint(L, -1, cm)
    res = vortex.track_two_vortices(psi, [cp, cm], [+1, -1], window=8)
    assert res[0] is not None and res[1] is not None
    assert res[0]["charge"] == +1
    assert res[1]["charge"] == -1


def test_track_two_vortices_returns_none_when_absent():
    # No matching-sign core in the window -> None for that slot.
    L = 128
    psi = _imprint(L, +1, (63.5, 63.5))
    # search for a -1 vortex far from the only (+1) core
    res = vortex.track_two_vortices(psi, [(20.5, 20.5)], [-1], window=8)
    assert res[0] is None


def test_track_two_vortices_overlapping_windows_stay_distinct():
    # Two same-sign cores closer than the window width: the overlapping search
    # boxes both contain both cores, yet continuity must return DISTINCT cores.
    L = 128
    c1, c2 = (60.5, 63.5), (68.5, 63.5)  # separation 8, window 8 -> heavy overlap
    psi = _imprint(L, +1, c1) * _imprint(L, +1, c2)
    res = vortex.track_two_vortices(psi, [c1, c2], [+1, +1], window=8)
    assert all(r is not None for r in res)
    # the two vortices must not collapse onto the same core
    assert (round(res[0]["x"]), round(res[0]["y"])) != (round(res[1]["x"]), round(res[1]["y"]))
    assert abs(res[0]["x"] - 60.5) < 2 and abs(res[1]["x"] - 68.5) < 2


def test_track_two_vortices_no_dual_selection_of_one_core():
    # Only ONE +1 core exists, but both searches look near it. The first claims
    # it; the second must NOT also grab it (returns None), so a real pair can
    # never be faked as a zero-separation coincidence.
    L = 128
    psi = _imprint(L, +1, (63.5, 63.5))
    res = vortex.track_two_vortices(psi, [(62.5, 63.5), (64.5, 63.5)], [+1, +1], window=8)
    assert sum(r is not None for r in res) == 1
