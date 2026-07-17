#!/usr/bin/env python3
"""Reaction-localization diagnostics for the Active Vessel white (P10, PR-1, role V).

WHAT IT IS
Measures WHERE a reaction is occurring relative to a vessel boundary, from a given field snapshot.
The reaction rate `R` is NEVER assumed localized by this module -- localization (if any) must be
MEASURED as a consequence of species partitioning, never placed at the interface by construction
(this is the target-encoding guard external review found on the F0: "reaction sites must not be
pre-registered at the interface", Codex #2, 2026-07-17). Callers pass whatever `R` their physics
run actually used (uniform by default per the F0's frozen `R=const` design) and this module reports
the resulting spatial pattern honestly, without assuming where it will land.

WHAT IT IS NOT
Not a physics model -- no reaction is integrated here, only measured from a snapshot the caller
already produced.
"""
import numpy as np


def reaction_rate_field(c, k, R=1.0):
    """Local reaction rate k*R*c. `R` defaults to spatially uniform (1.0, a true scalar); passing
    a field is the caller's explicit choice to make (never a hidden default that localizes
    reaction sites). A non-scalar `R` must match `c`'s shape EXACTLY (Codex): an incomplete or
    malformed `R` (e.g. a 1-D profile) would otherwise silently broadcast across the full field,
    fabricating a spatial reaction pattern before any localization audit runs, rather than
    failing closed on the shape mismatch."""
    c_arr = np.asarray(c)
    R_arr = np.asarray(R)
    if R_arr.ndim != 0 and R_arr.shape != c_arr.shape:
        raise ValueError(
            "reaction_rate_field: non-scalar R has shape %r, which does not match c's shape %r "
            "-- a real per-cell R must match exactly, not merely broadcast" %
            (R_arr.shape, c_arr.shape))
    return k * R_arr * c_arr


def band_vs_bulk_ratio(rate, phi, band_thresh=0.5, bulk_region="outside"):
    """Mean reaction rate in the interface band |phi|<band_thresh versus a bulk reference region
    (bulk_region='outside': phi<-band_thresh, or 'inside': phi>band_thresh). A ratio > 1 means
    reaction concentrates near the vessel boundary -- an EMERGENT readout of species partitioning,
    not something placed by construction (R itself may be perfectly uniform). NaN if either
    region is empty or the bulk mean is ~0 (undefined ratio, not silently reported as inf)."""
    band = np.abs(phi) < band_thresh
    if bulk_region == "outside":
        bulk = phi < -band_thresh
    elif bulk_region == "inside":
        bulk = phi > band_thresh
    else:
        raise ValueError("bulk_region must be 'outside' or 'inside'")
    if not band.any() or not bulk.any():
        return float("nan")
    bulk_mean = float(rate[bulk].mean())
    if abs(bulk_mean) < 1e-12:
        return float("nan")
    return float(rate[band].mean()) / bulk_mean


def radial_reaction_profile(rate, phi, n_bins=20, phi_range=(-1.0, 1.0)):
    """Mean reaction rate binned by phi value -- a full inside/interface/outside profile rather
    than a single ratio, for seeing exactly where (in phi-space) the reaction sits. Returns
    (bin_centers, mean_rate_per_bin); empty bins report NaN, never a silently-dropped zero.
    Values of `phi` OUTSIDE `phi_range` are EXCLUDED, not folded into the edge bins -- clipping
    them in would let out-of-range cells masquerade as edge-bin data when a caller narrows
    `phi_range` to inspect the interface region specifically."""
    edges = np.linspace(phi_range[0], phi_range[1], n_bins + 1)
    phi_flat = phi.ravel()
    flat = np.asarray(rate).ravel()
    in_range = (phi_flat >= phi_range[0]) & (phi_flat <= phi_range[1])
    idx = np.clip(np.digitize(phi_flat[in_range], edges) - 1, 0, n_bins - 1)
    vals = flat[in_range]
    means = np.array([vals[idx == b].mean() if np.any(idx == b) else np.nan for b in range(n_bins)])
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, means
