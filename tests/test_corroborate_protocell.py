"""P17: the one-chemistry containers do not depend on the discretisation -- local stencil vs spectral Laplacian."""
import numpy as np
import pytest

from genesis.diagnostics import corroborate_protocell as cp
from genesis.models import protocell_one as po


def test_spectral_laplacian_matches_the_stencil_on_a_smooth_wave():
    x = np.arange(64)
    f = np.sin(2 * np.pi * x / 64)[:, None] * np.cos(2 * np.pi * 2 * x / 64)[None, :]
    exact = -((2 * np.pi / 64) ** 2 + (4 * np.pi / 64) ** 2) * f
    assert np.allclose(po.spectral_laplacian(f.shape)(f), exact, atol=1e-12)
    assert np.allclose(po.laplacian(f), exact, atol=2e-4)


def test_grid_spacing_scales_both_laplacians():
    n, dx = 64, 0.5
    x = np.arange(n) * dx
    f = np.sin(2 * np.pi * x / (n * dx))[:, None] * np.ones((1, n))
    exact = -(2 * np.pi / (n * dx)) ** 2 * f
    assert np.allclose(po.spectral_laplacian(f.shape, dx)(f), exact, atol=1e-12)
    p = dict(po.DEFAULTS_2D, dx=dx, F=0.0, s=0.0, M=0.0, y=0.0)        # isolate the diffusion of U: (U_new − U)/dt
    U = 1.0 + 0.01 * f
    Un = po.step(np.zeros_like(f) - 1.0, U, 0 * f, 0 * f, dict(p, s=1.0, F=0.0))[1]
    assert np.allclose((Un - U) / p["dt"], p["Du"] * 0.01 * exact, atol=1e-5)


def test_agree_flags_disagreement():
    a = {"containers": 20, "box_share": 0.1, "replicators": 0.1, "in_out": 5.0}
    assert cp.agree(a, dict(a, containers=21))[0] and not cp.agree(a, dict(a, containers=5))[0]


@pytest.mark.slow
def test_local_and_spectral_agree_in_2d():
    v = cp.corroborate_local_vs_spectral((64, 64), 150.0)
    assert v["corroborated"] and v["local"]["containers"] >= 10 and max(v["rel_diff"].values()) < 0.1


@pytest.mark.slow
def test_local_and_spectral_agree_in_3d():
    v = cp.corroborate_local_vs_spectral((32, 32, 32), 100.0)             # enough containers to compare counts
    assert v["corroborated"] and v["local"]["containers"] >= 5 and v["spectral"]["containers"] >= 5
