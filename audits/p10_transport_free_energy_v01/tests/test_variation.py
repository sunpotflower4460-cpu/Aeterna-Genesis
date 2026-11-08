"""T1: the chemical potentials used by the audit are the exact variations of the stated free energies.

Finite differences of the discrete free energy must reproduce dx * mu (species), dx * mu_phi (phi) and
dx * mu_m (interfacial term). The naive kappa*lap(phi) form must be distinguishable from -div(kappa grad phi).
"""
import numpy as np

import _setup  # noqa: F401
import model

TOL = 1e-7


def _setup_state(N=32):
    dx, x = model.grid(N)
    rng = np.random.default_rng(1)
    phi = np.clip(0.8 * np.sin(3 * np.pi * x) + 0.1 * rng.standard_normal(N), -0.95, 0.95)
    m = 0.3 + 0.2 * np.sin(2 * np.pi * x)
    c1 = 0.5 + rng.random(N)
    c2 = 0.5 + rng.random(N)
    return dx, phi, m, c1, c2


def _fd(fun, arr, j, eps=1e-6):
    ap = arr.copy(); ap[j] += eps
    am = arr.copy(); am[j] -= eps
    return (fun(ap) - fun(am)) / (2 * eps)


def test_species_mu_is_variation_of_reference_free_energy():
    dx, phi, m, c1, c2 = _setup_state()
    betas = [0.5, -0.5]
    F = lambda cc: model.free_energy_phi_full([cc, c2], phi, m, betas, dx)
    exp = model.mu_species(c1, phi, betas[0]) * dx
    fd = np.array([_fd(F, c1, j) for j in range(c1.size)])
    assert np.max(np.abs(fd - exp)) / np.max(np.abs(exp)) < TOL


def test_phi_mu_matches_variation_including_kappa_of_x():
    dx, phi, m, c1, c2 = _setup_state()
    betas = [0.5, -0.5]
    F = lambda p: model.free_energy_phi_full([c1, c2], p, m, betas, dx)
    exp = model.mu_phi_discrete([c1, c2], phi, m, betas, dx) * dx
    fd = np.array([_fd(F, phi, j) for j in range(phi.size)])
    assert np.max(np.abs(fd - exp)) / np.max(np.abs(exp)) < TOL


def test_m_interfacial_chemical_potential_matches_variation():
    dx, phi, m, c1, c2 = _setup_state()
    betas = [0.5, -0.5]
    F = lambda mm: model.free_energy_phi_full([c1, c2], phi, mm, betas, dx)
    exp = model.mu_m_interface_discrete(m, phi, dx) * dx
    fd = np.array([_fd(F, m, j) for j in range(m.size)])
    assert np.max(np.abs(fd - exp)) / np.max(np.abs(exp)) < TOL


def test_div_form_differs_from_naive_laplacian_when_kappa_varies():
    dx, phi, m, _, _ = _setup_state()
    div_form = model.mu_phi_discrete([], phi, m, [], dx, a=0.0)
    naive = model.naive_laplacian_term(m, phi, dx)
    rel = np.max(np.abs(div_form - naive)) / np.max(np.abs(div_form))
    assert rel >= 1e-2


def test_constant_kappa_makes_div_and_laplacian_agree():
    dx, phi, _, _, _ = _setup_state()
    m_const = np.full(phi.shape, 0.0)           # kappa = kappa0 everywhere
    div_form = model.mu_phi_discrete([], phi, m_const, [], dx, a=0.0)
    naive = model.naive_laplacian_term(m_const, phi, dx)
    # interior agreement (the wall cells use one-sided stencils in the naive helper)
    assert np.max(np.abs(div_form[1:-1] - naive[1:-1])) / np.max(np.abs(div_form[1:-1])) < 1e-12
