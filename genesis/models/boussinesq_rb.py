#!/usr/bin/env python3
"""Genesis model G002: walled Rayleigh-Bénard convection (Boussinesq), fully spectral (2D).

Faithful field law (put in): incompressible Boussinesq flow in a fluid layer heated from below,
between two horizontal WALLS (free-slip), periodic in the horizontal, in the vorticity-streamfunction
formulation (pressure eliminated, incompressibility exact). Base conduction profile T_base = 1 - z.
Nondimensional units (length = layer depth, time = depth^2 / thermal diffusivity, temperature = imposed
difference):

    d_t omega + (u.grad) omega = Pr * lap(omega) + Pr * Ra * d(theta)/dx
    d_t theta + (u.grad) theta = lap(theta) + w
    lap(psi) = -omega ,  u = d(psi)/dz ,  w = -d(psi)/dx

NOTHING about convection rolls, their wavelength, or a flow direction is put in -- only the field law,
two walls, a fixed temperature difference (the environment), and a quiescent start with tiny noise.
Below Ra_c = 27*pi^4/4 ≈ 657.51 the noise decays (pure conduction, Nu -> 1); above it the layer
spontaneously breaks translational symmetry into steady convection cells (Nu > 1). A genuine
forward-in-time bifurcation, not a seeded pattern.

Why this is BOUNDED where a naive triperiodic DNS is not:
  * x: Fourier (periodic).  z: WALLS.
  * Free-slip walls give exact spectral bases: omega, theta, psi ~ sin(n*pi*z).  The vertical
    Laplacian is DIAGONAL, so diffusion is integrated EXACTLY (integrating factor) -- no
    explicit-diffusion CFL limit (the cause of the earlier NaNs in triperiodic attempts).
  * Vorticity-streamfunction enforces incompressibility exactly (no pressure, no elevator modes).
  * Only advection is explicit -> a mild CFL condition, handled adaptively; 2/3 dealiasing.

Dimension: 2D (x, z). The 3D promotion (walls in z, periodic x & y) is the audited next step
(docs/DIMENSION_POLICY.md): 2D is the validated screen, 3D is a separate promotion, not an
auto-extrapolation. The free-slip linear onset Ra_c and critical wavenumber are identical in 2D and 3D.
"""

import numpy as np

MODEL_ID = "g002_boussinesq_convection"

# free-slip linear onset (Rayleigh & classic): Ra_c = 27 pi^4 / 4 at k = pi/sqrt(2)
RA_C = 27.0 * np.pi ** 4 / 4.0            # ≈ 657.511
KC = np.pi / np.sqrt(2.0)

DEFAULTS = {"Pr": 1.0, "noise_amplitude": 1.0e-3, "cfl": 0.4, "dt_cap": 1.5e-3}


class Bouss:
    """Fully-spectral free-slip walled Rayleigh-Bénard (2D), vorticity-streamfunction."""

    def __init__(self, Nx, Nz, Ra, Pr=1.0, seed=0, Lx=None, noise_amplitude=1.0e-3):
        self.Nx, self.Nz, self.Ra, self.Pr = Nx, Nz, float(Ra), float(Pr)
        self.Lx = float(Lx) if Lx is not None else 2 * np.pi / KC     # one critical wavelength wide
        self.M = Nz - 1                                               # interior sine modes n=1..M
        j = np.arange(1, self.M + 1)
        n = np.arange(1, self.M + 1)
        self.x = np.arange(Nx) * self.Lx / Nx
        self.z = j / (self.M + 1)
        self.kx = np.fft.fftfreq(Nx, d=self.Lx / Nx) * 2 * np.pi
        self.S = np.sin(np.pi * np.outer(j, n) / (self.M + 1))       # sine synthesis (symmetric)
        self.C = np.cos(np.pi * np.outer(j, n) / (self.M + 1))       # cosine (for d/dz of sine)
        self.KX = self.kx[:, None]                                   # (Nx,1)
        self.NP = (n * np.pi)[None, :]                               # (1,M)
        self.K2 = self.KX ** 2 + self.NP ** 2                        # laplacian magnitude, > 0
        self.norm = 2.0 / (self.M + 1)
        keep_x = (np.abs(self.kx) < (2.0 / 3.0) * np.abs(self.kx).max() + 1e-12)[:, None]
        keep_n = (n < (2.0 / 3.0) * self.M)[None, :]
        self.mask = keep_x & keep_n
        rng = np.random.default_rng(seed)
        self.th = self.fwd(noise_amplitude * rng.standard_normal((Nx, self.M)))
        self.om = np.zeros_like(self.th)

    # ---- transforms between real grid (Nx, M) and spectral (kx, sine-n) ----
    def fwd(self, g):
        return (np.fft.fft(g, axis=0) @ self.S) * self.norm
    def bwd(self, Gh):
        return np.fft.ifft(Gh @ self.S, axis=0).real
    def bwd_cos(self, Gh):
        return np.fft.ifft(Gh @ self.C.T, axis=0).real

    # ---- velocity / fields on the grid ----
    def velocity(self):
        psih = self.om / self.K2
        u = self.bwd_cos(psih * self.NP)               # psi_z  (sin -> cos)
        w = -self.bwd(1j * self.KX * psih)             # -psi_x
        return u, w
    def fields(self):
        u, w = self.velocity()
        return u, None, w, self.bwd(self.th)           # (u, v=None, w, theta) -- v absent in 2D

    # ---- one integrating-factor (ETD1) step: exact diffusion, explicit advection + source ----
    def step(self, dt):
        psih = self.om / self.K2
        u = self.bwd_cos(psih * self.NP)
        w = -self.bwd(1j * self.KX * psih)
        om_x = self.bwd(1j * self.KX * self.om); om_z = self.bwd_cos(self.om * self.NP)
        th_x = self.bwd(1j * self.KX * self.th); th_z = self.bwd_cos(self.th * self.NP)
        Nom = -self.fwd(u * om_x + w * om_z) * self.mask + self.Pr * self.Ra * (1j * self.KX * self.th)
        Nth = -self.fwd(u * th_x + w * th_z) * self.mask + (-1j * self.KX * psih)   # +w = -psi_x
        Lom = -self.Pr * self.K2; Lth = -self.K2
        Eom = np.exp(Lom * dt); Eth = np.exp(Lth * dt)
        pom = np.expm1(Lom * dt) / Lom; pth = np.expm1(Lth * dt) / Lth
        self.om = Eom * self.om + pom * Nom
        self.th = Eth * self.th + pth * Nth

    def cfl_dt(self, cfl=0.4, cap=1.5e-3):
        u, w = self.velocity()
        s = np.max(np.abs(u)) / (self.Lx / self.Nx) + np.max(np.abs(w)) * (self.M + 1)
        return min(cap, cfl / (s + 1e-12))

    # ---- diagnostics ----
    def kinetic_energy(self):
        u, w = self.velocity()
        return 0.5 * float(np.mean(u * u + w * w))
    def nusselt_flux(self):
        """Nu from convective flux: Nu = 1 + <w theta> (volume average, nondim)."""
        _, w = self.velocity()
        return 1.0 + float(np.mean(w * self.bwd(self.th)))
    def nusselt_dissipation(self):
        """Nu from thermal dissipation: exact steady relation Nu = <|grad T_total|^2>, T = 1 - z + theta.
        Independent estimator -> agreement is a heat-conservation audit."""
        th_x = self.bwd(1j * self.KX * self.th)
        th_z = self.bwd_cos(self.th * self.NP)         # d theta / dz on the grid
        return float(np.mean(th_x ** 2 + (th_z - 1.0) ** 2))
    def finite(self):
        return bool(np.isfinite(self.om).all() and np.isfinite(self.th).all())
    def state_hash_arrays(self):
        return (np.ascontiguousarray(self.om), np.ascontiguousarray(self.th))


def run_to_steady(Ra, Nx, Nz, t_end=8.0, seed=0, sample=1.5, Pr=1.0,
                  noise_amplitude=1.0e-3, cfl=0.4, max_steps=40000):
    """Integrate from a quiescent + noise start to t_end; return time-averaged diagnostics over the
    last `sample` window (statistically steady). NO intervention: fixed walls + fixed Ra only."""
    s = Bouss(Nx, Nz, Ra, Pr=Pr, seed=seed, noise_amplitude=noise_amplitude)
    t = 0.0
    nsteps = 0
    nu_f, nu_d, ke = [], [], []
    while t < t_end:
        dt = s.cfl_dt(cfl=cfl, cap=DEFAULTS["dt_cap"])
        s.step(dt)
        t += dt
        nsteps += 1
        if not s.finite() or nsteps > max_steps:
            return {"Ra": Ra, "finite": s.finite(), "nsteps": nsteps, "converged": False}
        if t > t_end - sample:
            nu_f.append(s.nusselt_flux()); nu_d.append(s.nusselt_dissipation())
            ke.append(s.kinetic_energy())
    return {"Ra": Ra, "finite": True, "nsteps": nsteps, "converged": True,
            "nu_flux": float(np.mean(nu_f)), "nu_flux_std": float(np.std(nu_f)),
            "nu_diss": float(np.mean(nu_d)), "kinetic_energy": float(np.mean(ke)),
            "convecting": bool(np.mean(nu_f) > 1.02)}


if __name__ == "__main__":
    import time
    print("Ra_c = %.3f" % RA_C)
    for Ra in (300.0, 657.5, 1000.0, 2000.0, 5000.0):
        t0 = time.time(); r = run_to_steady(Ra, 48, 48, t_end=12.0)
        if r["converged"]:
            print("Ra=%7.1f: %4.1fs Nu_flux=%.4f Nu_diss=%.4f KE=%.3e convecting=%s"
                  % (Ra, time.time() - t0, r["nu_flux"], r["nu_diss"], r["kinetic_energy"],
                     r["convecting"]))
        else:
            print("Ra=%7.1f: not converged (finite=%s, steps=%d)" % (Ra, r["finite"], r["nsteps"]))
