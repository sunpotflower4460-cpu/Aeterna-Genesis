#!/usr/bin/env python3
"""Multi-species flux / mass-balance diagnostics for the Active Vessel white (P10, PR-1, role V).

WHAT IT IS
Extends the F1 V0-validated Scharfetter-Gummel (Boltzmann-balanced) flux instrument
(`genesis.diagnostics.vessel_permeability`) to multiple species, and reports diagnostics FROM A
GIVEN SNAPSHOT: partition ratios, instantaneous face/boundary flux, total mass, and reaction-chain
mass-balance residuals. These are measurement functions applied to a field, not a new physics
model or time-integrator -- the SG flux law itself was already validated as an instrument in F1 V0
(exact Boltzmann equilibrium at any interface sharpness/chi); this module reuses it (imports
`_bernoulli` rather than reimplementing it) to compute the instantaneous flux/partition state a
given (possibly N-species) snapshot is in.

WHAT IT IS NOT
Not a claim that any measured flux/partition pattern is self-formed or maintained -- that is the
S1/E2/E3 physics runs' job (separate PRs, per the P10 mainline). This module only reports numbers.
"""
import numpy as np

from genesis.diagnostics.vessel_permeability import _bernoulli


def species_partition_ratio(c, phi, thresh=0.5):
    """Inside/outside mean-concentration ratio (the F1 V0 selective-boundary readout, generalized
    to any species field `c`). NaN if either region is empty."""
    inside, outside = phi > thresh, phi < -thresh
    if not inside.any() or not outside.any():
        return float("nan")
    return float(c[inside].mean() / c[outside].mean())


def instantaneous_face_flux(c, phi, chi, D=1.0, axis=0):
    """Scharfetter-Gummel flux across the face between cell i and i+1 along `axis`, reusing the
    exact Boltzmann-balanced instrument validated in F1 V0 (`vessel_permeability._bernoulli`).
    `D` may be a scalar or a field (face-averaged automatically, matching F1 V0's fix for
    orientation-dependent transient flux with a spatial mobility)."""
    D_arr = np.asarray(D, dtype=float)
    cp = np.roll(c, -1, axis=axis)
    pp = np.roll(phi, -1, axis=axis)
    dpsi = chi * (pp - phi)
    D_face = D_arr if D_arr.ndim == 0 else 0.5 * (D_arr + np.roll(D_arr, -1, axis=axis))
    return D_face * (_bernoulli(dpsi) * c - _bernoulli(-dpsi) * cp)


def net_boundary_flux(c, phi, chi, D=1.0, thresh=0.5):
    """Net instantaneous flux crossing INTO the vessel interior across the |phi|=thresh shell:
    summed, over all axes, at faces where an outside cell borders an inside cell. Positive means
    net inward transport at this instant."""
    inside = phi > thresh
    total = 0.0
    for ax in range(c.ndim):
        J = instantaneous_face_flux(c, phi, chi, D=D, axis=ax)
        nb_inside = np.roll(inside, -1, axis=ax)
        crossing_in = (~inside) & nb_inside     # face i(outside)|i+1(inside): +ax flux enters
        crossing_out = inside & (~nb_inside)    # face i(inside)|i+1(outside): +ax flux exits
        total += float(J[crossing_in].sum()) - float(J[crossing_out].sum())
    return total


def total_mass(c, dx=1.0):
    """Total conserved species amount."""
    return float(c.sum()) * dx ** 3


def stoichiometric_invariant(species_masses, coeffs):
    """sum_k coeffs[k] * species_masses[k] -- for a closed reaction chain (no fuel-in/waste-out)
    this combination is conserved by construction; callers audit it against known source/sink
    terms via `mass_balance_residual`, not by assuming it is zero."""
    return float(sum(coeffs[k] * species_masses[k] for k in coeffs))


def mass_balance_residual(mass_before, mass_after, sources=0.0, sinks=0.0):
    """|Δmass - (sources - sinks)| -- should be ~0 to numerical precision for a correctly
    integrated finite-volume scheme; a nonzero residual flags an accounting bug in the caller's
    solver, not a physics result to interpret."""
    return float(abs((mass_after - mass_before) - (sources - sinks)))
