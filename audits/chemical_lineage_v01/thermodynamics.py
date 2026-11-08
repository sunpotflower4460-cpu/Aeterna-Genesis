"""Thermodynamic bookkeeping of the abstract network (v0.1). Units: RT = 1, standard concentration c0 = 1, V = 1.

Ideal dilute solutions: activity a_i = c_i / c0 (dimensionless). Chemical potential mu_i = g_i + ln c_i, with g_i
the standard chemical potential in RT units (declared in PRE_REGISTRATION.json, fixed before any run).

Free energy (ideal, closed): G = sum_i c_i (g_i + ln c_i - 1). Then dG/dt = sum_i mu_i dc_i/dt.
Reaction free energy: Delta_r G = sum_i nu_ir mu_i = Delta_r G0 + ln(Q_r), Q_r = prod(products)/prod(reactants).
Equilibrium constant K_r = exp(-Delta_r G0) and, with mass-action rates k+ = KF, k- = KF / K_r, detailed balance
holds: at Q_r = K_r the net rate is zero. The rate constants are NOT chosen independently.
"""
import numpy as np

from reaction_network import MP, MR, NU, REACTIONS
from species import SPECIES

# Standard chemical potentials g_i in RT units (declared). Pair associations ~ -2, the triple ~ -4.
# These values are an explicit assumption: they set the equilibrium constants, nothing else.
G0 = np.array([0.0, 0.0, 0.0, -2.0, -2.0, -4.0])   # X, Y, Z, XY, XZ, XYZ


def delta_r_G0():
    """Standard free energy change of each reaction, Delta_r G0 = sum_i nu_ir g_i."""
    return NU.T @ G0


def equilibrium_constants():
    return np.exp(-delta_r_G0())


def wegscheider_residual():
    """Thermodynamic cycle residual for the two routes to XYZ: K0*K2 / (K1*K3) must equal 1 (T02).

    Routes: X+Y -> XY -> (+Z) XYZ  and  X+Z -> XZ -> (+Y) XYZ. Residual is ln(K0 K2) - ln(K1 K3).
    """
    K = equilibrium_constants()
    return float(np.log(K[0] * K[2]) - np.log(K[1] * K[3]))


def forward_reverse_rates(kf=None):
    """Rate constants (k+, k-) with k- = k+ / K_r (detailed balance by construction)."""
    from reaction_network import KF
    kf = KF if kf is None else kf
    K = equilibrium_constants()
    return np.full(len(REACTIONS), kf), kf / K


def reaction_rates(c, kf, kr):
    """Net rate r_r = kf prod(c_R^nu) - kr prod(c_P^nu) for concentrations c (clipping forbidden)."""
    c = np.asarray(c, dtype=float)
    fwd = kf * np.prod(np.power(c[:, None], MR), axis=0)
    rev = kr * np.prod(np.power(c[:, None], MP), axis=0)
    return fwd - rev


def free_energy(c):
    """G = sum_i c_i (g_i + ln c_i - 1). Requires c > 0; otherwise raises (no clipping)."""
    c = np.asarray(c, dtype=float)
    if np.any(c <= 0):
        raise ValueError("free energy undefined for non-positive concentrations")
    return float(np.sum(c * (G0 + np.log(c) - 1.0)))


def reaction_free_energies(c):
    """Delta_r G = sum_i nu_ir mu_i evaluated at c (requires c > 0)."""
    c = np.asarray(c, dtype=float)
    if np.any(c <= 0):
        raise ValueError("reaction free energy undefined for non-positive concentrations")
    mu = G0 + np.log(c)
    return NU.T @ mu


def dG_dt_closed(c):
    """Analytic dG/dt for the closed network: sum_r r_r * Delta_r G_r (<= 0 by construction)."""
    kf, kr = forward_reverse_rates()
    r = reaction_rates(c, kf, kr)
    return float(np.sum(r * reaction_free_energies(c)))
