#!/usr/bin/env python3
"""3D-specific diagnostics + a 3D AUTHENTICITY audit -- the honesty keystone for the 3D-native turn.

A field of shape (Nx,Ny,Nz) is not automatically "really 3D": it could be a 2D pattern stacked/extruded
along z. And some quantities are IDENTICALLY ZERO in 2D (helicity, out-of-plane structure), so measuring
them proves genuine 3D physics. This module measures:
  - out_of_plane_variation : is the field genuinely varying along an axis (not extruded)?
  - three_axis_percolation : does the largest connected structure span ALL three axes?
  - helicity               : integral of u.(curl u) -- 0 for any 2D-embedded flow, != 0 for a helical/
                             chiral (e.g. Beltrami) flow -> a genuinely-3D, chirality-sensitive invariant.
  - three_d_authenticity   : an audit dict a room/AI run must pass before claiming "3D".

Not in `measures.py` (no_touch); this is an additive 3D toolkit usable by any 3D white (incl. the ported
Genesis-Room- models). 物理量を先に、意味ラベルは後.
"""
import numpy as np


def _mag(field):
    return np.abs(field) if np.iscomplexobj(field) else np.asarray(field, float)


def out_of_plane_variation(field, axis=-1):
    """Fraction of the field's variance that shows up as change ALONG `axis` (mean-squared adjacent-slice
    difference / total variance). ~0 => extruded/stacked-2D (fake 3D); > tol => genuinely varies along axis."""
    f = _mag(field)
    d = np.diff(f, axis=axis)
    return float(np.mean(d ** 2) / (np.var(f) + 1e-30))


def three_axis_percolation(mask):
    """Does the LARGEST connected component of `mask` span the domain along every axis? Returns
    {spans_all, span_frac (per axis), n_components}. A genuinely 3D space-filling network spans all axes;
    a stack of separate 2D blobs does not."""
    from scipy import ndimage
    mask = np.asarray(mask, bool)
    lbl, n = ndimage.label(mask)
    if n == 0:
        return {"spans_all": False, "span_frac": [0.0] * mask.ndim, "n_components": 0}
    sizes = np.bincount(lbl.ravel())[1:]
    big = 1 + int(np.argmax(sizes))
    coords = np.argwhere(lbl == big)
    span_frac = [float((coords[:, ax].max() - coords[:, ax].min() + 1) / mask.shape[ax])
                 for ax in range(mask.ndim)]
    return {"spans_all": bool(all(s > 0.9 for s in span_frac)), "span_frac": span_frac,
            "n_components": int(n)}


def _d(f, ax, dx):
    return (np.roll(f, -1, ax) - np.roll(f, 1, ax)) / (2.0 * dx)


def curl(ux, uy, uz, dx=1.0):
    """Periodic central-difference curl of a 3-component vector field on a 3D grid (axes x=0,y=1,z=2)."""
    wx = _d(uz, 1, dx) - _d(uy, 2, dx)
    wy = _d(ux, 2, dx) - _d(uz, 0, dx)
    wz = _d(uy, 0, dx) - _d(ux, 1, dx)
    return wx, wy, wz


def helicity(ux, uy, uz, dx=1.0):
    """Mean helicity density u.(curl u). Identically ~0 for any 2D-embedded flow (uz=0 and no z-dependence);
    non-zero for a helical/chiral flow (e.g. a Beltrami/ABC flow) -- a genuinely-3D, parity-odd invariant
    (the physical root of 'DNA-like twist')."""
    wx, wy, wz = curl(ux, uy, uz, dx)
    return float(np.mean(ux * wx + uy * wy + uz * wz))


def three_d_authenticity(field, axis=-1, extrude_tol=1e-3):
    """Audit whether `field` is a GENUINE 3D structure, not a stacked-2D extrusion. Returns a machine-readable
    dict; `genuinely_3d` requires a 3D array whose variation along `axis` exceeds `extrude_tol`."""
    f = _mag(field)
    full_volume = bool(f.ndim == 3)
    oop = out_of_plane_variation(f, axis=axis) if full_volume else 0.0
    extruded = bool(full_volume and oop < extrude_tol)
    return {"full_volume": full_volume, "z_variation_fraction": round(oop, 6),
            "extruded_from_2d": extruded, "z_derivatives_active": bool(oop >= extrude_tol),
            "genuinely_3d": bool(full_volume and not extruded)}
