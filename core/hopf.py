"""S^2-valued field tools for hopfions (e012): construction, energies, charge.

A hopfion is a smooth map n: R^3 -> S^2 (|n|=1) with a nonzero Hopf invariant
Q_H (the linking number of two preimages). The Faddeev-Skyrme energy is

    E = c2 * integral |d_i n|^2  +  c4 * integral sum_{j<k} F_jk^2 ,
    F_jk = n . (d_j n x d_k n)   (the pulled-back area 2-form curvature).

Derrick's theorem: under x -> x/L the two terms scale as E(L) = L*c2*E2 + c4*E4/L.
The pure-gradient (c4=0) energy is minimised at L -> 0 (COLLAPSE); the quartic
"third" term c4>0 gives a finite minimiser L* = sqrt(c4 E4 / (c2 E2)) -- a stable
size. This module supplies the rulers; e012 uses them statically (Q_H, Derrick
landscape) and dynamically (gradient flow).

Conventions: derivatives for the ENERGIES use periodic central differences
(np.roll), which are stable and have a clean adjoint (-D) for the gradient flow.
The Hopf CHARGE is computed spectrally (Whitehead integral Q_H = (1/16 pi^2)
integral A.B, B = curl A) because it is topological and converges to an integer
even where the gradient energy is still UV-sensitive.
"""

import numpy as np


def hopfion_field(L, scale, box):
    """Charge-1 hopfion: stereographic R^3 -> S^3 then the Hopf map S^3 -> S^2.

    Grid is the periodic cube [-box, box)^3 with L points/axis; `scale` sets the
    soliton size (larger scale = larger hopfion). Returns (n, dx) with n of
    shape (3, L, L, L) and |n| = 1.
    """
    x = np.linspace(-box, box, L, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    Xs, Ys, Zs = X / scale, Y / scale, Z / scale
    r2 = Xs ** 2 + Ys ** 2 + Zs ** 2
    den = r2 + 1.0
    Z1 = (2.0 * (Xs + 1j * Ys)) / den
    Z2 = (2.0 * Zs + 1j * (r2 - 1.0)) / den
    n = np.stack([2.0 * (Z1.conj() * Z2).real,
                  2.0 * (Z1.conj() * Z2).imag,
                  np.abs(Z1) ** 2 - np.abs(Z2) ** 2], axis=0)
    n = n / np.linalg.norm(n, axis=0, keepdims=True)
    return n, 2.0 * box / L


def central_diff(n, dx):
    """Periodic central differences; returns [d0 n, d1 n, d2 n] (component-stacked).

    Adjoint is exactly the negation, so the discrete Euler-Lagrange gradient
    assembled from these is consistent with the discrete energy (the gradient
    flow then decreases the energy monotonically -- the e012 sanity check).
    """
    return [(np.roll(n, -1, axis=ax + 1) - np.roll(n, 1, axis=ax + 1)) / (2 * dx)
            for ax in range(3)]


def _cross(a, b):
    return np.stack([a[1] * b[2] - a[2] * b[1],
                     a[2] * b[0] - a[0] * b[2],
                     a[0] * b[1] - a[1] * b[0]], axis=0)


def skyrme_F(n, dn):
    """F_jk = n . (d_j n x d_k n) for j<k; returns dict keyed by (j, k)."""
    return {(j, k): (n * _cross(dn[j], dn[k])).sum(axis=0)
            for j in range(3) for k in range(3) if j < k}


def energy2(dn, dx):
    """Gradient (sigma-model) energy integral |d_i n|^2."""
    return float(sum((dn[j] ** 2).sum() for j in range(3)) * dx ** 3)


def energy4(F, dx):
    """Skyrme (quartic) energy integral sum_{j<k} F_jk^2."""
    return float(sum(F[jk] ** 2 for jk in F).sum() * dx ** 3)


def hopf_charge(n, dx):
    """Whitehead Hopf invariant Q_H = (1/16 pi^2) integral A.B, B = curl A.

    Spectral derivatives (consistent B and A) so Q_H converges to an integer.
    """
    L = n.shape[1]
    k = np.fft.fftfreq(L, d=dx) * 2 * np.pi
    K = np.meshgrid(k, k, k, indexing="ij")
    dn = [np.stack([np.fft.ifftn(1j * K[ax] * np.fft.fftn(n[c])).real
                    for c in range(3)], axis=0) for ax in range(3)]
    F = skyrme_F(n, dn)
    B = [F[(1, 2)], -F[(0, 2)], F[(0, 1)]]
    k2 = K[0] ** 2 + K[1] ** 2 + K[2] ** 2
    k2[0, 0, 0] = 1.0
    Bh = [np.fft.fftn(B[i]) for i in range(3)]
    kxB = [K[1] * Bh[2] - K[2] * Bh[1],
           K[2] * Bh[0] - K[0] * Bh[2],
           K[0] * Bh[1] - K[1] * Bh[0]]
    A = [np.fft.ifftn(1j * kxB[i] / k2).real for i in range(3)]
    AB = sum(A[i] * B[i] for i in range(3)).sum() * dx ** 3
    return float(AB / (16.0 * np.pi ** 2))


def faddeev_energy(n, dx, c2, c4):
    """Total Faddeev-Skyrme energy E = c2*E2 + c4*E4 and the pieces (E2, E4)."""
    dn = central_diff(n, dx)
    E2 = energy2(dn, dx)
    E4 = energy4(skyrme_F(n, dn), dx)
    return c2 * E2 + c4 * E4, E2, E4


def l2_gradient(n, dx, c2, c4):
    """Discrete Euler-Lagrange gradient G = dE/dn (before tangent projection).

    Assembled from the SAME periodic central differences used by the energy, so
    G is consistent with the discrete energy and the gradient flow decreases it
    monotonically (the e012 sanity check). Derivation:
      E2: G2 = -2 c2 sum_i D_i(D_i n)              (discrete Laplacian)
      E4: G4 = P4 - sum_i D_i(Q4_i),
          P4   =  2 c4 sum_{j<k} F_jk (D_j n x D_k n)   (explicit n in F)
          Q4_i = -2 c4 sum_k   F_ik (n x D_k n)         (momentum in D_i n)
    with F_ik = n . (D_i n x D_k n) antisymmetric (F_ii=0, F_ki=-F_ik).
    """
    dn = central_diff(n, dx)
    G = -2.0 * c2 * sum(central_diff(dn[i], dx)[i] for i in range(3))
    if c4 > 0:
        F = [[None] * 3 for _ in range(3)]
        for j in range(3):
            for k in range(3):
                if j < k:
                    F[j][k] = (n * _cross(dn[j], dn[k])).sum(axis=0)
        for j in range(3):
            for k in range(3):
                if j > k:
                    F[j][k] = -F[k][j]
        P4 = np.zeros_like(n)
        for j in range(3):
            for k in range(3):
                if j < k:
                    P4 = P4 + 2.0 * c4 * F[j][k] * _cross(dn[j], dn[k])
        for i in range(3):
            Q4 = np.zeros_like(n)
            for k in range(3):
                if k != i:
                    Q4 = Q4 + (-2.0 * c4) * F[i][k] * _cross(n, dn[k])
            G = G - central_diff(Q4, dx)[i]
        G = G + P4
    return G


def flow_step(n, dx, c2, c4, dt):
    """One tangent-projected gradient-flow step; keeps |n|=1 by renormalising."""
    G = l2_gradient(n, dx, c2, c4)
    G = G - (n * G).sum(axis=0, keepdims=True) * n      # project onto T_n S^2
    n = n - dt * G
    return n / np.linalg.norm(n, axis=0, keepdims=True)


def e4_rms_size(n, dx):
    """RMS radius of the Skyrme (E4) density -- a size that stays meaningful.

    The quartic density localises on the hopfion core even as it moves, so its
    radius of gyration tracks the soliton SIZE; it goes to ~0 only when the
    structure unwinds (collapse). Returns 0.0 for a structureless field.
    """
    dn = central_diff(n, dx)
    F = skyrme_F(n, dn)
    w = sum(F[jk] ** 2 for jk in F)
    tot = w.sum()
    if tot <= 0:
        return 0.0
    L = n.shape[1]
    ax = (np.arange(L) - L / 2) * dx
    X, Y, Z = np.meshgrid(ax, ax, ax, indexing="ij")
    cx, cy, cz = (w * X).sum() / tot, (w * Y).sum() / tot, (w * Z).sum() / tot
    r2 = (X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2
    return float(np.sqrt((w * r2).sum() / tot))


def derrick_curve(E2, E4, c4, c2=1.0, lams=None):
    """Derrick energy E(L) = L*c2*E2 + c4*E4/L and the minimiser L*.

    Returns (lams, E(lams), L_star). For c4=0, L_star is 0 (collapse). For c4>0,
    L_star = sqrt(c4 E4 / (c2 E2)) -- a finite stable size.
    """
    if lams is None:
        lams = np.linspace(0.2, 3.0, 29)
    E = c2 * E2 * lams + (c4 * E4 / lams if c4 > 0 else 0.0 * lams)
    if c4 > 0:
        Lstar = float(np.sqrt(c4 * E4 / (c2 * E2)))
    else:
        Lstar = 0.0
    return lams, E, Lstar
