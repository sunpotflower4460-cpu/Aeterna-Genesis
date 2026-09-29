"""A universe in which a symmetric field breaks and "differences are born" (P19). Only the universe's CONDITIONS are
put in -- the field content, the shape of the potential (how many ways the first difference can go), the light-like
gauge field, the outside (closed box / expanding) and Planck's constant ħ. What then happens is not aimed at.

A universe is a SPEC (a dict), from which the law is built:

    real fields    φ_r (r = 0..R-1),  H_r = ½π_r² + ½c_r² Σ_i(φ_r(x+î) − φ_r(x))²
    complex fields φ_a (a = 0..N-1),  H_a = |π_a|² + c_a² Σ_i|e^{-iθ_i(x)}φ_a(x+î) − φ_a(x)|²   (charge 1 under the
                   compact U(1) gauge field θ, E when e > 0; e = 0: no light-like field)
    gauge          (e²/2)ΣE² + (1/e²)Σ_{i<j}(1 − cos P_ij)            (as genesis/models/abelian_higgs_nd.py)
    potential      V = Σ of TERMS on invariants of the fields (see TERMS); the canonical invariant of a selection
                   of fields is  s = ½Σ φ_r² + Σ |φ_a|²  (the same normalisation for real and complex fields).

Presets (PRESETS) are ready-made specs for the ways the first difference can go:
    yinyang        one real field, (λ/4)(s − v²)²: two valleys ±        (陰陽)
    yinyang_middle one real field, λ s (s − v²)²: three valleys −, 0, +; the middle is a valley of its own (陰陽＋中庸)
    three_equal    one complex field, (λ/4)(s − v²)² − g Re(φ³)/v: three equal valleys 120° apart (3 つ対等)
    continuous     N complex fields, (λ/4)(s − v²)² (+ κ Σ|φ_a|⁴): a continuous circle/sphere of valleys
    cascade        a complex field A (large v1) and a real field B (small v2), coupled g·s_A·s_B: two scales
Every spec is checked: the potential must be bounded below, and a gauged field may only carry U(1)-invariant terms.

Dynamics: Hamiltonian, kick–drift–kick leapfrog, nearest neighbours only (no FFT, no global solve) -- every site
reacts only with its neighbours. Temporal gauge; Gauss's law Σ_i[E_i(x) − E_i(x−î)] = Σ_a 2 Im(φ_a*π_a) is kept.
Outside: closed box (energy conserved), or a radiation-era expanding universe in conformal time with a(τ) = 1 + Hτ:
the comoving fields χ = aφ obey χ'' = c²∇²χ − a³ V'(χ/a) (a'' = 0), the gauge field is conformal and unchanged.
The step size follows from the fastest wave of the spec (auto_dt).

t = 0 (make_initial): the symmetric point φ = 0 with the QUANTUM VACUUM fluctuations of every wave (each mode
carries ħω/2; truncated-Wigner / classical-statistical approximation), optionally a hot start at temperature T0
(n + ½ quanta per mode). The FFT is used only to build this initial state. ħ → 0 is the classical field. The total
charge is set to exactly zero (required by Gauss's law on a closed box) and E starts as the Coulomb field of the
initial charges plus the photons' own vacuum fluctuations.

Placed: the spec (field content, speeds, terms and coefficients, e), the outside (H), ħ and T0, the lattice
(dx = 1) and the finite periodic box. Not placed: whatever forms. Limits: classical-statistical fields (quantum
only as fluctuations at t = 0), lattice and finite box, expansion only until the vacuum scale reaches the lattice.
"""
from __future__ import annotations

import copy
from typing import Any

import numpy as np

from genesis.models.abelian_higgs_nd import _sh, plaquette, planes, wrap  # noqa: F401

TERMS = ("mexican", "triple_well", "z3", "aniso", "cross", "mass")

BASE: dict[str, Any] = {"real": 0, "complex": 0, "c_real": 1.0, "c_complex": 1.0, "terms": [], "e": 0.0,
                        "H": 0.0, "a_max": None, "hbar": 1e-4, "T0": 0.0, "dt": None, "cfl": 0.4}

PRESETS: dict[str, dict[str, Any]] = {
    # coefficients chosen so that the heaviest mode of every valley has a length 1/m of about 3 cells (2.8 for
    # three_equal): what forms is resolved by the lattice (tools/sb_universe.py heaviest_mass)
    "yinyang": {"real": 1, "terms": [{"kind": "mexican", "on": "real", "lam": 0.1, "v": 1.0}]},
    "yinyang_middle": {"real": 1, "terms": [{"kind": "triple_well", "on": "real", "lam": 0.025, "v": 1.0}]},
    "three_equal": {"complex": 1, "terms": [{"kind": "mexican", "on": "complex", "lam": 0.1, "v": 1.0},
                                            {"kind": "z3", "on": "complex:0", "g": 0.015, "v": 1.0}]},
    "continuous": {"complex": 1, "e": 0.3, "terms": [{"kind": "mexican", "on": "complex", "lam": 0.1, "v": 1.0}]},
    # two scales: A (complex, v = 1) breaks first; B (real, v = 0.4) is slowed by its coupling to A (g > 0) and breaks
    # later -- faster where A is small
    "cascade": {"real": 1, "complex": 1,
                "terms": [{"kind": "mexican", "on": "complex", "lam": 0.1, "v": 1.0},
                          {"kind": "mexican", "on": "real", "lam": 0.1, "v": 0.4},
                          {"kind": "cross", "a": "complex", "b": "real", "g": 0.004}]},
}


def spec_from(preset: str | None = None, **over) -> dict[str, Any]:
    s = copy.deepcopy(BASE)
    if preset:
        s.update(copy.deepcopy(PRESETS[preset]))
    s.update(over)
    return validate(s)


# ------------------------------------------------------------------------------------------ selections
def _sel(spec, on) -> tuple[list[int], list[int]]:
    """'all' | 'real' | 'complex' | 'real:i' | 'complex:i' -> (real indices, complex indices)."""
    R, N = spec["real"], spec["complex"]
    if on == "all":
        return list(range(R)), list(range(N))
    if on == "real":
        return list(range(R)), []
    if on == "complex":
        return [], list(range(N))
    kind, _, idx = str(on).partition(":")
    i = int(idx)
    if kind == "real" and 0 <= i < R:
        return [i], []
    if kind == "complex" and 0 <= i < N:
        return [], [i]
    raise ValueError(f"bad selection {on!r}")


def _speeds(spec, key, n):
    c = spec[key]
    c = [float(c)] * n if np.isscalar(c) else [float(x) for x in c]
    if len(c) != n:
        raise ValueError(f"{key} must have {n} entries")
    return c


def validate(spec: dict[str, Any]) -> dict[str, Any]:
    R, N = int(spec["real"]), int(spec["complex"])
    if R < 0 or N < 0 or R + N == 0:
        raise ValueError("a universe needs at least one field")
    spec["real"], spec["complex"] = R, N
    spec["c_real"], spec["c_complex"] = _speeds(spec, "c_real", R), _speeds(spec, "c_complex", N)
    if spec["e"] and N == 0:
        raise ValueError("the light-like field needs charged (complex) fields")
    quartic_ok = False
    for t in spec["terms"]:
        if t["kind"] not in TERMS:
            raise ValueError(f"unknown term {t['kind']!r}")
        for key in ("on", "a", "b"):
            if key in t:
                _sel(spec, t[key])
        if t["kind"] == "z3":
            _, cs = _sel(spec, t["on"])
            if len(cs) != 1:
                raise ValueError("z3 acts on one complex field")
            if spec["e"]:
                raise ValueError("Re(φ³) is not U(1)-invariant: a z3 term needs e = 0")
        if t["kind"] in ("mexican", "triple_well") and t.get("lam", 0) > 0:
            quartic_ok = True
        if t["kind"] == "aniso" and t.get("kappa", 0) < 0 and not quartic_ok:
            raise ValueError("a negative κ needs a positive quartic term")
    if not _bounded_below(spec):
        raise ValueError("the potential is not bounded below")
    return spec


def _points(spec, rho, n, seed):
    """n points at canonical radius rho (s = ½ρ²) along random directions of field space: real fields r (R, n) and
    complex fields c (N, n) with φ_a = (q1 + i q2)/√2, so that s = ½Σφ_r² + Σ|φ_a|² = ½|x|²."""
    rng = np.random.default_rng(seed)
    R, N = spec["real"], spec["complex"]
    x = rng.standard_normal((R + 2 * N, n))
    x = x / np.linalg.norm(x, axis=0) * rho
    return x[:R], (x[R:R + N] + 1j * x[R + N:]) / np.sqrt(2.0)


def _bounded_below(spec, n=4000) -> bool:
    """Numerical check: along every sampled direction V is non-negative and not falling far out (no runaway)."""
    far = []
    for rho in (1e2, 1e3):
        r, c = _points(spec, rho, n, seed=0)
        far.append(potential(spec, r, c))
    return bool((far[0] >= 0).all() and (far[1] >= far[0]).all())         # V = 0 (a free field) is allowed


# ------------------------------------------------------------------------------------------ potential
def _s(spec, r, c, on):
    rs, cs = _sel(spec, on)
    s = 0.0
    for i in rs:
        s = s + 0.5 * r[i] ** 2
    for a in cs:
        s = s + np.abs(c[a]) ** 2
    return s, rs, cs


def potential(spec, r, c) -> np.ndarray:
    """V at every site (physical fields; r shape (R, …), c shape (N, …))."""
    shape = (r if spec["real"] else c).shape[1:]
    V = np.zeros(shape)
    for t in spec["terms"]:
        k = t["kind"]
        if k == "mexican":
            s, _, _ = _s(spec, r, c, t["on"])
            V = V + 0.25 * t["lam"] * (s - t["v"] ** 2) ** 2
        elif k == "triple_well":
            s, _, _ = _s(spec, r, c, t["on"])
            V = V + t["lam"] * s * (s - t["v"] ** 2) ** 2
        elif k == "z3":
            _, _, cs = _s(spec, r, c, t["on"])
            V = V - t["g"] / t["v"] * np.real(c[cs[0]] ** 3)
        elif k == "aniso":
            rs, cs = _sel(spec, t["on"])
            V = V + t["kappa"] * (sum((0.5 * r[i] ** 2) ** 2 for i in rs) + sum(np.abs(c[a]) ** 4 for a in cs))
        elif k == "cross":
            sa, _, _ = _s(spec, r, c, t["a"])
            sb, _, _ = _s(spec, r, c, t["b"])
            V = V + t["g"] * sa * sb
        elif k == "mass":
            s, _, _ = _s(spec, r, c, t["on"])
            V = V + t["m2"] * s
    return V


def potential_grad(spec, r, c):
    """(∂V/∂φ_r, ∂V/∂φ_a*) at every site; the complex part is the force term of π̇ = … − ∂V/∂φ*."""
    gr = np.zeros_like(r)
    gc = np.zeros_like(c)
    for t in spec["terms"]:
        k = t["kind"]
        if k in ("mexican", "triple_well", "mass"):
            s, rs, cs = _s(spec, r, c, t["on"])
            if k == "mexican":
                f = 0.5 * t["lam"] * (s - t["v"] ** 2)
            elif k == "triple_well":
                f = t["lam"] * ((s - t["v"] ** 2) ** 2 + 2.0 * s * (s - t["v"] ** 2))
            else:
                f = t["m2"]
            for i in rs:
                gr[i] = gr[i] + f * r[i]
            for a in cs:
                gc[a] = gc[a] + f * c[a]
        elif k == "z3":
            _, cs = _sel(spec, t["on"])
            a = cs[0]
            gc[a] = gc[a] - 1.5 * t["g"] / t["v"] * np.conj(c[a]) ** 2
        elif k == "aniso":
            rs, cs = _sel(spec, t["on"])
            for i in rs:
                gr[i] = gr[i] + 0.5 * t["kappa"] * r[i] ** 3
            for a in cs:
                gc[a] = gc[a] + 2.0 * t["kappa"] * np.abs(c[a]) ** 2 * c[a]
        elif k == "cross":
            sa, ra, ca = _s(spec, r, c, t["a"])
            sb, rb, cb = _s(spec, r, c, t["b"])
            for i in ra:
                gr[i] = gr[i] + t["g"] * sb * r[i]
            for a in ca:
                gc[a] = gc[a] + t["g"] * sb * c[a]
            for i in rb:
                gr[i] = gr[i] + t["g"] * sa * r[i]
            for a in cb:
                gc[a] = gc[a] + t["g"] * sa * c[a]
    return gr, gc


# ------------------------------------------------------------------------------------------ state
def scale_factor(spec, tau: float) -> float:
    return 1.0 + spec["H"] * tau


def field_reach(spec, n: int = 200, seed: int = 2) -> float:
    """How far (canonical radius ρ, s = ½ρ²) the fields can swing: along random rays of field space, the valley (the
    last lowest point of the ray), the highest barrier ΔV between the origin and it, and the farthest ρ where V is
    still within 2ΔV of the valley. The largest over the rays."""
    vmax = max([t.get("v", 1.0) for t in spec["terms"]] + [1.0])
    rho = np.linspace(0.0, 20.0 * vmax, 4001)
    r, c = _points(spec, 1.0, n, seed)
    V = potential(spec, r[:, :, None] * rho, c[:, :, None] * rho)            # (n, len(rho))
    reach = np.sqrt(2.0) * vmax
    for Vr in V:
        vmin = Vr.min()
        lows = np.flatnonzero((Vr[:-1] <= np.r_[np.inf, Vr[:-2]]) & (Vr[:-1] <= Vr[1:]))   # local minima of the ray
        j = max(i for i in lows if Vr[i] <= vmin + 1e-3 * (Vr[:i + 1].max() - vmin) + 1e-12)
        dV = max(Vr[:j + 1].max() - vmin, 1e-12)
        reach = max(reach, float(rho[np.flatnonzero(Vr <= vmin + 2.0 * dV)[-1]]))
    return reach


def curvature_bound(spec, a: float = 1.0, n: int = 2000) -> float:
    """A bound on the largest |V''| the fields meet (for the step size): numerical, along random directions of field
    space out to field_reach, in comoving units (× a² for the expanding universe)."""
    R, N = spec["real"], spec["complex"]
    rng = np.random.default_rng(1)
    r, c = _points(spec, 1.0, n, seed=1)
    rho = rng.uniform(0.0, field_reach(spec), n)
    r, c = r * rho, c * rho
    h = 1e-4
    best = 0.0
    V0 = potential(spec, r, c)
    for i in range(R):
        rp, rm = r.copy(), r.copy()
        rp[i] += h
        rm[i] -= h
        best = max(best, float(np.abs((potential(spec, rp, c) - 2 * V0 + potential(spec, rm, c)) / h ** 2).max()))
    for a_ in range(N):
        for u in (1.0, 1j):                              # both real directions of a complex field (φ = (q1+iq2)/√2)
            cp, cm = c.copy(), c.copy()
            cp[a_] += u * h / np.sqrt(2.0)
            cm[a_] -= u * h / np.sqrt(2.0)
            best = max(best, float(np.abs((potential(spec, r, cp) - 2 * V0
                                           + potential(spec, r, cm)) / h ** 2).max()))
    return best * a * a


def auto_dt(spec, d: int) -> float:
    """cfl · 2/ω_max with ω_max² = 4d·max(c²) + max|V''| (the fastest wave, at the largest scale factor used)."""
    if spec.get("dt"):
        return float(spec["dt"])
    cmax2 = max([c * c for c in spec["c_real"] + spec["c_complex"]] + ([1.0] if spec["e"] else []))
    a = spec["a_max"] or 1.0
    w2 = 4.0 * d * cmax2 + curvature_bound(spec, a)
    return spec["cfl"] * 2.0 / np.sqrt(w2)


def forces(spec, st, a: float = 1.0):
    """(dπ_r, dπ_a, dE) for the comoving fields at scale factor a."""
    r, c, th = st["r"], st["c"], st["th"]
    gr, gc = potential_grad(spec, r / a if a != 1.0 else r, c / a if a != 1.0 else c)
    if a != 1.0:
        gr, gc = a ** 3 * gr, a ** 3 * gc
    dpr = np.empty_like(r)
    for i in range(spec["real"]):
        f = r[i]
        lap = sum(_sh(f, ax) + _sh(f, ax, -1) for ax in range(f.ndim)) - 2.0 * f.ndim * f
        dpr[i] = spec["c_real"][i] ** 2 * lap - gr[i]
    dpc = np.empty_like(c)
    dE = None
    if spec["e"]:
        d = th.shape[0]
        inv_e2 = 1.0 / spec["e"] ** 2
        cur = np.zeros(th.shape)
        U = [np.exp(-1j * th[i]) for i in range(d)]                  # link phases, shared by every charged field
        Ub = [np.conj(_sh(U[i], i, -1)) for i in range(d)]
        for a_ in range(spec["complex"]):
            ca2 = spec["c_complex"][a_] ** 2
            f = c[a_]
            fwd = [U[i] * _sh(f, i) for i in range(d)]
            lap = -2.0 * d * f
            for i in range(d):
                lap = lap + fwd[i] + Ub[i] * _sh(f, i, -1)
            dpc[a_] = ca2 * lap - gc[a_]
            fc = np.conj(f)
            for i in range(d):
                cur[i] = cur[i] + ca2 * 2.0 * np.imag(fwd[i] * fc)
        sins = {(i, j): np.sin(plaquette(th, i, j)) for i, j in planes(d)}
        dE = np.empty_like(th)
        for i in range(d):
            acc = np.zeros(th.shape[1:])
            for j in range(d):
                if j == i:
                    continue
                s = sins[(i, j)] if i < j else -sins[(j, i)]
                acc = acc + s - _sh(s, j, -1)
            dE[i] = -inv_e2 * acc + cur[i]
    else:
        for a_ in range(spec["complex"]):
            f = c[a_]
            lap = sum(_sh(f, ax) + _sh(f, ax, -1) for ax in range(f.ndim)) - 2.0 * f.ndim * f
            dpc[a_] = spec["c_complex"][a_] ** 2 * lap - gc[a_]
    return dpr, dpc, dE


def step(spec, st, dt: float) -> dict:
    """One kick–drift–kick step; st = {'r','pr','c','pc','th','E','tau'}. Returns a new dict."""
    tau = st["tau"]
    a0, a1 = scale_factor(spec, tau), scale_factor(spec, tau + dt)
    dpr, dpc, dE = forces(spec, st, a0)
    pr = st["pr"] + 0.5 * dt * dpr
    pc = st["pc"] + 0.5 * dt * dpc
    E = st["E"] + 0.5 * dt * dE if dE is not None else st["E"]
    r = st["r"] + dt * pr
    c = st["c"] + dt * pc
    th = st["th"] + dt * spec["e"] ** 2 * E if spec["e"] else st["th"]
    new = dict(st, r=r, c=c, th=th, tau=tau + dt)
    dpr, dpc, dE = forces(spec, new, a1)
    new["pr"] = pr + 0.5 * dt * dpr
    new["pc"] = pc + 0.5 * dt * dpc
    new["E"] = E + 0.5 * dt * dE if dE is not None else E
    return new


def run(spec, st, dt: float, n: int) -> dict:
    """n steps; the force at the end of one step is the force at the start of the next (computed once). The same
    numbers as n calls of step()."""
    f = None
    for _ in range(n):
        tau = st["tau"]
        a0, a1 = scale_factor(spec, tau), scale_factor(spec, tau + dt)
        dpr, dpc, dE = f if f is not None else forces(spec, st, a0)
        pr = st["pr"] + 0.5 * dt * dpr
        pc = st["pc"] + 0.5 * dt * dpc
        E = st["E"] + 0.5 * dt * dE if dE is not None else st["E"]
        r = st["r"] + dt * pr
        c = st["c"] + dt * pc
        th = st["th"] + dt * spec["e"] ** 2 * E if spec["e"] else st["th"]
        new = dict(st, r=r, c=c, th=th, tau=tau + dt)
        f = forces(spec, new, a1)
        dpr, dpc, dE = f
        new["pr"] = pr + 0.5 * dt * dpr
        new["pc"] = pc + 0.5 * dt * dpc
        new["E"] = E + 0.5 * dt * dE if dE is not None else E
        st = new
    return st


# ------------------------------------------------------------------------------------------ t = 0
def _k2_lattice(shape) -> np.ndarray:
    return sum(np.meshgrid(*[4.0 * np.sin(np.pi * np.fft.fftfreq(n)) ** 2 for n in shape], indexing="ij"))


def _vacuum_real(shape, rng, hbar, T0, c, m2):
    """A real field and momentum with the quantum (+ thermal) fluctuations of the free field ω² = c²k² + m²."""
    w = np.sqrt(np.maximum(c * c * _k2_lattice(shape) + max(m2, 0.0), 0.0))
    w = np.where(w > 0, w, np.inf)                          # the zero mode of a massless field carries nothing
    occ = 0.5 + (1.0 / np.expm1(np.minimum(hbar * w / T0, 700.0)) if T0 > 0 else 0.0)   # Bose: n = 1/(e^{ħω/T}−1)
    q = np.fft.ifftn(np.sqrt(hbar * occ / w) * np.fft.fftn(rng.standard_normal(shape), norm="ortho"),
                     norm="ortho").real
    p = np.fft.ifftn(np.sqrt(hbar * occ * np.where(np.isfinite(w), w, 0.0))
                     * np.fft.fftn(rng.standard_normal(shape), norm="ortho"), norm="ortho").real
    return q, p


def _transverse(X):
    """Remove the lattice-longitudinal part of a link vector field (div X = Σ_i X_i(x) − X_i(x−î) = 0)."""
    d = X.shape[0]
    shape = X.shape[1:]
    ks = np.meshgrid(*[2 * np.pi * np.fft.fftfreq(n) for n in shape], indexing="ij")
    D = [1.0 - np.exp(-1j * k) for k in ks]
    Xk = [np.fft.fftn(X[i]) for i in range(d)]
    div = sum(D[i] * Xk[i] for i in range(d))
    nrm = sum(np.abs(D[i]) ** 2 for i in range(d))
    nrm[(0,) * d] = 1.0
    return np.stack([np.fft.ifftn(Xk[i] - np.conj(D[i]) * div / nrm).real for i in range(d)])


def coulomb_field(rho: np.ndarray) -> np.ndarray:
    """E_i = ψ(x+î) − ψ(x) with lap ψ = ρ: the longitudinal field whose lattice divergence is ρ (Σρ must be 0)."""
    d = rho.ndim
    k2 = _k2_lattice(rho.shape)
    k2[(0,) * d] = 1.0
    psi = np.fft.ifftn(-np.fft.fftn(rho) / k2).real
    return np.stack([_sh(psi, i) - psi for i in range(d)])


def charge_density(st) -> np.ndarray:
    return sum(2.0 * np.imag(np.conj(st["c"][a]) * st["pc"][a]) for a in range(st["c"].shape[0])) \
        if st["c"].shape[0] else np.zeros(st["r"].shape[1:])


def make_initial(spec, shape, rng: np.random.Generator) -> dict:
    d = len(shape)
    R, N = spec["real"], spec["complex"]
    hbar, T0 = spec["hbar"], spec["T0"]
    m2 = _mass2_at_origin(spec)
    r = np.zeros((R,) + tuple(shape))
    pr = np.zeros_like(r)
    for i in range(R):
        r[i], pr[i] = _vacuum_real(shape, rng, hbar, T0, spec["c_real"][i], m2["real"][i])
    c = np.zeros((N,) + tuple(shape), complex)
    pc = np.zeros_like(c)
    for a in range(N):
        q1, p1 = _vacuum_real(shape, rng, hbar, T0, spec["c_complex"][a], m2["complex"][a])
        q2, p2 = _vacuum_real(shape, rng, hbar, T0, spec["c_complex"][a], m2["complex"][a])
        c[a], pc[a] = (q1 + 1j * q2) / np.sqrt(2.0), (p1 + 1j * p2) / np.sqrt(2.0)
    th = np.zeros((d,) + tuple(shape))
    E = np.zeros_like(th)
    st = {"r": r, "pr": pr, "c": c, "pc": pc, "th": th, "E": E, "tau": 0.0}
    if spec["e"] and N:
        Q = charge_density(st).sum()                        # a closed box holds no net charge (Gauss's law)
        s2 = sum((np.abs(c[a]) ** 2).sum() for a in range(N))
        if s2 > 0:
            for a in range(N):
                pc[a] = pc[a] - (Q / (2.0 * s2)) * 1j * c[a]
        e = spec["e"]
        A, P = np.zeros_like(th), np.zeros_like(th)           # photons: A = θ/e, Π = eE, ω = |k|
        for i in range(d):
            A[i], P[i] = _vacuum_real(shape, rng, hbar, T0, 1.0, 0.0)
        st["th"] = e * _transverse(A)
        st["E"] = _transverse(P) / e + coulomb_field(charge_density(st))
    return st


def _mass2_at_origin(spec) -> dict[str, list[float]]:
    """V'' at φ = 0 per field (for the free-field frequencies of the initial fluctuations)."""
    R, N = spec["real"], spec["complex"]
    h = 1e-4
    out = {"real": [], "complex": []}
    for i in range(R):
        r, c = np.zeros((R, 1)), np.zeros((N, 1), complex)
        r[i] = h
        out["real"].append(float(2.0 * (potential(spec, r, c)[0] - potential(spec, 0 * r, c)[0]) / h ** 2))
    for a in range(N):
        r, c = np.zeros((R, 1)), np.zeros((N, 1), complex)
        c[a] = h / np.sqrt(2.0)
        out["complex"].append(float(2.0 * (potential(spec, r, c)[0] - potential(spec, r, 0 * c)[0]) / h ** 2))
    return out


# ------------------------------------------------------------------------------------------ measures
def energy_density(spec, st) -> np.ndarray:
    """Comoving energy density (closed box: its sum is conserved)."""
    r, c, th = st["r"], st["c"], st["th"]
    a = scale_factor(spec, st["tau"])
    out = a ** 4 * potential(spec, r / a, c / a) if a != 1.0 else potential(spec, r, c)
    for i in range(spec["real"]):
        f = r[i]
        out = out + 0.5 * st["pr"][i] ** 2 + 0.5 * spec["c_real"][i] ** 2 * sum(
            (_sh(f, ax) - f) ** 2 for ax in range(f.ndim))
    for a_ in range(spec["complex"]):
        f = c[a_]
        if spec["e"]:
            g = sum(np.abs(np.exp(-1j * th[ax]) * _sh(f, ax) - f) ** 2 for ax in range(f.ndim))
        else:
            g = sum(np.abs(_sh(f, ax) - f) ** 2 for ax in range(f.ndim))
        out = out + np.abs(st["pc"][a_]) ** 2 + spec["c_complex"][a_] ** 2 * g
    if spec["e"]:
        d = th.shape[0]
        out = out + 0.5 * spec["e"] ** 2 * (st["E"] ** 2).sum(0) + sum(
            1.0 - np.cos(plaquette(th, i, j)) for i, j in planes(d)) / spec["e"] ** 2
    return out


def energy(spec, st) -> float:
    return float(energy_density(spec, st).sum())


def gauss_residual(spec, st) -> np.ndarray:
    if not spec["e"]:
        return np.zeros(st["r"].shape[1:] if spec["real"] else st["c"].shape[1:])
    E = st["E"]
    div = sum(E[i] - _sh(E[i], i, -1) for i in range(E.shape[0]))
    return div - charge_density(st)


def flavor_charges(st) -> np.ndarray:
    """Global charge of every complex field, Q_a = Σ 2 Im(φ_a*π_a) (conserved in a closed box when the potential is
    U(1)-invariant field by field)."""
    return np.array([float((2.0 * np.imag(np.conj(st["c"][a]) * st["pc"][a])).sum()) for a in range(st["c"].shape[0])])


def order_parameter(spec, st) -> np.ndarray:
    """The canonical invariant s = ½Σφ_r² + Σ|φ_a|² of the physical fields at every site."""
    a = scale_factor(spec, st["tau"])
    s, _, _ = _s(spec, st["r"] / a, st["c"] / a, "all")
    return s

