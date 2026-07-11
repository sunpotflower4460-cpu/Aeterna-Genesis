#!/usr/bin/env python3
"""G002 3D frontier solver: 3D free-slip walled Rayleigh-Bénard, fully spectral with 3/2 dealiasing.

**STATUS: EXPERIMENTAL / FRONTIER — not wired to any official Room.** The official G002 Room
(rooms/official/room-g002-a) is the validated 2D convection (genesis/models/boussinesq_rb.py). This
module is the honest, reproducible record of the attempted 3D promotion (docs/DIMENSION_POLICY.md):
2D success is NOT auto-extrapolated to 3D; the 3D DNS must stand on its own, and here it does not yet.

What is VERIFIED (see tests/test_boussinesq_rb_3d.py):
  * The spectral machinery is exact: the 3/2 zero-padded transforms round-trip to ~1e-14, so the
    nonlinear products are truly dealiased (this fixed the earlier aliasing that made the naive 2/3
    scheme blow up even harder). Free-slip walls give exact sine/cosine z-bases; pressure is removed by
    an exact per-mode spectral projection; diffusion is integrated exactly (integrating factor).
  * SUBCRITICAL is correct and bounded: at Ra < Ra_c = 27*pi^4/4 the quiescent state is stable, the
    noise decays, and Nu -> 1 (pure conduction). Confirmed at Ra=300, N=16: Nu=1.0000, bounded.

What is NOT yet achieved (the frontier):
  * SUPERCRITICAL convection blows up at the resolutions affordable here. The blow-up time is
    resolution/Ra-controlled (Ra=1000,N=16 -> t~2.3; Ra=800,N=20 -> t~5.2) and dt-INDEPENDENT
    (cfl 0.4 vs 0.12 blow up at the same physical time), i.e. it is genuine UNDER-RESOLUTION, not
    aliasing (already removed) nor a CFL error. A bounded, grid-converged 3D DNS at Ra a few times
    critical needs N >= ~32-40 (and likely a more robust, e.g. semi-implicit-advection, integrator).
    That is a compute/R&D step, not a bug -- left here, reproducible, for a higher-resolution run.

Formulation (free-slip walls, z in [0,1]): w,theta ~ sin(m pi z); u,v,p ~ cos(n pi z); x,y periodic.
"""

import numpy as np

MODEL_ID = "g002_boussinesq_convection_3d"      # same physics as g002; 3D, experimental
RA_C = 27.0 * np.pi ** 4 / 4.0
KC = np.pi / np.sqrt(2.0)
STATUS = "experimental"                         # NOT an official-Room solver


class RB3D:
    """3D free-slip walled Rayleigh-Bénard, fully spectral with exact 3/2 dealiasing."""

    def __init__(self, Nx, Nz, Ra, Pr=1.0, seed=0, Lx=None, noise_amplitude=1e-3):
        self.Nx, self.Nz, self.Ra, self.Pr = Nx, Nz, float(Ra), float(Pr)
        self.Lx = float(Lx) if Lx is not None else 2 * np.pi / KC
        self.Ly = self.Lx
        kx = np.fft.fftfreq(Nx, d=self.Lx / Nx) * 2 * np.pi
        KX, KY = np.meshgrid(kx, kx, indexing="ij")
        self.KX = KX[:, :, None]; self.KY = KY[:, :, None]
        self.Kh2 = self.KX ** 2 + self.KY ** 2
        self.kxmax = np.pi * Nx / self.Lx                 # spectral max wavenumber (for CFL)
        ms = np.arange(1, Nz + 1); nc = np.arange(0, Nz)
        zc = (np.arange(Nz) + 0.5) / Nz
        self.Ssyn = np.sin(np.pi * np.outer(zc, ms)); self.Csyn = np.cos(np.pi * np.outer(zc, nc))
        self.Sana = np.linalg.inv(self.Ssyn); self.Cana = np.linalg.inv(self.Csyn)
        self.Dsin = (ms * np.pi) * np.cos(np.pi * np.outer(zc, ms))
        self.Dcos = (-nc * np.pi) * np.sin(np.pi * np.outer(zc, nc))
        Pz = int(np.ceil(1.5 * Nz)); self.Pz = Pz
        zf = (np.arange(Pz) + 0.5) / Pz
        self.Ssyn_f = np.sin(np.pi * np.outer(zf, ms)); self.Csyn_f = np.cos(np.pi * np.outer(zf, nc))
        self.Sana_f = (2.0 / Pz) * self.Ssyn_f.T
        cn = np.ones(Nz); cn[0] = 0.5; self.Cana_f = (2.0 / Pz) * (cn[:, None] * self.Csyn_f.T)
        self.mpi = (ms * np.pi)[None, None, :]; self.npi = (nc * np.pi)[None, None, :]
        self.Ksin2 = self.Kh2 + self.mpi ** 2; self.Kcos2 = self.Kh2 + self.npi ** 2
        self.Nf = (3 * Nx) // 2; self._h = Nx // 2
        rng = np.random.default_rng(seed)
        self.th = self._killny(self._fwd_s(noise_amplitude * rng.standard_normal((Nx, Nx, Nz))))
        self.w = np.zeros_like(self.th)
        self.u = np.zeros((Nx, Nx, Nz), complex); self.v = np.zeros((Nx, Nx, Nz), complex)

    def _killny(self, C):
        # zero the unresolved Nyquist row/col so the real-field 3/2 pad is an exact identity
        C[self._h, :, :] = 0.0; C[:, self._h, :] = 0.0
        return C

    # ---- coarse transforms ----
    def _fwd_s(self, g): return np.einsum("xyz,jz->xyj", np.fft.fft2(g, axes=(0, 1)), self.Sana)
    def _fwd_c(self, g): return np.einsum("xyz,jz->xyj", np.fft.fft2(g, axes=(0, 1)), self.Cana)
    def _grid_s(self, C): return np.fft.ifft2(np.einsum("xyz,jz->xyj", C, self.Ssyn), axes=(0, 1)).real
    def _grid_c(self, C): return np.fft.ifft2(np.einsum("xyz,jz->xyj", C, self.Csyn), axes=(0, 1)).real
    def _dz_s(self, C): return np.fft.ifft2(np.einsum("xyz,jz->xyj", C, self.Dsin), axes=(0, 1)).real
    def _dz_c(self, C): return np.fft.ifft2(np.einsum("xyz,jz->xyj", C, self.Dcos), axes=(0, 1)).real

    # ---- 3/2 dealiased fine-grid helpers ----
    def _pad_h(self, F):
        Nx, Nf = self.Nx, self.Nf
        Fs = np.fft.fftshift(F, axes=(0, 1))
        G = np.zeros((Nf, Nf) + F.shape[2:], complex)
        lo = (Nf - Nx) // 2; G[lo:lo + Nx, lo:lo + Nx] = Fs
        return np.fft.ifftshift(G, axes=(0, 1)) * ((Nf / Nx) ** 2)
    def _unpad_h(self, G):
        Nx, Nf = self.Nx, self.Nf
        Gs = np.fft.fftshift(G, axes=(0, 1)); lo = (Nf - Nx) // 2
        return np.fft.ifftshift(Gs[lo:lo + Nx, lo:lo + Nx], axes=(0, 1)) * ((Nx / Nf) ** 2)
    def _to_fine(self, C, basis):
        syn = self.Ssyn_f if basis == "s" else self.Csyn_f
        return np.fft.ifft2(self._pad_h(np.einsum("xyz,jz->xyj", C, syn)), axes=(0, 1)).real
    def _from_fine_s(self, phys):
        return np.einsum("xyz,jz->xyj", self._unpad_h(np.fft.fft2(phys, axes=(0, 1))), self.Sana_f)
    def _from_fine_c(self, phys):
        return np.einsum("xyz,jz->xyj", self._unpad_h(np.fft.fft2(phys, axes=(0, 1))), self.Cana_f)
    def _dx_fine(self, C, basis): return self._to_fine(1j * self.KX * C, basis)
    def _dy_fine(self, C, basis): return self._to_fine(1j * self.KY * C, basis)
    def _dz_fine_s(self, C):
        return np.fft.ifft2(self._pad_h(np.einsum("xyz,jz->xyj", C * self.mpi, self.Csyn_f)), axes=(0, 1)).real
    def _dz_fine_c(self, C):
        return np.fft.ifft2(self._pad_h(np.einsum("xyz,jz->xyj", -C * self.npi, self.Ssyn_f)), axes=(0, 1)).real

    def project(self):
        wz = self._fwd_c(self._dz_s(self.w))
        div = 1j * self.KX * self.u + 1j * self.KY * self.v + wz
        K2 = self.Kcos2.copy(); K2[0, 0, 0] = 1.0
        phi = -div / K2
        self.u = self.u - 1j * self.KX * phi; self.v = self.v - 1j * self.KY * phi
        self.w = self.w - self._fwd_s(self._dz_c(phi))

    def rhs(self):
        uf = self._to_fine(self.u, "c"); vf = self._to_fine(self.v, "c"); wf = self._to_fine(self.w, "s")
        ux = self._dx_fine(self.u, "c"); uy = self._dy_fine(self.u, "c"); uz = self._dz_fine_c(self.u)
        vx = self._dx_fine(self.v, "c"); vy = self._dy_fine(self.v, "c"); vz = self._dz_fine_c(self.v)
        wx = self._dx_fine(self.w, "s"); wy = self._dy_fine(self.w, "s"); wz = self._dz_fine_s(self.w)
        tx = self._dx_fine(self.th, "s"); ty = self._dy_fine(self.th, "s"); tz = self._dz_fine_s(self.th)
        Au = self._from_fine_c(uf * ux + vf * uy + wf * uz); Av = self._from_fine_c(uf * vx + vf * vy + wf * vz)
        Aw = self._from_fine_s(uf * wx + vf * wy + wf * wz); At = self._from_fine_s(uf * tx + vf * ty + wf * tz)
        return -Au, -Av, -Aw + self.Pr * self.Ra * self.th, -At + self.w

    @staticmethod
    def _EP(L, dt):
        Ldt = L * dt
        p = np.where(np.abs(Ldt) < 1e-12, dt, np.expm1(Ldt) / np.where(L == 0, 1.0, L))
        return np.exp(Ldt), p

    def step(self, dt):
        Eu, pu = self._EP(-self.Pr * self.Kcos2, dt)
        Ew, pw = self._EP(-self.Pr * self.Ksin2, dt)
        Et, pt = self._EP(-self.Ksin2, dt)
        Ru, Rv, Rw, Rt = self.rhs()
        self.u = Eu * self.u + pu * Ru; self.v = Eu * self.v + pu * Rv
        self.w = Ew * self.w + pw * Rw; self.th = Et * self.th + pt * Rt
        self.project()
        for A in (self.u, self.v, self.w, self.th):
            self._killny(A)

    def velocity(self):
        return self._grid_c(self.u), self._grid_c(self.v), self._grid_s(self.w)
    def cfl_dt(self, cfl=0.4, cap=2e-3):
        # spectral CFL: use the MAX WAVENUMBER (pi/dx), not the grid spacing 1/dx
        u, v, w = self.velocity()
        s = (np.max(np.abs(u)) + np.max(np.abs(v))) * self.kxmax + np.max(np.abs(w)) * (np.pi * self.Nz)
        return min(cap, cfl / (s + 1e-12))
    def nusselt_flux(self):
        _, _, w = self.velocity(); return 1.0 + float(np.mean(w * self._grid_s(self.th)))
    def kinetic_energy(self):
        u, v, w = self.velocity(); return 0.5 * float(np.mean(u * u + v * v + w * w))
    def finite(self):
        return bool(np.isfinite(self.w).all() and np.isfinite(self.th).all())

    def transform_roundtrip_error(self, seed=0):
        """Self-test: the dealiased fine<->coarse transforms must round-trip to ~machine precision
        (this is what makes the nonlinear products truly dealiased)."""
        rng = np.random.default_rng(seed)
        Cs = self._killny(self._fwd_s(rng.standard_normal((self.Nx, self.Nx, self.Nz))))
        Cc = self._killny(self._fwd_c(rng.standard_normal((self.Nx, self.Nx, self.Nz))))
        es = np.max(np.abs(self._from_fine_s(self._to_fine(Cs, "s")) - Cs))
        ec = np.max(np.abs(self._from_fine_c(self._to_fine(Cc, "c")) - Cc))
        return float(max(es, ec))


def run_subcritical_check(Ra, Nx, Nz, t_end, seed=0, cfl=0.3, max_steps=8000):
    """Integrate a SUBCRITICAL case to t_end; return Nu (should -> 1) and boundedness. This is the
    regime this experimental solver is verified in."""
    s = RB3D(Nx, Nz, Ra, seed=seed)
    t = 0.0; n = 0
    while t < t_end and n < max_steps:
        dt = s.cfl_dt(cfl=cfl); s.step(dt); t += dt; n += 1
        if not s.finite():
            return {"finite": False, "nsteps": n}
    return {"finite": True, "nsteps": n, "nusselt_flux": s.nusselt_flux(),
            "kinetic_energy": s.kinetic_energy()}


if __name__ == "__main__":
    import time
    s = RB3D(16, 16, 300.0)
    print("transform roundtrip error: %.2e (must be ~1e-13)" % s.transform_roundtrip_error())
    t0 = time.time()
    r = run_subcritical_check(300.0, 16, 16, t_end=6.0)
    print("subcritical Ra=300: finite=%s Nu=%.4f KE=%.2e (%.0fs)"
          % (r["finite"], r.get("nusselt_flux", float("nan")), r.get("kinetic_energy", float("nan")),
             time.time() - t0))
