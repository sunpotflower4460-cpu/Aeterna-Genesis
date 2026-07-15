"""Nematic Q-tensor Landau-de Gennes free energy on a FIXED diffuse-interface droplet (P06 / F1-V1).

ROLE: V (validation). This module evaluates a *full* nematic free energy

    F[phi, Q] = F_interface[phi] + F_LdG[Q; phi] + F_elastic[Q; L1, L2] + F_anchoring[phi, Q]

on a FIXED phase field `phi` (the droplet shape is PLACED, not grown) by relaxing only the
orientational order Q with a gradient flow  dQ/dt = -Gamma * P_ST(delta F / delta Q)  at fixed phi.
Because phi never moves, NO hole can open here -- this is deliberately the V1 rung of
docs/frontier/F0_P06_sphere_to_torus.md, not S1/E2 (dynamic genus transition), which is out of scope.

WHAT IS PLACED (honest): the shape phi (ball or torus) and the boundary condition (planar-degenerate
anchoring on the interface). WHAT IS MEASURED: the relaxed nematic texture's free energy for each fixed
shape, and whether F(torus) crosses below F(ball) as the anchoring strength grows -- the Koizumi/Lin-Wang
mechanism (a sphere cannot carry a defect-free tangential director -- hairy-ball obstruction -- while a
torus can, so strong planar anchoring eventually favours the torus, paying extra interfacial area to shed
the forced surface defects). Reproducing that crossing on FIXED shapes is a *validation* (V) of the free-
energy landscape; it is NOT a claim that a hole opens by itself (that would be E, and is not done here).

DISCIPLINE (F0 / AGENTS.md):
- Nondimensionalisation, coefficients, grid and dt are FROZEN in `FROZEN` below and are NOT retuned after
  looking at the numbers. --quick only subsamples (coarser grid, fewer steps/sweep points); it never
  changes the physics constants.
- No genus/handle/hole term, no preferred axis, no target shape is encoded in F. The only anisotropy is the
  standard L2 elastic term (splay/bend) and the standard planar-degenerate (Fournier-Galatola) anchoring.
- We never call the fixed-shape crossing "emergence"; we never say life/mind/universe.

Representation: Q is symmetric-traceless 3x3, stored as 5 arrays [Qxx, Qxy, Qxz, Qyy, Qyz] on an N^3 grid;
Qzz = -(Qxx+Qyy). The gradient flow steps only these 5 components with a traceless molecular field, so the
symmetric-traceless projection P_ST is enforced by construction. All derivatives are central differences
via np.roll (local stencils, no global solver); the box is large enough that Q ~ 0 at its walls.
"""
import numpy as np

# ---- frozen constants (chosen a priori for the nematic regime; not tuned after seeing results) ----
FROZEN = dict(
    A_in=-0.20,     # Landau-de Gennes A INSIDE the droplet (<0 -> nematic ordered phase)
    A_out=1.0,      # A OUTSIDE (>0 -> isotropic, forces Q->0 in the exterior)
    B=-2.0,         # cubic LdG coefficient
    C=2.25,         # quartic LdG coefficient
    L1=0.05,        # isotropic (one-constant) elasticity
    L2=0.05,        # anisotropic elasticity (splay/bend distinction); L2=0 -> one-constant
    kappa=1.0,      # phase-field gradient stiffness (interface width scale)
    sigma0=0.08,    # interfacial energy scale (multiplies the double-well + gradient interface energy)
    eps=1.6,        # diffuse-interface half-width (lattice units)
    Gamma=1.0,      # rotational mobility of the gradient flow
    dt=0.04,        # explicit relaxation step (stable for the frozen L1,L2 above)
    W_planar=2.0,   # planar anchoring strength held fixed while the elastic constant K is swept (V1 Frank)
)


def s_eq(A, B, C):
    """Equilibrium uniaxial scalar order S* minimising f = A/2 trQ^2 + B/3 trQ^3 + C/4 (trQ^2)^2.
    From 3A + B S + 2C S^2 = 0 (nonzero branch)."""
    disc = B * B - 24.0 * A * C
    if disc < 0:
        return 0.0
    return (-B + np.sqrt(disc)) / (4.0 * C)


# ---------------------------------------------------------------- geometry (fixed shapes)
def _grid(N):
    x = np.arange(N) - (N - 1) / 2.0
    return np.meshgrid(x, x, x, indexing="ij")


def phi_ball(N, Rb, eps):
    """Diffuse-interface ball, phi = +1 inside / -1 outside, tanh profile of half-width eps."""
    X, Y, Z = _grid(N)
    r = np.sqrt(X * X + Y * Y + Z * Z)
    return np.tanh((Rb - r) / (np.sqrt(2.0) * eps))


def phi_torus(N, R, a, eps):
    """Diffuse-interface solid torus (ring radius R, tube radius a) about the z-axis."""
    X, Y, Z = _grid(N)
    rho = np.sqrt(X * X + Y * Y)
    d = np.sqrt((rho - R) ** 2 + Z * Z)   # distance to the ring
    return np.tanh((a - d) / (np.sqrt(2.0) * eps))


def torus_from_ball(Rb, aspect=2.5):
    """Torus (R, a) with the SAME material volume as a ball of radius Rb, at fixed R/a = aspect.
    Ball vol = 4/3 pi Rb^3;  torus vol = 2 pi^2 R a^2 = 2 pi^2 aspect a^3  =>  solve for a, R=aspect*a."""
    vol = 4.0 / 3.0 * np.pi * Rb ** 3
    a = (vol / (2.0 * np.pi ** 2 * aspect)) ** (1.0 / 3.0)
    return aspect * a, a


# ---------------------------------------------------------------- differential operators (local stencils)
def _lap(f):
    return (np.roll(f, 1, 0) + np.roll(f, -1, 0) + np.roll(f, 1, 1) + np.roll(f, -1, 1)
            + np.roll(f, 1, 2) + np.roll(f, -1, 2) - 6.0 * f)


def _d(f, axis):
    return 0.5 * (np.roll(f, -1, axis) - np.roll(f, 1, axis))


# Forward/backward differences form an exact adjoint pair: sum(a*_df(b)) = -sum(_db(a)*b), and
# sum_ax _db(_df(f,ax),ax) == the compact 7-point _lap(f). So when an elastic ENERGY is written with _df,
# the compact Laplacian _lap is its EXACT discrete gradient (variational-consistent, no checkerboard).
def _df(f, axis):
    return np.roll(f, -1, axis) - f


def _db(f, axis):
    return f - np.roll(f, 1, axis)


# ---------------------------------------------------------------- Q algebra on the 5 stored components
def _full(q):
    """Return the six independent components (xx,xy,xz,yy,yz,zz) from the 5 stored (zz = -(xx+yy))."""
    qxx, qxy, qxz, qyy, qyz = q
    qzz = -(qxx + qyy)
    return qxx, qxy, qxz, qyy, qyz, qzz


def tr_q2(q):
    xx, xy, xz, yy, yz, zz = _full(q)
    return xx * xx + yy * yy + zz * zz + 2.0 * (xy * xy + xz * xz + yz * yz)


def tr_q3(q):
    xx, xy, xz, yy, yz, zz = _full(q)
    det = (xx * (yy * zz - yz * yz) - xy * (xy * zz - yz * xz) + xz * (xy * yz - yy * xz))
    return 3.0 * det


def _q_square(q):
    """Components (xx,xy,xz,yy,yz) of Q*Q (symmetric)."""
    xx, xy, xz, yy, yz, zz = _full(q)
    sxx = xx * xx + xy * xy + xz * xz
    sxy = xx * xy + xy * yy + xz * yz
    sxz = xx * xz + xy * yz + xz * zz
    syy = xy * xy + yy * yy + yz * yz
    syz = xy * xz + yy * yz + yz * zz
    return sxx, sxy, sxz, syy, syz


def _detrace5(mxx, mxy, mxz, myy, myz, mzz):
    """Subtract trace/3 from a symmetric tensor, return the 5 stored (traceless) components."""
    t = (mxx + myy + mzz) / 3.0
    return np.stack([mxx - t, mxy, mxz, myy - t, myz])


# ---------------------------------------------------------------- free energy + molecular field
def _interface_energy(phi, p):
    """F_interface[phi] = sigma0 * integral[ (phi^2-1)^2/4 + (kappa/2)|grad phi|^2 ] dV (phi fixed)."""
    gx, gy, gz = _d(phi, 0), _d(phi, 1), _d(phi, 2)
    dens = 0.25 * (phi * phi - 1.0) ** 2 + 0.5 * p["kappa"] * (gx * gx + gy * gy + gz * gz)
    return p["sigma0"] * float(dens.sum())


def _anchoring_normal(q, nx, ny, nz, gmag, Seq):
    """Planar-degenerate (Fournier-Galatola) normal-part tensor N = Qtilde - P Qtilde P,
    with Qtilde = Q + (Seq/3) I and P = I - nu nu.  N_ij = nu_i a_j + a_i nu_j - s nu_i nu_j,
    a_i = (Qtilde nu)_i, s = nu.Qtilde.nu, tr(N)=s.  Returns (N components) and s."""
    xx, xy, xz, yy, yz, zz = _full(q)
    c = Seq / 3.0
    txx, tyy, tzz = xx + c, yy + c, zz + c           # Qtilde diagonal
    ax = txx * nx + xy * ny + xz * nz
    ay = xy * nx + tyy * ny + yz * nz
    az = xz * nx + yz * ny + tzz * nz
    s = ax * nx + ay * ny + az * nz
    Nxx = 2 * nx * ax - s * nx * nx
    Nyy = 2 * ny * ay - s * ny * ny
    Nzz = 2 * nz * az - s * nz * nz
    Nxy = nx * ay + ax * ny - s * nx * ny
    Nxz = nx * az + ax * nz - s * nx * nz
    Nyz = ny * az + ay * nz - s * ny * nz
    return (Nxx, Nxy, Nxz, Nyy, Nyz, Nzz), s


def energy_terms(q, phi, W, p, nu=None):
    """Total free energy and its parts for a fixed phi and current Q (all frozen constants in p)."""
    h = np.clip(0.5 * (phi + 1.0), 0.0, 1.0)
    A_eff = p["A_in"] * h + p["A_out"] * (1.0 - h)
    t2 = tr_q2(q)
    t3 = tr_q3(q)
    f_ldg = float((0.5 * A_eff * t2 + (1.0 / 3.0) * p["B"] * t3 + 0.25 * p["C"] * t2 * t2).sum())
    # elastic L1 (|grad Q|^2 over all 9 components) and L2 ((div Q)^2). L1 uses forward differences so the
    # compact Laplacian in molecular_field() is its EXACT discrete gradient; L2 uses central differences,
    # matched by its own central-difference molecular field.
    xx, xy, xz, yy, yz, zz = _full(q)
    grad2 = np.zeros_like(phi)
    for comp, wgt in ((xx, 1.0), (yy, 1.0), (zz, 1.0), (xy, 2.0), (xz, 2.0), (yz, 2.0)):
        grad2 += wgt * (_df(comp, 0) ** 2 + _df(comp, 1) ** 2 + _df(comp, 2) ** 2)
    f_l1 = float((0.5 * p["L1"] * grad2).sum())
    dx = _d(xx, 0) + _d(xy, 1) + _d(xz, 2)
    dy = _d(xy, 0) + _d(yy, 1) + _d(yz, 2)
    dz = _d(xz, 0) + _d(yz, 1) + _d(zz, 2)
    f_l2 = float((0.5 * p["L2"] * (dx * dx + dy * dy + dz * dz)).sum())
    # anchoring at the interface
    if nu is None:
        nu = interface_normal(phi)
    nx, ny, nz, gmag = nu
    Seq = s_eq(p["A_in"], p["B"], p["C"])
    (Nxx, Nxy, Nxz, Nyy, Nyz, Nzz), _s = _anchoring_normal(q, nx, ny, nz, gmag, Seq)
    NN = Nxx ** 2 + Nyy ** 2 + Nzz ** 2 + 2.0 * (Nxy ** 2 + Nxz ** 2 + Nyz ** 2)
    f_anch = float((W * gmag * NN).sum())
    f_int = _interface_energy(phi, p)
    total = f_ldg + f_l1 + f_l2 + f_anch + f_int
    return dict(total=total, ldg=f_ldg, elastic=f_l1 + f_l2, anchoring=f_anch, interface=f_int)


def interface_normal(phi):
    """Unit interface normal nu = grad phi / |grad phi| and |grad phi| (localises anchoring)."""
    gx, gy, gz = _d(phi, 0), _d(phi, 1), _d(phi, 2)
    gmag = np.sqrt(gx * gx + gy * gy + gz * gz)
    inv = 1.0 / (gmag + 1e-12)
    return gx * inv, gy * inv, gz * inv, gmag


def molecular_field(q, phi, W, p, nu):
    """H = -delta F / delta Q, symmetric-traceless (returns the 5 stored components)."""
    h = np.clip(0.5 * (phi + 1.0), 0.0, 1.0)
    A_eff = p["A_in"] * h + p["A_out"] * (1.0 - h)
    t2 = tr_q2(q)
    sxx, sxy, sxz, syy, syz = _q_square(q)
    szz = -(sxx + syy) + tr_q2(q)  # (Q^2)_zz = trQ2 - (Q^2)_xx - (Q^2)_yy
    xx, xy, xz, yy, yz, zz = _full(q)
    # bulk: -(A_eff Q + B (Q^2 - trQ2/3 I) + C trQ2 Q); detrace the whole thing
    bxx = -(A_eff * xx + p["B"] * sxx + p["C"] * t2 * xx)
    byy = -(A_eff * yy + p["B"] * syy + p["C"] * t2 * yy)
    bzz = -(A_eff * zz + p["B"] * szz + p["C"] * t2 * zz)
    bxy = -(A_eff * xy + p["B"] * sxy + p["C"] * t2 * xy)
    bxz = -(A_eff * xz + p["B"] * sxz + p["C"] * t2 * xz)
    byz = -(A_eff * yz + p["B"] * syz + p["C"] * t2 * yz)
    H = _detrace5(bxx, bxy, bxz, byy, byz, bzz)
    # elastic L1: +L1 lap(Q) (component-wise; traceless preserved)
    H = H + p["L1"] * np.stack([_lap(xx), _lap(xy), _lap(xz), _lap(yy), _lap(yz)])
    # elastic L2: +L2 * ST( sym( d_i(div Q)_j ) )
    dvx = _d(xx, 0) + _d(xy, 1) + _d(xz, 2)
    dvy = _d(xy, 0) + _d(yy, 1) + _d(yz, 2)
    dvz = _d(xz, 0) + _d(yz, 1) + _d(zz, 2)
    Gxx = _d(dvx, 0); Gyy = _d(dvy, 1); Gzz = _d(dvz, 2)
    Gxy = 0.5 * (_d(dvx, 1) + _d(dvy, 0))
    Gxz = 0.5 * (_d(dvx, 2) + _d(dvz, 0))
    Gyz = 0.5 * (_d(dvy, 2) + _d(dvz, 1))
    H = H + p["L2"] * _detrace5(Gxx, Gxy, Gxz, Gyy, Gyz, Gzz)
    # anchoring: -2 W gmag ST(N)
    nx, ny, nz, gmag = nu
    Seq = s_eq(p["A_in"], p["B"], p["C"])
    (Nxx, Nxy, Nxz, Nyy, Nyz, Nzz), _s = _anchoring_normal(q, nx, ny, nz, gmag, Seq)
    Ha = -2.0 * W * gmag
    H = H + _detrace5(Ha * Nxx, Ha * Nxy, Ha * Nxz, Ha * Nyy, Ha * Nyz, Ha * Nzz)
    return H


# ---------------------------------------------------------------- relaxation (gradient flow at fixed phi)
def seed_Q(N, Seq, seed=0, kind="random", axis=2, noise=0.02):
    """Deterministic IC. kind='uniform': a uniform uniaxial director along `axis`; kind='random': a
    spatially random director field (uncorrelated unit vectors). Both are SHAPE-BLIND -- the same seeding
    recipe is used for every shape, so no target topology is encoded. Randomness lets the gradient flow
    escape the symmetric uniform saddle and find each shape's own low-energy anchoring-compatible texture
    (on a torus a defect-free tangential one exists; on a sphere the hairy-ball theorem forbids it)."""
    rng = np.random.default_rng(seed)
    q = np.zeros((5, N, N, N))
    if kind == "uniform":
        n = np.zeros(3); n[axis] = 1.0
        nx = np.full((N, N, N), n[0]); ny = np.full((N, N, N), n[1]); nz = np.full((N, N, N), n[2])
    elif kind == "azimuthal":
        # phi-hat about the z-axis: a fixed field in SPACE, applied identically to every shape (NOT a
        # shape-specific placement). It is defect-free tangent to a z-torus but has forced pole defects
        # on a sphere -- the functional, not this seed, decides which shape it helps.
        X, Y, Z = _grid(N)
        rho = np.sqrt(X * X + Y * Y) + 1e-9
        nx, ny, nz = -Y / rho, X / rho, np.zeros((N, N, N))
    else:
        v = rng.normal(size=(3, N, N, N))
        norm = np.sqrt((v * v).sum(0)) + 1e-12
        nx, ny, nz = v[0] / norm, v[1] / norm, v[2] / norm
    q[0] = Seq * (nx * nx - 1.0 / 3.0); q[1] = Seq * nx * ny; q[2] = Seq * nx * nz
    q[3] = Seq * (ny * ny - 1.0 / 3.0); q[4] = Seq * ny * nz
    if noise:
        q += noise * (rng.random((5, N, N, N)) - 0.5)
    return q


def relax(phi, W, p, steps, seed=0, kind="random", record_every=0):
    """Relax Q by dQ/dt = Gamma * H at fixed phi; return final Q, energy history, and terms."""
    Seq = s_eq(p["A_in"], p["B"], p["C"])
    q = seed_Q(phi.shape[0], Seq, seed=seed, kind=kind)
    nu = interface_normal(phi)
    hist = []
    for it in range(steps):
        H = molecular_field(q, phi, W, p, nu)
        q = q + p["Gamma"] * p["dt"] * H
        if record_every and (it % record_every == 0 or it == steps - 1):
            hist.append(energy_terms(q, phi, W, p, nu=nu)["total"])
    return q, hist, energy_terms(q, phi, W, p, nu=nu)


def relax_min(phi, W, p, steps, seeds=(0, 1, 2), kind="random"):
    """Relax from several shape-blind random seeds and KEEP THE LOWEST-ENERGY texture (an honest,
    protocol-identical approximation of each shape's free-energy minimum)."""
    best = None
    for s in seeds:
        q, hist, terms = relax(phi, W, p, steps, seed=s, kind=kind, record_every=0)
        if best is None or terms["total"] < best[2]["total"]:
            best = (q, hist, terms, s)
    return best  # (q, hist, terms, winning_seed)


def sphere_torus_crossing(N, Rb, Ws, p=FROZEN, steps=400, seeds=(0, 1, 2), aspect=2.5):
    """Evaluate F(ball) and F(torus) (volume-matched) across a frozen sweep of anchoring strengths W.
    Each shape's energy is the minimum over shape-blind random seeds. Returns per-W energies and the
    crossing W* (linear interpolation of the sign change of dF = F_torus - F_ball)."""
    R, a = torus_from_ball(Rb, aspect)
    pb = phi_ball(N, Rb, p["eps"])
    pt = phi_torus(N, R, a, p["eps"])
    rows = []
    for W in Ws:
        _qb, _hb, tb, _sb = relax_min(pb, W, p, steps, seeds=seeds)
        _qt, _ht, tt, _st = relax_min(pt, W, p, steps, seeds=seeds)
        rows.append(dict(W=float(W), F_ball=tb["total"], F_torus=tt["total"],
                         dF=tt["total"] - tb["total"], ball=tb, torus=tt))
    Wstar = _crossing(Ws, [r["dF"] for r in rows])
    return dict(N=N, Rb=float(Rb), R=float(R), a=float(a), hole_radius=float(R - a),
                interface_eps=p["eps"], rows=rows, W_star=Wstar)


def _crossing(xs, dF):
    """First x where dF changes sign from + (ball wins) to - (torus wins); linear-interpolated."""
    for i in range(len(xs) - 1):
        if dF[i] > 0.0 >= dF[i + 1] or (dF[i] >= 0.0 > dF[i + 1]):
            f0, f1 = dF[i], dF[i + 1]
            frac = f0 / (f0 - f1) if f0 != f1 else 0.0
            return float(xs[i] + frac * (xs[i + 1] - xs[i]))
    return None


# =====================================================================================================
# Frank director limit (fixed |n|=1) -- the V1 crossing demonstrator.
#
# The full Q-tensor above lets a defect core MELT (S->0) and escape into 3D; at accessible grid spacing
# its core size xi=sqrt(L1/|A|) is sub-cell, so a sphere resolves its planar-anchoring-forced defects
# almost for free and NO sphere->torus crossing appears (an honest property, and exactly the escape
# ingredient that F2's dynamic hole-opening needs). In the fixed-length Frank limit the sphere's forced
# defects (Poincare-Hopf: a tangent field on S^2 has total index +2, on a torus it can be 0) CANNOT melt,
# so the sphere pays a real elastic defect energy. Sweeping the elastic-capillary ratio K/(sigma*R) then
# reproduces the crossing: small K -> ball (surface area wins); large K -> torus (defect energy exceeds the
# extra interfacial area). Anchoring OFF (W=0) removes the forced defects and the crossing vanishes -- the
# mechanism control of F0 section 5.  Same free energy family, fixed shapes -> this is V, not E.
# =====================================================================================================
def _frank_seed(N, kind, seed):
    rng = np.random.default_rng(seed)
    if kind == "azimuthal":
        X, Y, Z = _grid(N)
        rho = np.sqrt(X * X + Y * Y) + 1e-9
        nx, ny, nz = -Y / rho, X / rho, np.zeros((N, N, N))
    elif kind == "uniform":
        nx, ny, nz = np.zeros((N, N, N)), np.zeros((N, N, N)), np.ones((N, N, N))
    else:
        v = rng.normal(size=(3, N, N, N))
        q = np.sqrt((v * v).sum(0)) + 1e-12
        nx, ny, nz = v[0] / q, v[1] / q, v[2] / q
    nx = nx + 0.01 * (rng.random((N, N, N)) - 0.5)
    ny = ny + 0.01 * (rng.random((N, N, N)) - 0.5)
    nz = nz + 0.01 * (rng.random((N, N, N)) - 0.5)
    q = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
    return nx / q, ny / q, nz / q


def frank_energy(n, phi, W, K, p):
    """Director free energy on a FIXED phi: F = interface[phi] + K/2 int h|grad n|^2 + W int|grad phi|(n.nu)^2.
    Planar-degenerate anchoring penalises the normal component (n.nu)."""
    nx, ny, nz = n
    h = np.clip(0.5 * (phi + 1.0), 0.0, 1.0)
    vx, vy, vz, g = interface_normal(phi)
    dp = nx * vx + ny * vy + nz * vz
    f_anch = float((W * g * dp * dp).sum())
    grad2 = sum(_df(c, i) ** 2 for c in (nx, ny, nz) for i in range(3))   # forward diff -> exact grad below
    f_el = float((0.5 * K * h * grad2).sum())
    f_int = _interface_energy(phi, p)
    return dict(total=f_el + f_anch + f_int, elastic=f_el, anchoring=f_anch, interface=f_int)


def frank_relax(phi, W, K, p, steps, seed=0, kind="random", dt=0.08):
    """Gradient flow of the unit director at fixed phi (renormalise to |n|=1 each step)."""
    h = np.clip(0.5 * (phi + 1.0), 0.0, 1.0)
    vx, vy, vz, g = interface_normal(phi)
    nx, ny, nz = _frank_seed(phi.shape[0], kind, seed)

    def hlap(f):  # exact discrete gradient of (K/2) int h |grad f|^2 with forward-difference energy
        return sum(_db(h * _df(f, ax), ax) for ax in range(3))
    for _ in range(steps):
        dp = nx * vx + ny * vy + nz * vz
        nx = nx + dt * (K * hlap(nx) - 2.0 * W * g * dp * vx)
        ny = ny + dt * (K * hlap(ny) - 2.0 * W * g * dp * vy)
        nz = nz + dt * (K * hlap(nz) - 2.0 * W * g * dp * vz)
        q = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
        nx, ny, nz = nx / q, ny / q, nz / q
    return (nx, ny, nz), frank_energy((nx, ny, nz), phi, W, K, p)


def frank_min(phi, W, K, p, steps, seeds=(0, 1), kinds=("azimuthal", "random", "uniform")):
    """Lowest director energy over a fixed, shape-blind seed/ansatz ensemble (same recipe for every shape)."""
    best = None
    for kind in kinds:
        for s in seeds:
            n, terms = frank_relax(phi, W, K, p, steps, seed=s, kind=kind)
            if best is None or terms["total"] < best[1]["total"]:
                best = (n, terms, kind, s)
    return best


def sphere_torus_crossing_frank(N, Rb, Ks, W, p=FROZEN, steps=450, seeds=(0, 1), aspect=2.5):
    """Sweep the elastic constant K (with planar anchoring W fixed) and locate the sphere->torus crossing.
    Each shape's energy is the minimum over a shape-blind director ensemble. Returns rows and K*."""
    R, a = torus_from_ball(Rb, aspect)
    pb = phi_ball(N, Rb, p["eps"])
    pt = phi_torus(N, R, a, p["eps"])
    rows = []
    for K in Ks:
        _nb, tb, _kb, _sb = frank_min(pb, W, K, p, steps, seeds=seeds)
        _nt, tt, _kt, _st = frank_min(pt, W, K, p, steps, seeds=seeds)
        rows.append(dict(K=float(K), F_ball=tb["total"], F_torus=tt["total"], dF=tt["total"] - tb["total"],
                         ball=tb, torus=tt))
    Kstar = _crossing(Ks, [r["dF"] for r in rows])
    return dict(N=N, Rb=float(Rb), R=float(R), a=float(a), hole_radius=float(R - a), W=float(W),
                interface_eps=p["eps"], sigma0=p["sigma0"], rows=rows, K_star=Kstar,
                area_penalty=float(rows[0]["torus"]["interface"] - rows[0]["ball"]["interface"]))
