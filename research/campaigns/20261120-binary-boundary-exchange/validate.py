"""Use a SciPy periodic tree to verify forces, ledgers and one archived isolated interval."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from measure import PLAN
from run import reduced_pairs
from tools.study_record import check_record, load_plan, read_object


def reference_force(q, species, length, reduced, cutoff):
    sigmas, epsilons = np.array(reduced).T
    limit = sigmas * cutoff
    i, j = cKDTree(q, boxsize=length).query_pairs(float(limit.max()), output_type="ndarray").T
    rij = q[i] - q[j]
    rij -= length * np.rint(rij / length)
    distance = np.linalg.norm(rij, axis=1)
    kind = species[i] + species[j]
    keep = distance < limit[kind]
    i, j, rij, distance, kind = i[keep], j[keep], rij[keep], distance[keep], kind[keep]
    sigma, epsilon, rc = sigmas[kind], epsilons[kind], limit[kind]
    a = (sigma / distance)**6
    b = (sigma / rc)**6
    at_cutoff = 24 * epsilon / rc * (2 * b**2 - b)
    magnitude = 24 * epsilon / distance * (2 * a**2 - a) - at_cutoff
    values = rij * (magnitude / distance)[:, None]
    force = np.column_stack([
        np.bincount(i, weights=axis, minlength=len(q)) - np.bincount(j, weights=axis, minlength=len(q))
        for axis in values.T
    ])
    potential = 4 * epsilon * (a**2 - a - b**2 + b) + at_cutoff * (distance - rc)
    return force, potential.sum(), np.dot(distance, magnitude)


def measured_values(q, v, masses, length, potential, virial):
    twice_k = np.sum(masses[:, None] * v**2)
    momentum = masses @ v
    twice_thermal_k = twice_k - np.dot(momentum, momentum) / masses.sum()
    return np.array([twice_thermal_k / (3 * (len(q) - 1)), twice_k / 2, potential, *momentum,
                     (twice_thermal_k + virial) / (3 * length**3)])


def verify(evidence, case_name):
    plan = load_plan(PLAN)
    record_path = evidence / "record.json"
    check_record(PLAN, record_path)
    record = read_object(record_path)
    variant = plan["cases"][case_name]
    if variant["mode"] != "isolated":
        raise ValueError("choose an isolated history")
    evidence_case = record["cases"][case_name][-1]
    length, dt, cutoff = (variant[key] for key in ("length", "dt", "cutoff"))
    material = plan["material"]
    pairs = reduced_pairs(variant, material)
    with np.load(evidence / evidence_case["prefix"]) as parent, np.load(evidence / (case_name + ".npz")) as arm:
        q, v = parent["common_state"]
        initial_q, initial_v = parent["initial_state"]
        species = parent["species"]
        mass_ratio = material["kr_mass_kg"] / material["ar_mass_kg"]
        masses = np.take([1, mass_ratio], species)
        force, u, virial = reference_force(q, species, length, pairs, cutoff)
        _force, initial_u, initial_virial = reference_force(initial_q, species, length, pairs, cutoff)
        ledger = arm["ledger"]
        quantized = arm["positions"][1]
        columns = [2, 3, 4, 6, 7, 8, 9]
        np.testing.assert_allclose(measured_values(q, v, masses, length, u, virial), ledger[0, columns],
                                   rtol=1e-10, atol=2e-10)
        np.testing.assert_allclose(measured_values(initial_q, initial_v, masses, length, initial_u, initial_virial),
                                   parent["ledger"][0, columns], rtol=1e-10, atol=2e-10)

    step = 0.5 * dt / masses[:, None]
    for _ in range(round(plan["protocol"]["sample"] / dt)):
        v += step * force
        q = (q + dt * v) % length
        force, u, virial = reference_force(q, species, length, pairs, cutoff)
        v += step * force
    np.testing.assert_allclose(measured_values(q, v, masses, length, u, virial), ledger[1, columns],
                               rtol=1e-9, atol=2e-8)
    resolution = length / 65536
    archived_centres = (quantized.astype(float) + 0.5) * resolution
    delta = q - archived_centres
    max_error = float(np.abs(delta - length * np.rint(delta / length)).max())
    if max_error > 0.50001 * resolution:
        raise ValueError(f"independent integrator falls outside the stored position bin: {max_error} σ")
    return {"case": case_name, "verified_isolated_tau": plan["protocol"]["sample"],
            "max_coordinate_error_sigma_ar": max_error, "bin_width_sigma_ar": resolution,
            "initial_and_first_two_isolated_ledger_rows_verified": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--case", default="binary-93601-isolated")
    args = parser.parse_args()
    print(json.dumps(verify(args.evidence, args.case), sort_keys=True))


if __name__ == "__main__":
    main()
