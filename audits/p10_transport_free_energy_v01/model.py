"""Independent 1-D reference equations for the P10 transport audit (v0.1).

Pure equations, written from FORMULA_AUDIT.md. This module must NOT import or call
genesis/diagnostics/vessel_permeability.py (PRE_REGISTRATION.json: independent_model_must_not_call).

Units (main runs): RT = 1, c_ref = 1, domain length L = 1, D0 = 1.
Staggered layout: N cells, cell-centre values c[j], N+1 faces; face 0 and face N are the no-flux
walls. Flux arrays have length N+1 with J[0] = J[N] = 0 by construction.
"""
import numpy as np


def grid(N, L=1.0):
    """Cell width and cell-centre coordinates."""
    dx = L / N
    x = (np.arange(N) + 0.5) * dx
    return dx, x


def phi_profile(x, x0=0.5, width=0.05):
    """Fixed planar interface phi = tanh((x0 - x)/width): +1 on the left (inside), -1 on the right."""
    return np.tanh((x0 - x) / width)


def D_field(phi, D0=1.0, kind="const"):
    """Shared transport coefficient D(phi). The same field is used for every species (no D_i)."""
    if kind == "const":
        return np.full(phi.shape, float(D0))
    if kind == "linear":
        return D0 * (1.0 + 0.5 * phi)
    raise ValueError(f"unknown D kind: {kind}")


def chi_from_beta(beta, RT=1.0):
    """chi = beta * RT (beta = chi / RT is the dimensionless partition coupling)."""
    return beta * RT


def mu_species(c, phi, beta, RT=1.0, c_ref=1.0):
    """Chemical potential of one species: mu = RT ln(c/c_ref) + chi * phi (FORMULA_AUDIT R-1)."""
    return RT * np.log(c / c_ref) + chi_from_beta(beta, RT) * phi


def free_energy_species(c, phi, beta, dx, RT=1.0, c_ref=1.0):
    """Discrete reference free energy of one species: dx * sum[RT c (ln(c/c_ref) - 1) + chi phi c] (R-0)."""
    chi = chi_from_beta(beta, RT)
    return float(dx * np.sum(RT * c * (np.log(c / c_ref) - 1.0) + chi * phi * c))


def flux_mu(c, phi, beta, D, dx, RT=1.0, c_ref=1.0):
    """Mu-gradient flux (main flux, FORMULA_AUDIT R-2/R-3).

    J_{j+1/2} = -M_face * c_face * (mu_{j+1} - mu_j) / dx, with M = D/RT,
    M_face = arithmetic mean of M, c_face = arithmetic mean of c.
    """
    M = D / RT
    mu = mu_species(c, phi, beta, RT, c_ref)
    M_f = 0.5 * (M[:-1] + M[1:])
    c_f = 0.5 * (c[:-1] + c[1:])
    J = np.zeros(c.size + 1)
    J[1:-1] = -M_f * c_f * (mu[1:] - mu[:-1]) / dx
    return J


def flux_fick(c, D, dx):
    """Literal F0 control flux A: J = -D_face * (c_{j+1} - c_j) / dx, with no chi term (F0-flux)."""
    D_f = 0.5 * (D[:-1] + D[1:])
    J = np.zeros(c.size + 1)
    J[1:-1] = -D_f * (c[1:] - c[:-1]) / dx
    return J


def rhs_from_flux(J, dx):
    """Conservative update: dc_j/dt = -(J_{j+1/2} - J_{j-1/2}) / dx."""
    return -(J[1:] - J[:-1]) / dx


def dissipation_mu(c, phi, beta, D, dx, RT=1.0, c_ref=1.0):
    """Discrete free-energy dissipation of the mu-flux: sum_faces M_face c_face (dmu)^2 / dx (>= 0).

    Identity (FORMULA_AUDIT E-1): dF_ref/dt = -dissipation_mu.
    """
    M = D / RT
    mu = mu_species(c, phi, beta, RT, c_ref)
    M_f = 0.5 * (M[:-1] + M[1:])
    c_f = 0.5 * (c[:-1] + c[1:])
    dmu = mu[1:] - mu[:-1]
    return float(np.sum(M_f * c_f * dmu ** 2 / dx))


def kappa_of_m(m, kappa0=1.0, alpha=0.5):
    """kappa(m) = kappa0 (1 - alpha m) (F0 §2 / T1 only)."""
    return kappa0 * (1.0 - alpha * m)


def dkappa_dm(m, kappa0=1.0, alpha=0.5):
    """kappa'(m) = -kappa0 alpha (constant for the linear form)."""
    return -kappa0 * alpha * np.ones_like(m)


def free_energy_phi_full(c_list, phi, m, betas, dx, a=1.0, kappa0=1.0, alpha=0.5, RT=1.0, c_ref=1.0):
    """Discrete F = dx sum[a/4 (phi^2-1)^2] + sum_faces kappa_f Delta^2/(2 dx) + sum_i species terms.

    kappa_f = arithmetic mean of kappa(m) on the two cells of the face. No-flux ends (no boundary term).
    """
    kap = kappa_of_m(m, kappa0, alpha)
    kf = 0.5 * (kap[:-1] + kap[1:])
    dphi = np.diff(phi)
    F = dx * np.sum(a / 4.0 * (phi ** 2 - 1.0) ** 2)
    F += np.sum(kf * dphi ** 2 / (2.0 * dx))
    for c, b in zip(c_list, betas):
        F += free_energy_species(c, phi, b, dx, RT, c_ref)
    return float(F)


def mu_phi_discrete(c_list, phi, m, betas, dx, a=1.0, kappa0=1.0, alpha=0.5, RT=1.0):
    """Discrete mu_phi = a phi(phi^2-1) - div_h(kappa(m) grad phi) + sum_i chi_i c_i (F-1).

    The gradient term uses face fluxes g = kappa_f * (phi_{j+1}-phi_j)/dx with g = 0 at the walls,
    so that dF/dphi_j = dx * mu_phi_j exactly (checked in T1).
    """
    kap = kappa_of_m(m, kappa0, alpha)
    kf = 0.5 * (kap[:-1] + kap[1:])
    g = np.zeros(phi.size + 1)
    g[1:-1] = kf * np.diff(phi) / dx
    div = (g[1:] - g[:-1]) / dx
    chi_sum = np.zeros_like(phi)
    for c, b in zip(c_list, betas):
        chi_sum += chi_from_beta(b, RT) * c
    return a * phi * (phi ** 2 - 1.0) - div + chi_sum


def mu_m_interface_discrete(m, phi, dx, kappa0=1.0, alpha=0.5):
    """Interfacial contribution to mu_m: (kappa'(m)/4)(Delta_+^2 + Delta_-^2)/dx^2 (FORMULA_AUDIT §4).

    This is NOT in the F0 transport equation for m (finding D-3). Used only to verify the variation in T1.
    """
    dphi_f = np.zeros(phi.size + 1)
    dphi_f[1:-1] = np.diff(phi)
    return dkappa_dm(m, kappa0, alpha) / 4.0 * (dphi_f[1:] ** 2 + dphi_f[:-1] ** 2) / dx ** 2


def naive_laplacian_term(m, phi, dx, kappa0=1.0, alpha=0.5):
    """Wrong form kappa(m) * lap(phi) (constant-kappa shortcut). Used only as a sensitivity check in T1."""
    kap = kappa_of_m(m, kappa0, alpha)
    lap = np.zeros_like(phi)
    lap[1:-1] = (phi[2:] - 2.0 * phi[1:-1] + phi[:-2]) / dx ** 2
    lap[0] = (phi[1] - phi[0]) / dx ** 2
    lap[-1] = (phi[-2] - phi[-1]) / dx ** 2
    return -kap * lap
