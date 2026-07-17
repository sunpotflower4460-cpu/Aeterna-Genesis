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


def _reject_invalid_dx(dx):
    """Raise iff `dx` is not a finite, non-boolean real number strictly greater than zero
    (CodeRabbit): `dx=0` silently erases every extensive measurement in this module (`dx**3`
    zeroes the whole ledger), and a negative or non-finite `dx` flips signs or produces invalid
    totals -- neither is a valid cell spacing, so every `dx`-weighted function must fail closed
    on it rather than silently computing a meaningless ledger value."""
    if isinstance(dx, (bool, np.bool_)):
        raise ValueError("dx must be a real number, not a boolean, got %r" % (dx,))
    try:
        dxf = float(dx)
    except (TypeError, ValueError):
        raise ValueError("dx must be a finite positive real number, got %r" % (dx,))
    if not np.isfinite(dxf) or dxf <= 0.0:
        raise ValueError("dx must be a finite positive real number, got %r" % (dx,))
    return dxf


def _reject_invalid_RT(RT):
    """Raise iff `RT` is not a finite, non-boolean real number strictly greater than zero
    (CodeRabbit): `RT=0` divides by zero in some callers and returns silently-zeroed chemical
    potentials in others (`RT*log(...)`), a negative `RT` reverses thermodynamic signs, and a
    non-finite `RT` contaminates every downstream free-energy/entropy measurement -- none of
    these is a valid absolute-temperature-scaled energy unit, so every RT-consuming function must
    fail closed on it."""
    if isinstance(RT, (bool, np.bool_)):
        raise ValueError("RT must be a real number, not a boolean, got %r" % (RT,))
    try:
        rtf = float(RT)
    except (TypeError, ValueError):
        raise ValueError("RT must be a finite positive real number, got %r" % (RT,))
    if not np.isfinite(rtf) or rtf <= 0.0:
        raise ValueError("RT must be a finite positive real number, got %r" % (RT,))
    return rtf


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
    CELLS while refining shrinks the shell's physical thickness and understates `matter_in`.

    `shell_width` must be a positive integer (Codex): `int(shell_width)` silently TRUNCATES a
    fractional width (e.g. `1.7` -> `1`) and silently ACCEPTS a negative width as a valid Python
    slice bound (`slice(0, -1)` marks almost the entire box as the reservoir instead of failing)
    -- this mask defines the fixed, preregistered fuel-source geometry that `matter_in` integrates
    over, so a config typo must fail closed rather than silently redefining that geometry."""
    if isinstance(shell_width, (bool, np.bool_)):
        raise ValueError("shell_width must be a positive integer, not a boolean, got %r" % (shell_width,))
    if shell_width != int(shell_width) or shell_width <= 0:
        raise ValueError(
            "shell_width must be a positive integer (in cells), got %r -- a fractional or "
            "non-positive width would silently truncate or redefine the reservoir geometry" %
            (shell_width,))
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
    (both computed via `vessel_flux_3d.total_mass`'s identical `dx^3` convention).

    `outer_mask` must have EXACTLY `f`'s shape (Codex): a scalar or wrong-shaped-but-broadcast-
    compatible mask would otherwise silently broadcast and integrate the WRONG region -- e.g. a
    bare `outer_mask=True` integrates fuel exchange over the ENTIRE domain instead of the fixed
    outer shell, corrupting the stop/restart mass/energy ledger this function feeds. `outer_mask`
    must ALSO have `dtype == bool` exactly (CodeRabbit): a same-shaped NUMERIC mask (e.g. all
    `0.5`) passes the shape check but is not a 0/1 selector -- it silently WEIGHTS the reservoir
    integration by arbitrary fractional values instead of selecting the shell region, corrupting
    the ledger without any shape mismatch to catch it. `dx` is validated as finite/positive/
    non-boolean (CodeRabbit): `dx=0` would silently erase this measurement entirely.

    `f` (a non-negative concentration field, see `_reject_negative_concentration`) and `k_res`/
    `f_res` (finite, non-negative, non-boolean rate/reference-concentration constants) are
    validated before use (Codex): an unchecked negative/non-finite `f` -- e.g. from a solver
    overshoot -- would otherwise be folded directly into `matter_in` and could offset a matching
    mass change in the stop/restart ledger. The computed TOTAL may still be legitimately negative
    when a valid `f > f_res` (net efflux) -- only the individual inputs are constrained, not the
    formula's sign."""
    dx = _reject_invalid_dx(dx)
    f_arr = _reject_negative_concentration(f, eps=1e-12)
    if isinstance(k_res, (bool, np.bool_)) or not np.isfinite(k_res) or k_res < 0.0:
        raise ValueError("matter_in: k_res must be a finite, non-negative rate constant, got %r" % (k_res,))
    if isinstance(f_res, (bool, np.bool_)) or not np.isfinite(f_res) or f_res < 0.0:
        raise ValueError(
            "matter_in: f_res must be a finite, non-negative reference concentration, got %r" % (f_res,))
    mask_arr = np.asarray(outer_mask)
    if mask_arr.dtype != np.bool_:
        raise ValueError(
            "matter_in: outer_mask must have dtype bool, got %r -- a numeric mask silently "
            "weights the reservoir integration by arbitrary values instead of selecting cells" %
            (mask_arr.dtype,))
    if mask_arr.shape != f_arr.shape:
        raise ValueError(
            "matter_in: outer_mask shape %r does not match f's shape %r -- a malformed mask "
            "must fail closed rather than silently broadcast over the wrong region" %
            (mask_arr.shape, f_arr.shape))
    return float((k_res * (f_res - f_arr) * mask_arr).sum()) * dx ** 3


def _reject_negative_concentration(c, eps):
    """Raise iff `c` contains a genuinely NEGATIVE value (beyond `eps` floating-point noise) --
    a negative concentration is unphysical and indicates a caller/solver bug (overshoot), not a
    valid near-zero state. Only `[0, eps)` is treated as numerical noise and floored to `eps` for
    `log(0)`; a real negative value must surface as an error, not be silently floored to look
    like a tiny-but-valid concentration (Codex: clipping c<0 straight to eps let a solver
    overshoot pass a downstream reaction_delta_g/entropy_production check as if nothing were
    wrong). A boolean `c` (scalar or array) is rejected before the float cast (Codex, third
    finding): an accidentally-passed occupancy/mask array would otherwise have its `True`/`False`
    cells silently cast to `1.0`/`0.0` by `np.asarray(c, dtype=float)` and flow through
    `chemical_potential`/`reaction_delta_g`/`chemical_free_energy_change` as if it were a real
    measured concentration. The boolean check converts `c` to an array FIRST and inspects its
    `dtype` (CodeRabbit): checking `isinstance(c, (bool, np.bool_))` on the raw input misses a
    plain PYTHON LIST of booleans (e.g. `[True, False]`), which is neither a `bool` scalar nor an
    `np.ndarray` yet, but still has its elements silently cast to `1.0`/`0.0` once converted."""
    c_check = np.asarray(c)
    if c_check.dtype == np.bool_:
        raise ValueError(
            "concentration must be a real-valued field/scalar, not a boolean array/value -- "
            "True/False must never silently convert to 1.0/0.0 and be treated as a measured "
            "concentration")
    c = c_check.astype(float)
    if not np.all(np.isfinite(c)):
        raise ValueError(
            "non-finite concentration (inf/nan) detected -- indicates a solver blow-up, not a "
            "valid measurement (Codex: inf/nan are invisible to the c < -eps check below, since "
            "both `inf < -eps` and `nan < -eps` are False)")
    if np.any(c < -eps):
        raise ValueError(
            "negative concentration detected (c < -eps): unphysical, indicates a solver bug -- "
            "not silently floored to eps")
    return c


def chemical_potential(c, mu0=0.0, RT=1.0, eps=1e-12):
    """Dilute-ideal chemical potential mu = mu0 + RT*ln(c) (F0 frozen reference state). Clipped at
    `eps` to keep log finite for c=0 cells -- this clip is a numerical floor for c>=0, not a
    physics claim. A genuinely negative `c` raises (see `_reject_negative_concentration`) rather
    than being silently treated as ~0. `RT` is validated as finite/positive/non-boolean
    (CodeRabbit, see `_reject_invalid_RT`): `RT=0`/negative/non-finite silently zeroes, reverses
    the sign of, or contaminates every chemical potential computed from this function."""
    c = _reject_negative_concentration(c, eps)
    RT = _reject_invalid_RT(RT)
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
    over a large grid with many empty cells. `RT` is validated as finite/positive/non-boolean
    (CodeRabbit, see `_reject_invalid_RT`), matching `chemical_potential`'s discipline -- the two
    must agree on which `RT` values are valid since this function's derivative must reproduce
    `chemical_potential` exactly."""
    c = _reject_negative_concentration(c, eps)
    RT = _reject_invalid_RT(RT)
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
    fabricated uniform field instead of failing closed on the shape mismatch.

    ALL species (not just each species' own before/after pair) must share ONE common non-scalar
    grid shape (CodeRabbit): the per-species check above only compares a species against ITSELF,
    so two DIFFERENT species could each pass with internally-consistent but mutually different
    shapes (e.g. species 'a' on a 2x2x2 grid, species 'b' on a 4x4x4 grid) and still be summed
    together into one purported domain integral -- a physically meaningless total, since `dx^3`
    then means a different physical cell volume for each species' contribution."""
    dx = _reject_invalid_dx(dx)
    domain_shape = None
    for k in sorted(set(species_before) | set(species_after)):
        for side, d in (("before", species_before), ("after", species_after)):
            if k in d:
                s = np.asarray(d[k]).shape
                if s == ():
                    continue
                if domain_shape is None:
                    domain_shape = s
                elif s != domain_shape:
                    raise ValueError(
                        "chemical_free_energy_change: species %r (%s) has shape %r, which does "
                        "not match the common domain shape %r established by another species -- "
                        "every species must share ONE grid, not be independently shaped" %
                        (k, side, s, domain_shape))
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


def _reject_invalid_coefficient(nu, label):
    """Raise iff `nu` is not a finite, non-boolean real SCALAR -- a stoichiometric coefficient's
    SIGN is meaningful (negative for reactants, positive for products) and must NOT be
    restricted, unlike a mass/amount magnitude (CodeRabbit/Codex: `nu` values are used without
    validation, so a `NaN` coefficient silently propagates a `NaN` audit result, and an array
    `nu` can introduce unintended broadcasting into what should be a per-species scalar term)."""
    if isinstance(nu, (bool, np.bool_)):
        raise ValueError("%s must be a real number, not a boolean, got %r" % (label, nu))
    try:
        nuf = float(nu)
    except (TypeError, ValueError):
        raise ValueError("%s must be a finite real scalar, got %r" % (label, nu))
    if not np.isfinite(nuf):
        raise ValueError("%s must be a finite real scalar, got %r" % (label, nu))
    return nuf


def reaction_delta_g(concentrations, stoich, mu0, RT=1.0):
    """Delta G_rxn field = sum_i nu_i * mu_i(c_i), evaluated pointwise (F0 frozen formula).
    `stoich`: dict species -> stoichiometric coefficient nu_i (negative for reactants). This is
    Delta G_rxn itself, NOT the affinity A = -Delta G_rxn -- pass `-reaction_delta_g(...)` as the
    driving force to `entropy_production_reaction` (affinity = -Delta G_rxn, per the F0's frozen
    `entropy_production = sum_rxn(rate*affinity/RT)`).

    Every non-scalar species concentration used in `stoich` must share the SAME grid shape
    (Codex): a broadcast-compatible placeholder (e.g. a 1-element array for one species against a
    full 3-D field for another) would otherwise silently broadcast in the `total = term if ...
    else total + term` sum, fabricating a finite Delta G_rxn field from malformed reaction
    metadata instead of failing closed on the shape mismatch. Every coefficient `nu_i` is
    validated as a finite, non-boolean real scalar (see `_reject_invalid_coefficient`) -- signed
    values remain valid (a coefficient's sign IS its physical meaning)."""
    shapes = {np.asarray(concentrations[k]).shape for k in stoich} - {()}
    if len(shapes) > 1:
        raise ValueError(
            "reaction_delta_g: species concentration fields have mismatched shapes %r -- every "
            "species used in this reaction must share the same grid shape" % (sorted(shapes),))
    total = None
    for k, nu in stoich.items():
        nu = _reject_invalid_coefficient(nu, "stoich[%r]" % (k,))
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
    inconsistent whenever `dx != 1`.

    `w` and `k_out` are validated as finite and non-negative (Codex): the frozen ledger treats
    waste removal as a positive sink magnitude, so a negative concentration overshoot in `w` or a
    negative/non-finite `k_out` -- either of which would otherwise silently produce a negative or
    infinite `waste_out` -- must fail closed instead of letting a corrupted sink measurement flow
    into `mass_balance_error`'s accounting and coincidentally offset a real mass change. A
    non-`None` `region_mask` must have `dtype == bool` AND exactly `w`'s shape (CodeRabbit): a
    bare `region_mask=True` would otherwise silently ignore the intended subregion (integrating
    the whole domain), and a numeric mask would silently RESCALE the sink by arbitrary weights,
    corrupting the subregion accounting without any error. `dx` is validated as finite/positive/
    non-boolean (see `_reject_invalid_dx`)."""
    dx = _reject_invalid_dx(dx)
    w_arr = _reject_negative_concentration(w, eps=1e-12)
    if isinstance(k_out, (bool, np.bool_)) or not np.isfinite(k_out) or k_out < 0.0:
        raise ValueError(
            "waste_out: k_out must be a finite, non-negative rate constant, got %r" % (k_out,))
    arr = k_out * w_arr
    if region_mask is not None:
        mask_arr = np.asarray(region_mask)
        if mask_arr.dtype != np.bool_:
            raise ValueError(
                "waste_out: region_mask must have dtype bool, got %r -- a numeric mask silently "
                "rescales the sink instead of selecting cells" % (mask_arr.dtype,))
        if mask_arr.shape != w_arr.shape:
            raise ValueError(
                "waste_out: region_mask shape %r does not match w's shape %r" %
                (mask_arr.shape, w_arr.shape))
        arr = arr * mask_arr
    return float(arr.sum()) * dx ** 3


def entropy_production_reaction(rate, affinity, RT=1.0, dx=1.0):
    """Reaction contribution to entropy production: sum(rate * affinity / RT) * dx^3 -- pass
    the reaction's driving force as `affinity` = -Delta G_rxn (i.e. `-reaction_delta_g(...)`) so
    that a spontaneous (Delta G_rxn<0) reaction contributes a non-negative term, matching the F0's
    ">=0 for a thermodynamically consistent reaction" requirement. A negative result is a real,
    reportable finding (an inconsistent rate law), never silently clipped to zero. `rate` is a
    volumetric reaction-rate DENSITY (matching `reaction_localization.reaction_rate_field`'s
    `k*R*c` convention); `dx^3` converts the per-cell sum into the extensive total entropy
    production (Codex: without it, the required `entropy_production>0` ledger check would scale
    with the number of grid cells, not physical entropy production, under grid refinement).

    When BOTH `rate` and `affinity` are non-scalar, their shapes must match EXACTLY (Codex,
    second finding): a broadcast-compatible-but-incomplete placeholder for one of them (e.g. a
    1-element array standing in for a full 3-D field) would otherwise silently broadcast across
    the whole domain and report a finite entropy-production total from malformed per-cell
    reaction metadata, satisfying a downstream `entropy_production>0` ledger check without a real
    measured rate/affinity field. A scalar `rate` or `affinity` (a caller's deliberate uniform
    value) remains a legitimate broadcast against the other.

    `rate` and `affinity` are each rejected outright if boolean (scalar or array) or non-finite
    (Codex, third finding): `np.asarray(x, dtype=float)` would otherwise silently cast a boolean
    mask's `True`/`False` to `1.0`/`0.0`, and an unchecked `inf` would propagate to a positive-
    infinite entropy-production total -- either way letting corrupted/unmeasured reaction
    metadata satisfy the preregistered `entropy_production > 0` maintenance-evidence check instead
    of failing closed. Sign itself is NOT restricted (a negative rate*affinity combination is a
    real, reportable inconsistent-rate-law finding, per this function's own documented behavior).
    The boolean check converts to an array FIRST and inspects `dtype` (CodeRabbit), matching
    `_reject_negative_concentration`'s discipline -- an `isinstance` check on the raw input misses
    a plain Python list of booleans. `RT` is validated as finite/positive/non-boolean (CodeRabbit,
    see `_reject_invalid_RT`) and `dx` as finite/positive/non-boolean (see `_reject_invalid_dx`)."""
    RT = _reject_invalid_RT(RT)
    dx = _reject_invalid_dx(dx)
    rate_check = np.asarray(rate)
    if rate_check.dtype == np.bool_:
        raise ValueError("entropy_production_reaction: rate must be real-valued, not boolean")
    affinity_check = np.asarray(affinity)
    if affinity_check.dtype == np.bool_:
        raise ValueError("entropy_production_reaction: affinity must be real-valued, not boolean")
    rate_arr = rate_check.astype(float)
    affinity_arr = affinity_check.astype(float)
    if not np.all(np.isfinite(rate_arr)):
        raise ValueError("entropy_production_reaction: rate contains non-finite values (inf/nan)")
    if not np.all(np.isfinite(affinity_arr)):
        raise ValueError("entropy_production_reaction: affinity contains non-finite values (inf/nan)")
    if rate_arr.ndim != 0 and affinity_arr.ndim != 0 and rate_arr.shape != affinity_arr.shape:
        raise ValueError(
            "entropy_production_reaction: non-scalar rate has shape %r but non-scalar affinity "
            "has shape %r -- both must describe the same grid cells, not merely broadcast" %
            (rate_arr.shape, affinity_arr.shape))
    return float((rate_arr * affinity_arr / RT).sum()) * dx ** 3


def viscous_dissipation(strain_rate_sq, eta=1.0, dx=1.0):
    """2*eta*integral(e:e) dV -- zero for the S1 stage (u=0, no hydrodynamics yet); kept as a
    hook for later hydrodynamic stages of the P10 mainline (F0 §8). `dx^3` cell-volume weighting
    converts the per-cell sum into the extensive volume integral the F0 defines (`∫ 2η e:e dV`),
    matching `entropy_production_reaction`/`useful_work`'s identical convention (Codex: without
    it, a fixed-L resolution sweep would change the entropy/thermodynamic balance purely from the
    number of grid cells, not the physical dissipation).

    `strain_rate_sq` (e:e, a sum of squared tensor components) is a real physical quantity that
    is ALWAYS non-negative and finite -- boolean, negative, or non-finite entries are impossible
    measurements and must fail closed rather than being integrated as valid dissipation (Codex,
    second finding: `True`/`False` silently cast to `1.0`/`0.0`, and `inf` stays positive, so
    missing/corrupted hydrodynamic metadata could otherwise report a positive viscous-dissipation
    total that feeds the thermodynamic ledger's entropy-production evidence as if it were real).

    `eta` (a physical viscosity coefficient) is validated as finite/non-negative/non-boolean
    (CodeRabbit): an invalid `eta` -- e.g. `-1`, `nan`, or a boolean -- would otherwise convert
    directly into negative, non-finite, or mask-derived dissipation despite `strain_rate_sq`
    itself being fully validated. `dx` is validated as finite/positive/non-boolean (see
    `_reject_invalid_dx`)."""
    dx = _reject_invalid_dx(dx)
    if isinstance(eta, (bool, np.bool_)) or not np.isfinite(eta) or eta < 0.0:
        raise ValueError("viscous_dissipation: eta must be a finite, non-negative real number, got %r" % (eta,))
    sr = np.asarray(strain_rate_sq)
    if sr.dtype == np.bool_:
        raise ValueError(
            "viscous_dissipation: strain_rate_sq must be a real-valued field, not a boolean "
            "array -- True/False must never silently convert to 1.0/0.0")
    sr = sr.astype(float)
    if not np.all(np.isfinite(sr)):
        raise ValueError("viscous_dissipation: strain_rate_sq contains non-finite values (inf/nan)")
    if np.any(sr < 0.0):
        raise ValueError(
            "viscous_dissipation: strain_rate_sq contains negative values -- e:e is a sum of "
            "squared tensor components and can never be negative, indicates corrupted metadata")
    return float(2.0 * eta * sr.sum()) * dx ** 3


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
    fabricating a uniform "measured" field from data that was never actually per-cell.

    A boolean `stress_power_density` (scalar or array) is rejected outright, before the `float`
    cast (Codex, fourth finding): `np.asarray(x, dtype=float)` silently turns `True`/`False` cells
    into `1.0`/`0.0`, which could otherwise report positive boundary-maintenance work from a
    boolean mask rather than any real measured `sigma_M:grad(u)` field. Non-finite (`inf`/`nan`)
    entries are also rejected: an `inf` cell would otherwise propagate to a positive-infinite
    `useful_work` total, letting a Gate III ledger's `useful_work>0` check pass corrupted
    hydrodynamic metadata instead of failing closed.

    `phi` itself is validated as finite and non-boolean BEFORE `band` is constructed (CodeRabbit):
    a `NaN` cell makes `abs(phi) < band_thresh` False (NaN comparisons are always False), so a
    corrupted interface cell would otherwise be silently EXCLUDED from the band rather than
    failing the whole measurement, underreporting Gate III work instead of surfacing the
    corruption. `dx` is validated as finite/positive/non-boolean (see `_reject_invalid_dx`)."""
    dx = _reject_invalid_dx(dx)
    phi_check = np.asarray(phi)
    if phi_check.dtype == np.bool_:
        raise ValueError("useful_work: phi must be a real-valued field, not boolean")
    phi_arr = phi_check.astype(float)
    if not np.all(np.isfinite(phi_arr)):
        raise ValueError(
            "useful_work: phi contains non-finite values (inf/nan) -- a corrupted interface "
            "field would otherwise be silently excluded from band (NaN comparisons are always "
            "False) instead of failing the whole measurement")
    band = np.abs(phi_arr) < band_thresh
    phi_shape = phi_arr.shape
    spd_raw = np.asarray(stress_power_density)
    if spd_raw.dtype == np.bool_:
        raise ValueError(
            "useful_work: stress_power_density must be a real-valued field/scalar, not a "
            "boolean array/value -- True/False must never silently convert to 1.0/0.0")
    spd = spd_raw.astype(float)
    if not np.all(np.isfinite(spd)):
        raise ValueError("useful_work: stress_power_density contains non-finite values (inf/nan)")
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


def _reject_invalid_signed_amount(x, label):
    """Raise iff `x` is not a finite, non-boolean real number -- unlike `_reject_invalid_mass`,
    sign is NOT restricted here: `matter_in_amt` can be genuinely NEGATIVE (the frozen `matter_in`
    formula `k_res*(f_res-f)` summed over the outer shell is a net rate that flips sign under a
    real net-efflux transient, e.g. once interior fuel diffuses out and locally exceeds the
    reservoir concentration), so forcing non-negative here would reject a real measurement, not
    just corrupted data. Booleans and non-finite (`inf`/`nan`) values ARE always corruption
    regardless of sign (Codex: `True`/`False` silently cast to `1.0`/`0.0`, and an unchecked
    `inf`/`nan` term could coincidentally offset the balance and pass the audit) and are rejected
    outright."""
    if isinstance(x, (bool, np.bool_)):
        raise ValueError("%s must be a real number, not a boolean" % label)
    try:
        xf = float(x)
    except (TypeError, ValueError):
        raise ValueError("%s must be a finite real number, got %r" % (label, x))
    if not np.isfinite(xf):
        raise ValueError("%s must be a finite real number, got %r" % (label, x))
    return xf


def mass_balance_error(mass_before, mass_after, matter_in_amt, waste_out_amt, other_sinks=0.0):
    """|Δmass - (matter_in - waste_out - other_sinks)| -- an accounting residual; should be ~0 to
    numerical precision for a correctly integrated scheme.

    `mass_before`/`mass_after` (a `total_mass`-style sum of a non-negative concentration field)
    are validated as finite, non-negative, non-boolean. `matter_in_amt` is the ONLY term
    validated as merely finite/non-boolean via `_reject_invalid_signed_amount` (sign
    unrestricted -- it can be legitimately negative under net efflux, per `matter_in`'s own
    formula). `waste_out_amt`/`other_sinks` are SINK magnitudes -- they are SUBTRACTED, so they
    must be non-negative via `_reject_invalid_mass` (CodeRabbit/Codex: `_reject_invalid_signed_
    amount` on these would let a negative value become an ADDITION and silently cancel a real
    residual, e.g. `mass_before=10, mass_after=15, matter_in_amt=3, waste_out_amt=-2` passing as
    if `+2` of extra waste had left the system, exactly backwards for an impossible negative
    waste-removal magnitude). Without any validation, a negative or boolean mass could otherwise
    coincidentally offset the residual and pass the `mass_balance_error ~ 0` audit with corrupted
    accounting data instead of surfacing it (Codex)."""
    mass_before = _reject_invalid_mass(mass_before, "mass_before")
    mass_after = _reject_invalid_mass(mass_after, "mass_after")
    matter_in_amt = _reject_invalid_signed_amount(matter_in_amt, "matter_in_amt")
    waste_out_amt = _reject_invalid_mass(waste_out_amt, "waste_out_amt")
    other_sinks = _reject_invalid_mass(other_sinks, "other_sinks")
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
    raise, never silently produce a coincidentally-balanced zero residual. Every `stoich[k]`
    coefficient is also validated as a finite, non-boolean real scalar (see
    `_reject_invalid_coefficient`, CodeRabbit) -- a `NaN` coefficient would otherwise silently
    return a `NaN` audit result, and an array coefficient could introduce unintended broadcasting;
    sign remains unrestricted (a coefficient's sign is its physical meaning)."""
    lhs_before = sum(
        _reject_invalid_coefficient(stoich[k], "stoich[%r]" % (k,)) *
        _reject_invalid_mass(species_masses_before.get(k, 0.0),
                              "species_masses_before[%r]" % (k,))
        for k in stoich)
    lhs_after = sum(
        _reject_invalid_coefficient(stoich[k], "stoich[%r]" % (k,)) *
        _reject_invalid_mass(species_masses_after.get(k, 0.0),
                              "species_masses_after[%r]" % (k,))
        for k in stoich)
    rhs_sources = sum(_reject_invalid_mass(v, "sources[%r]" % (k,)) for k, v in sources.items()) if sources else 0.0
    rhs_sinks = sum(_reject_invalid_mass(v, "sinks[%r]" % (k,)) for k, v in sinks.items()) if sinks else 0.0
    return float(abs((lhs_after - lhs_before) - (rhs_sources - rhs_sinks)))
