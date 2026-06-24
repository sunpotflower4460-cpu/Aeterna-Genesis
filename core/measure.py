"""Measurement instruments: conserved quantities and (later) geometry probes.

These are the "rulers" of LAW.md audit 5 -- agreement with reality is checked
by number, not by eye. For e001 the relevant rulers are the GPE norm and
energy (which the conservative real-time split-step should preserve).
"""

import numpy as np

from .fft import k_squared


def norm(psi, dx=1.0):
    """integral |psi|^2 dV."""
    return float(np.sum(np.abs(psi) ** 2) * dx * dx)


def energy(psi, V, g, dx=1.0):
    """GPE energy functional E = integral[ 1/2|grad psi|^2 + V|psi|^2 + 1/2 g|psi|^4 ].

    Kinetic part is evaluated spectrally via Parseval:
    sum_x |grad psi|^2 = (1/N) sum_k k^2 |psi_hat_k|^2.
    """
    L = psi.shape[0]
    k2 = k_squared(L, dx)
    psi_hat = np.fft.fft2(psi)
    N = psi.size
    kinetic = 0.5 * np.sum(k2 * np.abs(psi_hat) ** 2) / N * dx * dx
    rho = np.abs(psi) ** 2
    potential = np.sum(V * rho) * dx * dx
    interaction = 0.5 * g * np.sum(rho ** 2) * dx * dx
    return float(kinetic + potential + interaction)


def relative_drift(series):
    """Max fractional deviation of a series from its initial value.

    Useful for reporting conservation: relative_drift(norms) ~ 0 means norm is
    conserved. Returns 0.0 for an empty/degenerate series.
    """
    arr = np.asarray(series, dtype=float)
    if arr.size == 0 or arr[0] == 0.0:
        return 0.0
    return float(np.max(np.abs(arr - arr[0]) / np.abs(arr[0])))


def unwrap_cumulative(angles):
    """Cumulative rotation (radians) from a sequence of polar angles.

    Wraps each step difference into (-pi, pi] and accumulates, so a vortex that
    circulates many times produces a monotonically growing total rather than a
    sawtooth. Returns an array the same length as `angles`, starting at 0.
    """
    angles = np.asarray(angles, dtype=float)
    if angles.size == 0:
        return np.array([])
    diffs = np.diff(angles)
    diffs = (diffs + np.pi) % (2.0 * np.pi) - np.pi
    cum = np.concatenate([[0.0], np.cumsum(diffs)])
    return cum
