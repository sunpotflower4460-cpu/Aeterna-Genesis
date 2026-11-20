"""Axisymmetric linear-response calculation for the measured hard-wall cylinder."""
from __future__ import annotations

import math

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigs, splu
from scipy.special import j0


def material(reference):
    data = reference["material"]
    trap = reference["experimental_geometry"]
    mass = data["mass_u"] * data["atomic_mass_constant_kg"]
    hbar = data["hbar_J_s"]
    a = data["a_bohr"] * data["bohr_m"]
    volume = math.pi * trap["radius_um"]**2 * trap["length_um"] * 1e-18
    n = data["reference_atoms"] / volume
    mu = 4 * math.pi * hbar**2 * a * n / mass
    return {
        "mass_kg": mass,
        "mean_density_m-3": n,
        "scattering_length_m": a,
        "energy_J": mu,
        "ell_m": hbar / math.sqrt(mass * mu),
        "tau_s": hbar / mu,
        "sound_m_s": math.sqrt(mu / mass),
        "diluteness_n_a3": n * a**3,
    }


def digitize(reference, case):
    p = reference["digitization"]
    x, y = case["marker_xy"]
    ax, bx = np.polyfit(p["x_tick_px"], np.log(p["x_tick_atoms"]), 1)
    ay, by = np.polyfit(p["y_tick_px"], np.log(p["y_tick_hz"]), 1)
    return {
        "atoms": float(np.exp(ax * x + bx)),
        "observed_hz": float(np.exp(ay * y + by)),
        "raster_readout_relative": float(np.expm1(abs(ay * p["uncertainty_px"]))),
    }


def operators(radius, half_length, radial_cells, axial_cells):
    """Cell-centred finite volumes on the half cylinder, scaled by sqrt(cell weight).

    The central symmetry plane is reflecting for the ground state and Dirichlet
    for the odd axial excitation. The radial outer wall and axial end are Dirichlet.
    """
    dr, dz = radius / radial_cells, half_length / axial_cells
    r = (np.arange(radial_cells) + 0.5) * dr
    z = (np.arange(axial_cells) + 0.5) * dz
    radial_links = np.arange(1, radial_cells) / (2 * dr * np.sqrt(r[1:] * r[:-1]))
    radial_diagonal = np.full(radial_cells, 1 / dr**2)
    # At the outer wall the face lies half a cell from the last cell centre.
    radial_diagonal[-1] += radius / (2 * r[-1] * dr**2)
    kr = sparse.diags((-radial_links, radial_diagonal, -radial_links), (-1, 0, 1))
    off = np.full(axial_cells - 1, -0.5 / dz**2)
    axial_diagonal = np.full(axial_cells, 1 / dz**2)
    axial_diagonal[0] -= 0.5 / dz**2
    axial_diagonal[-1] += 0.5 / dz**2
    kz = sparse.diags((off, axial_diagonal, off), (-1, 0, 1))
    even = sparse.kronsum(kz, kr, format="csc")
    central = np.zeros(axial_cells)
    central[0] = 1 / dz**2
    odd = even + sparse.kron(sparse.eye(radial_cells), sparse.diags(central), format="csc")
    weights = np.broadcast_to(r[:, None], (radial_cells, axial_cells)).flatten().copy()
    weights /= weights.sum()
    guess = j0(2.404825557695773 * r[:, None] / radius) * np.cos(0.5 * np.pi * z / half_length)
    return even, odd, weights, guess.ravel()


def ground_state(kinetic, weights, guess, interaction):
    u = guess * np.sqrt(weights)
    u /= np.linalg.norm(u)
    precondition = splu(kinetic + 4 * sparse.eye(len(u), format="csc")).solve
    for iteration in range(6000):
        density_term = interaction * u**2 / weights
        hu = kinetic @ u + density_term * u
        mu = u @ hu
        residual = hu - mu * u
        error = float(np.linalg.norm(residual))
        if error <= 1e-10:
            return density_term, float(mu), error, iteration
        u -= precondition(residual)
        u /= np.linalg.norm(u)
    raise RuntimeError(f"ground state residual {error:.6g} after 6000 iterations")


def frequency(scales, atoms_ratio, L_um, R_um, mesh_um):
    ell = scales["ell_m"]
    nr, nz = math.ceil(R_um / mesh_um), math.ceil(0.5 * L_um / mesh_um)
    even, odd, weights, guess = operators(R_um * 1e-6 / ell, 0.5 * L_um * 1e-6 / ell, nr, nz)
    density, mu, residual, iterations = ground_state(even, weights, guess, atoms_ratio)
    minus = odd + sparse.diags(density - mu, format="csc")
    plus = odd + sparse.diags(3 * density - mu, format="csc")
    inverse_minus, inverse_plus = splu(minus).solve, splu(plus).solve
    inverse = LinearOperator(odd.shape, lambda x: inverse_plus(inverse_minus(x)), dtype=float)
    # Minus is positive on the odd subspace, so the inverse product has positive real eigenvalues.
    inverse_value, vectors = eigs(inverse, k=1, which="LM", tol=1e-11, v0=guess * np.sqrt(weights))
    iv = inverse_value[0]
    if abs(iv.imag) > 1e-10 or iv.real <= 0:
        raise RuntimeError(f"non-positive or complex squared-frequency inverse {iv}")
    u = vectors[:, 0].real
    eig_error = float(np.linalg.norm(inverse @ u - iv.real * u) / iv.real)
    return {
        "hz": float(1 / (2 * math.pi * scales["tau_s"] * np.sqrt(iv.real))),
        "radial_cells": nr,
        "half_axial_cells": nz,
        "ground_residual": residual,
        "ground_iterations": iterations,
        "relative_inverse_eigen_residual": eig_error,
    }


def calculate(reference, case):
    scales = material(reference)
    point = digitize(reference, case)
    atoms = point["atoms"]
    trap = reference["experimental_geometry"]
    L, R, uncertainty = trap["length_um"], trap["radius_um"], trap["quoted_uncertainty_um"]
    nref = reference["material"]["reference_atoms"]

    def compute(length, radius, mesh):
        # Reference time and energy units stay fixed as N and the physical density change.
        density_ratio = atoms / nref * L / length * (R / radius)**2
        return frequency(scales, density_ratio, length, radius, mesh)

    coarse, fine = case["target_mesh_um"]
    return {
        **point,
        "coarse": compute(L, R, coarse),
        "fine": compute(L, R, fine),
        "geometry_corners_coarse_mesh": [
            {"length_um": L + dl, "radius_um": R + dr, **compute(L + dl, R + dr, coarse)}
            for dl in (-uncertainty, uncertainty) for dr in (-uncertainty, uncertainty)
        ],
        "ideal_gas_hz": 3 * math.pi * reference["material"]["hbar_J_s"] / (4 * scales["mass_kg"] * (L * 1e-6)**2),
        "standing_sound_hz": scales["sound_m_s"] * math.sqrt(atoms / nref) / (2 * L * 1e-6),
    }
