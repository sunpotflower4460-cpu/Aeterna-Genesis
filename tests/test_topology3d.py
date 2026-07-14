"""topology3d: 3D authenticity audit + 3D-specific invariants (out-of-plane variation, 3-axis percolation,
helicity). Helicity is IDENTICALLY ~0 for a 2D-embedded flow and != 0 for a helical/Beltrami flow -> proves
genuinely-3D, chirality-sensitive physics. no_touch: measures.py untouched."""
import numpy as np

from genesis.diagnostics import topology3d as t3


def test_out_of_plane_variation_extruded_vs_real3d():
    rng = np.random.default_rng(0)
    plane = rng.standard_normal((16, 16))
    extruded = np.repeat(plane[:, :, None], 16, axis=2)          # stacked-2D (fake 3D)
    real3d = rng.standard_normal((16, 16, 16))
    assert t3.out_of_plane_variation(extruded, axis=-1) < 1e-9
    assert t3.out_of_plane_variation(real3d, axis=-1) > 0.1


def test_three_axis_percolation():
    full = np.ones((12, 12, 12), bool)
    assert t3.three_axis_percolation(full)["spans_all"] is True
    blob = np.zeros((12, 12, 12), bool)
    blob[5:7, 5:7, 5:7] = True                                  # small central blob spans no axis
    r = t3.three_axis_percolation(blob)
    assert r["spans_all"] is False and max(r["span_frac"]) < 0.5


def test_helicity_zero_in_2d_nonzero_for_beltrami():
    N = 24
    x = np.linspace(0, 2 * np.pi, N, endpoint=False)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    dx = x[1] - x[0]
    # 2D-embedded flow: uz=0 and no z-dependence -> helicity identically ~0
    ux2, uy2, uz2 = np.sin(Y), np.cos(X), np.zeros_like(X)
    assert abs(t3.helicity(ux2, uy2, uz2, dx)) < 1e-6
    # ABC/Beltrami flow (A=B=C=1): curl u = u  -> helicity = mean(|u|^2) > 0
    ux, uy, uz = np.sin(Z) + np.cos(Y), np.sin(X) + np.cos(Z), np.sin(Y) + np.cos(X)
    h = t3.helicity(ux, uy, uz, dx)
    assert h > 0.5                                              # genuinely 3D, parity-odd, non-zero


def test_three_d_authenticity_flags():
    rng = np.random.default_rng(1)
    extruded = np.repeat(rng.standard_normal((16, 16))[:, :, None], 16, axis=2)
    ae = t3.three_d_authenticity(extruded)
    assert ae["full_volume"] and ae["extruded_from_2d"] and not ae["genuinely_3d"]
    real3d = rng.standard_normal((16, 16, 16))
    ar = t3.three_d_authenticity(real3d)
    assert ar["genuinely_3d"] and not ar["extruded_from_2d"]
