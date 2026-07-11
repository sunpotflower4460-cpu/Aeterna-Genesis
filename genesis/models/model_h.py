#!/usr/bin/env python3
"""Genesis model G003: Model H — phase separation + fluid co-evolution (2D, bi-periodic, spectral).

Faithful field law (put in): ONE order-parameter field phi (composition) and ONE incompressible
velocity field u, both driven by the SAME free energy F[phi] = ∫ (-phi^2/2 + phi^4/4 + (kappa/2)|grad phi|^2).
The chemical potential mu = dF/dphi = -phi + phi^3 - kappa*lap(phi) both relaxes phi (Cahn-Hilliard) and,
through the Korteweg capillary stress, drives the flow (Navier-Stokes); the flow in turn advects phi:

    d_t phi + (u.grad) phi = M * lap(mu)                         (Cahn-Hilliard, conserves mass)
    d_t omega + (u.grad) omega = nu * lap(omega) + curl(-phi grad mu)_z   (vorticity form of Navier-Stokes)
    lap(psi) = -omega ,  u = d(psi)/dy ,  v = -d(psi)/dx        (incompressible, pressure eliminated)

NO domains, interfaces, droplets, or a length scale are put in -- only the field law and a UNIFORM
mixture + tiny noise. The uniform state is spinodally unstable: composition spontaneously separates
into domains (Level 1), sharp interfaces localize (Level 2), and capillary forces at those interfaces
generate a flow that advects and coarsens the pattern -- boundary, interface, flow and transport all
emerge from the SAME field and free energy, not bolted-together modules (the Model H point).

Why this is BOUNDED: Model H is RELAXATIONAL -- the free energy is a Lyapunov functional and decreases
(diffusive + viscous dissipation), unlike driven Rayleigh-Bénard which needs walls. Bi-periodic is fine.
Numerics: pseudospectral (FFT). The stiff 4th-order Cahn-Hilliard term is treated implicitly
(unconditionally stable); viscosity by exact integrating factor; advection explicit; 2/3 dealiasing.
Mass (integral of phi) is conserved to machine precision by the flux form.
"""

import numpy as np

MODEL_ID = "g003_model_h_phase_field"

DEFAULTS = {"kappa": 1.0, "M": 1.0, "nu": 1.0, "coupling": 1.0, "dt": 0.04,
            "noise_amplitude": 0.05, "mean_phi": 0.0, "L": 128.0}


class ModelH:
    """2D bi-periodic Model H: Cahn-Hilliard phi coupled to vorticity-streamfunction Navier-Stokes."""

    def __init__(self, N, kappa=1.0, M=1.0, nu=1.0, coupling=1.0, seed=0,
                 noise_amplitude=0.05, mean_phi=0.0, L=128.0):
        self.N, self.L = N, float(L)
        self.kappa, self.M, self.nu, self.C = kappa, M, nu, coupling
        k = np.fft.fftfreq(N, d=self.L / N) * 2 * np.pi
        KX, KY = np.meshgrid(k, k, indexing="ij")
        self.KX, self.KY = KX, KY
        self.K2 = KX ** 2 + KY ** 2
        self.K2inv = np.where(self.K2 == 0, 1.0, self.K2)           # safe divide (k=0 handled separately)
        kmax = np.abs(k).max()
        self.mask = (np.abs(KX) < (2.0 / 3.0) * kmax) & (np.abs(KY) < (2.0 / 3.0) * kmax)
        rng = np.random.default_rng(seed)
        phi0 = mean_phi + noise_amplitude * rng.standard_normal((N, N))
        self.phih = np.fft.fft2(phi0)
        self.omh = np.zeros((N, N), complex)                        # start at rest
        self.mean_phi0 = float(phi0.mean())

    # ---- spectral helpers ----
    def _ir(self, F):
        return np.real(np.fft.ifft2(F))
    def velocity(self):
        psih = self.omh / self.K2inv
        psih = np.where(self.K2 == 0, 0.0, self.omh / self.K2inv)
        u = self._ir(1j * self.KY * psih)                           #  d psi / dy
        v = self._ir(-1j * self.KX * psih)                          # -d psi / dx
        return u, v
    def phi(self):
        return self._ir(self.phih)
    def mu_hat(self):
        phi = self._ir(self.phih)
        phi3 = np.fft.fft2(phi ** 3)
        return -self.phih + phi3 + self.kappa * self.K2 * self.phih  # mu = -phi + phi^3 - kappa lap phi

    def step(self, dt):
        phi = self._ir(self.phih)
        u, v = self.velocity()
        # --- gradients ---
        phix = self._ir(1j * self.KX * self.phih); phiy = self._ir(1j * self.KY * self.phih)
        muh = self.mu_hat()
        mux = self._ir(1j * self.KX * muh); muy = self._ir(1j * self.KY * muh)
        omx = self._ir(1j * self.KX * self.omh); omy = self._ir(1j * self.KY * self.omh)
        # --- Cahn-Hilliard: implicit 4th-order term, explicit rest + advection ---
        phi3h = np.fft.fft2(phi ** 3)
        adv_phi = np.fft.fft2(u * phix + v * phiy) * self.mask
        expl = self.M * self.K2 * self.phih - self.M * self.K2 * phi3h - adv_phi
        self.phih = (self.phih + dt * expl) / (1.0 + dt * self.M * self.kappa * self.K2 ** 2)
        # --- vorticity: capillary source + advection, viscosity by integrating factor ---
        source = self.C * (phiy * mux - phix * muy)                 # curl(-phi grad mu)_z
        adv_om = u * omx + v * omy
        Nom = np.fft.fft2(source - adv_om) * self.mask
        E = np.exp(-self.nu * self.K2 * dt)
        phi1 = np.where(self.K2 == 0, dt, np.expm1(-self.nu * self.K2 * dt) / (-self.nu * self.K2inv))
        self.omh = E * self.omh + phi1 * Nom

    # ---- diagnostics ----
    def mass(self):
        return float(np.real(self.phih[0, 0]) / (self.N ** 2))      # spatial mean of phi (conserved)
    def free_energy(self):
        phi = self._ir(self.phih)
        gx = self._ir(1j * self.KX * self.phih); gy = self._ir(1j * self.KY * self.phih)
        return float(np.mean(-0.5 * phi ** 2 + 0.25 * phi ** 4 + 0.5 * self.kappa * (gx ** 2 + gy ** 2)))
    def kinetic_energy(self):
        u, v = self.velocity()
        return 0.5 * float(np.mean(u * u + v * v))
    def structure_scale(self):
        """Domain length L1 = 2*pi * <|phi_k|^2> / <k |phi_k|^2> (first moment of the structure factor).
        Grows as domains coarsen -> a measured order parameter for phase separation."""
        P = np.abs(self.phih) ** 2
        P[0, 0] = 0.0
        kmag = np.sqrt(self.K2)
        num = np.sum(P); den = np.sum(kmag * P)
        return float(2 * np.pi * num / den) if den > 0 else 0.0
    def phase_amplitude(self):
        """RMS composition contrast -- ~0 in the uniform state, saturates to the binodal after separation."""
        return float(np.std(self._ir(self.phih)))
    def interface_fraction(self, lo=-0.6, hi=0.6):
        """Fraction of cells that are interfacial (|phi| between the two wells) -> localized structure."""
        phi = self._ir(self.phih)
        return float(np.mean((phi > lo) & (phi < hi)))
    def finite(self):
        return bool(np.isfinite(self.phih).all() and np.isfinite(self.omh).all())
    def state_hash_arrays(self):
        return (np.ascontiguousarray(self.phih), np.ascontiguousarray(self.omh))


def run(N, steps, dt=None, seed=0, coupling=1.0, snapshots=0, **kw):
    """Evolve from a uniform + noise mixture; return the trajectory of measured quantities.
    NO intervention: fixed field law, no seeded pattern."""
    dt = DEFAULTS["dt"] if dt is None else dt
    s = ModelH(N, seed=seed, coupling=coupling, **kw)
    traj = []
    snap_every = max(1, steps // snapshots) if snapshots else steps + 1
    rec = lambda t: traj.append({"step": t, "scale": s.structure_scale(),
                                 "amp": s.phase_amplitude(), "F": s.free_energy(),
                                 "ke": s.kinetic_energy(), "mass": s.mass(),
                                 "interface": s.interface_fraction()})
    rec(0)
    for t in range(1, steps + 1):
        s.step(dt)
        if not s.finite():
            return {"finite": False, "traj": traj, "solver": s, "nsteps": t}
        if t % snap_every == 0 or t == steps:
            rec(t)
    return {"finite": True, "traj": traj, "solver": s, "nsteps": steps}


if __name__ == "__main__":
    import time
    for C in (0.0, 1.0):
        t0 = time.time()
        r = run(128, 1500, seed=0, coupling=C, snapshots=5)
        tr = r["traj"]
        tag = "no-flow (Cahn-Hilliard only)" if C == 0 else "Model H (coupled flow)"
        print("== %s ==" % tag)
        for row in tr:
            print("  step %4d: L1=%6.2f amp=%.3f F=%+.4f KE=%.2e interf=%.3f mass=%+.2e"
                  % (row["step"], row["scale"], row["amp"], row["F"], row["ke"],
                     row["interface"], row["mass"]))
        F = [row["F"] for row in tr]
        print("  finite=%s  F monotone-decreasing=%s  domain grew=%s  (%.1fs)"
              % (r["finite"], all(F[i] >= F[i + 1] - 1e-6 for i in range(len(F) - 1)),
                 tr[-1]["scale"] > tr[0]["scale"], time.time() - t0))
