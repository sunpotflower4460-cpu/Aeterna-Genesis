"""Independent instrument checks and a basis expansion for two published cylinder points."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import eigh
from scipy.special import j0, j1, jn_zeros

from analyze import phase_crossings
from cylinder import material
from loops import decode, minimum_image
from tools.study_record import load_plan, read_object


def check_loops():
    shape = (24, 24, 24)
    x, y, z = np.ogrid[:24, :24, :24]
    r2 = minimum_image(x - 0.2, 24)**2 + minimum_image(y - 11.8, 24)**2
    phase = 2 * np.pi * (z - 6.3) / 24
    synthetic = r2 / 5.0**2 - 1 + (1 - np.cos(phase)) + 1j * np.sin(phase)
    ring, = decode(np.array(phase_crossings(synthetic)), shape, 1.0, 0.0, 0.0)
    shifted, = decode(np.array(phase_crossings(np.roll(synthetic, -1, 0))), shape, 1.0, 0.0, 0.0)
    assert ring["status"] == shifted["status"] == "closed"
    np.testing.assert_allclose(minimum_image(np.subtract(ring["center"], shifted["center"]), 24), (1, 0, 0),
                               atol=1e-12)
    spanning = np.array([[2, 0, 0, z, 1] for z in range(4)])
    assert decode(spanning, (4, 4, 4), 1.0, 0.0, 0.0)[0]["status"] == "wraps"
    assert phase_crossings(np.ones(shape, dtype=complex)) == []
    return {"contractible_loop_edges": ring["edges"], "seam_translation": "matched", "winding_line": "rejected"}


def basis_frequency(L, R, alpha, tau, count):
    """Dirichlet Bessel and axial modes with quadrature, independent of the cell-centred solver."""
    u, g = np.polynomial.legendre.leggauss(5 * count)
    s, w = (u + 1) / 2, g / 2
    radius_wave_numbers = jn_zeros(0, count)
    radial = j0(s[:, None] * radius_wave_numbers) / np.abs(j1(radius_wave_numbers))
    weights = np.multiply.outer(2 * s * w, w).ravel()

    def project(axial, axial_wave_numbers):
        basis = (radial[:, None, :, None] * axial[None, :, None, :]).reshape(len(weights), -1)
        energy = 0.5 * ((radius_wave_numbers[:, None] / R)**2 + (axial_wave_numbers / L)**2)
        return basis, energy.ravel()

    even_k = np.pi * (2 * np.arange(count) + 1)
    odd_k = 2 * np.pi * (np.arange(count) + 1)
    even, E = project(np.sqrt(2) * np.cos(s[:, None] * even_k / 2), even_k)
    odd, E_odd = project(np.sqrt(2) * np.sin(s[:, None] * odd_k / 2), odd_k)
    # Orthonormal coefficients use a mean-density-normalized condensate.
    v = np.zeros(E.size)
    v[0] = 1
    for _ in range(6000):
        field = even @ v
        result = E * v + even.T @ (weights * alpha * field**3)
        mu = float(v @ result)
        residual = result - mu * v
        if np.linalg.norm(residual) < 1e-10:
            break
        v -= residual / (4 + E)
        v /= np.linalg.norm(v)
    else:
        raise RuntimeError("Bessel-basis ground state did not converge")
    density = odd.T @ ((weights * alpha * field**2)[:, None] * odd)
    base = np.diag(E_odd - mu)
    minus_values, minus_modes = eigh(base + density)
    minus_sqrt = (minus_modes * np.sqrt(minus_values)) @ minus_modes.T
    square = eigh(minus_sqrt @ (base + 3 * density) @ minus_sqrt, subset_by_index=(0, 0),
                  eigvals_only=True)[0]
    return float(np.sqrt(square) / (2 * math.pi * tau))


def check_cylinder(plan, evidence):
    trap = plan["reference"]["experimental_geometry"]
    units = material(plan["reference"])
    L = trap["length_um"] * 1e-6 / units["ell_m"]
    R = trap["radius_um"] * 1e-6 / units["ell_m"]
    nref = plan["reference"]["material"]["reference_atoms"]
    result = {}
    for name in ("cylinder-1", "cylinder-8"):
        case = read_object(evidence / f"{name}.json")
        observed = case["observed_hz"]
        point = case["atoms"] / nref
        basis = [basis_frequency(L, R, point, units["tau_s"], modes) for modes in (8, 12)]
        result[name] = {
            "observed_hz": observed, "finite_volume_hz": case["fine"]["hz"],
            "bessel_basis_8_hz": basis[0], "bessel_basis_12_hz": basis[1],
        }
        if abs(basis[-1] / case["fine"]["hz"] - 1) > 0.004:
            raise ValueError(f"independent discretizations disagree for {name}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    plan = load_plan(Path(__file__).with_name("PLAN.json"))
    print(json.dumps({"phase": check_loops(), "cylinder": check_cylinder(plan, args.evidence)}, indent=2))


if __name__ == "__main__":
    main()
