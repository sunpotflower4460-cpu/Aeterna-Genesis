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


def _reject_non_boolean_mask(mask, label):
    """Raise iff `mask` does not have `dtype == bool` exactly (Codex): every geometry function in
    this module trusts a mask's values as ARITHMETIC (summed for volume, compared across
    neighbors for surface area, labeled by `ndimage.label` for components) -- a labeled or
    weighted numeric array (e.g. `np.full(shape, 2)`) is not a 0/1 selector and silently produces
    false geometry (e.g. `volume` reporting TWICE the true voxel count) instead of failing
    closed. Downstream Gate-I checks rely on voxel counts and fractions of a genuinely BINARY
    vessel mask, so a non-boolean input must never be silently integrated as if it were one."""
    mask_arr = np.asarray(mask)
    if mask_arr.dtype != np.bool_:
        raise ValueError(
            "%s must have dtype bool, got %r -- a numeric/labeled mask is not a 0/1 selector and "
            "would silently produce false geometry instead of failing closed" %
            (label, mask_arr.dtype))
    return mask_arr


def vessel_mask(phi, thresh=0.0):
    """The vessel interior as a boolean mask: phi > thresh.

    `phi` must be entirely finite (Codex): a solver blow-up leaving `NaN`/`inf` cells would
    otherwise be silently classified as outside/inside by the bare `>` comparison (`nan > thresh`
    is always False, `inf > thresh` is always True), letting downstream geometry
    (`connected_components`, `boundary_topology`, `surface_area`, `volume`, split/fusion
    detection -- everything in this module that consumes a mask) report a plausible-looking
    finite result computed from a corrupted interface field instead of failing closed."""
    phi = np.asarray(phi)
    if not np.all(np.isfinite(phi)):
        raise ValueError(
            "vessel_mask: phi contains non-finite values (inf/nan) -- indicates a solver "
            "blow-up, not a valid interface field; must fail closed rather than being silently "
            "classified as inside/outside by the > comparison")
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
    # Vectorized relabel via a lookup table (CodeRabbit): building a per-label mapping array and
    # indexing `lbl` through it is O(V), unlike the O(n_labels * V) cost of masking the full array
    # once per label -- matters on noisy grids with many components.
    max_label = int(lbl.max())
    mapping = np.arange(max_label + 1, dtype=lbl.dtype)
    for label in range(1, max_label + 1):
        mapping[label] = find(label)
    return mapping[lbl]


def connected_components(mask):
    """(n_components, sizes_desc): 6-connected component count and voxel counts, largest first --
    periodic across the domain boundary (a component that crosses a seam counts as ONE object,
    matching the periodic-box vessel model; see `_merge_periodic_labels`). `mask` must have
    `dtype == bool` (see `_reject_non_boolean_mask`, Codex)."""
    mask = _reject_non_boolean_mask(mask, "connected_components: mask")
    lbl, n = ndimage.label(mask)
    if n == 0:
        return 0, []
    lbl = _merge_periodic_labels(lbl, mask)
    # np.bincount (CodeRabbit) is O(V) versus summing a fresh `lbl == label` boolean mask per
    # label (O(n_labels * V)) -- the merged labels are no longer contiguous from 1, so bins for
    # merged-away labels are simply empty and filtered out below.
    counts = np.bincount(lbl.ravel())
    sizes = [int(s) for s in counts[1:] if s > 0]
    return len(sizes), sorted(sizes, reverse=True)


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
    to the domain edge (the F1 V0 / early P10 S1 placement pattern). `mask` must have
    `dtype == bool` (see `_reject_non_boolean_mask`, Codex)."""
    mask = _reject_non_boolean_mask(mask, "boundary_topology: mask")
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
    correction (e.g. marching-cubes) rather than trust this number at face value. `mask` must
    have `dtype == bool` (see `_reject_non_boolean_mask`, Codex)."""
    mask = _reject_non_boolean_mask(mask, "surface_area: mask")
    area_faces = 0
    for ax in range(mask.ndim):
        nb = np.roll(mask, -1, axis=ax)
        area_faces += int(np.sum(mask != nb))
    return float(area_faces) * dx * dx


def volume(mask, dx=1.0):
    """Interior volume: voxel count times dx^3. `mask` must have `dtype == bool` (see
    `_reject_non_boolean_mask`, Codex): a non-boolean mask (e.g. `np.full(shape, 2)`) is summed
    as arithmetic, not counted as a 0/1 selector, and would silently report a false volume."""
    mask = _reject_non_boolean_mask(mask, "volume: mask")
    return float(mask.sum()) * dx ** 3


def volume_fraction(mask):
    """Interior volume as a fraction of the total domain (dx-independent, useful for tracking a
    vessel's relative size/integrity over time or across resolutions). `mask` must have
    `dtype == bool` (see `_reject_non_boolean_mask`, Codex)."""
    mask = _reject_non_boolean_mask(mask, "volume_fraction: mask")
    return float(np.mean(mask))


def _periodic_gradient(phi, dx=1.0):
    """Central-difference gradient with PERIODIC (wraparound) boundary treatment, matching the
    periodic-box vessel model `surface_area`/`connected_components` already assume. Identical to
    `np.gradient`'s formula in the domain INTERIOR (`(f[i+1]-f[i-1])/(2*dx)`, verified to machine
    precision) but wraps at the domain edge instead of `np.gradient`'s default one-sided edge
    difference (Codex: for a vessel that crosses the periodic seam -- the same context
    `connected_components` already supports -- a one-sided edge difference creates an artificial
    gradient discontinuity right at the seam, corrupting `interface_width`/`mean_curvature_field`
    for exactly the cells `connected_components` already treats as a single continuous object)."""
    phi = np.asarray(phi)
    return [(np.roll(phi, -1, axis=ax) - np.roll(phi, 1, axis=ax)) / (2.0 * dx)
            for ax in range(phi.ndim)]


def interface_width(phi, dx=1.0, band_thresh=0.9, eps=1e-9):
    """Estimated diffuse-interface THICKNESS in physical length units (e.g. cells at dx=1),
    intrinsic to the local tanh-like transition profile and INDEPENDENT of vessel size or surface
    area -- NOT a band volume fraction (Codex: `np.mean(|phi|<thresh)` is the interface band's
    share of total domain VOLUME, which shrinks as the vessel grows even at a perfectly constant
    physical interface thickness, e.g. from ~0.15 at R=6 to ~0.06 at R=15 for the identical
    `width=1.5` synthetic sphere -- unusable as a preregistered "interface is 4-6 cells" gate).

    Uses the tanh-profile identity: for phi=tanh(n/w) along the interface normal n, d(phi)/dn =
    (1-phi^2)/w, so w(x) = (1-phi(x)^2) / |grad phi(x)| recovers the LOCAL width at every point,
    averaged over the diffuse interface band |phi|<band_thresh. Verified to recover the exact
    `width` parameter of `vessel_permeability.radial_phi`'s synthetic spheres to <1% regardless
    of R. NaN if the band is empty. Uses a periodic gradient (see `_periodic_gradient`), so a
    vessel that crosses the domain seam still measures the same intrinsic width as one placed
    away from any boundary."""
    grads = _periodic_gradient(phi, dx)
    mag = np.sqrt(sum(g ** 2 for g in grads)) + eps
    local_width = (1.0 - np.asarray(phi) ** 2) / mag
    band = np.abs(phi) < band_thresh
    return float(local_width[band].mean()) if band.any() else float("nan")


def mean_curvature_field(phi, dx=1.0, eps=1e-9):
    """Discrete mean curvature kappa = -div(grad(phi)/|grad(phi)|) (sum-of-principal-curvatures
    convention, i.e. kappa=2/R for a sphere of radius R, since grad(phi) points INWARD for the
    phi=tanh((R-r)/width) convention used throughout this campaign -- see F1 V0's `radial_phi`).
    Returns the full field; most callers want `mean_curvature` (its interface-band average). Uses
    a periodic gradient/divergence throughout (see `_periodic_gradient`) so a vessel crossing the
    domain seam doesn't pick up an artificial curvature discontinuity there (Codex)."""
    grads = _periodic_gradient(phi, dx)
    mag = np.sqrt(sum(g ** 2 for g in grads)) + eps
    n = [g / mag for g in grads]
    div = sum(_periodic_gradient(ni, dx)[ax] for ax, ni in enumerate(n))
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
    should inspect the labeled components directly (e.g. via `connected_components`).

    `mask_prev`/`mask_curr` must have the SAME shape (Codex): a split/fusion event is a same-grid
    temporal change, so frames accidentally taken from different grid sizes or cropped domains
    must fail closed rather than being compared by component COUNT alone (which `connected_
    components` can still compute on either shape independently, silently reporting a plausible
    but meaningless 'split'/'fusion'/'ambiguous' classification). Both masks must also have
    `dtype == bool` (see `_reject_non_boolean_mask`, Codex)."""
    mask_prev = _reject_non_boolean_mask(mask_prev, "detect_split_fusion: mask_prev")
    mask_curr = _reject_non_boolean_mask(mask_curr, "detect_split_fusion: mask_curr")
    if mask_prev.shape != mask_curr.shape:
        raise ValueError(
            "detect_split_fusion: mask_prev shape %r does not match mask_curr shape %r -- a "
            "split/fusion event can only be measured between two snapshots of the SAME grid" %
            (mask_prev.shape, mask_curr.shape))
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
