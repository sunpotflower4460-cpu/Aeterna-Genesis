"""M2 -> 3D: the coupled-spectrum measurement machinery is now dimension-aware. In 3D it uses THREE
translation Goldstones (Tx,Ty,Tz) and classifies angular content by SPHERICAL-HARMONIC degree ell
(0=breathing, 1=translation/drift, 2=split) -- so the same drift-before-split logic (ell=1 before ell=2)
works in 3D. These tests validate the 3D machinery on analytically-known fields and check the 3D code path
runs end-to-end; a full 3D drift measurement awaits a 3D stable-spot white (future M2-E-3D). no_touch."""
import numpy as np

from genesis.diagnostics import coupled_spectrum as cs
from genesis.models.adapters.state_layout import StateLayout


def _bump3d(N, w=6.0):
    x = np.arange(N) - N / 2
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    r2 = X ** 2 + Y ** 2 + Z ** 2
    return X, Y, Z, r2, np.exp(-r2 / (2 * w ** 2))


def test_angular_content_3d_classifies_spherical_degree():
    N = 40
    X, Y, Z, r2, g = _bump3d(N)
    c = (N / 2, N / 2, N / 2)
    assert cs.angular_content(g, c, 1.0)[0] == 0                 # monopole / breathing
    assert cs.angular_content(X * g, c, 1.0)[0] == 1             # dipole / translation
    assert cs.angular_content((3 * Z ** 2 - r2) * g, c, 1.0)[0] == 2  # quadrupole / split


def test_translation_modes_3d_count_and_orthonormal():
    N = 24
    _, _, _, _, g = _bump3d(N)
    lay = StateLayout(("u",), ((N, N, N),))
    trans = cs.translation_modes([g], 1.0, lay)
    assert len(trans) == 3                                       # Tx, Ty, Tz
    for T in trans:
        assert abs(lay.inner(T, T) - 1.0) < 1e-6                 # unit-normalised
    # distinct axes are ~orthogonal
    assert abs(lay.inner(trans[0], trans[1])) < 1e-6
    assert abs(lay.inner(trans[0], trans[2])) < 1e-6


def test_coupled_spectrum_3d_path_runs_and_reports_z_overlap():
    """End-to-end 3D smoke test: the coupled eigen-solver runs on a 3D state and every mode carries an
    overlap_z and a spherical-degree m in 0..2 (3D code path, not the 2D one)."""
    N = 16
    _, _, _, _, g = _bump3d(N, w=3.0)
    lay = StateLayout(("u",), ((N, N, N),))
    k2 = cs_k2 = None

    def step_T(vec):
        u = vec.reshape(N, N, N)
        uh = np.fft.fftn(u)
        kk = sum(ki ** 2 for ki in np.meshgrid(*[np.fft.fftfreq(N) * 2 * np.pi] * 3, indexing="ij"))
        for _ in range(3):
            uh = uh * np.exp(-0.05 * kk)                         # a few diffusion sub-steps (linear)
        return np.real(np.fft.ifftn(uh)).ravel()

    spec = cs.coupled_spectrum(g.ravel(), step_T, lay, dx=1.0, T_dt=0.15, k=6)
    assert len(spec) == 6
    assert all("overlap_z" in s for s in spec)                  # 3D path used
    assert all(0 <= s["m"] <= 2 for s in spec)                  # spherical degree
    assert all(isinstance(s["is_goldstone"], bool) for s in spec)
