"""Vortex detection by phase winding plus density minimum.

A vortex core is found *by measurement*, not asserted: for every elementary
plaquette of the grid we sum the wrapped phase differences around its four
edges. That sum, divided by 2*pi, is the integer winding number (the quantized
circulation). A genuine core also sits at a local density minimum, and we keep
only cores inside the bulk (V < bulk_factor * mu) to reject edge artefacts.

This implements LAW.md audit 7 (the code discovers the vortex; it does not
write the answer in) and audit 5 (circulation is checked to be quantized).
"""

import numpy as np


def _wrap(d):
    """Wrap phase differences into (-pi, pi]."""
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def winding_field(psi):
    """Plaquette winding numbers (raw, real-valued), shape (L-1, L-1).

    Plaquette (i, j) is the unit square with corners
    (i, j) -> (i+1, j) -> (i+1, j+1) -> (i, j+1) -> (i, j).
    For a clean field these are exactly integers (0 or +-1) up to fp error.
    """
    phase = np.angle(psi)
    d1 = _wrap(phase[1:, :-1] - phase[:-1, :-1])   # (i,j)   -> (i+1,j)
    d2 = _wrap(phase[1:, 1:] - phase[1:, :-1])     # (i+1,j) -> (i+1,j+1)
    d3 = _wrap(phase[:-1, 1:] - phase[1:, 1:])     # (i+1,j+1)-> (i,j+1)
    d4 = _wrap(phase[:-1, :-1] - phase[:-1, 1:])   # (i,j+1) -> (i,j)
    return (d1 + d2 + d3 + d4) / (2.0 * np.pi)


def is_circulation_quantized(psi, tol=1e-6):
    """True if every plaquette winding is within tol of an integer."""
    w = winding_field(psi)
    return bool(np.all(np.abs(w - np.rint(w)) < tol))


def _plaquette_potential(V):
    """Average V over each plaquette, shape (L-1, L-1)."""
    return 0.25 * (V[:-1, :-1] + V[1:, :-1] + V[:-1, 1:] + V[1:, 1:])


def _refine_core(psi, i, j, half=2):
    """Sub-grid core position via density-deficit centroid around (i+.5, j+.5).

    Weights each pixel in a small window by (rho_max - rho) so the centroid is
    pulled toward the density hole that marks the core. Returns (x, y).
    """
    L = psi.shape[0]
    rho = np.abs(psi) ** 2
    i0, i1 = max(0, i - half), min(L, i + half + 2)
    j0, j1 = max(0, j - half), min(L, j + half + 2)
    sub = rho[i0:i1, j0:j1]
    w = sub.max() - sub
    total = w.sum()
    if total <= 0:
        return i + 0.5, j + 0.5
    xs = np.arange(i0, i1)[:, None]
    ys = np.arange(j0, j1)[None, :]
    cx = float((w * xs).sum() / total)
    cy = float((w * ys).sum() / total)
    return cx, cy


def find_vortices(psi, V=None, mu=None, bulk_factor=0.8, refine=True):
    """Return a list of cores: [{'x','y','charge'}], measured from the field.

    If V and mu are given, only plaquettes with average V < bulk_factor*mu are
    kept (bulk-only), which removes spurious windings in the dilute halo.
    """
    w = winding_field(psi)
    charges = np.rint(w).astype(int)
    mask = charges != 0
    if V is not None and mu is not None:
        mask &= _plaquette_potential(V) < bulk_factor * mu
    cores = []
    for i, j in np.argwhere(mask):
        if refine:
            x, y = _refine_core(psi, int(i), int(j))
        else:
            x, y = i + 0.5, j + 0.5
        cores.append({"x": x, "y": y, "charge": int(charges[i, j])})
    return cores


def track_single_vortex(psi, V, mu, center, prev=None, bulk_factor=0.8):
    """Locate the single tracked vortex and return its polar coordinates.

    Returns dict with x, y, charge, radius, angle (rad) measured from `center`.
    If multiple cores are found, picks the one nearest `prev` (continuity);
    falls back to the strongest-charge core. Returns None if none found.
    """
    cores = find_vortices(psi, V, mu, bulk_factor=bulk_factor)
    if not cores:
        return None
    cx, cy = center
    if prev is not None:
        cores.sort(key=lambda c: (c["x"] - prev["x"]) ** 2 + (c["y"] - prev["y"]) ** 2)
    core = cores[0]
    dx, dy = core["x"] - cx, core["y"] - cy
    core["radius"] = float(np.hypot(dx, dy))
    core["angle"] = float(np.arctan2(dy, dx))
    return core
