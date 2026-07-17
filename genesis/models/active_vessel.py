#!/usr/bin/env python3
"""Coupled dynamic 'chemically active vessel' solver (Active Vessel white P10, F2 S1) -- WIP.

STATUS (2026-07-17): WORK IN PROGRESS, NOT MERGED, NO EMERGENCE CLAIM YET.
The chemistry (SG partition transport, single D(phi), outside-only fuel, R=const reaction),
the maintenance coupling kappa(m), and the role-V measurement helpers are implemented and stable.
BUT the phi integrator below uses CONSERVED ALLEN-CAHN (nonlocal Lagrange multiplier), and a
direct artifact check found that a BARE seeded vessel (zero chemistry) DISSOLVES to a uniform phi
under it: the nonlocal multiplier conserves TOTAL phi globally but lets a single droplet shrink
while the background rises to compensate (a known property of conserved Allen-Cahn -- it is NOT
locally mass-conserving like Model B/H). Any "maintenance-loop" signal measured on top of this is
confounded by the dissolution artifact and must NOT be reported as emergence. The correct vessel
model is locally-conserved CAHN-HILLIARD (Model B/H, as the F0 specifies), which requires a
stable semi-implicit spectral integrator (explicit CH is biharmonic-stiff and blows up). Replacing
the phi step with that is the next step before any S1 Gate-II-candidate measurement is trustworthy.
Kept as scaffolding: the chemistry/coupling/measurement code is reusable once phi uses CH.

--- original design intent (unchanged) ---


WHAT IT IS
The dynamic step up from the F1 V0 fixed-sphere validator (`genesis/diagnostics/vessel_permeability.py`):
a coupled model where a conserved phase field phi (the vessel, Cahn-Hilliard / Model B, u=0 for S1)
carries three chemical species f->m->w with a SINGLE shared mobility D(phi), fuel supplied only in
the OUTSIDE bulk, and a maintenance coupling where the reaction product m modulates the interface
stiffness kappa(m). This is the instrument the S1 stage of `docs/frontier/F0_P10_active_vessel.md`
uses to ask whether a selective boundary, reaction concentration, and a maintenance loop EMERGE from
the coupled local dynamics on a SEEDED vessel (the phi bump is placed; the loop is measured, not
placed) -- a Gate II *candidate* for the Vertical Emergence Contract (docs/VERTICAL_EMERGENCE_CONTRACT.md).

HONESTY / target-encoding guards carried over from the F0 review (Codex, 2026-07-17)
- Selectivity is NOT placed: diffusion is one shared D(phi); species separate only through the
  free-energy partition coefficients chi_i (emergent partition). A chi_i=const control kills it.
- Reaction is NOT placed at the interface: R is spatially uniform (R=const); any concentration of
  reaction near the interface is an EMERGENT consequence of partitioning, measured against a
  no-vessel (phi=const) control.
- Fuel enters only the OUTSIDE bulk (phi < -thresh), never injected in the interior, so the interior
  reaction requires fuel to permeate the selective boundary.
- The maintenance loop is a real term: m enters the interface physics via kappa(m); an alpha=0
  control (coupling off) is the matched control for its effect.

WHAT IT IS NOT
- NOT a self-formed vessel (S1 seeds phi; emergence of the vessel ITSELF is E2/E3, later stages).
- NOT hydrodynamic yet (u=0 for S1; Stokes flow enters at a later stage).
- NOT a life/cell/metabolism claim -- at most a "self-maintaining chemically-selective vessel
  candidate" direction (Vertical Emergence Contract prohibited-claims discipline).

Periodic boundaries (a droplet in a periodic box); finite-volume fluxes conserve phi mass exactly
and species mass up to the explicit fuel-in/waste-out source terms (audited by the tests).
no_touch: additive model module; does not modify measures.py or any official Room.
"""
import numpy as np

from genesis.diagnostics.vessel_permeability import _bernoulli


def radial_phi_bump(shape, radius, width, center=None):
    """Seeded vessel: a tanh spherical phi bump (+1 inside, -1 outside) on a periodic grid."""
    if center is None:
        center = tuple((s - 1) / 2.0 for s in shape)
    grids = np.meshgrid(*[np.arange(s, dtype=float) for s in shape], indexing="ij")
    r = np.sqrt(sum((g - c) ** 2 for g, c in zip(grids, center)))
    return np.tanh((radius - r) / width)


def _laplacian(u):
    return sum(np.roll(u, 1, ax) + np.roll(u, -1, ax) for ax in range(u.ndim)) - 2 * u.ndim * u


def _div_kappa_grad(phi, kappa):
    """Finite-volume  div( kappa grad phi )  with periodic BC and a symmetric FACE average of the
    (spatial) stiffness kappa(m). Face-shared with opposite sign -> conserves the phi 'charge'."""
    out = np.zeros_like(phi)
    for ax in range(phi.ndim):
        pp = np.roll(phi, -1, ax)
        pm = np.roll(phi, 1, ax)
        kp = 0.5 * (kappa + np.roll(kappa, -1, ax))   # face i|i+1
        km = 0.5 * (kappa + np.roll(kappa, 1, ax))    # face i-1|i
        out += kp * (pp - phi) - km * (phi - pm)
    return out


def _species_div_flux(c, phi, chi, D):
    """d_t c contribution from  -div J,  J = -D (grad c + chi c grad phi), via the Scharfetter-
    Gummel (Boltzmann-balanced) face flux with a face-averaged mobility D(phi), periodic BC.
    Reuses the exact-partition flux validated in F1 V0 -- so the dynamic solver's transport carries
    the same certified equilibrium (c ∝ exp(-chi phi)) the validator established."""
    out = np.zeros_like(c)
    for ax in range(c.ndim):
        cp = np.roll(c, -1, ax)
        pp = np.roll(phi, -1, ax)
        dpsi = chi * (pp - phi)
        D_face = D if np.ndim(D) == 0 else 0.5 * (D + np.roll(D, -1, ax))
        J = D_face * (_bernoulli(dpsi) * c - _bernoulli(-dpsi) * cp)   # flux across face i|i+1
        Jm = np.roll(J, 1, ax)                                          # flux across face i-1|i
        out += (Jm - J)                                                # d_t c = J_{i-1} - J_i
    return out


def default_params():
    """Frozen S1 parameters (pre-registered scale; overridable per run, recorded in provenance)."""
    return dict(
        a=1.0, kappa0=1.0, alpha=0.6, M_phi=1.0,     # phi: Model B + kappa(m)=kappa0(1-alpha*m_norm)
        D0=1.0, D_ratio=1.0,                          # single shared mobility D(phi) (ratio!=1 -> D(phi))
        chi_f=-0.5, chi_m=0.0, chi_w=0.0,            # f prefers the interior (chi<0): fuel supplied
        #                                              only outside must permeate IN and concentrate
        #                                              -- selectivity from chi alone; m,w neutral
        k1=0.4, k2=0.15, k_out=0.1,                  # f ->(k1) m ->(k2) w ->(k_out, outside) removed
        f_res=1.0, k_res=0.3,                          # outside-bulk fuel reservoir exchange
        dt=0.05, out_thresh=0.5,
    )


def D_of_phi(phi, p):
    """Single shared mobility, optionally phi-dependent (same function for ALL species -- selectivity
    is never encoded here; it lives in chi_i). D_ratio=1 -> constant D0."""
    if p["D_ratio"] == 1.0:
        return p["D0"]
    inside = 0.5 * (1.0 + phi)                        # ~1 inside, ~0 outside
    return p["D0"] * (1.0 + (p["D_ratio"] - 1.0) * inside)


def step(state, p, fuel_on=True):
    """One explicit step of the coupled (phi, f, m, w) dynamics at u=0. Returns a new state dict."""
    phi, f, m, w = state["phi"], state["f"], state["m"], state["w"]
    D = D_of_phi(phi, p)
    # maintenance coupling: reaction product m softens the interface stiffness kappa(m).
    m_norm = np.clip(m / (1.0 + m), 0.0, 1.0)
    kappa = p["kappa0"] * (1.0 - p["alpha"] * m_norm)
    # phi: CONSERVED Allen-Cahn (nonlocal Lagrange-multiplier form). The variational derivative
    # dF/dphi = a phi(phi^2-1) - div(kappa(m) grad phi) + sum chi_i c_i drives phase separation; the
    # 2nd-order (not 4th-order) relaxation d_t phi = -M (dF/dphi - <dF/dphi>) is numerically robust
    # (unlike explicit Cahn-Hilliard, which is biharmonic-stiff and blows up here) while the mean
    # subtraction makes d/dt integral(phi) = 0 EXACTLY, so phi mass is conserved like Model B/H.
    dFdphi = p["a"] * phi * (phi ** 2 - 1.0) - _div_kappa_grad(phi, kappa) \
        + p["chi_f"] * f + p["chi_m"] * m + p["chi_w"] * w
    phi_new = phi - p["dt"] * p["M_phi"] * (dFdphi - float(dFdphi.mean()))
    # chemistry: single shared D(phi); reaction R=const (NOT placed at interface); fuel only outside.
    outside = phi < -p["out_thresh"]
    J_fuel = p["k_res"] * (p["f_res"] - f) * outside if fuel_on else 0.0
    react1 = p["k1"] * f                                        # f -> m  (R=const: rate = k1*f everywhere)
    react2 = p["k2"] * m                                        # m -> w
    f_new = f + p["dt"] * (_species_div_flux(f, phi, p["chi_f"], D) + J_fuel - react1)
    m_new = m + p["dt"] * (_species_div_flux(m, phi, p["chi_m"], D) + react1 - react2)
    w_new = w + p["dt"] * (_species_div_flux(w, phi, p["chi_w"], D) + react2 - p["k_out"] * w * outside)
    return dict(phi=phi_new, f=np.maximum(f_new, 0.0), m=np.maximum(m_new, 0.0), w=np.maximum(w_new, 0.0))


def run(shape=(32, 32, 32), radius=8.0, width=1.5, n_steps=2000, params=None, fuel_on=True, seed_c=0.0):
    """S1 run: seed a phi bump (vessel), start chemistry at seed_c, evolve, return final state + history."""
    p = default_params()
    if params:
        p.update(params)
    phi = radial_phi_bump(shape, radius, width)
    state = dict(phi=phi, f=np.full(shape, float(seed_c)), m=np.full(shape, float(seed_c)),
                 w=np.full(shape, float(seed_c)))
    hist = []
    for t in range(int(n_steps)):
        state = step(state, p, fuel_on=fuel_on)
        if t % max(1, n_steps // 20) == 0:
            hist.append(dict(t=t, phi_mass=float(state["phi"].sum()),
                             interface_width=interface_width(state["phi"]),
                             reaction_conc_ratio=reaction_concentration_ratio(state, p)))
    return dict(state=state, params=p, history=hist)


# ------------------------------- measurement helpers (role V) -------------------------------

def partition_ratio(c, phi, thresh=0.5):
    """Inside/outside mean-concentration ratio (selective boundary readout, as in F1 V0)."""
    inside, outside = phi > thresh, phi < -thresh
    return float(c[inside].mean() / c[outside].mean())


def interface_width(phi, thresh=0.9):
    """Fraction of cells in the diffuse interface band |phi|<thresh -- a proxy for vessel sharpness/
    integrity; the maintenance coupling is expected to move this measurably (alpha ON vs OFF)."""
    return float(np.mean(np.abs(phi) < thresh))


def vessel_volume(phi, thresh=0.0):
    """Interior volume fraction (phi>thresh) -- vessel size / integrity over time."""
    return float(np.mean(phi > thresh))


def reaction_concentration_ratio(state, p, thresh=0.5):
    """Ratio of mean local reaction rate (k1*f) in the interface band to the outside bulk. >1 means
    reaction concentrates at the vessel -- an EMERGENT effect of partitioning (R itself is uniform)."""
    phi, f = state["phi"], state["f"]
    band = np.abs(phi) < thresh                       # interface band
    outside = phi < -thresh
    r = p["k1"] * f
    ob = r[outside].mean()
    return float(r[band].mean() / ob) if ob > 1e-12 else float("nan")
