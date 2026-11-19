"""Independent checks for the finite generator, bath projection and spectral readout."""
import csv
from dataclasses import replace
import io
from pathlib import Path
import subprocess

import numpy as np
import pytest

from longtime import wavelength_from_density
from stationary import Rates, generator, measure

PAIR = Rates(-1.2, 1.2, -4.0, 1.0, 1.0, 0.5, (100.0, 7.0))
ROOT = Path(__file__).resolve().parents[3]


def test_relative_ctmc_excludes_collision_and_combines_the_two_hop_paths():
    q, states, index = generator(4, PAIR)
    assert len(states) == 4 * (4**3 - 1)
    assert (q.sum(axis=1).A.ravel() == pytest.approx(np.zeros(len(states)), abs=1e-12))
    i = index[((1, 0, 0), 1, 0)]
    j = index[((2, 0, 0), 1, 0)]
    assert q[i, j] == pytest.approx((100.0 + 7.0) / 6)
    assert len(q.getrow(i).nonzero()[0]) == 5 + 2 + 1


def test_canonical_nulls_and_affinity_have_independent_checks():
    for z in (None, 0.25):
        active = replace(PAIR, z_total=z)
        for null in (replace(active, mu=0.0), replace(active, driven=0.0), replace(active, passive=0.0)):
            m = measure(4, null)
            assert m["conditional_contact"] == pytest.approx(m["canonical_conditional_contact"], abs=1e-12)
            assert m["cycle_log_ratio"] == pytest.approx(0.0, abs=1e-12)
            assert m["max_canonical_error"] <= 1e-12
        assert measure(4, active)["cycle_log_ratio"] == pytest.approx(active.analytic_affinity(), abs=1e-12)


def test_instantaneous_bath_averages_only_accessible_faces():
    bath = replace(PAIR, passive=0.0, driven=10.0, z_total=0.25)
    z_f = bath.z_total / (1 + np.exp(-bath.mu))
    z_w = bath.z_total / (1 + np.exp(bath.mu))
    empty = 1 / (1 + z_f + z_w)
    # Individually enumerate the vacancy and fuel states at all six adjacent faces.
    # Exactly one face is blocked by the other macro.
    b_to_i = sum((0.0, *[10 * np.exp(1.2 - .6) * z_f * empty / 6] * 5))
    i_to_b = sum((0.0, *[10 * np.exp(.6) * z_w * empty / 6] * 5))
    assert bath.flip(1, 1, 1) == pytest.approx(b_to_i)
    assert bath.flip(0, 1, 1) == pytest.approx(i_to_b)
    assert bath.hop(1, 0, True) == pytest.approx((100 + 7) * empty / 6)


def test_implicit_rates_agree_with_original_cpp(tmp_path):
    source = ROOT / "research/campaigns/20261108-local-reactive-lattice-v02/local_kmc.cpp"
    binary = tmp_path / "lattice_rates"
    subprocess.run(["g++", "-O2", "-std=c++17", str(source), "-o", str(binary)], check=True)
    args = ["--rates", "-1.2", "1.2", "-4", "1", ".5", "100", "1", "3"]
    printed = subprocess.check_output([str(binary), *args], text=True)
    for row in csv.DictReader(io.StringIO(printed)):
        n = int(row["n"])
        assert PAIR.flip(1, n, 0) == pytest.approx(float(row["bp"]) + float(row["bd"]), rel=1e-14)
        assert PAIR.flip(0, n, 0) == pytest.approx(float(row["ip"]) + float(row["id"]), rel=1e-14)


def test_known_diagonal_fourier_mode_and_periodic_translation():
    n = 12
    x, y, z = np.indices((n, n, n))
    field = np.cos(2 * np.pi * (x + 2 * y) / n)
    length, variance = wavelength_from_density(field)
    assert length == pytest.approx(n / np.sqrt(5), rel=1e-13)
    assert variance == pytest.approx(0.5, rel=1e-13)
    assert wavelength_from_density(np.roll(field, (5, 3, 7), (0, 1, 2))) == pytest.approx((length, variance))
    assert wavelength_from_density(np.zeros_like(field)) == (None, 0.0)
