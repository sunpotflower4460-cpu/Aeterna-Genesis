"""cgl_local: dimension-agnostic LOCAL complex Ginzburg-Landau (np.roll stencil, no FFT). Grows a vortex
tangle from a structureless start; the SAME code runs 2D and 3D. Good part imported from Genesis-Room-.
no_touch: measures.py untouched."""
import numpy as np

from genesis.models import cgl_local as cg
from genesis.diagnostics import topology3d as t3


def test_local_stencil_is_nearest_neighbour_only():
    """A single spike's Laplacian is nonzero ONLY at the spike and its 2*ndim face-neighbours (local)."""
    z = np.zeros((7, 7, 7), complex)
    z[3, 3, 3] = 1.0
    lap = cg.local_laplacian(z)
    nz = np.argwhere(np.abs(lap) > 0)
    assert len(nz) == 1 + 2 * 3                                  # centre + 6 neighbours (3D)
    assert lap[3, 3, 3] == -6.0                                  # -2*ndim
    assert lap[4, 3, 3] == 1.0 and lap[3, 3, 2] == 1.0           # face neighbours only


def test_grows_from_noise_2d_and_3d_deterministic():
    """From near-zero + tiny noise the amplitude self-organises to O(1) in BOTH 2D and 3D (grow, not placed)."""
    for shape in ((32, 32), (24, 24, 24)):
        snaps, phys = cg.run(shape, t_final=30.0, seed=1, noise_amplitude=0.01)
        assert not phys["diverged"]
        amax = float(np.abs(snaps[-1]["field"]).max())
        assert amax > 0.5                                        # grew from 0.01 to O(1)
    # determinism: same seed -> identical field
    a = cg.run((24, 24, 24), t_final=20.0, seed=2)[0][-1]["field"]
    b = cg.run((24, 24, 24), t_final=20.0, seed=2)[0][-1]["field"]
    assert np.allclose(a, b)


def test_3d_run_is_genuinely_3d_not_extruded():
    """The 3D CGL field genuinely varies along z (vortex LINES thread the volume) -> passes 3D authenticity."""
    snaps, _ = cg.run((24, 24, 24), t_final=30.0, seed=1)
    aud = t3.three_d_authenticity(snaps[-1]["field"])
    assert aud["full_volume"] and aud["genuinely_3d"] and not aud["extruded_from_2d"]
    assert aud["z_variation_fraction"] > 1e-3
