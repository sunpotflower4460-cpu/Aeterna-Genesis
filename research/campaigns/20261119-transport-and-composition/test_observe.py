import itertools

import numpy as np
import pytest

from observe import encounter_rates, periodic_components, time_mean


def test_periodic_seam_merges_an_island_without_winding():
    mask = np.zeros((7, 7, 7), dtype=bool)
    mask[[0, 6], 2:4, 3:5] = True
    result = periodic_components(mask)
    assert result["count"] == 1
    assert result["cut_open_count"] == 2
    assert result["largest_volumes"] == [8]
    assert result["winding_axes_any"] == [False, False, False]
    shifted = periodic_components(np.roll(mask, 3, axis=0))
    assert shifted["largest_volumes"] == result["largest_volumes"]
    assert shifted["winding_axes_any"] == result["winding_axes_any"]


def test_winding_detects_complete_axes_and_survives_shifts():
    mask = np.zeros((7, 7, 7), dtype=bool)
    mask[:, 1, 1] = True
    mask[3, :, 4] = True
    for shift in [(0, 0, 0), (1, 2, 3), (6, 5, 4)]:
        result = periodic_components(np.roll(mask, shift, axis=(0, 1, 2)))
        assert result["count"] == 2
        assert result["largest_volumes"] == [7, 7]
        assert result["winding_axes_any"] == [True, True, False]
        assert result["winding_component_count"] == 2
    empty = periodic_components(np.zeros_like(mask))
    full = periodic_components(np.ones_like(mask))
    assert empty["count"] == 0
    assert full["winding_axes_any"] == [True, True, True]


def test_direct_pair_enumeration_matches_observed_and_reference_rates():
    n = 5
    cells = np.random.default_rng(45).integers(0, 5, size=(n, n, n))
    parameters = {"epsilon": -1.2, "df": 2.4, "eta": 10.0}
    rates = encounter_rates(cells, parameters)
    possible_pairs = list(itertools.product(range(3), [-1, 1]))
    for name, macro_code, fuel_code in (("B_to_I", 2, 3), ("I_to_B", 1, 4)):
        total = {key: 0.0 for key in ("observed", "well_mixed", "same_x_mixed")}
        counts = np.zeros(7, dtype=int)
        available = (cells != 1) & (cells != 2)
        global_fraction = np.count_nonzero(cells == fuel_code) / np.count_nonzero(available)
        for site in np.ndindex(cells.shape):
            if cells[site] != macro_code:
                continue
            adjacent = []
            for axis, sign in possible_pairs:
                location = list(site)
                location[axis] = (location[axis] + sign) % n
                adjacent.append(tuple(location))
            bonded = sum(cells[target] == 2 for target in adjacent)
            exponent = 2.4 - .6 * bonded if macro_code == 2 else .6 * bonded
            for target in adjacent:
                if not available[target]:
                    continue
                occupied = int(cells[target] == fuel_code)
                counts[bonded] += occupied
                plane = target[0]
                plane_fraction = np.count_nonzero(cells[plane] == fuel_code) / np.count_nonzero(available[plane])
                weight = parameters["eta"] * np.exp(exponent) / 6
                total["observed"] += weight * occupied
                total["well_mixed"] += weight * global_fraction
                total["same_x_mixed"] += weight * plane_fraction
        assert np.array_equal(rates[name]["contacts_by_B_neighbors"]["observed"], counts)
        assert rates[name]["propensities"] == pytest.approx(total)


def test_time_mean_with_exact_window_and_interpolated_boundary():
    assert time_mean([0, 5, 15, 20], [1, 11, 31, 41], 4, 19) == pytest.approx(24)
    with pytest.raises(ValueError):
        time_mean([0, 5], [2, 4], 4, 8)


def test_periodic_winds_agree_with_direct_voxel_lifts():
    rng = np.random.default_rng(66)
    shape = (4, 5, 6)
    for probability in (0.1, 0.25, 0.55, 0.8):
        mask = rng.random(shape) < probability
        occupied = {point for point in np.ndindex(shape) if mask[point]}
        seen = {}
        components = []
        for start in sorted(occupied):
            if start in seen:
                continue
            queue = [start]
            seen[start] = start
            winding = [False] * 3
            for point in queue:
                for axis, sign in itertools.product(range(3), [-1, 1]):
                    lift = list(seen[point])
                    lift[axis] += sign
                    point2 = tuple(value % extent for value, extent in zip(lift, shape))
                    if point2 not in occupied:
                        continue
                    if point2 in seen:
                        winding = [flag or value != previous
                                   for flag, value, previous in zip(winding, lift, seen[point2])]
                    else:
                        seen[point2] = tuple(lift)
                        queue.append(point2)
            components.append((len(queue), winding))
        measured = periodic_components(mask)
        assert measured["count"] == len(components)
        assert measured["largest_volumes"] == sorted((volume for volume, _ in components), reverse=True)[:8]
        assert measured["winding_component_count"] == sum(any(winding) for _, winding in components)
        assert measured["winding_axes_any"] == [any(winding[axis] for _, winding in components) for axis in range(3)]
