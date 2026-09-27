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


def test_agree_flags_disagreement():
    a = {"containers": 20, "box_share": 0.1, "replicators": 0.1, "in_out": 5.0}
    assert cp.agree(a, dict(a, containers=21))[0] and not cp.agree(a, dict(a, containers=5))[0]


@pytest.mark.slow
def test_local_and_spectral_agree_in_2d():
    v = cp.corroborate_local_vs_spectral((64, 64), 150.0)
    assert v["corroborated"] and v["local"]["containers"] >= 10 and max(v["rel_diff"].values()) < 0.1


@pytest.mark.slow
def test_local_and_spectral_agree_in_3d():
    v = cp.corroborate_local_vs_spectral((24, 24, 24), 60.0)
    ok, rel = cp.agree(v["local"], v["spectral"], keys=("box_share", "replicators", "in_out"))
    assert ok and v["local"]["containers"] >= 1 and max(rel.values()) < 0.1
