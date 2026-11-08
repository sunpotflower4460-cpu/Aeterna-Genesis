"""Measurements for the independent audit (v0.1). Measurements only: thresholds live in run_audit.py / PRE_REGISTRATION.json.

Conventions: c, phi are cell-centred arrays of length N; dx = L/N; halves are split at x0 = L/2
(the interface sits exactly on the cell face x0 when N is even, so 'inside' = left half, 'outside' = right half).
"""
import numpy as np

import model


def total_mass(c, dx):
    """Total species amount sum_j c_j dx."""
    return float(np.sum(c) * dx)


def mass_residual_rel(C_series, dx, M0):
    """max over saved times of |M(t) - M0| / M0 for a (n_t x N) array."""
    masses = np.sum(C_series, axis=1) * dx
    return float(np.max(np.abs(masses - M0)) / M0)


def finite_and_positive(C_series):
    """(all_finite, min_value). Positivity is judged by the caller (strictly > 0 required)."""
    finite = bool(np.all(np.isfinite(C_series)))
    return finite, float(np.min(C_series)) if finite else float("nan")


def boltzmann_invariant_cv(c, phi, beta):
    """CV of g_j = c_j exp(beta phi_j). Zero iff c_j is proportional to exp(-beta phi_j)."""
    g = c * np.exp(beta * phi)
    return float(np.std(g) / np.mean(g))


def discrete_equilibrium(phi, beta, M0, dx):
    """Exact discrete zero-flux state of the mu-flux scheme: c_j = K exp(-beta phi_j), sum c_j dx = M0."""
    w = np.exp(-beta * phi)
    K = M0 / (np.sum(w) * dx)
    return K * w


def continuum_equilibrium(x, phi_fn, beta, M0, L=1.0, n_quad=16384):
    """Continuum Boltzmann profile c(x) = M0 exp(-beta phi(x)) / int exp(-beta phi) dx, sampled at x."""
    xq = (np.arange(n_quad) + 0.5) * (L / n_quad)
    Z = np.sum(np.exp(-beta * phi_fn(xq))) * (L / n_quad)
    return M0 * np.exp(-beta * phi_fn(x)) / Z


def partition_ratio_measured(c, x, x0=0.5):
    """Mean concentration on the inside half over mean on the outside half (cell-centred)."""
    inside = x < x0
    outside = x > x0
    return float(np.mean(c[inside]) / np.mean(c[outside]))


def partition_ratio_predicted_discrete(phi, beta, x, x0=0.5):
    """Discrete Boltzmann-factor half-average prediction for the same cells (exact zero-flux state)."""
    w = np.exp(-beta * phi)
    inside = x < x0
    outside = x > x0
    return float(np.mean(w[inside]) / np.mean(w[outside]))


def partition_ratio_predicted_continuum(beta, phi_fn, x0=0.5, L=1.0, n_quad=16384):
    """Continuum half-domain average of exp(-beta phi) ratio (quadrature)."""
    xq_in = (np.arange(n_quad) + 0.5) * (x0 / n_quad)
    xq_out = x0 + (np.arange(n_quad) + 0.5) * ((L - x0) / n_quad)
    num = np.mean(np.exp(-beta * phi_fn(xq_in)))
    den = np.mean(np.exp(-beta * phi_fn(xq_out)))
    return float(num / den)


def max_face_flux(c, phi, beta, D, dx):
    """Largest |J| over interior faces of the mu-flux (equilibrium check)."""
    J = model.flux_mu(c, phi, beta, D, dx)
    return float(np.max(np.abs(J)))


def mu_spread(c, phi, beta):
    """max_j |mu_j - mean(mu)| for the species chemical potential."""
    mu = model.mu_species(c, phi, beta)
    return float(np.max(np.abs(mu - np.mean(mu))))


def relaxation_time(t, C_series, c_eq, tol=1e-2):
    """First time at which max_j |c_j(t) - c_eq_j| / c_eq_j <= tol, linearly interpolated between saved
    samples (so that grid spacing does not contribute to the measured time). nan if never reached."""
    dev = np.max(np.abs(C_series - c_eq[None, :]) / c_eq[None, :], axis=1)
    idx = np.nonzero(dev <= tol)[0]
    if idx.size == 0:
        return float("nan")
    k = idx[0]
    if k == 0:
        return float(t[0])
    d0, d1 = dev[k - 1], dev[k]
    frac = (d0 - tol) / (d0 - d1)
    return float(t[k - 1] + frac * (t[k] - t[k - 1]))


def observed_order(err_coarse, err_fine, ratio=2.0):
    """Observed convergence order p = log(e_coarse / e_fine) / log(ratio)."""
    if err_fine <= 0 or err_coarse <= 0:
        return float("nan")
    return float(np.log(err_coarse / err_fine) / np.log(ratio))


def coarse_average(c_fine, factor):
    """Average a fine-grid cell array onto a coarser grid by consecutive blocks of 'factor' cells."""
    return c_fine.reshape(-1, factor).mean(axis=1)


def L1_cell_error(c_a, c_b, dx):
    """Discrete L1 norm of the difference, dx * sum |c_a - c_b|."""
    return float(np.sum(np.abs(c_a - c_b)) * dx)


def energy_series(C_series, phi, beta, dx):
    """F_ref at each saved time."""
    return np.array([model.free_energy_species(c, phi, beta, dx) for c in C_series])
