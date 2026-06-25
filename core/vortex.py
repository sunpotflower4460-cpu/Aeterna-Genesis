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


def _plaquette_average(a):
    """Average a scalar field over each unit plaquette, shape (L-1, L-1)."""
    return 0.25 * (a[:-1, :-1] + a[1:, :-1] + a[:-1, 1:] + a[1:, 1:])


def _plaquette_potential(V):
    """Average V over each plaquette, shape (L-1, L-1)."""
    return _plaquette_average(V)


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


def _plaquette_density(psi):
    """Average |psi|^2 over each plaquette, shape (L-1, L-1)."""
    return _plaquette_average(np.abs(psi) ** 2)


def count_defects(psi, frac=0.1):
    """Count quantized point vortices in a condensate, by MEASUREMENT.

    A plaquette is a genuine vortex core when (a) its phase winding is nonzero
    AND (b) its minimum-corner density falls below `frac` times the mean
    density -- the density depletion that distinguishes a real core from a
    sound-wave phase wrinkle. Returns (n_defects, net_winding).

    This is the Kibble-Zurek counter (e008): on a turbulent post-quench field a
    bare winding count would be swamped by sound, so the density gate is what
    makes "vortices emerged" a measured statement, not a noise artefact.
    """
    w = np.rint(winding_field(psi)).astype(int)
    rho = np.abs(psi) ** 2
    corner_min = np.minimum.reduce([rho[:-1, :-1], rho[1:, :-1],
                                    rho[:-1, 1:], rho[1:, 1:]])
    mask = (w != 0) & (corner_min < frac * rho.mean())
    return int(mask.sum()), int(w[mask].sum())


def track_two_vortices(psi, prev_positions, signs, window=8):
    """Continuity-track two vortices, each within +-window of its last position.

    For each (prev_position, target_sign) pair, search only the +-window box of
    plaquettes around the previous position for cells whose winding has the
    target sign, and pick -- by *continuity* -- the matching-sign core NEAREST
    to that vortex's own previous position. The position is then sub-grid
    refined.

    Continuity (nearest-to-prev), rather than "deepest density in the window",
    is what preserves vortex IDENTITY when the two search windows overlap: each
    vortex follows its own trajectory and the labels cannot swap (a swap would
    flip the connecting-line angle by 180 deg and corrupt the rotation). The two
    vortices are also forbidden from selecting the same plaquette (`taken`), so a
    pair that drifts together cannot collapse to a spurious zero separation.

    Searching locally per vortex -- rather than scanning the whole grid -- also
    rejects the sound-wave false cores a global scan would pick up
    (LAW.md audit 4/7: measured, not asserted).

    The window does NOT wrap across the periodic boundary; the experiments keep
    both cores well away from the edges, and a core that approaches the boundary
    simply ends the clean window (handled by the caller's separation guard).

    Args:
        prev_positions: iterable of (x, y) for each vortex's last known position.
        signs:          iterable of target charges (+1 / -1), same length/order.
        window:         half-width (in grid cells) of the local search box.

    Returns a list (same order) of {'x','y','charge'} dicts, or None for a
    vortex that has no matching-sign core left in its window (left the clean
    window / annihilated).
    """
    charges = np.rint(winding_field(psi)).astype(int)
    n = charges.shape[0]  # L - 1
    taken = set()
    out = []
    for (px, py), s in zip(prev_positions, signs):
        pi, pj = int(round(px)), int(round(py))
        target = 1 if s > 0 else -1
        i0, i1 = max(0, pi - window), min(n, pi + window + 1)
        j0, j1 = max(0, pj - window), min(n, pj + window + 1)
        cand = np.argwhere(charges[i0:i1, j0:j1] == target)
        best, best_d = None, np.inf
        for a, b in cand:
            i, j = i0 + int(a), j0 + int(b)
            if (i, j) in taken:
                continue  # the other vortex already owns this core
            d = (i + 0.5 - px) ** 2 + (j + 0.5 - py) ** 2  # nearest to prev
            if d < best_d:
                best_d, best = d, (i, j)
        if best is None:
            out.append(None)
            continue
        taken.add(best)
        x, y = _refine_core(psi, best[0], best[1])
        out.append({"x": x, "y": y, "charge": int(charges[best])})
    return out


def track_ring_cross_section(psi_slice, axis_coord, prev_outer, prev_inner,
                             axial_bounds):
    """Track a vortex ring via its two cross-section cores in a 2D slice.

    A vortex ring pierces a meridional plane (here the x-z plane through the
    symmetry axis) as TWO opposite-winding cores: a +1 core on one side of the
    axis and a -1 core on the other. Their distance from the axis gives the ring
    RADIUS; their mean axial coordinate gives the ring's AXIAL POSITION. We pick
    each core by continuity (nearest to its previous position) and restrict the
    axial coordinate to `axial_bounds` to exclude the static boundary sheet that
    the (non-periodic) ring imprint seeds near z~0 (see e003 AUDIT, honesty).

    Args:
        psi_slice:   2D complex array; axis 0 = radial coord, axis 1 = axial (z).
        axis_coord:  position of the symmetry axis along axis 0 (cx).
        prev_outer:  (coord0, coord1) previous +1 core position.
        prev_inner:  previous -1 core position.
        axial_bounds: (lo, hi) allowed range on axis 1 (exclude boundary).

    Returns {'radius','axial','outer','inner'} or None if either core is lost.
    """
    charges = np.rint(winding_field(psi_slice)).astype(int)
    lo, hi = axial_bounds

    def pick(target, prev):
        best, best_d = None, np.inf
        for a, b in np.argwhere(charges == target):
            zc = b + 0.5
            if zc < lo or zc > hi:
                continue
            d = (a + 0.5 - prev[0]) ** 2 + (b + 0.5 - prev[1]) ** 2
            if d < best_d:
                best_d, best = d, (a + 0.5, b + 0.5)
        return best

    outer = pick(+1, prev_outer)
    inner = pick(-1, prev_inner)
    if outer is None or inner is None:
        return None
    # the two cross-section cores must straddle the axis (one each side); if both
    # land on the same side (e.g. a boundary-sheet core intruded) the radius would
    # be meaningless -- reject so the caller ends the clean window.
    if (outer[0] - axis_coord) * (inner[0] - axis_coord) >= 0:
        return None
    radius = 0.5 * (abs(outer[0] - axis_coord) + abs(inner[0] - axis_coord))
    axial = 0.5 * (outer[1] + inner[1])
    return {"radius": float(radius), "axial": float(axial),
            "outer": outer, "inner": inner}
