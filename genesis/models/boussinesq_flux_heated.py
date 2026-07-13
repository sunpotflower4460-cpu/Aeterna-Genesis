#!/usr/bin/env python3
"""G002-C3: FLUX-HEATED Boussinesq convection -- the temperature GRADIENT is GENERATED from an absorbed
energy flux, NOT imposed as a fixed temperature difference (docs/CAUSAL_CLOSURE.md).

The parent official Room room-g002-a imposes a fixed ΔT at the walls (a base profile T_base = 1 - z): the
temperature gradient is an **environmental condition** placed at t=0 (causal-closure C1). Here we do NOT
impose a gradient. We start the temperature UNIFORM + tiny noise (`quiescent_plus_noise`, no ΔT) and apply
an **absorbed-flux volumetric heating** S(z) (both walls held cold). The temperature gradient then DEVELOPS
self-consistently from the flux vs conduction balance, and -- once the developed profile is supercritical --
convection emerges from rest. So the **gradient is an Emerged State (generated)**, and the imposed
environment is now the **energy flux** (claim_excludes: spontaneous_energy_flux). That is the C-level step:
the gradient moves from imposed (C1) to generated (C3-toward). The flux itself is still imposed
(flux-from-an-upstream-Room = frontier).

Reuses the VALIDATED free-slip spectral machinery of boussinesq_rb.Bouss (both walls cold -> the temperature
lives in the same sine basis, so vertical diffusion is integrated EXACTLY -- no explicit-diffusion CFL NaN).
Nothing about rolls / wavelength / flow direction is put in.

    d_t omega + (u.grad) omega = Pr lap(omega) + Pr Ra d(T)/dx
    d_t T     + (u.grad) T     = lap(T) + S(z)            (S = absorbed-flux heating; T=0 at both walls)
    lap(psi) = -omega ,  u = psi_z ,  w = -psi_x

「同じ数学 != 同じもの」: this is generated convection in a fluid, not life. spots≠life. tier=measured for
the gradient-development + convection; the flux remains an imposed environment (honestly labelled).
"""

import numpy as np

from genesis.models.boussinesq_rb import Bouss

MODEL_ID = "g002c3_boussinesq_flux_heated"

# Robust supercritical, statistically steady, finite (validated in-repo). absorption=0 -> uniform internal
# heating; absorption>0 -> flux absorbed more strongly near the bottom (Beer-Lambert, ground-absorbed light).
DEFAULTS = {"Pr": 1.0, "Ra": 2000.0, "Q": 20.0, "absorption": 0.0,
            "noise_amplitude": 1.0e-3, "cfl": 0.4, "dt_cap": 1.0e-3}


class FluxHeatedBouss(Bouss):
    """Boussinesq with an absorbed-flux heating source and NO imposed temperature gradient (both walls cold).
    self.th is reinterpreted as the FULL temperature T (starts as noise only)."""

    def __init__(self, Nx, Nz, Ra, Q, absorption=0.0, Pr=1.0, seed=0, noise_amplitude=1.0e-3):
        super().__init__(Nx, Nz, Ra, Pr=Pr, seed=seed, noise_amplitude=noise_amplitude)
        z = self.z                                                # interior nodes in (0,1)
        prof = np.ones_like(z) if absorption <= 0 else np.exp(-absorption * z)   # absorbed near bottom z~0
        prof = prof / np.mean(prof)                               # normalise so mean(S) = Q
        self.Shat = self.fwd(np.broadcast_to(Q * prof[None, :], (self.Nx, self.M))) * self.mask
        self.Q = float(Q)

    def step(self, dt):
        psih = self.om / self.K2
        u = self.bwd_cos(psih * self.NP); w = -self.bwd(1j * self.KX * psih)
        om_x = self.bwd(1j * self.KX * self.om); om_z = self.bwd_cos(self.om * self.NP)
        th_x = self.bwd(1j * self.KX * self.th); th_z = self.bwd_cos(self.th * self.NP)
        Nom = -self.fwd(u * om_x + w * om_z) * self.mask + self.Pr * self.Ra * (1j * self.KX * self.th)
        Nth = -self.fwd(u * th_x + w * th_z) * self.mask + self.Shat        # heating source (not the +w base)
        Lom = -self.Pr * self.K2; Lth = -self.K2
        Eom = np.exp(Lom * dt); Eth = np.exp(Lth * dt)
        pom = np.expm1(Lom * dt) / Lom; pth = np.expm1(Lth * dt) / Lth
        self.om = Eom * self.om + pom * Nom
        self.th = Eth * self.th + pth * Nth

    def vertical_gradient_rms(self):
        """RMS of dT/dz -- ~noise at t=0 (uniform), grows as the flux builds the gradient."""
        return float(np.sqrt(np.mean(self.bwd_cos(self.th * self.NP) ** 2)))

    def nusselt_flux(self):
        _, w = self.velocity()
        return 1.0 + float(np.mean(w * self.bwd(self.th)))


def run_flux_heated(Ra=None, Q=None, absorption=None, Nx=48, Nz=49, t_end=6.0, seed=0, p=None):
    """From a UNIFORM+noise temperature (NO imposed gradient), run to a statistically steady state. Returns
    the gradient DEVELOPMENT (g_start ~ noise -> g_final) and whether convection EMERGED from rest."""
    p = dict(DEFAULTS if p is None else p)
    Ra = p["Ra"] if Ra is None else Ra
    Q = p["Q"] if Q is None else Q
    absorption = p["absorption"] if absorption is None else absorption
    s = FluxHeatedBouss(Nx, Nz, Ra, Q, absorption=absorption, Pr=p["Pr"], seed=seed,
                        noise_amplitude=p["noise_amplitude"])
    g0 = s.vertical_gradient_rms(); ke0 = s.kinetic_energy()
    t = 0.0; nsteps = 0
    while t < t_end:
        u, w = s.velocity()
        dt = min(p["dt_cap"], p["cfl"] / (np.max(np.abs(u)) / (s.Lx / s.Nx)
                                          + np.max(np.abs(w)) * (s.M + 1) + 1e-12))
        s.step(dt); t += dt; nsteps += 1
        if not s.finite() or nsteps > 60000:
            return {"finite": s.finite(), "converged": False, "nsteps": nsteps}
    return {"finite": True, "converged": True, "nsteps": nsteps,
            "gradient_start": g0, "gradient_final": s.vertical_gradient_rms(),
            "ke_start": ke0, "ke_final": s.kinetic_energy(), "nusselt": s.nusselt_flux(),
            "gradient_generated": bool(s.vertical_gradient_rms() > 20.0 * max(g0, 1e-6)),
            "convection_from_rest": bool(ke0 < 1e-6 and s.kinetic_energy() > 1.0 and s.nusselt_flux() > 1.02)}
