"""Frontier Campaign M1: angular-mode growth-rate spectroscopy. Measure which mode destabilises FIRST
instead of searching for moving models. The variational Swift-Hohenberg white must show the self-propulsion
NO-GO by MEASUREMENT: translation (m=1) is marginal (<=0), so a gradient flow does not self-propel.
no_touch: measures.py is untouched (this is an additive diagnostic).
"""

import numpy as np

from genesis.diagnostics import angular_modes as am
from genesis.models import swift_hohenberg as sh


def _settle_sh(N=64, steps=2500, seed=0):
    p = dict(sh.DEFAULTS)
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    k2 = sh._k2(N, p["dx"])
    for _ in range(steps):
        u = sh.step(u, p, k2)
    return u, (lambda v: sh.step(v, p, k2)), p


def test_swift_hohenberg_variational_no_go_translation_is_marginal():
    """MEASURED no-go: for the variational SH localized state the translation mode (m=1) is marginal/decaying
    (sigma <= 0) -- a gradient flow cannot spontaneously self-propel. Breathing/split are stable. No mode is
    unstable => classified 'static' (NOT self-propelled). This reproduces the GPT/Claude no-go by measurement."""
    u_star, step_fn, p = _settle_sh()
    sig = am.angular_mode_growth_rates(u_star, step_fn, dx=p["dx"], dt=p["dt"], t_steps=300)
    assert sig["m1_translation"] <= 1.0e-3          # translation marginal/stable -> does NOT self-propel
    assert sig["m0_breathing"] < 0.0                # breathing stable
    assert sig["m2_split"] < 0.0                    # split/elliptical stable
    label, det, mb = am.classify_angular_spectrum(sig)
    assert label == "static" and det["static"] and not det["self_propelled_drift"]
    assert det["translation_marginal_or_stable"] is True
    assert mb["first_unstable_mode"] is None         # nothing destabilises


def test_classifier_drift_before_split_vs_split_first_vs_static():
    """The classifier names the structure from the angular spectrum (measure first, label after): m=1 first
    => self-propelled drift; m=2 first => splitting (the replication trap, not one body); nothing => static."""
    # drift-before-split: translation destabilises first and most -> self-propelled candidate
    lab1, d1, m1 = am.classify_angular_spectrum({"m0_breathing": -0.1, "m1_translation": 0.05, "m2_split": 0.01})
    assert lab1 == "self_propelled_drift" and d1["self_propelled_drift"] and m1["first_unstable_mode"] == "m1_translation"
    # split-first: m=2 wins -> splitting (Gray-Scott-like trap), NOT self-propelled
    lab2, d2, _ = am.classify_angular_spectrum({"m0_breathing": -0.1, "m1_translation": 0.01, "m2_split": 0.06})
    assert lab2 == "splitting" and d2["splitting"] and not d2["self_propelled_drift"]
    # nothing unstable (variational) -> static
    lab3, d3, _ = am.classify_angular_spectrum({"m0_breathing": -0.2, "m1_translation": -1e-6, "m2_split": -0.1})
    assert lab3 == "static" and not d3["self_propelled_drift"]
    # breathing-first -> breathing (pulsating), not self-propelled
    lab4, d4, _ = am.classify_angular_spectrum({"m0_breathing": 0.08, "m1_translation": 0.01, "m2_split": 0.0})
    assert lab4 == "breathing" and not d4["self_propelled_drift"]
