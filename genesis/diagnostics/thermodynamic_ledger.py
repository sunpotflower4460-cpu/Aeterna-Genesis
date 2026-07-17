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
  matter_in = sum over the FIXED outer-shell reservoir region k_res*(f_res-f) (box geometry, not
    phi-relative).
  chemical potential: dilute-ideal  mu_i = mu0_i + RT*ln(c_i).
  chemical free-energy change: Delta G = sum_i integral( c_i*mu_i ) dV, before/after difference
    (an EXTENSIVE quantity).
  reaction Delta G_rxn = sum_i nu_i * mu_i  (nu_i: stoichiometric coefficients); affinity = -Delta
    G_rxn.
  waste_out = sum of k_out*w over the WHOLE domain (the frozen PDE's `-k_out*w` sink is global).
  entropy_production = sum_rxn(rate * affinity / RT) + viscous dissipation (>=0 for consistency).
  mass_balance_error / stoichiometric_balance_error: before/after accounting residuals, should be
    ~0.

WHAT IT IS NOT
Not a physics model -- these are audits computed FROM fields a physics run already produced (a
before/after pair of snapshots, or an instantaneous rate field), never claims about what SHOULD
happen. A large residual flags a bug in the caller's integrator, not a physics discovery.
"""
import numpy as np


def outer_shell_mask(shape, shell_width=1):
    """Boolean mask of the FIXED outer-shell reservoir region: cells within `shell_width` of any
    domain boundary face, on any axis. This is a BOX geometry, independent of the vessel's
    position -- the F0's frozen fuel term is `J_f^ext = k_res*(f_res-f)*1_{outer(x)}` where
    `outer(x)` is the fixed reservoir shell, never derived from `phi` (deriving it from phi would
    make the reservoir track the vessel instead of being a fixed exterior boundary condition)."""
    mask = np.zeros(shape, dtype=bool)
    sw = int(shell_width)
    for ax in range(len(shape)):
        for edge in (slice(0, sw), slice(shape[ax] - sw, shape[ax])):
            sl = [slice(None)] * len(shape)
            sl[ax] = edge
            mask[tuple(sl)] = True
    return mask


def matter_in(f, outer_mask, k_res, f_res):
    """matter_in = sum(k_res*(f_res-f)) restricted to the FIXED outer-shell reservoir region
    `outer_mask` (from `outer_shell_mask`), matching the F0's frozen `J_f^ext =
    k_res*(f_res-f)*1_{outer(x)}` term exactly -- NOT restricted by `phi`, which would make the
    reservoir region track the vessel's position instead of being a fixed box-geometry boundary."""
    return float((k_res * (f_res - f) * outer_mask).sum())


def chemical_potential(c, mu0=0.0, RT=1.0, eps=1e-12):
    """Dilute-ideal chemical potential mu = mu0 + RT*ln(c) (F0 frozen reference state). Clipped at
    `eps` to keep log finite for c=0 cells -- this clip is a numerical floor, not a physics claim."""
    return mu0 + RT * np.log(np.clip(np.asarray(c), eps, None))


def chemical_free_energy_change(species_before, species_after, mu0, RT=1.0):
    """Delta G = sum_i integral( c_i_after*mu_i(c_i_after) - c_i_before*mu_i(c_i_before) ) dV
    (F0 frozen formula). `species_before`/`species_after`: dict species-name -> field. `mu0`: dict
    or scalar. Weighted by concentration `c_i` (an EXTENSIVE free-energy density, `c*mu`), not the
    bare intensive `mu_after - mu_before` -- the chemical potential alone has no volume/amount
    information, so summing it directly would silently drop the amount-of-substance factor."""
    total = 0.0
    for k in species_before:
        mu0_k = mu0.get(k, 0.0) if isinstance(mu0, dict) else mu0
        c_before = np.asarray(species_before[k])
        c_after = np.asarray(species_after[k])
        mu_before = chemical_potential(c_before, mu0_k, RT)
        mu_after = chemical_potential(c_after, mu0_k, RT)
        total += float((c_after * mu_after - c_before * mu_before).sum())
    return total


def reaction_delta_g(concentrations, stoich, mu0, RT=1.0):
    """Delta G_rxn field = sum_i nu_i * mu_i(c_i), evaluated pointwise (F0 frozen formula).
    `stoich`: dict species -> stoichiometric coefficient nu_i (negative for reactants). This is
    Delta G_rxn itself, NOT the affinity A = -Delta G_rxn -- pass `-reaction_delta_g(...)` as the
    driving force to `entropy_production_reaction` (affinity = -Delta G_rxn, per the F0's frozen
    `entropy_production = sum_rxn(rate*affinity/RT)`)."""
    total = None
    for k, nu in stoich.items():
        mu0_k = mu0.get(k, 0.0) if isinstance(mu0, dict) else mu0
        term = nu * chemical_potential(concentrations[k], mu0_k, RT)
        total = term if total is None else total + term
    return total


def waste_out(w, k_out, region_mask=None):
    """waste_out = sum(k_out*w) over the WHOLE domain by default (F0's frozen PDE sink `-k_out*w`
    in `∂_t w + u·grad w = div(D(phi) grad w) + k2 m - k_out w` is global, not restricted to any
    sub-region). Pass `region_mask` only for an explicit diagnostic sub-region breakdown -- the
    default (None) must match the frozen PDE exactly."""
    arr = k_out * np.asarray(w)
    if region_mask is not None:
        arr = arr * region_mask
    return float(arr.sum())


def entropy_production_reaction(rate, affinity, RT=1.0):
    """Reaction contribution to entropy production: sum(rate * (-affinity) / RT) -- pass the
    reaction's driving force as `affinity` = -Delta G_rxn (i.e. `-reaction_delta_g(...)`) so that a
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


def stoichiometric_balance_error(species_masses_before, species_masses_after, stoich,
                                  source_terms=None):
    """|Delta(sum_i nu_i * mass_i) - sum(source_terms)| for a reaction chain's conserved
    combination (e.g. total f+m+w for f->m->w with matched coefficients), compared ACROSS A
    BEFORE/AFTER WINDOW (matching `mass_balance_error`'s existing before/after pattern) -- zero
    without external sources; with sources/sinks it must match `matter_in`/`waste_out` exactly.
    Comparing the CHANGE in the invariant, not its absolute total, matters: a perfectly conserved
    but nonzero-total system (e.g. mass never leaves f+m+w, but f+m+w != 0) must read as zero
    error, not flag the total mass itself as an accounting bug."""
    lhs_before = sum(stoich[k] * species_masses_before[k] for k in stoich)
    lhs_after = sum(stoich[k] * species_masses_after[k] for k in stoich)
    rhs = sum(source_terms.values()) if source_terms else 0.0
    return float(abs((lhs_after - lhs_before) - rhs))
