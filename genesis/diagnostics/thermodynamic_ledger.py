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
  matter_in = sum over the FIXED outer-shell reservoir region k_res*(f_res-f) * dx^3 (box
    geometry, not phi-relative; volumetric, matching the frozen PDE's volumetric source term).
  chemical potential: dilute-ideal  mu_i = mu0_i + RT*ln(c_i).
  chemical free-energy change: Delta G = sum_i integral( f_i(c_i_after) - f_i(c_i_before) ) dV *
    dx^3, where f_i(c) = mu0_i*c + RT*(c*ln(c) - c) is the free-energy DENSITY whose derivative is
    mu_i(c) (the Legendre-consistent integral of mu dc, NOT the bare product c*mu).
  reaction Delta G_rxn = sum_i nu_i * mu_i  (nu_i: stoichiometric coefficients); affinity = -Delta
    G_rxn.
  waste_out = sum of k_out*w * dx^3 over the WHOLE domain (the frozen PDE's `-k_out*w` sink is
    global and volumetric).
  entropy_production = sum_rxn(rate * affinity / RT) * dx^3 + viscous dissipation (>=0 for
    consistency).
  useful_work = interface-band integral of sigma_M:grad(u) * dx^3 (free energy converted to
    boundary maintenance; zero while u=0 pre-hydrodynamics).
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
    make the reservoir track the vessel instead of being a fixed exterior boundary condition).
    `shell_width` is in CELLS: the shell's PHYSICAL thickness is `shell_width * dx`. For
    `matter_in`'s total to converge to a fixed physical value under grid refinement (same box
    size, same physical shell thickness), callers comparing across resolutions must scale
    `shell_width` as `~1/dx` (e.g. double it when halving dx) -- holding `shell_width` fixed in
    CELLS while refining shrinks the shell's physical thickness and understates `matter_in`."""
    mask = np.zeros(shape, dtype=bool)
    sw = int(shell_width)
    for ax in range(len(shape)):
        for edge in (slice(0, sw), slice(shape[ax] - sw, shape[ax])):
            sl = [slice(None)] * len(shape)
            sl[ax] = edge
            mask[tuple(sl)] = True
    return mask


def matter_in(f, outer_mask, k_res, f_res, dx=1.0):
    """matter_in = sum(k_res*(f_res-f))*dx^3 restricted to the FIXED outer-shell reservoir region
    `outer_mask` (from `outer_shell_mask`), matching the F0's frozen volumetric source term
    `J_f^ext = k_res*(f_res-f)*1_{outer(x)}` (added directly into `d_t f`, so its cumulative
    contribution is a VOLUME integral over the outer-shell cells) -- NOT restricted by `phi`,
    which would make the reservoir region track the vessel's position instead of being a fixed
    box-geometry boundary. The `dx^3` cell-volume weighting is required for the total to converge
    under grid refinement at fixed physical box size and fixed physical shell thickness (Codex:
    a bare per-cell sum scales with the number of boundary cells, not the physical fuel-exchange
    rate, so refining 48^3 -> 96^3 would silently change the apparent fuel input); it also keeps
    `matter_in` in the same physical units as `mass_balance_error`'s `mass_before`/`mass_after`
    (both computed via `vessel_flux_3d.total_mass`'s identical `dx^3` convention)."""
    return float((k_res * (f_res - f) * outer_mask).sum()) * dx ** 3


def _reject_negative_concentration(c, eps):
    """Raise iff `c` contains a genuinely NEGATIVE value (beyond `eps` floating-point noise) --
    a negative concentration is unphysical and indicates a caller/solver bug (overshoot), not a
    valid near-zero state. Only `[0, eps)` is treated as numerical noise and floored to `eps` for
    `log(0)`; a real negative value must surface as an error, not be silently floored to look
    like a tiny-but-valid concentration (Codex: clipping c<0 straight to eps let a solver
    overshoot pass a downstream reaction_delta_g/entropy_production check as if nothing were
    wrong)."""
    c = np.asarray(c, dtype=float)
    if np.any(c < -eps):
        raise ValueError(
            "negative concentration detected (c < -eps): unphysical, indicates a solver bug -- "
            "not silently floored to eps")
    return c


def chemical_potential(c, mu0=0.0, RT=1.0, eps=1e-12):
    """Dilute-ideal chemical potential mu = mu0 + RT*ln(c) (F0 frozen reference state). Clipped at
    `eps` to keep log finite for c=0 cells -- this clip is a numerical floor for c>=0, not a
    physics claim. A genuinely negative `c` raises (see `_reject_negative_concentration`) rather
    than being silently treated as ~0."""
    c = _reject_negative_concentration(c, eps)
    return mu0 + RT * np.log(np.clip(c, eps, None))


def _dilute_ideal_free_energy_density(c, mu0=0.0, RT=1.0, eps=1e-12):
    """f(c) = mu0*c + RT*(c*ln(c) - c) -- the dilute-ideal bulk free-energy density whose
    derivative df/dc reproduces `chemical_potential` exactly (mu0 + RT*ln c). This is the
    Legendre-consistent integral of mu(c) dc, NOT `c*mu(c)`: `c*mu(c) = mu0*c + RT*c*ln(c)`
    differs from f(c) by exactly `RT*c` (Codex, 2026-07-17: an earlier version of
    `chemical_free_energy_change` used the bare `c*mu(c)` product, which overstates the true
    free-energy change by `RT*Delta(c)` whenever the total amount of material changes, e.g.
    across a fuel-in/waste-out window -- silently wrong even though `c*mu` LOOKS extensive).
    A genuinely negative `c` raises, matching `chemical_potential`'s discipline. Tolerated
    near-zero noise (`c` in `[-eps, 0)`, allowed through by `_reject_negative_concentration`) is
    normalized to exactly `0.0` before the linear/multiplicative terms (CodeRabbit, second
    finding): otherwise a tolerated tiny-negative value would still flow into `mu0*c + ...` as a
    small but genuinely negative number, giving a spurious nonzero free-energy contribution for a
    cell that's physically empty. The `eps` floor applies ONLY inside the log argument
    (CodeRabbit, first finding): clipping `c` itself before the linear/multiplicative terms would
    give an exact-zero cell a spurious `eps*ln(eps)-eps` contribution (~-2.9e-11 at the default
    eps) instead of exactly 0, which accumulates into a nonzero baseline offset when integrated
    over a large grid with many empty cells."""
    c = _reject_negative_concentration(c, eps)
    c_physical = np.maximum(c, 0.0)
    c_log = np.clip(c_physical, eps, None)
    return mu0 * c_physical + RT * (c_physical * np.log(c_log) - c_physical)


def _mu0_for_species(mu0, k):
    """Look up the preregistered per-species reference potential mu0_i (F0: `mu_i^0` must be
    preregistered) -- a dict `mu0` missing an entry for `k` raises, rather than silently defaulting
    to 0.0 (Codex: a species newly appearing on one side of a stop/restart window, e.g. via
    `chemical_free_energy_change`'s union-of-keys handling, could silently get an unregistered
    mu0=0.0 reference instead of surfacing that the caller forgot to preregister it -- changing
    the ledger's answer without any failure). Pass a plain scalar `mu0` (not a dict) for an
    intentional single shared reference across all species."""
    if isinstance(mu0, dict):
        if k not in mu0:
            raise KeyError(
                "mu0 dict is missing a preregistered reference potential for species %r -- a "
                "missing entry must not silently default to 0.0" % (k,))
        return mu0[k]
    return mu0


def chemical_free_energy_change(species_before, species_after, mu0, RT=1.0, dx=1.0):
    """Delta G = sum_i integral( f_i(c_i_after) - f_i(c_i_before) ) dV, where `f_i(c) = mu0_i*c +
    RT*(c*ln(c) - c)` is the dilute-ideal free-energy DENSITY (see `_dilute_ideal_free_energy_
    density`) whose derivative reproduces `chemical_potential` -- the physically correct integral
    of mu(c) dc for a FINITE concentration change, not the bare product `c*mu(c)` (which is a
    different, larger quantity by `RT*c`). `species_before`/`species_after`: dict species-name ->
    field. `mu0`: dict or scalar. `dx^3` cell-volume weighting converts the free-energy DENSITY
    sum into the extensive integral (Codex: a bare per-cell sum would make this change with grid
    resolution relative to the rest of the ledger -- `matter_in`/`waste_out`/`total_mass` already
    use `dx^3`).

    Iterates the UNION of `species_before`/`species_after` keys (sorted, for run-to-run
    deterministic summation order regardless of Python's hash-randomized set iteration), treating
    a species missing on one side as concentration 0 there -- e.g. a waste/product species that
    is genuinely absent before the window and appears after it (Codex: iterating only
    `species_before`'s keys silently dropped that species' free-energy contribution entirely,
    underreporting Delta G for exactly the stop/restart reaction-chain ledgers this module
    exists to audit). A species present on BOTH sides must have EXACTLY matching field shapes
    (Codex): a malformed snapshot (e.g. a scalar/1-cell placeholder against a full 3D field)
    would otherwise silently broadcast in the `f_after - f_before` subtraction and integrate a
    fabricated uniform field instead of failing closed on the shape mismatch."""
    total = 0.0
    for k in sorted(set(species_before) | set(species_after)):
        mu0_k = _mu0_for_species(mu0, k)
        if k in species_before and k in species_after:
            shape_before = np.asarray(species_before[k]).shape
            shape_after = np.asarray(species_after[k]).shape
            if shape_before != shape_after:
                raise ValueError(
                    "chemical_free_energy_change: species %r has mismatched shapes before %r "
                    "vs after %r" % (k, shape_before, shape_after))
        c_before = species_before[k] if k in species_before else np.zeros_like(species_after[k])
        c_after = species_after[k] if k in species_after else np.zeros_like(species_before[k])
        f_before = _dilute_ideal_free_energy_density(c_before, mu0_k, RT)
        f_after = _dilute_ideal_free_energy_density(c_after, mu0_k, RT)
        total += float((f_after - f_before).sum())
    return total * dx ** 3


def reaction_delta_g(concentrations, stoich, mu0, RT=1.0):
    """Delta G_rxn field = sum_i nu_i * mu_i(c_i), evaluated pointwise (F0 frozen formula).
    `stoich`: dict species -> stoichiometric coefficient nu_i (negative for reactants). This is
    Delta G_rxn itself, NOT the affinity A = -Delta G_rxn -- pass `-reaction_delta_g(...)` as the
    driving force to `entropy_production_reaction` (affinity = -Delta G_rxn, per the F0's frozen
    `entropy_production = sum_rxn(rate*affinity/RT)`)."""
    total = None
    for k, nu in stoich.items():
        mu0_k = _mu0_for_species(mu0, k)
        term = nu * chemical_potential(concentrations[k], mu0_k, RT)
        total = term if total is None else total + term
    return total


def waste_out(w, k_out, region_mask=None, dx=1.0):
    """waste_out = sum(k_out*w)*dx^3 over the WHOLE domain by default (F0's frozen PDE sink
    `-k_out*w` in `∂_t w + u·grad w = div(D(phi) grad w) + k2 m - k_out w` is global, not
    restricted to any sub-region, and is itself a volumetric rate, matching F0's `∮ k_out w dV`).
    Pass `region_mask` only for an explicit diagnostic sub-region breakdown -- the default (None)
    must match the frozen PDE exactly. `dx^3` cell-volume weighting keeps this in the same units
    as `matter_in`/`mass_balance_error`'s before/after mass (`vessel_flux_3d.total_mass`'s `dx^3`
    convention); without it the two terms in `mass_balance_error` would be dimensionally
    inconsistent whenever `dx != 1`."""
    arr = k_out * np.asarray(w)
    if region_mask is not None:
        arr = arr * region_mask
    return float(arr.sum()) * dx ** 3


def entropy_production_reaction(rate, affinity, RT=1.0, dx=1.0):
    """Reaction contribution to entropy production: sum(rate * (-affinity) / RT) * dx^3 -- pass
    the reaction's driving force as `affinity` = -Delta G_rxn (i.e. `-reaction_delta_g(...)`) so
    that a spontaneous (Delta G_rxn<0) reaction contributes a non-negative term, matching the F0's
    ">=0 for a thermodynamically consistent reaction" requirement. A negative result is a real,
    reportable finding (an inconsistent rate law), never silently clipped to zero. `rate` is a
    volumetric reaction-rate DENSITY (matching `reaction_localization.reaction_rate_field`'s
    `k*R*c` convention); `dx^3` converts the per-cell sum into the extensive total entropy
    production (Codex: without it, the required `entropy_production>0` ledger check would scale
    with the number of grid cells, not physical entropy production, under grid refinement)."""
    return float((np.asarray(rate) * affinity / RT).sum()) * dx ** 3


def viscous_dissipation(strain_rate_sq, eta=1.0, dx=1.0):
    """2*eta*integral(e:e) dV -- zero for the S1 stage (u=0, no hydrodynamics yet); kept as a
    hook for later hydrodynamic stages of the P10 mainline (F0 §8). `dx^3` cell-volume weighting
    converts the per-cell sum into the extensive volume integral the F0 defines (`∫ 2η e:e dV`),
    matching `entropy_production_reaction`/`useful_work`'s identical convention (Codex: without
    it, a fixed-L resolution sweep would change the entropy/thermodynamic balance purely from the
    number of grid cells, not the physical dissipation)."""
    return float(2.0 * eta * np.asarray(strain_rate_sq).sum()) * dx ** 3


def useful_work(stress_power_density, phi, band_thresh=0.9, dx=1.0):
    """Free energy converted into boundary MAINTENANCE (F0 §4: `useful_work` = "界面維持へ回った
    自由エネルギー（sigma_M:grad(u) の界面寄与）") -- the caller-supplied `stress_power_density`
    field (= sigma_M : grad(u), the Marangoni-stress power DENSITY; depends on the full stress
    tensor and velocity gradient, which S1 does not yet produce since u=0 -- same caller-supplies-
    the-field pattern as `viscous_dissipation`'s hydrodynamic hook) integrated over ONLY the
    diffuse interface band |phi|<band_thresh, not the bulk -- this is the required Gate III ledger
    field distinguishing energy that maintained the BOUNDARY from energy dissipated in the bulk.
    `dx^3` cell-volume weighting converts the per-cell density sum into the extensive integral
    (Codex: without it, `useful_work` would grow with the number of interface-band cells rather
    than the physical boundary-maintenance power under grid refinement). Zero by construction
    whenever `stress_power_density` is all-zero (S1, u=0) -- callers may pass the bare scalar
    `0.0` for this S1 case (broadcast to `phi`'s shape before masking) rather than being forced
    to construct a full zero-filled field array. A NONZERO scalar is rejected (raises
    ValueError), not silently broadcast: sigma_M:grad(u) is a real per-cell velocity-gradient
    quantity that is never physically uniform across the whole interface band, so a nonzero
    scalar is never a valid measured field -- only ever an accident (e.g. incomplete
    hydrodynamic metadata or a caller passing a scalar total) that must not be able to satisfy a
    downstream `useful_work>0` Gate III check as if it were a real measurement (Codex, second
    finding: the scalar special-case must be limited to the documented 0.0 S1 case). A non-scalar
    `stress_power_density` must match `phi`'s shape EXACTLY, not merely be broadcast-compatible
    (Codex, third finding): an incomplete/malformed field (e.g. a 1-element array or a lower-
    dimensional profile) would otherwise silently broadcast across the whole interface band,
    fabricating a uniform "measured" field from data that was never actually per-cell."""
    band = np.abs(phi) < band_thresh
    phi_shape = np.asarray(phi).shape
    spd = np.asarray(stress_power_density, dtype=float)
    if spd.ndim == 0:
        if spd != 0.0:
            raise ValueError(
                "useful_work: a nonzero scalar stress_power_density is not a valid measured "
                "field -- only the scalar 0.0 (S1 pre-hydrodynamic stage) is accepted; a real "
                "sigma_M:grad(u) measurement must be a per-cell array")
        spd = np.zeros(phi_shape, dtype=float)
    else:
        if spd.shape != phi_shape:
            raise ValueError(
                "useful_work: stress_power_density shape %r does not match phi's shape %r -- a "
                "real per-cell measurement must match exactly, not merely broadcast" %
                (spd.shape, phi_shape))
    return float(spd[band].sum()) * dx ** 3


def mass_balance_error(mass_before, mass_after, matter_in_amt, waste_out_amt, other_sinks=0.0):
    """|Δmass - (matter_in - waste_out - other_sinks)| -- an accounting residual; should be ~0 to
    numerical precision for a correctly integrated scheme."""
    return float(abs((mass_after - mass_before) - (matter_in_amt - waste_out_amt - other_sinks)))


def _reject_invalid_mass(x, label):
    """Raise iff `x` is not a finite, non-negative, non-boolean real number -- a species mass or
    a named source/sink MAGNITUDE can never be negative, non-finite, or a stray boolean (Codex/
    CodeRabbit: an impossible negative mass -- e.g. from a solver bug -- must not be able to
    silently flow into `stoichiometric_balance_error`'s residual and coincidentally balance to
    zero, hiding the corruption instead of surfacing it)."""
    if isinstance(x, (bool, np.bool_)):
        raise ValueError("%s must be a real number, not a boolean" % label)
    try:
        xf = float(x)
    except (TypeError, ValueError):
        raise ValueError("%s must be a finite non-negative real number, got %r" % (label, x))
    if not np.isfinite(xf) or xf < 0.0:
        raise ValueError("%s must be a finite non-negative real number, got %r" % (label, x))
    return xf


def stoichiometric_balance_error(species_masses_before, species_masses_after, stoich,
                                  sources=None, sinks=None):
    """|Delta(sum_i nu_i * mass_i) - (sum(sources) - sum(sinks))| for a reaction chain's conserved
    combination (e.g. total f+m+w for f->m->w with matched coefficients), compared ACROSS A
    BEFORE/AFTER WINDOW (matching `mass_balance_error`'s existing before/after pattern) -- zero
    without external sources/sinks; with them it must match `matter_in`/`waste_out` exactly.
    Comparing the CHANGE in the invariant, not its absolute total, matters: a perfectly conserved
    but nonzero-total system (e.g. mass never leaves f+m+w, but f+m+w != 0) must read as zero
    error, not flag the total mass itself as an accounting bug. A species in `stoich` that is
    absent from `species_masses_before`/`species_masses_after` is treated as mass 0 there (Codex:
    a waste/product species genuinely absent before the window and appearing after it must not
    abort the residual computation -- the same sparse-dictionary handling
    `chemical_free_energy_change` already supports).

    `sources`/`sinks`: optional dicts of named POSITIVE-magnitude terms, mirroring
    `mass_balance_error`'s explicit `matter_in_amt`/`waste_out_amt` sign convention -- `sinks`
    are SUBTRACTED, not blindly summed as if every named term were an addition (Codex: an
    earlier single-dict `source_terms` design would make a caller naturally passing the positive
    `waste_out` MAGNITUDE report a spurious nonzero residual for a correctly balanced window,
    unless they manually negated it first; `sources`/`sinks` removes that footgun by construction,
    same as `mass_balance_error` already does).

    Every consumed mass/source/sink value is validated as a finite, non-negative, non-boolean
    real number (see `_reject_invalid_mass`) before use -- an impossible negative mass must
    raise, never silently produce a coincidentally-balanced zero residual."""
    lhs_before = sum(
        stoich[k] * _reject_invalid_mass(species_masses_before.get(k, 0.0),
                                          "species_masses_before[%r]" % (k,))
        for k in stoich)
    lhs_after = sum(
        stoich[k] * _reject_invalid_mass(species_masses_after.get(k, 0.0),
                                          "species_masses_after[%r]" % (k,))
        for k in stoich)
    rhs_sources = sum(_reject_invalid_mass(v, "sources[%r]" % (k,)) for k, v in sources.items()) if sources else 0.0
    rhs_sinks = sum(_reject_invalid_mass(v, "sinks[%r]" % (k,)) for k, v in sinks.items()) if sinks else 0.0
    return float(abs((lhs_after - lhs_before) - (rhs_sources - rhs_sinks)))
