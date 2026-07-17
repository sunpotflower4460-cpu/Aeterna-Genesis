#!/usr/bin/env python3
"""Boundary-geometry diagnostics for the Active Vessel white (P10, PR-1 measurement suite, role V).

WHAT IT IS
Pure measurement functions on a GIVEN phi (or mask) snapshot: connected components, closed-surface
topology, surface area, volume, diffuse-interface width, mean curvature, and a coarse split/fusion
detector between two consecutive frames. No physics model, no time integration, no emergence claim
-- this module answers "what shape is the vessel right now", nothing about how it got there.

Reuses `genesis.diagnostics.topology_betti.betti3d` (Topology Instrument v1) for Betti numbers /
genus rather than reimplementing cubical-complex homology (no_touch discipline: additive sibling,
not a rewrite).

VALIDATION
All functions are checked against ANALYTICALLY KNOWN synthetic geometry (spheres of known radius)
in `tests/test_vessel_geometry_3d.py`; no threshold here was tuned after seeing P10 physics data.
"""
import numpy as np
from scipy import ndimage

from genesis.diagnostics.topology_betti import betti3d


def vessel_mask(phi, thresh=0.0):
    """The vessel interior as a boolean mask: phi > thresh."""
    return phi > thresh


def _merge_periodic_labels(lbl, mask):
    """Union `ndimage.label`'s (non-periodic) labels across the domain's periodic boundary faces:
    for the periodic-box vessel model this campaign uses (`surface_area` already treats the
    domain as periodic via `np.roll`), a component that crosses a seam is ONE object, but
    `ndimage.label` alone splits it into two labels since it only sees face-adjacency within the
    array, never wraparound (Codex). Returns a relabeled array with seam-connected labels merged."""
    parent = {}

    def find(x):
        root = x
        while parent.get(root, root) != root:
            root = parent[root]
        while parent.get(x, x) != root:
            parent[x], x = root, parent.get(x, x)
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for ax in range(mask.ndim):
        face0 = [slice(None)] * mask.ndim
        face0[ax] = 0
        face1 = [slice(None)] * mask.ndim
        face1[ax] = -1
        l0 = lbl[tuple(face0)]
        l1 = lbl[tuple(face1)]
        both = (l0 > 0) & (l1 > 0)
        for a, b in zip(l0[both].ravel().tolist(), l1[both].ravel().tolist()):
            union(a, b)

    if not parent:
        return lbl
    out = lbl.copy()
    for label in np.unique(lbl):
        if label == 0:
            continue
        root = find(int(label))
        if root != label:
            out[lbl == label] = root
    return out


def connected_components(mask):
    """(n_components, sizes_desc): 6-connected component count and voxel counts, largest first --
    periodic across the domain boundary (a component that crosses a seam counts as ONE object,
    matching the periodic-box vessel model; see `_merge_periodic_labels`)."""
    lbl, n = ndimage.label(mask)
    if n == 0:
        return 0, []
    lbl = _merge_periodic_labels(lbl, mask)
    labels_present = [int(x) for x in np.unique(lbl) if x != 0]
    sizes = [int((lbl == label).sum()) for label in labels_present]
    return len(labels_present), sorted(sizes, reverse=True)


def boundary_topology(mask):
    """Betti numbers (b0/b1/b2), Euler characteristic, and a closed-single-component flag for a
    vessel mask -- delegates entirely to the validated Topology Instrument v1 (`topology_betti.
    betti3d`); does not reimplement homology.

    KNOWN GAP (documented, not silently papered over): unlike this module's own
    `connected_components` (periodic across the domain boundary, see `_merge_periodic_labels`),
    `topology_betti.betti3d` does not yet implement periodic connectivity, so `b0`/
    `is_closed_single_component` here can disagree with `connected_components`'s count for a
    vessel that touches or crosses the periodic boundary. Fixing this requires updating the
    shared, already-validated Topology Instrument itself (out of this additive PR's no_touch
    scope) -- deferred to a dedicated follow-up. Not a concern for a centered vessel with margin
    to the domain edge (the F1 V0 / early P10 S1 placement pattern)."""
    b = betti3d(mask)
    b["is_closed_single_component"] = bool(b["b0"] == 1 and b["b2"] == 0)
    return b


def surface_area(mask, dx=1.0):
    """Discrete surface area: dx^2 times the count of unit-cube faces where the mask flips across
    a neighbor (periodic wrap included, matching the periodic-box vessel model) -- the standard
    voxel surface-area estimator.

    KNOWN BIAS (documented, not corrected): this axis-aligned face-counting estimator
    systematically OVERESTIMATES a smoothly curved surface's true area by a roughly constant
    factor (~1.5x, empirically stable across R=6..15 for a sphere -- see
    `tests/test_vessel_geometry_3d.py`), because staircased cube faces have more area than the
    smooth surface they approximate. Reported honestly rather than silently corrected: callers
    comparing surface area ACROSS TIME on a fixed grid (e.g. "did the vessel's area grow") get a
    valid relative signal; callers wanting an absolute area estimate should apply an independent
    correction (e.g. marching-cubes) rather than trust this number at face value."""
    area_faces = 0
    for ax in range(mask.ndim):
        nb = np.roll(mask, -1, axis=ax)
        area_faces += int(np.sum(mask != nb))
    return float(area_faces) * dx * dx


def volume(mask, dx=1.0):
    """Interior volume: voxel count times dx^3."""
    return float(mask.sum()) * dx ** 3


def volume_fraction(mask):
    """Interior volume as a fraction of the total domain (dx-independent, useful for tracking a
    vessel's relative size/integrity over time or across resolutions)."""
    return float(np.mean(mask))


def interface_width_fraction(phi, thresh=0.9):
    """Fraction of cells in the diffuse interface band |phi|<thresh -- a resolution- and
    sharpness-sensitive proxy for how diffuse (vs sharp) the boundary currently is."""
    return float(np.mean(np.abs(phi) < thresh))


def mean_curvature_field(phi, dx=1.0, eps=1e-9):
    """Discrete mean curvature kappa = -div(grad(phi)/|grad(phi)|) (sum-of-principal-curvatures
    convention, i.e. kappa=2/R for a sphere of radius R, since grad(phi) points INWARD for the
    phi=tanh((R-r)/width) convention used throughout this campaign -- see F1 V0's `radial_phi`).
    Returns the full field; most callers want `mean_curvature` (its interface-band average)."""
    grads = np.gradient(phi, dx)
    mag = np.sqrt(sum(g ** 2 for g in grads)) + eps
    n = [g / mag for g in grads]
    div = sum(np.gradient(ni, dx, axis=ax) for ax, ni in enumerate(n))
    return -div


def mean_curvature(phi, dx=1.0, band_thresh=0.9, eps=1e-9):
    """Mean curvature averaged over the diffuse interface band |phi|<band_thresh -- a single
    scalar summary of `mean_curvature_field`, NaN if the band is empty."""
    kappa = mean_curvature_field(phi, dx=dx, eps=eps)
    band = np.abs(phi) < band_thresh
    return float(kappa[band].mean()) if band.any() else float("nan")


def detect_split_fusion(mask_prev, mask_curr):
    """Coarse component-count-based event classifier between two consecutive frames: 'none',
    'split', 'fusion', 'appear', 'vanish', or 'ambiguous' (component count unchanged but not
    trivially 'none' -- e.g. a simultaneous split+fusion elsewhere). This is a cheap screening
    signal for automated runs, NOT a definitive topological proof; callers needing certainty
    should inspect the labeled components directly (e.g. via `connected_components`)."""
    n_prev, _ = connected_components(mask_prev)
    n_curr, _ = connected_components(mask_curr)
    if n_prev == n_curr:
        # same component COUNT does not mean nothing happened -- a simultaneous split+fusion
        # elsewhere leaves the count unchanged but the mask itself differs; only report 'none'
        # when the mask is actually unchanged, per this function's own documented 'ambiguous'
        # outcome (Codex finding: the count-only check never actually reached 'ambiguous').
        event = "none" if np.array_equal(mask_prev, mask_curr) else "ambiguous"
    elif n_prev == 0 and n_curr > 0:
        event = "appear"
    elif n_curr == 0 and n_prev > 0:
        event = "vanish"
    elif n_curr > n_prev:
        event = "split"
    elif n_curr < n_prev:
        event = "fusion"
    else:
        event = "ambiguous"
    return dict(n_prev=n_prev, n_curr=n_curr, event=event)
