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


def _reject_invalid_nonneg_field(x, label):
    """Raise iff `x` is not a finite, non-negative, non-boolean real field/scalar -- a
    concentration/rate-constant/rate-multiplier operand of the frozen `k*R*c` reaction-rate
    density is never physically negative or non-finite (Codex): an unchecked solver overshoot or
    `inf` catalyst would otherwise multiply directly into the measured rate field, producing a
    plausible positive or infinite band/bulk readout from corrupted reaction metadata."""
    x_check = np.asarray(x)
    if x_check.dtype == np.bool_:
        raise ValueError("%s must be a real-valued field/scalar, not boolean" % label)
    x_arr = x_check.astype(float)
    if not np.all(np.isfinite(x_arr)):
        raise ValueError("%s contains non-finite values (inf/nan)" % label)
    if np.any(x_arr < 0.0):
        raise ValueError("%s contains negative values -- never physically valid here" % label)
    return x_arr


def reaction_rate_field(c, k, R=1.0):
    """Local reaction rate k*R*c. `R` defaults to spatially uniform (1.0, a true scalar); passing
    a field is the caller's explicit choice to make (never a hidden default that localizes
    reaction sites). A non-scalar `R` must match `c`'s shape EXACTLY (Codex): an incomplete or
    malformed `R` (e.g. a 1-D profile) would otherwise silently broadcast across the full field,
    fabricating a spatial reaction pattern before any localization audit runs, rather than
    failing closed on the shape mismatch.

    `c`, `k`, and `R` are each validated as finite and non-negative (Codex, second finding): the
    frozen `k*R*c` rate is a non-negative real density, so a negative or non-finite operand (a
    solver overshoot in `c`, or an `inf` catalyst rate `k`) must fail closed rather than
    multiplying directly into a plausible-looking measured rate field."""
    c_arr = _reject_invalid_nonneg_field(c, "reaction_rate_field: c")
    if isinstance(k, (bool, np.bool_)) or not np.isfinite(k) or k < 0.0:
        raise ValueError("reaction_rate_field: k must be a finite, non-negative real number, got %r" % (k,))
    R_arr = _reject_invalid_nonneg_field(R, "reaction_rate_field: R")
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
    region is empty or the bulk mean is ~0 (undefined ratio, not silently reported as inf).

    `rate` must have EXACTLY `phi`'s shape (Codex): a stacked extra-dimensional `rate` (e.g. a
    `(L, L, L, n_species)` array) is otherwise still accepted by the `phi`-derived boolean masks
    (NumPy broadcasts the 3-D mask across the trailing axis), and `.mean()` then silently averages
    over the remaining species axis too, reporting a plausible-looking localization ratio for a
    MIXTURE of rates rather than the single per-cell reaction field this diagnostic audits.

    `rate` and `phi` are also validated as finite before any mask/mean is built (Codex, second
    finding): an unchecked `inf` rate confined to the interface band (with an otherwise finite
    bulk) would otherwise return `inf`, which can satisfy ANY `ratio > 1` reaction-localization
    gate on a blown-up run instead of surfacing the corrupted field."""
    rate_check = np.asarray(rate)
    if rate_check.dtype == np.bool_:
        raise ValueError("band_vs_bulk_ratio: rate must be a real-valued field, not boolean")
    rate_arr = rate_check.astype(float)
    if not np.all(np.isfinite(rate_arr)):
        raise ValueError("band_vs_bulk_ratio: rate contains non-finite values (inf/nan)")
    phi_check = np.asarray(phi)
    if phi_check.dtype == np.bool_:
        raise ValueError("band_vs_bulk_ratio: phi must be a real-valued field, not boolean")
    phi_arr = phi_check.astype(float)
    if not np.all(np.isfinite(phi_arr)):
        raise ValueError("band_vs_bulk_ratio: phi contains non-finite values (inf/nan)")
    if rate_arr.shape != phi_arr.shape:
        raise ValueError(
            "band_vs_bulk_ratio: rate shape %r does not match phi's shape %r -- a real "
            "single-field measurement must match exactly, not merely be mask-broadcast-compatible"
            % (rate_arr.shape, phi_arr.shape))
    band = np.abs(phi_arr) < band_thresh
    if bulk_region == "outside":
        bulk = phi_arr < -band_thresh
    elif bulk_region == "inside":
        bulk = phi_arr > band_thresh
    else:
        raise ValueError("bulk_region must be 'outside' or 'inside'")
    if not band.any() or not bulk.any():
        return float("nan")
    bulk_mean = float(rate_arr[bulk].mean())
    if abs(bulk_mean) < 1e-12:
        return float("nan")
    return float(rate_arr[band].mean()) / bulk_mean


def radial_reaction_profile(rate, phi, n_bins=20, phi_range=(-1.0, 1.0)):
    """Mean reaction rate binned by phi value -- a full inside/interface/outside profile rather
    than a single ratio, for seeing exactly where (in phi-space) the reaction sits. Returns
    (bin_centers, mean_rate_per_bin); empty bins report NaN, never a silently-dropped zero.
    Values of `phi` OUTSIDE `phi_range` are EXCLUDED, not folded into the edge bins -- clipping
    them in would let out-of-range cells masquerade as edge-bin data when a caller narrows
    `phi_range` to inspect the interface region specifically.

    `rate` and `phi` must share the EXACT SAME shape, not merely the same element count (Codex):
    a reshaped or transposed `rate` array with the same size but a different shape would otherwise
    still `.ravel()` successfully and get binned against unrelated `phi` cells via the shared flat
    index, producing a plausible-looking but spatially scrambled localization profile instead of
    failing closed on the shape mismatch."""
    rate_arr = np.asarray(rate)
    phi_arr = np.asarray(phi)
    if rate_arr.shape != phi_arr.shape:
        raise ValueError(
            "radial_reaction_profile: rate shape %r does not match phi's shape %r -- both must "
            "describe the same grid cells in the same layout, not merely the same element count" %
            (rate_arr.shape, phi_arr.shape))
    edges = np.linspace(phi_range[0], phi_range[1], n_bins + 1)
    phi_flat = phi_arr.ravel()
    flat = rate_arr.ravel()
    in_range = (phi_flat >= phi_range[0]) & (phi_flat <= phi_range[1])
    idx = np.clip(np.digitize(phi_flat[in_range], edges) - 1, 0, n_bins - 1)
    vals = flat[in_range]
    means = np.array([vals[idx == b].mean() if np.any(idx == b) else np.nan for b in range(n_bins)])
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, means
