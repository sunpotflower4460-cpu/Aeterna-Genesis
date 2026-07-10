#!/usr/bin/env python3
"""Measurement-based emergence diagnostics (genesis/registry/diagnostics.yaml).

Level is decided by NUMBERS, not by looking at an image (EMERGENCE_LEVELS.md). These are the reference
diagnostics the Runner records; each returns a plain float/int so it can go straight into emergence.json.
"""

import numpy as np


def mean_amplitude(psi):
    """Mean field amplitude <|psi|> -- the order-parameter magnitude (Level 1: rises from the noise floor
    to O(1) as the disordered state symmetry-breaks)."""
    return float(np.mean(np.abs(psi)))


def amplitude_variance(psi):
    """Spatial variance of |psi| (recorded; note it is non-monotonic once |psi| saturates to ~1 uniformly,
    so the Level-1 gate uses mean-amplitude GROWTH + a structure-factor peak, not this)."""
    return float(np.var(np.abs(psi)))


def structure_factor_peak(psi):
    """Return (peak_k, peak_over_mean): radial |FFT|^2 peak position and its prominence.

    A peak at k>0 that is prominent over the mean is the Level-1 signature of a characteristic wavelength.
    """
    f = np.fft.fftn(psi - psi.mean())
    S = np.abs(f) ** 2
    # radial wavenumber grid
    ks = [np.fft.fftfreq(n) * n for n in psi.shape]
    grids = np.meshgrid(*ks, indexing="ij")
    kr = np.sqrt(sum(g ** 2 for g in grids))
    kbin = kr.round().astype(int)
    nb = kbin.max() + 1
    radial = np.bincount(kbin.ravel(), weights=S.ravel(), minlength=nb)
    counts = np.bincount(kbin.ravel(), minlength=nb)
    radial = radial / np.maximum(counts, 1)
    if nb <= 2:
        return 0.0, 0.0
    prof = radial[1:]                       # drop k=0 (mean)
    peak_idx = int(np.argmax(prof)) + 1
    mean_pos = float(prof.mean()) if prof.size else 0.0
    prom = float(radial[peak_idx] / mean_pos) if mean_pos > 0 else 0.0
    return float(peak_idx), prom


def winding_defect_count(psi):
    """Count phase-winding defects (Level 2: topological, not mere low density).

    2D: number of plaquettes whose summed wrapped phase differences ~ +/-2*pi (point vortices).
    3D: number of voxels pierced by a vortex line, detected as plaquette winding on the (x,y) faces
        summed over z (a lower-bound proxy for vortex-line length).
    """
    theta = np.angle(psi)

    def _wrap(d):
        return (d + np.pi) % (2 * np.pi) - np.pi

    amp = np.abs(psi)
    thr = 0.25 * float(amp.max()) if amp.size else 0.0   # mask disordered near-zero regions (noise phase)
    if psi.ndim == 2:
        return _plaquette_defects(theta, amp, thr)
    if psi.ndim == 3:
        total = 0
        for z in range(theta.shape[2]):
            total += _plaquette_defects(theta[:, :, z], amp[:, :, z], thr)
        return total
    return 0


def _plaquette_defects(theta, amp, thr):
    a = theta
    b = np.roll(theta, -1, 0)
    c = np.roll(np.roll(theta, -1, 0), -1, 1)
    d = np.roll(theta, -1, 1)

    def wrap(x):
        return (x + np.pi) % (2 * np.pi) - np.pi

    circ = wrap(b - a) + wrap(c - b) + wrap(d - c) + wrap(a - d)
    winding = np.round(circ / (2 * np.pi)).astype(int)
    # only count windings whose plaquette sits in the ORDERED bulk (mean corner amplitude above threshold);
    # a vortex core is low-amplitude but its surrounding plaquette is ordered, whereas pure noise is not.
    mean4 = 0.25 * (amp + np.roll(amp, -1, 0) + np.roll(np.roll(amp, -1, 0), -1, 1) + np.roll(amp, -1, 1))
    return int(np.count_nonzero((winding != 0) & (mean4 > thr)))


def assess_level(traj):
    """Given per-snapshot dicts (mean_amp, sk_prom, defects), decide the reached Level BY NUMBERS.

    traj[i] = {"mean_amp": float, "sk_prom": float, "defects": int}
    Level 1 (difference): the order parameter emerges from the disordered start -- mean amplitude grows
      well above the noise floor AND a structure-factor peak stands at k>0.
    Level 2 (localization): phase-winding defects form AND persist to the run's tail.
    Returns (reached_level, detected_dict, measured_by_dict).
    """
    a0 = traj[0]["mean_amp"] + 1e-30
    aN = traj[-1]["mean_amp"]
    amp_growth = float(aN / a0)
    sk_prom = float(traj[-1]["sk_prom"])
    defects = int(traj[-1]["defects"])
    tail = traj[max(1, 2 * len(traj) // 3):]
    persistent_defects = all(s["defects"] > 0 for s in tail) if tail else False

    difference = bool(amp_growth > 5.0 and sk_prom > 1.5)       # Level 1
    localization = bool(defects > 0 and persistent_defects)     # Level 2
    reached = 0
    if difference:
        reached = 1
    if difference and localization:
        reached = 2
    detected = {"difference": difference, "localization": localization}
    measured_by = {"mean_amplitude_growth": round(amp_growth, 4),
                   "structure_factor_prominence": round(sk_prom, 4),
                   "defect_count": defects,
                   "persistent_defects": persistent_defects}
    return reached, detected, measured_by
