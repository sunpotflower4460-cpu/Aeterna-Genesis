"""M2-E-3D-NR -- mass-conserved 3D ball + slow NON-RECIPROCAL inhibitor w. These tests pin the honest null:

  - the non-reciprocal coupling still conserves total (a+b) EXACTLY (the +-kappa*w cancels term-by-term);
  - kappa=0 reduces to the static single ball of mass_conserved_3d (a sanity anchor);
  - the dynamical drift meter (wrap-aware centroid velocity) is validated on an analytically-translated field;
  - in the single-individual regime the ball is NOT self-propelled (terminal speed at the noise floor) --
    self-propulsion in this white only appears together with fragmentation (existence lost), i.e. the M2
    'scissors' persists at the non-reciprocal level (frontier; see m2e3d_nr_null.yaml).

no_touch: measures.py untouched. Language: a field 'ball' is a field structure, not life (spots != life)."""
import numpy as np

from genesis.models import mass_conserved_nr_3d as nr


def test_nonreciprocal_coupling_still_conserves_total_mass():
    """Even with kappa>0 the -kappa*w in a and +kappa*w in b cancel, so a+b has no source: total mass invariant."""
    r = nr.run_drift((16, 16, 16), params={"kappa": 0.4, "tau": 6.0, "Dw": 6.0}, steps=300, seed=1)
    assert not r["diverged"]
    assert r["mass_drift"] < 1e-12


def test_kappa_zero_reduces_to_static_single_ball():
    r = nr.run_drift((20, 20, 20), params={"kappa": 0.0}, steps=2500, seed=0)
    assert not r["diverged"]
    assert r["ncomp"] == 1                          # single individual (as in mass_conserved_3d)
    assert not r["self_propelled"]                  # static: no self-propulsion
    assert r["speed_late"] < 1e-3                   # terminal centroid speed at the noise floor


def test_centroid_drift_meter_recovers_a_known_translation():
    """Validate the instrument: an activator ball translated by a known interior displacement is measured with
    the right vector (this is what the physics run uses -- the spot sits near the domain centre)."""
    N = 24
    x = np.arange(N)

    def ball(c, s=1.6):
        return np.exp(-((x[:, None, None] - c[0]) ** 2 + (x[None, :, None] - c[1]) ** 2
                        + (x[None, None, :] - c[2]) ** 2) / (2 * s ** 2))

    c0 = nr.periodic_centroid(ball((11.0, 12.0, 12.0)), 0.2)
    c1 = nr.periodic_centroid(ball((13.5, 12.0, 12.0)), 0.2)
    disp = nr._wrap_disp(c1, c0, N)
    assert np.allclose(disp, [2.5, 0.0, 0.0], atol=0.05)
    # minimal-image property holds everywhere (never reports more than half the box)
    assert np.all(np.abs(nr._wrap_disp(np.array([23.0, 0, 0]), np.array([1.0, 0, 0]), N)) <= N / 2 + 1e-9)


def test_single_individual_regime_is_not_self_propelled():
    """The best single-individual non-reciprocal point from the scan (kappa=0.6, tau=8): the ball stays single
    but does NOT self-propel -- terminal centroid speed stays at the noise floor (~0.01 voxel of net motion over
    the run). This pins the drift half of the scissors persisting under non-reciprocity."""
    r = nr.run_drift((20, 20, 20), params={"kappa": 0.6, "tau": 8.0, "Dw": 6.0}, steps=3000, seed=0)
    assert not r["diverged"]
    assert r["ncomp"] == 1                          # a single individual (not fragmented at this point)
    assert not r["self_propelled"]                  # ...but static
    assert r["speed_late"] < 1e-3                   # far below a genuine self-propulsion speed
