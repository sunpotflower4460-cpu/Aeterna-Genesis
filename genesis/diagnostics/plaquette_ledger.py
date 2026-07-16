"""Orientation-complete plaquette winding ledger (Loop-Trinity integration, Phase LT-3). role: V.

WHAT IT IS
For a 3D complex field psi, the integer phase winding of every unit plaquette (2x2 corner loop) in all THREE
orientations -- XY (looping over z-slices), YZ (over x-slices), ZX (over y-slices) -- with signed +/-/net/
absolute/invalid counts, per-slice tallies, an amplitude/near-pi reliability gate, and a gauge-invariant map
hash. This localizes complex-phase defects (vortex-line piercings) far better than a single central z-slice.

WHAT IT IS **NOT** (responsibility boundaries -- do not conflate):
- NOT volume Betti. genesis/diagnostics/topology_betti.betti3d measures b0/b1/b2/chi/genus of a MATERIAL region
  (a |psi|^2 level-set mask). This module measures COMPLEX-PHASE winding on plaquettes. Different quantities.
- NOT global line winding. genesis/diagnostics/winding_reliability measures the winding of a whole periodic
  LINE (e.g. a global x-winding W=1). A field can have global line winding W=1 with ZERO local plaquette
  winding everywhere (smooth phase ramp) -- both are reported, never merged. (Regression fixture below.)
- NOT an exact 3D topology proof. A signed plaquette map is a defect BALLOT, not a traced vortex curve; a
  vortex-core graph is a later, explicitly-limited step. Count agreement between two fields is NOT identity.

DISCIPLINE
- Diagnostic only; changes no physics/IC/law/artifact (no_touch; NEW sibling module).
- Gauge-invariant by construction (windings depend only on phase DIFFERENCES), so a global phase offset leaves
  every count unchanged (tested).
- Thresholds (amp_threshold, near_pi_margin) are RETURNED for provenance and per-model preregistration; Loop
  numeric values are not imported. A plaquette is invalid where its min corner amplitude < amp_threshold or any
  of its 4 edges is near +-pi (ambiguous).
- The periodic net=0 accounting only holds for fields periodic in the looped plane; we report net but never
  assert net==0 as a gate on non-periodic data.
"""
import hashlib

import numpy as np

SIGN_CONVENTION = ("plaquette winding = round( [dh(i,j)+dv(i+1,j)-dh(i,j+1)-dv(i,j)] / 2pi ), CCW, "
                   "dh/dv = wrapped forward phase diffs along the two in-plane axes")


def _wrap(d):
    return (d + np.pi) % (2.0 * np.pi) - np.pi


def _slice_ledger(sl, amp_threshold, near_pi_margin):
    """Signed plaquette winding + reliability for one 2D complex slice. Returns per-plaquette arrays."""
    amp = np.abs(sl)
    ph = np.angle(sl)
    dh = _wrap(ph[1:, :] - ph[:-1, :])        # forward diff along axis 0 (shape n0-1, n1)
    dv = _wrap(ph[:, 1:] - ph[:, :-1])        # forward diff along axis 1 (shape n0, n1-1)
    # plaquette (i,j) CCW: +dh[i,j] +dv[i+1,j] -dh[i,j+1] -dv[i,j]  (telescoping shared edges reused)
    loop = dh[:, :-1] + dv[1:, :] - dh[:, 1:] - dv[:-1, :]
    w = np.rint(loop / (2.0 * np.pi)).astype(int)
    # min corner amplitude over the 4 plaquette corners
    corner_min = np.minimum(np.minimum(amp[:-1, :-1], amp[1:, :-1]), np.minimum(amp[:-1, 1:], amp[1:, 1:]))
    # near-pi ambiguous edges touching each plaquette (its 4 bounding edges)
    nph = np.abs(dh) > (np.pi - near_pi_margin)   # horizontal edges
    npv = np.abs(dv) > (np.pi - near_pi_margin)   # vertical edges
    near = nph[:, :-1].astype(int) + nph[:, 1:] + npv[1:, :] + npv[:-1, :]
    valid = (corner_min >= amp_threshold) & (near == 0)
    return w, valid, near


def _orientation(psi, plane_axes, amp_threshold, near_pi_margin):
    """Loop `psi` over the axis NOT in plane_axes, ledger each in-plane slice, aggregate."""
    slice_axis = ({0, 1, 2} - set(plane_axes)).pop()
    ax0, ax1 = plane_axes
    n_slices = psi.shape[slice_axis]
    pos = neg = inval = npq = ntot = 0
    per_slice_abs = []
    wmaps = []
    for s in range(n_slices):
        sl = np.take(psi, s, axis=slice_axis)
        # ensure slice axes are in (ax0, ax1) order
        sl = np.moveaxis(sl, 0, 0)  # sl already 2D with axes = the two non-slice axes in ascending order
        w, valid, near = _slice_ledger(sl, amp_threshold, near_pi_margin)
        vw = w[valid]
        pos += int((vw > 0).sum()); neg += int((vw < 0).sum())
        inval += int((~valid).sum()); npq += int((near > 0).sum()); ntot += int(w.size)
        per_slice_abs.append(int(np.abs(vw).sum()))
        wmaps.append(np.where(valid, w, 0).astype(np.int16))
    absolute = pos + neg
    net = pos - neg
    hsh = hashlib.sha256(b"".join(m.tobytes() for m in wmaps)).hexdigest()[:16]
    return dict(positive=pos, negative=neg, net=net, absolute=absolute, invalid=inval,
                n_plaquettes=ntot, near_pi_plaquettes=npq, per_slice_absolute=per_slice_abs,
                map_hash=hsh), wmaps


def plaquette_ledger(psi, amp_frac=0.2, near_pi_margin=0.15, amp_threshold=None):
    """Full 3-orientation plaquette ledger of a 3D complex field. See module docstring for scope/limits."""
    psi = np.asarray(psi, dtype=np.complex128)
    if psi.ndim != 3:
        raise ValueError("plaquette_ledger requires a 3D complex field; got ndim=%d" % psi.ndim)
    thr = float(amp_threshold) if amp_threshold is not None else float(amp_frac * np.median(np.abs(psi)))
    oris = {}
    total = dict(positive=0, negative=0, net=0, absolute=0, invalid=0, near_pi_plaquettes=0, n_plaquettes=0)
    hashes = []
    for name, axes in (("xy", (0, 1)), ("yz", (1, 2)), ("zx", (0, 2))):
        summ, _wmaps = _orientation(psi, axes, thr, near_pi_margin)
        oris[name] = summ
        for k in ("positive", "negative", "net", "absolute", "invalid", "near_pi_plaquettes", "n_plaquettes"):
            total[k] += summ[k]
        hashes.append(name + ":" + summ["map_hash"])
    near_frac = total["near_pi_plaquettes"] / total["n_plaquettes"] if total["n_plaquettes"] else 0.0
    return dict(
        grid=list(psi.shape), amp_threshold=thr, amp_frac=float(amp_frac), near_pi_margin=float(near_pi_margin),
        orientations=oris, total=total, near_pi_plaquette_fraction=float(near_frac),
        map_hash=hashlib.sha256("|".join(hashes).encode()).hexdigest()[:16],
        sign_convention=SIGN_CONVENTION,
        scope_note=("local complex-phase plaquette winding; NOT volume Betti (topology_betti) and NOT global "
                    "line winding (winding_reliability); not an exact 3D topology proof."),
    )


def ledger_map_distance(psiA, psiB, amp_frac=0.2, near_pi_margin=0.15, amp_threshold=None):
    """Per-orientation count of plaquettes whose (valid) winding differs between two same-shape fields.
    A *position-aware* A/B distance (stronger than comparing total counts). Gauge-invariant."""
    A = np.asarray(psiA, dtype=np.complex128); B = np.asarray(psiB, dtype=np.complex128)
    if A.shape != B.shape or A.ndim != 3:
        raise ValueError("both fields must be 3D with identical shape")
    thrA = float(amp_threshold) if amp_threshold is not None else float(amp_frac * np.median(np.abs(A)))
    thrB = float(amp_threshold) if amp_threshold is not None else float(amp_frac * np.median(np.abs(B)))
    out = {}
    tot = 0
    for name, axes in (("xy", (0, 1)), ("yz", (1, 2)), ("zx", (0, 2))):
        _sa, wa = _orientation(A, axes, thrA, near_pi_margin)
        _sb, wb = _orientation(B, axes, thrB, near_pi_margin)
        diff = int(sum(int(np.count_nonzero(a != b)) for a, b in zip(wa, wb)))
        out[name] = diff; tot += diff
    out["total"] = tot
    return out


# ------------------------------------------------------------------ synthetic controls (known answers)
def _grid(n):
    x = np.arange(n) - (n - 1) / 2.0
    return np.meshgrid(x, x, x, indexing="ij")


def _z_vortex_line(n=20, charge=1):
    """A straight charge-`charge` vortex line along z: e^{i*charge*atan2(y,x)}, uniform in z, tanh core."""
    X, Y, Z = _grid(n)
    amp = np.tanh(np.sqrt(X ** 2 + Y ** 2) / 2.0)
    return amp * np.exp(1j * charge * np.arctan2(Y, X))


def _controls():
    out = []
    n = 20
    # 1. uniform field -> no defects anywhere
    u = np.ones((n, n, n), complex)
    r = plaquette_ledger(u)
    out.append(("uniform_no_defects", r, r["total"]["absolute"] == 0))
    # 2. z vortex line -> shows in XY every slice, ~none in YZ/ZX; net_xy ~ +n
    r = plaquette_ledger(_z_vortex_line(n, +1))
    xy, yz, zx = r["orientations"]["xy"], r["orientations"]["yz"], r["orientations"]["zx"]
    out.append(("z_line_orientation_specific", r,
                xy["net"] >= n - 2 and xy["positive"] >= n - 2 and yz["absolute"] <= 2 and zx["absolute"] <= 2))
    # 3. gauge invariance -> global phase leaves all counts identical
    v = _z_vortex_line(n, +1)
    r0 = plaquette_ledger(v); r1 = plaquette_ledger(np.exp(1j * 0.9) * v)
    out.append(("gauge_invariant", r1, r0["total"] == r1["total"] and r0["map_hash"] == r1["map_hash"]))
    # 4. +/- pair -> net 0, absolute 2 per slice
    X, Y, Z = _grid(n)
    amp = np.tanh(np.sqrt((np.abs(X) - 4) ** 2 + Y ** 2) / 2.0)
    pair = np.exp(1j * (np.arctan2(Y, X - 4) - np.arctan2(Y, X + 4)))
    r = plaquette_ledger(pair * np.ones_like(amp))
    out.append(("pm_pair_net_zero", r, r["orientations"]["xy"]["net"] == 0 and r["orientations"]["xy"]["absolute"] > 0))
    # 5. translation invariance of totals
    v = _z_vortex_line(n, +1)
    r = plaquette_ledger(np.roll(v, 3, axis=0))
    out.append(("translation_invariant", r, r["orientations"]["xy"]["net"] == plaquette_ledger(v)["orientations"]["xy"]["net"]))
    # 6. global line winding != plaquette winding: smooth x-ramp phase -> ZERO plaquette winding everywhere
    X, Y, Z = _grid(n)
    ramp = np.exp(1j * 2 * np.pi * (np.arange(n)[:, None, None] / n) * np.ones((n, n, n)))
    r = plaquette_ledger(ramp)
    out.append(("line_winding_not_plaquette", r, r["total"]["absolute"] == 0))
    return out


if __name__ == "__main__":
    allok = True
    for name, r, ok in _controls():
        allok &= ok
        t = r["total"]
        print("  [%s] %-30s xy(net=%+d abs=%d) total_abs=%d invalid=%d"
              % ("PASS" if ok else "FAIL", name, r["orientations"]["xy"]["net"],
                 r["orientations"]["xy"]["absolute"], t["absolute"], t["invalid"]))
    print("STATUS:", "GREEN" if allok else "RED", "(role V: complex-phase plaquette ledger; no physics changed)")
