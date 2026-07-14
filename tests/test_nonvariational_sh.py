"""Frontier Campaign M1 / V1: NON-VARIATIONAL Swift-Hohenberg. The affirmative counterpart to the SH
variational no-go (#44) -- can breaking the gradient structure lift the translation mode (m=1) so the static
individual self-propels? MEASURED answer for this white: NO -- the non-variational term drives the SPLIT
mode (m=2) toward instability BEFORE translation (m=1), which stays marginal (split-before-drift). So no
self-propulsion in the SH family; this is a white-specific frontier with a mechanistic finding.
no_touch: measures.py untouched.
"""

from genesis.models import nonvariational_swift_hohenberg as nv


def test_variational_baseline_is_static():
    """With the non-variational coefficient off, the white is the variational SH: translation marginal,
    split stable -> classified static (reproduces #44 through the NV model)."""
    r = nv.angular_spectrum(0.0)
    assert not r["unstable"]
    assert r["sigmas"]["m1_translation"] <= 1.0e-3            # translation marginal (no drift)
    assert r["sigmas"]["m2_split"] < -0.1                     # split stable
    assert r["label"] == "static" and not r["detected"]["self_propelled_drift"]


def test_nonvariational_lifts_split_before_drift_no_self_propulsion():
    """MEASURED: the non-variational term drives the SPLIT mode (m=2) toward instability while the
    TRANSLATION mode (m=1) stays marginal -> split-before-drift. No drift bifurcation, so no self-propelled
    individual in this white (frontier). The mechanistic finding: this family couples to m=2, not m=1."""
    r0 = nv.angular_spectrum(0.0)
    r1 = nv.angular_spectrum(0.5)
    assert not r1["unstable"]
    # the non-variational term RESPONDS on the split mode (m=2 moves toward onset by ~0.19)...
    assert r1["sigmas"]["m2_split"] - r0["sigmas"]["m2_split"] > 0.1
    # ...but NOT on the translation mode (m=1 stays marginal, unchanged) -> split-before-drift
    assert r1["sigmas"]["m1_translation"] <= 1.0e-3
    assert abs(r1["sigmas"]["m1_translation"] - r0["sigmas"]["m1_translation"]) < 0.05
    # never classified self-propelled (drift-before-split) in this white
    assert r1["label"] != "self_propelled_drift" and not r1["detected"]["self_propelled_drift"]
