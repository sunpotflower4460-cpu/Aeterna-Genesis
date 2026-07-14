"""Frontier Campaign M2-A: coupled-Jacobian eigenvalue base. Validates on scalar Swift-Hohenberg that the
near-zero m=1 modes are the translation GOLDSTONE (correctly identified & excluded), NOT a drift mode --
making the M1 proxy result precise (GPT M2 addendum §1). no_touch: measures.py untouched.
"""

import numpy as np

from genesis.models import swift_hohenberg as sh
from genesis.models.adapters.state_layout import StateLayout
from genesis.diagnostics import coupled_spectrum as cs


def _settle(N=64, steps=2500, seed=0):
    p = dict(sh.DEFAULTS)
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    k2 = sh._k2(N, p["dx"])
    for _ in range(steps):
        u = sh.step(u, p, k2)
    return u, p, k2


def _spectrum(u, p, k2, N, T=50, eps=1e-4, k=8):
    lay = StateLayout(("u",), ((N, N),))

    def step_T(vec):
        w = vec.reshape(N, N)
        for _ in range(T):
            w = sh.step(w, p, k2)
        return w.ravel()

    return cs.coupled_spectrum(u.ravel(), step_T, lay, dx=p["dx"], T_dt=T * p["dt"], k=k, eps=eps)


def test_state_layout_roundtrip_and_weighted_inner():
    lay = StateLayout(("u", "v"), ((8, 8), (8, 8)), metric={"v": 0.2})
    a = np.arange(128, dtype=float)
    fu, fv = lay.unflatten(a)
    assert fu.shape == (8, 8) and fv.shape == (8, 8)
    assert np.allclose(lay.flatten((fu, fv)), a)
    # weighted inner: v contributes at weight 0.2
    b = np.ones(128)
    assert np.isclose(lay.inner(b, b), (64 * 1.0) + (64 * 0.2))


def test_scalar_sh_m1_is_the_goldstone_not_drift():
    """The two near-zero m=1 modes are the translation GOLDSTONE (lambda~0, overlap with d_x/d_y u* ~1,
    x/y degenerate). There is NO non-Goldstone m=1 -> classify 'static'. This corrects the M1 proxy: its
    'sigma(m=1)~0' was the Goldstone being neutral, not evidence about drift."""
    u, p, k2 = _settle()
    N = u.shape[0]
    res = float(np.linalg.norm(sh.step(u, p, k2) - u))
    assert res < 1e-6                                          # settled state is a genuine fixed point
    spec = _spectrum(u, p, k2, N)
    gold = [s for s in spec if s["is_goldstone"]]
    assert len(gold) == 2                                      # x/y translation doublet
    assert all(abs(s["lambda"]) < 5e-3 and s["m"] == 1 and max(s["overlap_x"], s["overlap_y"]) > 0.9
               for s in gold)
    assert abs(gold[0]["lambda"] - gold[1]["lambda"]) < 5e-3   # x/y degenerate
    label, det, mb = cs.classify_drift_before_split(spec)
    assert label == "static"                                  # nothing non-Goldstone unstable
    assert mb["lambda_m1_non_goldstone"] is None              # the ONLY m=1 modes are Goldstone (excluded)
    assert not det["non_goldstone_m1_unstable"]
    assert mb["lambda_m2plus"] < 0.0                          # split stable -> matches M1 sign order


def test_scalar_sh_spectrum_converges_in_eps_and_T():
    """The leading split (m>=2) eigenvalue is stable across eps x {0.3,1,3} and across T -- a real spectral
    quantity, not a proxy artefact (GPT M2 addendum §6)."""
    u, p, k2 = _settle()
    N = u.shape[0]

    def lead_split(spec):
        vals = [s["lambda"] for s in spec if not s["is_goldstone"] and s["m"] >= 2]
        return max(vals)

    base = lead_split(_spectrum(u, p, k2, N, eps=1e-4))
    for eps in (3e-5, 3e-4):
        assert abs(lead_split(_spectrum(u, p, k2, N, eps=eps)) - base) < 2e-2
    assert abs(lead_split(_spectrum(u, p, k2, N, T=40)) - base) < 3e-2   # dt/T convergence


def test_classifier_excludes_goldstone_and_names_from_non_goldstone():
    """Synthetic spectra: a POSITIVE eigenvalue tagged Goldstone must NOT make a drift candidate; only a
    NON-Goldstone m=1 crossing first does. m=2 first -> splitting; nothing -> static."""
    # a positive m=1 that is the GOLDSTONE -> excluded -> static (not a drift candidate)
    spec_g = [{"lambda": 0.05, "m": 1, "is_goldstone": True, "overlap_x": 1.0, "overlap_y": 0.0},
              {"lambda": -0.1, "m": 2, "is_goldstone": False, "overlap_x": 0.0, "overlap_y": 0.0}]
    lab_g, det_g, _ = cs.classify_drift_before_split(spec_g)
    assert lab_g == "static" and not det_g["spectral_drift_candidate"]
    # a NON-Goldstone m=1 crossing first -> spectral drift candidate
    spec_d = [{"lambda": 0.04, "m": 1, "is_goldstone": False, "overlap_x": 0.1, "overlap_y": 0.0},
              {"lambda": 0.01, "m": 2, "is_goldstone": False, "overlap_x": 0.0, "overlap_y": 0.0},
              {"lambda": 0.0, "m": 1, "is_goldstone": True, "overlap_x": 1.0, "overlap_y": 0.0}]
    lab_d, det_d, mb_d = cs.classify_drift_before_split(spec_d)
    assert lab_d == "spectral_drift_candidate" and det_d["spectral_drift_candidate"]
    assert mb_d["drift_margin"] > 0
    # m=2 first -> splitting (the replication trap), not self-propelled
    spec_s = [{"lambda": 0.05, "m": 2, "is_goldstone": False, "overlap_x": 0.0, "overlap_y": 0.0},
              {"lambda": 0.01, "m": 1, "is_goldstone": False, "overlap_x": 0.0, "overlap_y": 0.0}]
    lab_s, det_s, _ = cs.classify_drift_before_split(spec_s)
    assert lab_s == "splitting" and not det_s["spectral_drift_candidate"]
