"""Holonomy: winding and circulation read on a closed loop (LAW.md audit 5/7).

A winding number is the quantized phase circulation on a loop -- an integer read
*by measurement* (summed wrapped phase increments / 2*pi around a circle), never
asserted. Unlike ``core.vortex.winding_field`` (per-plaquette, whole grid), this
module reads a single named loop of radius ``R`` about a chosen centre, which is
how a "receiver" reads the charge it encloses.

    winding_around(phase, cx, cy, R)  winding of a real phase field on a CCW circle
    ring_winding(psi, cx, cy, R)      same, from a complex field (phase = angle psi)
    circulation(psi, cx, cy, R, dR)   tangential current Im(conj psi grad psi) on a ring

THE TRAP (designer hit it, we avoid it): the loop MUST be traversed
counter-clockwise (CCW). A clockwise loop flips the sign of every winding, so a
clean +1 vortex would read -1 and a noise-free field could mis-report "0%".
Phase increments are wrapped into (-pi, pi]. The reading loop must enclose
exactly ONE hole -- the winding equals the enclosed vortex charge, so a radius
that straddles two cores mixes them.

Floors: a pixel-sampled circle (integer grid indices) reads winding exactly for
a well-separated core but blurs if two cores sit within a pixel of the ring;
periodic wrap of indices assumes the loop lies inside the array. Winding is a
topological label of a phase field -- naming it "identity" or "self" is analogy
(kept out of this module; see the experiments' AUDIT.md).
"""

import numpy as np


def _wrap(d):
    """Wrap phase differences into (-pi, pi]."""
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def _ring_indices(shape, cx, cy, R, n):
    """Integer grid indices of ``n`` points on a CCW circle (cx,cy,R).

    ``cx`` indexes axis 0, ``cy`` indexes axis 1 (meshgrid indexing='ij').
    The angle sweeps 0 -> 2*pi counter-clockwise; indices wrap periodically.
    """
    a = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)      # CCW
    xi = np.rint(cx + R * np.cos(a)).astype(int) % shape[0]
    yi = np.rint(cy + R * np.sin(a)).astype(int) % shape[1]
    return xi, yi


def winding_around(phase, cx, cy, R, n=600):
    """Winding number of a real phase field on the CCW circle (cx, cy, R).

    Sums the wrapped phase increments around the closed loop and divides by
    2*pi: an integer for a clean field, the net enclosed vortex charge.
    """
    xi, yi = _ring_indices(phase.shape, cx, cy, R, n)
    ph = phase[xi, yi]
    d = _wrap(np.diff(np.concatenate([ph, ph[:1]])))
    return float(np.sum(d) / (2.0 * np.pi))


def ring_winding(psi, cx, cy, R, n=600):
    """Winding read from a complex field psi (phase = angle(psi))."""
    return winding_around(np.angle(psi), cx, cy, R, n=n)


def circulation(psi, cx, cy, R, dR=6.0):
    """Mean tangential current on the annulus |r - R| < dR about (cx, cy).

    The current density j = Im(conj(psi) grad psi); its component along the CCW
    tangent (-sin th, cos th) is the "reading" of a permanent circulating flow.
    Returns 0.0 if the annulus is empty.
    """
    gx, gy = np.gradient(psi)
    jx = np.imag(np.conj(psi) * gx)
    jy = np.imag(np.conj(psi) * gy)
    ii, jj = np.mgrid[0:psi.shape[0], 0:psi.shape[1]]
    dx = ii - cx
    dy = jj - cy
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    ring = np.abs(r - R) < dR
    if not ring.any():
        return 0.0
    tang = jx * (-np.sin(th)) + jy * np.cos(th)
    return float(np.mean(tang[ring]))
