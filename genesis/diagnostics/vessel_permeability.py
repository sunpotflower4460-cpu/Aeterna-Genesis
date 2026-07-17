#!/usr/bin/env python3
"""Fixed-geometry selective-permeability validator for the Active Vessel white (P10, F1 V0, role V).

WHAT IT IS
A VALIDATOR, not an emergence claim. On a FIXED spherical interface (`phi` = a hand-placed tanh
radial profile — the "vessel" is seeded here, deliberately), it checks that the selective-
permeability instrument this campaign will use for Gate I (`docs/VERTICAL_EMERGENCE_CONTRACT.md`
§2, `docs/frontier/F0_P10_active_vessel.md`) measures the KNOWN equilibrium partition law
correctly, and — the point of the whole exercise — that species selectivity comes from the
free-energy partition coefficients `chi_i` (emergent partitioning driven by a SINGLE shared
mobility) and NOT from hand-placed species-specific diffusivities. That distinction is exactly
the target-encoding hole external review (Codex, 2026-07-16) flagged on the F0: species-specific
`D_i(phi)` would bake the desired selectivity into the law before any vessel forms, so "selective
permeability" would just read back the chosen functions. Here D is one shared `D(phi)` and
selectivity must come from `chi_i` — this validator proves the instrument honours that.

KNOWN LAW (what we validate against)
For a conserved species `c` with free-energy density  `RT (c ln c - c) + chi phi c` , the chemical
potential is  `mu = RT ln c + chi phi` . Conserved (Model-B) relaxation with a single mobility M,

    d_t c = -div J ,   J = -D ( grad c + chi c grad phi ) ,   D := M RT ,

drives c to the zero-flux steady state  `c(x) ∝ exp(-chi phi(x) / RT)`  (Boltzmann/Nernst
partition). Equivalently, at steady state the invariant  `g(x) := c(x) exp(chi phi(x) / RT)`  is
spatially UNIFORM — a geometry-independent check we use directly. For a tanh sphere with phi -> +1
inside and phi -> -1 outside, the inside/outside partition ratio is  `c_in/c_out ≈ exp(-chi (⟨phi⟩_in
- ⟨phi⟩_out) / RT)` . Selectivity between two species is set by `chi_a - chi_b` ONLY; with
`chi_a == chi_b` there is NO selectivity even though both diffuse under the identical `D(phi)`.

WHAT IT IS NOT
- NOT a self-formed vessel: `phi` is fixed and placed. This validator must PASS before any
  S1/E2/E3 emergence claim of the P10 ladder — it establishes the Gate-I instrument, nothing more.
- NOT the full non-equilibrium permeability (fuel source inside/sink outside): that arrives at
  F2+. V0 validates the equilibrium partition (the core Gate-I selectivity readout) and exact
  discrete mass conservation of the transport instrument.
- no_touch: this is an additive observer; it does NOT modify `measures.py` or any official Room
  (same discipline as LT-1/2/3 and `vortex_lines_3d.py`).
"""
import numpy as np


def radial_phi(L, radius, width, center=None):
    """Fixed tanh spherical interface on an (L, L, L) grid: phi -> +1 inside r<radius, -1 outside.

    This is the HAND-PLACED vessel geometry of the F1 V0 validator (seeded, not emergent).
    """
    if center is None:
        center = (L - 1) / 2.0
    idx = np.arange(L, dtype=float)
    X, Y, Z = np.meshgrid(idx, idx, idx, indexing="ij")
    r = np.sqrt((X - center) ** 2 + (Y - center) ** 2 + (Z - center) ** 2)
    return np.tanh((radius - r) / width)


def _bernoulli(x):
    """Bernoulli function B(x) = x / (exp(x) - 1), with the removable singularity B(0)=1 handled
    by a small-argument series. Used for the Scharfetter-Gummel face flux (below)."""
    out = np.empty_like(x, dtype=float)
    big = np.abs(x) >= 1e-6
    xb = x[big]
    out[big] = xb / np.expm1(xb)
    xs = x[~big]
    out[~big] = 1.0 - xs / 2.0 + xs * xs / 12.0   # Taylor of x/(e^x-1) about 0
    return out


def relax_step(c, phi, chi, D=1.0, dt=0.1, RT=1.0):
    """One explicit finite-VOLUME step of  d_t c = -div J,  J = -D (grad c + (chi/RT) c grad phi),
    with no-flux (Neumann) domain boundaries, using the SCHARFETTER-GUMMEL (exponentially fitted)
    face flux.

    Why SG rather than a central face flux (external review, Codex, 2026-07-17): a central flux
    `J = -D[(c_{i+1}-c_i) + beta*c_face*(phi_{i+1}-phi_i)]` has zero-flux state
    `c_{i+1}/c_i = (1 - beta*dphi/2)/(1 + beta*dphi/2)`, which only matches the true Boltzmann
    ratio `exp(-beta*dphi)` to second order -- so for a sharp interface or large chi the scheme's
    own steady state drifts from the KNOWN law this validator must certify. The SG face flux
    `J = D[ B(beta*dphi) c_i - B(-beta*dphi) c_{i+1} ]` (B = Bernoulli) is exactly Boltzmann-
    balanced: its zero-flux state is `c_{i+1}/c_i = B(beta*dphi)/B(-beta*dphi) = exp(-beta*dphi)`
    for ANY dphi, so the discrete equilibrium IS `c ∝ exp(-beta phi)` to machine precision.

    Still a shared per-face value used with opposite sign by the two adjacent cells, so discrete
    mass stays EXACTLY conserved (checked by `test_mass_is_exactly_conserved`).
    """
    L = c.shape[0]
    dc = np.zeros_like(c)
    beta = chi / RT
    for ax in range(3):
        cp = np.roll(c, -1, axis=ax)          # c[i+1]
        pp = np.roll(phi, -1, axis=ax)        # phi[i+1]
        dpsi = beta * (pp - phi)              # potential jump across the face i|i+1
        # Scharfetter-Gummel flux toward +ax across the face between cell i and i+1:
        J = D * (_bernoulli(dpsi) * c - _bernoulli(-dpsi) * cp)
        # Neumann: no flux across the domain boundary (the wrap-around face at index L-1 along ax).
        sl = [slice(None)] * 3
        sl[ax] = L - 1
        J[tuple(sl)] = 0.0
        Jm = np.roll(J, 1, axis=ax)           # flux across the face between cell i-1 and i
        sl0 = [slice(None)] * 3
        sl0[ax] = 0
        Jm[tuple(sl0)] = 0.0                  # first cell has no left neighbour
        dc += (Jm - J)                        # d_t c[i] = J_{i-1} - J_i  (in from left, out right)
    return c + dt * dc


def equilibrate(phi, chi, D=1.0, dt=0.1, RT=1.0, n_steps=4000, c0=1.0):
    """Relax a single conserved species from a uniform field c0 to the partition steady state.

    Returns (c, converged, boltzmann_cv): `c` the final field, `converged` whether the Boltzmann
    invariant g = c exp(chi phi / RT) is uniform to <1% (CV), and the CV value itself.
    """
    c = np.full(phi.shape, float(c0))
    for _ in range(int(n_steps)):
        c = relax_step(c, phi, chi, D=D, dt=dt, RT=RT)
    cv = boltzmann_invariant_cv(c, phi, chi, RT=RT)
    return c, bool(cv < 1e-2), cv


def boltzmann_invariant_cv(c, phi, chi, RT=1.0):
    """Coefficient of variation of g(x) = c(x) exp(chi phi(x) / RT). Zero iff c ∝ exp(-chi phi/RT)
    exactly (the Boltzmann/Nernst partition law) -- the geometry-independent Gate-I validation."""
    g = c * np.exp((chi / RT) * phi)
    return float(np.std(g) / np.mean(g))


def partition_ratio(c, phi, thresh=0.5):
    """Inside/outside concentration ratio: mean c where phi>thresh over mean c where phi<-thresh."""
    inside = phi > thresh
    outside = phi < -thresh
    return float(c[inside].mean() / c[outside].mean())


def predicted_partition_ratio(phi, chi, thresh=0.5, RT=1.0):
    """The known-law prediction for `partition_ratio`, which compares VOLUME-AVERAGED
    concentrations. With c ∝ exp(-chi phi/RT), the correct target is therefore
    `mean(exp(-chi phi/RT))_in / mean(exp(-chi phi/RT))_out` -- the mean of the Boltzmann factor,
    NOT `exp(-chi (⟨phi⟩_in-⟨phi⟩_out)/RT)` (those differ by Jensen's inequality whenever phi
    varies within the masks, e.g. a diffuse interface or a looser threshold -- external review,
    Codex, 2026-07-17)."""
    inside = phi > thresh
    outside = phi < -thresh
    w = np.exp(-(chi / RT) * phi)
    return float(w[inside].mean() / w[outside].mean())


def total_mass(c):
    """Total conserved species amount (should be invariant under `relax_step`)."""
    return float(c.sum())


def net_interface_flux(c, phi, chi, D=1.0, RT=1.0, thresh=0.5):
    """Net species flux crossing into the vessel interior (|phi|<thresh shell boundary), measured
    as d(inside mass)/dt from the same finite-volume fluxes. ~0 at equilibrium (Gate-I sanity)."""
    c_next = relax_step(c, phi, chi, D=D, dt=1.0, RT=RT)
    inside = phi > thresh
    return float((c_next - c)[inside].sum())
