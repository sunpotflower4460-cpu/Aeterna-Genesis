from itertools import combinations
import math

import numpy as np
import pytest
from scipy.ndimage import uniform_filter

from measure import component_sizes, half_correlation, material_hop_derivative, reaction_fields, spectral_length
from mixing import mean_exponential
from stability import fourier_jacobian, homogeneous_roots, jacobian_stencil, model_cases, rhs
from track_domains import DOMAIN_PLAN, RegionFrame, classify_transition, read_json

PARAMETERS = {"D_I": 3.0, "D_B": 11.0, "epsilon": -1.2, "df": 0.7, "passive_rate": 2.0, "eta": 7.0}


def test_spectrum_has_the_prescribed_periodic_mode_and_parseval_variance():
    n = 24
    x, y, z = np.indices((n,) * 3)
    density = np.cos(2 * np.pi * (x + 2 * y + z) / n)
    assert spectral_length(density) == pytest.approx((n / math.sqrt(6), 0, 0.5), abs=1e-13)
    assert spectral_length(np.roll(density, (3, 7, 2), (0, 1, 2))) == pytest.approx(spectral_length(density))
    assert spectral_length(np.cos(2 * np.pi * x / n)) == pytest.approx((n, 1, 0.5))
    assert spectral_length(np.ones((n,) * 3)) == (None, None, 0.0)


def test_independent_axial_correlation_of_a_three_dimensional_field():
    n = 24
    signs = 2 * (np.indices((n,) * 3) < (n // 2)).astype(np.int16) - 1
    counts = 32 + 8 * signs.sum(axis=0, dtype=np.int16)
    assert half_correlation(counts) == 3 * n / 8
    assert half_correlation(np.roll(counts, (3, 5, 7), (0, 1, 2))) == 3 * n / 8
    assert half_correlation(np.zeros_like(counts)) is None


def test_periodic_faces_join_without_joining_diagonal_points():
    mask = np.zeros((8,) * 3, dtype=bool)
    mask[0, 0, 0] = mask[-1, 0, 0] = mask[0, -1, 0] = mask[0, 0, -1] = True
    mask[1, 1, 0] = True
    assert component_sizes(mask).tolist() == [4, 1]
    assert component_sizes(np.roll(mask, (1, 2, 3), (0, 1, 2))).tolist() == [4, 1]
    assert not len(component_sizes(np.zeros_like(mask)))


def test_material_hop_divergence_checks_diffusivities_and_conserves_mass():
    cells = np.zeros((5,) * 3, dtype=np.uint8)
    cells[0, 0, 0] = 1
    cells[1, 1, 1] = 2
    result = material_hop_derivative(cells, PARAMETERS)
    assert result[0, 0, 0] == -3
    assert result[1, 1, 1] == -11
    assert result[-1, 0, 0] == 3 / 6
    assert result[2, 1, 1] == 11 / 6
    assert math.fsum(result.flat) == pytest.approx(0, abs=1e-14)


def test_forward_and_reverse_pair_rates_use_the_same_material_density_bin():
    cells = np.zeros((5,) * 3, dtype=np.uint8)
    center, resource, b_neighbor = (2, 2, 2), (3, 2, 2), (1, 2, 2)
    cells[center], cells[resource], cells[b_neighbor] = 1, 4, 2
    reverse_cells = cells.copy()
    reverse_cells[center], reverse_cells[resource] = 2, 3
    energy_change = PARAMETERS["df"] + PARAMETERS["epsilon"]
    forward_p, _, forward_d, _ = reaction_fields(cells, PARAMETERS)
    _, reverse_p, _, reverse_d = reaction_fields(reverse_cells, PARAMETERS)
    assert forward_d[center] == pytest.approx(PARAMETERS["eta"] * math.exp(0.6) / 6)
    assert forward_d[center] / reverse_d[center] == pytest.approx(math.exp(-energy_change))
    assert forward_p[center] / reverse_p[center] == pytest.approx(math.exp(-energy_change))
    coarse = lambda scene: uniform_filter(((scene == 1) | (scene == 2)).astype(float), size=4, mode="wrap")
    assert np.array_equal(coarse(cells), coarse(reverse_cells))


def test_periodic_domain_event_requires_both_overlap_and_retained_material():
    plan = read_json(DOMAIN_PLAN)
    pair = np.repeat([1, 2], 100)
    merged = np.ones(len(pair), dtype=int)
    before = RegionFrame(pair, pair, np.asarray([0, 100, 100]), np.asarray([0, 100, 100]))
    after = RegionFrame(merged, merged, np.asarray([0, 200]), np.asarray([0, 200]))
    joined = classify_transition(before, after, plan)
    assert [event["kind"] for event in joined["events"]] == ["many-to-one"]
    assert [link["shared_molecules"] for link in joined["links"]] == [100, 100]
    assert [event["kind"] for event in classify_transition(after, before, plan)["events"]] == ["one-to-many"]
    displaced_labels = np.concatenate((np.zeros(len(pair), dtype=int), merged))
    old_labels = np.concatenate((pair, np.zeros(len(pair), dtype=int)))
    a = RegionFrame(old_labels, pair, before.volumes, before.populations)
    b = RegionFrame(displaced_labels, merged, after.volumes, after.populations)
    drift = classify_transition(a, b, plan)
    assert drift["events"] == []
    assert (drift["unlinked_before"], drift["unlinked_after"]) == (2, 1)


def test_no_bond_material_drift_is_the_vacancy_limited_diffusion_of_an_empty_bath():
    p = dict(model_cases())["reversible_df0.2"] | {"epsilon": 0.0}
    n = 8
    x = np.indices((n,)*3)[0]
    material = 0.18 + 0.02 * np.cos(2 * np.pi * x / n)
    s = np.array([0.8 * material, 0.2 * material, np.zeros_like(material), np.zeros_like(material)])
    observed = rhs(s, p)[:2].sum(axis=0)
    target = (p["D_I"] / 6) * (np.roll(material, 1, axis=0) + np.roll(material, -1, axis=0) - 2 * material)
    assert np.allclose(observed, target, rtol=0, atol=1e-13)


def test_fourier_symbol_matches_a_direct_periodic_perturbation():
    p = dict(model_cases())["uniform_minus"]
    s = homogeneous_roots(p)[0]
    offsets, stencil = jacobian_stencil(s, p)
    n = 8
    q = 2 * np.pi * np.array([1, 2, 1]) / n
    coordinate = np.indices((n,)*3)
    wave = np.cos(np.einsum("a,axyz->xyz", q, coordinate))
    directions = np.asarray([0.3, 0.13, -0.07, 0.24])
    base = s[:, None, None, None] * np.ones((n,)*3)
    disturbance = 1e-6 * directions[:, None, None, None] * wave
    numerical = (rhs(base + disturbance, p) - rhs(base - disturbance, p)) / 2e-6
    amplitude = fourier_jacobian(offsets, stencil, q[None, :])[0] @ directions
    assert np.allclose(numerical, amplitude[:, None, None, None] * wave, rtol=0, atol=1e-7)


def test_fixed_count_neighbor_average_matches_all_combinations():
    populations = np.array([3, 0, 7])
    factor = mean_exponential(7, populations, 5, -1.2)
    enumeration = list(combinations(range(7), 5))
    expected = [sum(math.exp(-1.2 * sum(index < count for index in selected))
                    for selected in enumeration) / len(enumeration) for count in populations]
    assert factor == pytest.approx(expected, abs=1e-14)
