"""Complex-field construction and split-step GPE propagators.

Conventions used everywhere in Aeterna-Genesis:
  * The grid is L x L with unit spacing (dx = 1) unless stated otherwise.
  * Indexing is 'ij': axis 0 is the x coordinate, axis 1 is the y coordinate.
  * The trap centre defaults to (L/2, L/2).

The split-step propagators implement the Gross-Pitaevskii equation

    i d psi/dt = [ -1/2 laplacian + V + g|psi|^2 ] psi

with the chemical potential mu subtracted in the potential factor so that the
ground state is stationary (its global phase does not wind in time). This is
the real, faithful field equation of a BEC/superfluid -- it does NOT mention
the result ("precess"); the dynamics emerge from it (see LAW.md, audit 1-2).
"""

import numpy as np

from .fft import fft2, ifft2


def index_grid(L):
    """Return (X, Y) integer-coordinate meshes as floats, indexing='ij'."""
    i = np.arange(L, dtype=float)
    X, Y = np.meshgrid(i, i, indexing="ij")
    return X, Y


def default_center(L):
    """Geometric centre of an L-point grid: (L-1)/2.

    Using the half-integer geometric centre (31.5 for L=64) keeps the trap
    symmetric about the grid and places the imprinted vortex singularity at a
    plaquette centre rather than on a grid node -- a node coincidence would
    smear the measured winding. The radius from this centre to (cx+R0, cy) is
    exactly R0.
    """
    return ((L - 1) / 2.0, (L - 1) / 2.0)


def harmonic_trap(L, Omega, center=None):
    """V(r) = 1/2 Omega^2 r^2, r measured from `center` (default (L-1)/2)."""
    if center is None:
        center = default_center(L)
    X, Y = index_grid(L)
    r2 = (X - center[0]) ** 2 + (Y - center[1]) ** 2
    return 0.5 * Omega ** 2 * r2


def thomas_fermi_amplitude(V, mu):
    """Thomas-Fermi amplitude sqrt(max(0, mu - V))."""
    return np.sqrt(np.maximum(0.0, mu - V))


def vortex_phase(L, charge, center):
    """Single-charge phase field exp(i*charge*atan2(y-cy, x-cx))'s argument.

    Returns the (real) phase angle array; multiply into amplitude with
    np.exp(1j * phase) to imprint a vortex of the given charge at `center`.
    """
    X, Y = index_grid(L)
    cx, cy = center
    return charge * np.arctan2(Y - cy, X - cx)


def initial_vortex_state(L, Omega, mu, R0, charge=1, center=None):
    """Build the e001 initial state: TF amplitude with one imprinted vortex.

    The vortex sits at (cx + R0, cy). Returns (psi, phase0) where phase0 is the
    imprinted phase, kept so imaginary-time relaxation can re-pin the vortex.
    """
    if center is None:
        center = default_center(L)
    cx, cy = center
    V = harmonic_trap(L, Omega, center)
    amp = thomas_fermi_amplitude(V, mu)
    phase0 = vortex_phase(L, charge, (cx + R0, cy))
    psi = amp * np.exp(1j * phase0)
    return psi, phase0


def norm(psi, dx=1.0):
    """Total norm integral integral |psi|^2 dV."""
    return float(np.sum(np.abs(psi) ** 2) * dx * dx)


def renormalize(psi, target_norm, dx=1.0):
    """Scale psi so that norm(psi) == target_norm (amplitude only)."""
    current = norm(psi, dx)
    if current == 0.0:
        return psi
    return psi * np.sqrt(target_norm / current)


# --- split-step propagators ------------------------------------------------
# Real time: i d psi/dt = [-1/2 lap + V + g|psi|^2 - mu] psi
#   potential half-step: psi *= exp(-i (V + g|psi|^2 - mu) dt/2)
#   kinetic full-step:   psi_hat *= exp(-i 1/2 k^2 dt)
# Imaginary time (dt -> -i dtau): same with the i removed (real decaying
# exponentials), used to relax the density into its ground-state profile.


def potential_step_real(psi, V, g, mu, dt):
    rho = np.abs(psi) ** 2
    return psi * np.exp(-1j * (V + g * rho - mu) * (dt * 0.5))


def kinetic_step_real(psi, k2, dt):
    psi_hat = fft2(psi)
    psi_hat *= np.exp(-1j * 0.5 * k2 * dt)
    return ifft2(psi_hat)


def potential_step_imag(psi, V, g, mu, dtau):
    rho = np.abs(psi) ** 2
    return psi * np.exp(-(V + g * rho - mu) * (dtau * 0.5))


def kinetic_step_imag(psi, k2, dtau):
    psi_hat = fft2(psi)
    psi_hat *= np.exp(-0.5 * k2 * dtau)
    return ifft2(psi_hat)


def step_real(psi, V, k2, g, mu, dt):
    """One real-time split-step: potential/2 -> kinetic -> potential/2."""
    psi = potential_step_real(psi, V, g, mu, dt)
    psi = kinetic_step_real(psi, k2, dt)
    psi = potential_step_real(psi, V, g, mu, dt)
    return psi


def step_imag(psi, V, k2, g, mu, dtau):
    """One imaginary-time split-step: potential/2 -> kinetic -> potential/2."""
    psi = potential_step_imag(psi, V, g, mu, dtau)
    psi = kinetic_step_imag(psi, k2, dtau)
    psi = potential_step_imag(psi, V, g, mu, dtau)
    return psi


def step_damped_2d(psi, V, k2, g, mu, dt, gamma):
    """One step of the phenomenologically DAMPED GPE (2D split-step).

        d psi/dt = -(i + gamma) (H - mu) psi,   H = -1/2 lap + V + g|psi|^2

    gamma=0 recovers the conservative GPE; gamma>0 removes energy so the field
    relaxes toward the (broken-symmetry) ground state. This is the standard
    setting for a Kibble-Zurek quench (e008): from white noise the field
    condenses and leaves behind well-separated quantized vortices. Norm is NOT
    conserved for gamma>0 (it is a driven relaxation at fixed mu).
    """
    cf = 1j + gamma
    rho = np.abs(psi) ** 2
    psi = psi * np.exp(-cf * (V + g * rho - mu) * (dt * 0.5))
    psi_hat = fft2(psi)
    psi_hat *= np.exp(-cf * 0.5 * k2 * dt)
    psi = ifft2(psi_hat)
    rho = np.abs(psi) ** 2
    psi = psi * np.exp(-cf * (V + g * rho - mu) * (dt * 0.5))
    return psi


# --- 3D split-step (e003 vortex ring) -------------------------------------
# The potential half-steps are element-wise, so they are reused unchanged; only
# the kinetic step changes fft2 -> fftn over all three axes.

def index_grid_3d(L):
    """Return (X, Y, Z) index meshes on an L^3 grid, indexing='ij'."""
    i = np.arange(L, dtype=float)
    return np.meshgrid(i, i, i, indexing="ij")


def vortex_ring_phase(L, R, charge=1, center=None):
    """Phase of a vortex ring of radius R in the z=cz plane about the z-axis.

    phase = charge * atan2(z - cz, rho - R), rho = sqrt((x-cx)^2+(y-cy)^2).
    The vortex line is the circle rho=R, z=cz -- a closed loop (a torus tube).
    NOTE (honesty): this imprint is not periodic across the z boundary, so a
    static vortex sheet seeds at z~0; experiments track the ring in the bulk.
    """
    if center is None:
        center = ((L - 1) / 2.0,) * 3
    cx, cy, cz = center
    X, Y, Z = index_grid_3d(L)
    rho = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    return charge * np.arctan2(Z - cz, rho - R)


def kinetic_step_real_3d(psi, k2, dt):
    psi_hat = np.fft.fftn(psi)
    psi_hat *= np.exp(-1j * 0.5 * k2 * dt)
    return np.fft.ifftn(psi_hat)


def kinetic_step_imag_3d(psi, k2, dtau):
    psi_hat = np.fft.fftn(psi)
    psi_hat *= np.exp(-0.5 * k2 * dtau)
    return np.fft.ifftn(psi_hat)


def step_real_3d(psi, V, k2, g, mu, dt):
    """One 3D real-time split-step (V may be a scalar 0 for a uniform box)."""
    psi = potential_step_real(psi, V, g, mu, dt)
    psi = kinetic_step_real_3d(psi, k2, dt)
    psi = potential_step_real(psi, V, g, mu, dt)
    return psi


def step_imag_3d(psi, V, k2, g, mu, dtau):
    """One 3D imaginary-time split-step."""
    psi = potential_step_imag(psi, V, g, mu, dtau)
    psi = kinetic_step_imag_3d(psi, k2, dtau)
    psi = potential_step_imag(psi, V, g, mu, dtau)
    return psi
