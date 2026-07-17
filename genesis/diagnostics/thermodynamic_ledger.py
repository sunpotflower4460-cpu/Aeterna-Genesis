#!/usr/bin/env python3
"""Thermodynamic ledger for the Active Vessel white (P10, PR-1, role V).

WHAT IT IS
Implements, as code, the exact frozen definitions pre-registered in
`docs/frontier/F0_P10_active_vessel.md`'s `thermodynamic_ledger` block (Codex #6, 2026-07-17: "the
gate relies on thermodynamic_ledger [...] but the preregistration only names ledger fields and
never fixes reservoir chemical potentials, reference states, units [...] the free-energy accounting
[could] change without changing the dynamics, making the stop/restart pass condition
non-reproducible"). Every formula here matches the F0's frozen prose 1:1; changing a formula here
without a documented, dated reason is exactly the drift this module exists to prevent.

Frozen reference (F0 §4, `thermodynamic_ledger`):
  matter_in = sum over outer-shell reservoir exchange k_res*(f_res-f), OUTSIDE region only.
  chemical potential: dilute-ideal  mu_i = mu0_i + RT*ln(c_i).
  reaction free-energy change: Delta G_rxn = sum_i nu_i * mu_i  (nu_i: stoichiometric coefficients).
  waste_out = sum of k_out*w over the OUTSIDE region.
  entropy_production = sum_rxn(rate * affinity / RT) + viscous dissipation (>=0 for consistency).
  mass_balance_error / stoichiometric_balance_error: accounting residuals, should be ~0.

WHAT IT IS NOT
Not a physics model -- these are audits computed FROM fields a physics run already produced (a
before/after pair of snapshots, or an instantaneous rate field), never claims about what SHOULD
happen. A large residual flags a bug in the caller's integrator, not a physics discovery.
"""
import numpy as np


def matter_in(f, phi, k_res, f_res, out_thresh=0.5):
    """matter_in = sum(k_res*(f_res-f)) restricted to the OUTSIDE bulk (phi<-out_thresh) -- fuel
    is exchanged only outside, never injected directly at the interior (F0 frozen formula)."""
    outside = phi < -out_thresh
    return float((k_res * (f_res - f) * outside).sum())


def chemical_potential(c, mu0=0.0, RT=1.0, eps=1e-12):
    """Dilute-ideal chemical potential mu = mu0 + RT*ln(c) (F0 frozen reference state). Clipped at
    `eps` to keep log finite for c=0 cells -- this clip is a numerical floor, not a physics claim."""
    return mu0 + RT * np.log(np.clip(np.asarray(c), eps, None))


def chemical_free_energy_change(species_before, species_after, mu0, RT=1.0):
    """Delta G = sum_i integral( mu_i(c_i_after) - mu_i(c_i_before) ) dV (F0 frozen formula).
    `species_before`/`species_after`: dict species-name -> field. `mu0`: dict or scalar."""
    total = 0.0
    for k in species_before:
        mu0_k = mu0.get(k, 0.0) if isinstance(mu0, dict) else mu0
        mu_before = chemical_potential(species_before[k], mu0_k, RT)
        mu_after = chemical_potential(species_after[k], mu0_k, RT)
        total += float((mu_after - mu_before).sum())
    return total


def reaction_affinity(concentrations, stoich, mu0, RT=1.0):
    """Delta G_rxn field = sum_i nu_i * mu_i(c_i), evaluated pointwise (F0 frozen formula).
    `stoich`: dict species -> stoichiometric coefficient nu_i (negative for reactants)."""
    total = None
    for k, nu in stoich.items():
        mu0_k = mu0.get(k, 0.0) if isinstance(mu0, dict) else mu0
        term = nu * chemical_potential(concentrations[k], mu0_k, RT)
        total = term if total is None else total + term
    return total


def waste_out(w, phi, k_out, out_thresh=0.5):
    """waste_out = sum(k_out*w) over the OUTSIDE bulk (F0 frozen formula)."""
    outside = phi < -out_thresh
    return float((k_out * w * outside).sum())


def entropy_production_reaction(rate, affinity, RT=1.0):
    """Reaction contribution to entropy production: sum(rate * (-affinity) / RT) -- pass the
    reaction's driving force as `affinity` = -Delta G_rxn (from `reaction_affinity`) so that a
    spontaneous (Delta G_rxn<0) reaction contributes a non-negative term, matching the F0's
    ">=0 for a thermodynamically consistent reaction" requirement. A negative result is a real,
    reportable finding (an inconsistent rate law), never silently clipped to zero."""
    return float((np.asarray(rate) * affinity / RT).sum())


def viscous_dissipation(strain_rate_sq, eta=1.0):
    """2*eta*integral(e:e) dV -- zero for the S1 stage (u=0, no hydrodynamics yet); kept as a
    hook for later hydrodynamic stages of the P10 mainline (F0 §8)."""
    return float(2.0 * eta * np.asarray(strain_rate_sq).sum())


def mass_balance_error(mass_before, mass_after, matter_in_amt, waste_out_amt, other_sinks=0.0):
    """|Δmass - (matter_in - waste_out - other_sinks)| -- an accounting residual; should be ~0 to
    numerical precision for a correctly integrated scheme."""
    return float(abs((mass_after - mass_before) - (matter_in_amt - waste_out_amt - other_sinks)))


def stoichiometric_balance_error(species_masses, stoich, source_terms=None):
    """|sum_i nu_i * mass_i - sum(source_terms)| for a reaction chain's conserved combination
    (e.g. total f+m+w for f->m->w with matched coefficients) -- zero without external sources;
    with sources/sinks it must match `matter_in`/`waste_out` exactly, not merely approximately."""
    lhs = sum(stoich[k] * species_masses[k] for k in stoich)
    rhs = sum(source_terms.values()) if source_terms else 0.0
    return float(abs(lhs - rhs))
