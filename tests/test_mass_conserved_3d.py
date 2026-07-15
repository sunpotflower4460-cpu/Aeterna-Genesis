"""M2-E-3D -- the mass-conserved 3D activator-inhibitor white. These tests pin the honest finding:

  (existence half of the M2 'scissors' is BROKEN in 3D) a genuinely-3D stable COMPACT SINGLE individual GROWS
  from a structureless start and PASSES the existence gate -- something no 2D white in M2-C/M2-D could do; and

  (drift half of the scissors PERSISTS) the coupled 3D spectrum of that individual is `static`: no unstable
  mode, the only lambda~=0 mode is the mass-conservation zero mode, and the ell=1 modes are lattice-pinned
  TRANSLATION Goldstones (high translation overlap, stable) -- NO non-Goldstone drift-polarity mode. The ball
  is stable but does not self-propel.

no_touch: measures.py untouched. Language: a settling 'ball' is a field structure, not life (spots != life)."""
import numpy as np

from genesis.models import mass_conserved_3d as mc
from genesis.diagnostics import coupled_spectrum as cs


def test_reaction_conserves_total_mass_exactly():
    """The SAME f is added to a and subtracted from b, so a+b changes only by the (equal, cancelling) diffusion
    of two conserved-total fields -> total mass is invariant to round-off over a short run."""
    r = mc.settle((12, 12, 12), steps=200, seed=1)
    assert not r["diverged"]
    assert r["mass_drift"] < 1e-12


def test_local_laplacian_is_nearest_neighbour_and_kills_constants():
    z = np.full((6, 6, 6), 3.7)
    assert np.allclose(mc.local_laplacian(z), 0.0)                 # constant -> 0
    # a single hot voxel: centre = -6, each of 6 face neighbours = +1 (7-point stencil, no diagonals)
    z = np.zeros((5, 5, 5)); z[2, 2, 2] = 1.0
    lap = mc.local_laplacian(z)
    assert lap[2, 2, 2] == -6.0
    assert lap[1, 2, 2] == 1.0 and lap[3, 2, 2] == 1.0
    assert lap[1, 1, 2] == 0.0                                     # diagonal untouched


def test_3d_single_individual_grows_and_passes_existence_gate():
    """From bump+noise the white settles to ONE compact localized stationary 3D activator core (gate PASS),
    with total mass conserved. This breaks the EXISTENCE half of the M2 scissors in 3D."""
    r = mc.settle((20, 20, 20), steps=2000, seed=0)
    assert not r["diverged"]
    assert r["mass_drift"] < 1e-9                                  # conserved
    ok, info = mc.existence_report(r["a"], r["b"], r["params"], r["dt"])
    assert ok, info
    assert info["ncomp"] == 1                                      # a single individual, not a labyrinth
    assert 0.0 < info["vol_frac"] < 0.5                            # localized, does not fill the domain
    assert info["stationary"]                                      # a fixed point, not still evolving


def test_settled_ball_is_genuinely_3d_not_extruded_2d():
    from genesis.diagnostics import topology3d as t3
    r = mc.settle((20, 20, 20), steps=2000, seed=0)
    aud = t3.three_d_authenticity(r["a"])
    assert aud["genuinely_3d"]
    assert not aud["extruded_from_2d"]


def test_drift_spectrum_is_static_no_self_propulsion():
    """The coupled 3D spectrum of the settled ball: `static`. The only ~0 mode is the mass-conservation zero
    mode; the three ell=1 modes are translation Goldstones (high translation overlap) and are STABLE; no
    non-Goldstone drift mode. This is the DRIFT half of the scissors persisting in 3D (individual != self-mover)."""
    r = mc.settle((20, 20, 20), steps=2000, seed=0)
    a, b, p, dt = r["a"], r["b"], r["params"], r["dt"]
    lay, step_T = mc.drift_step_map(a, b, p, dt, n_sub=60)
    spec = cs.coupled_spectrum(lay.flatten((a, b)), step_T, lay, dx=1.0, T_dt=60 * dt, k=8)
    label, detected, _ = cs.classify_drift_before_split(spec)

    assert label == "static"                                      # nothing non-Goldstone is unstable
    assert not detected["spectral_drift_candidate"]               # no drift-before-split
    assert max(s["lambda"] for s in spec) < 1e-3                  # no growing mode (mass mode ~0, rest < 0)

    ell1 = [s for s in spec if s["m"] == 1]
    assert len(ell1) == 3                                         # Tx, Ty, Tz doublet-triplet in 3D
    # every ell=1 mode is a translation Goldstone: strong overlap with a translation direction...
    for s in ell1:
        assert max(s["overlap_x"], s["overlap_y"], s["overlap_z"]) > 0.4
    # ...and NONE of them is a growing drift mode
    assert all(s["lambda"] < 1e-3 for s in ell1)
