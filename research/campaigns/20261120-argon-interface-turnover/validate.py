"""Independent short force integration and known-input checks of the observer."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from analyze import exchange, minimum_image, separate
from tools.study_record import load_plan, read_object


def artificial_regions():
    n = 18
    field = np.zeros((n,) * 3)
    field[1:7, 1:7, 1:7] = 0.68
    cut = np.roll(field, -3, axis=0)
    dense, liquid, vapor, bounded, second = separate(cut, 80, 1.0, 0.35, 2.0)
    assert bounded and np.count_nonzero(dense) == 216 and second == 0
    assert liquid.any() and not (liquid & vapor).any()
    wrapped = np.zeros_like(field)
    wrapped[:, 4:8, 4:8] = 0.74
    assert not separate(wrapped, 80, 1.0, 0.35, 2.0)[3]
    assert not separate(np.full_like(field, 0.122), 80, 1.0, 0.35, 2.0)[3]

    visits = np.array([[1], [1], [1], [2], [0], [2], [2], [2]])
    coords = np.zeros((8, 1, 3), dtype=np.uint16)
    coords[5:, 0, 0] = 20000
    row = exchange(visits, coords, np.arange(8), 2, 7, 3, 18.0, 2.0)
    assert row["departure_events"] == row["departures_with_displacement"] == 1
    assert row["events"][0]["to_t"] == 7
    frozen = exchange(visits, np.zeros_like(coords), np.arange(8), 2, 7, 3, 18.0, 2.0)
    assert frozen["departure_events"] == 1 and frozen["departures_with_displacement"] == 0
    return {"periodic_bounded_voxels": 216, "spanning_region_reported_separately": True,
            "brief_visit_excluded": True, "stationary_atom_does_not_pass_displacement_filter": True}


def pair_forces(position, length, cutoff):
    # Rebuild from a fresh exact periodic spatial search at every step.
    near = cKDTree(position, boxsize=length).query_pairs(cutoff, output_type="ndarray")
    i, j = near.T
    offset = minimum_image(position[i] - position[j], length)
    rr = np.linalg.norm(offset, axis=1)
    coeff = 24 * (2 * rr**-12 - rr**-6) / rr
    at_cutoff = 24 * (2 * cutoff**-12 - cutoff**-6) / cutoff
    vector = ((coeff - at_cutoff) / rr)[:, None] * offset
    force = np.zeros_like(position)
    np.add.at(force, i, vector)
    np.add.at(force, j, -vector)
    raw = 4 * (rr**-12 - rr**-6)
    shifted = raw - 4 * (cutoff**-12 - cutoff**-6) + (rr - cutoff) * at_cutoff
    return force, float(shifted.sum())


def compare_short_trajectory(evidence):
    plan = load_plan(Path(__file__).with_name("PLAN.json"))
    witness = "base-93201-isolated"
    case = plan["cases"][witness]
    length, cutoff, dt = (case[k] for k in ("length", "cutoff", "dt"))
    manifest = read_object(evidence / "record.json")
    state = manifest["cases"][witness][-1]["prefix"]
    with np.load(evidence / state) as raw:
        position, velocity = raw["common_state"]
    with np.load(evidence / (witness + ".npz")) as raw:
        ledger = raw["ledger"]
        initial_q, ending_q = raw["positions"][:2]
    assert np.array_equal(np.floor(position * (65536 / length)).astype(np.uint16), initial_q)
    force, start_energy = pair_forces(position, length, cutoff)
    np.testing.assert_allclose(start_energy, ledger[0, 4], rtol=0, atol=1e-8)
    for _ in range(round(plan["protocol"]["sample"] / dt)):
        velocity += (0.5 * dt) * force
        position = (position + dt * velocity) % length
        force, potential = pair_forces(position, length, cutoff)
        velocity += (0.5 * dt) * force
    energy = float(0.5 * np.square(velocity).sum())
    end_bin_centre = (ending_q.astype(float) + 0.5) * (length / 65536)
    position_error = float(np.abs(minimum_image(position - end_bin_centre, length)).max())
    assert position_error <= length / 131072 + 1e-10
    np.testing.assert_allclose([energy, potential], ledger[1, 3:5], rtol=0, atol=1e-8)
    return {
        "atoms": len(position),
        "steps": round(plan["protocol"]["sample"] / dt),
        "max_position_error_from_bin_centre_sigma": position_error,
        "quantization_half_bin_sigma": length / 131072,
        "potential_error": potential - float(ledger[1, 4]),
        "kinetic_error": energy - float(ledger[1, 3]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps({"synthetic_observer": artificial_regions(),
                      "independent_force": compare_short_trajectory(args.evidence)}, indent=2))


if __name__ == "__main__":
    main()
