"""Frontier Campaign M2-B: re-audit the (a,c) plane of the (non-)variational Swift-Hohenberg with the
COUPLED-Jacobian eigenvalue solver (not the M1 c=0 proxy). The honest measured finding for the SCANNED
region: NO non-Goldstone m=1 mode exists (the only m=1 is the translation Goldstone, excluded); the
non-variational term destabilises the m=2 (split) mode as `a` grows; c>0 blows up. So no drift candidate
in this white/domain (N2 split-first, white-specific). no_touch: measures.py untouched.
"""

from genesis.models import nonvariational_swift_hohenberg as nv


def test_variational_point_has_only_goldstone_m1_and_stable_split():
    r = nv.coupled_audit(0.0, 0.0)
    assert not r["unstable"]
    assert r["residual"] < 1e-6 and r["center_drift"] < 1e-3      # genuine static fixed point
    assert r["n_goldstone"] == 2                                  # translation doublet
    assert r["measured_by"]["lambda_m1_non_goldstone"] is None    # NO non-Goldstone m=1 mode exists
    assert r["measured_by"]["lambda_m2plus"] < 0.0                # split stable
    assert r["label"] == "static" and not r["detected"]["spectral_drift_candidate"]


def test_nonvariational_destabilises_split_not_drift():
    """As `a` grows (c=0) the m=2 (split) eigenvalue rises toward onset, but STILL no non-Goldstone m=1
    mode appears -> not a drift candidate. The SH family has no polarity/drift mode here (mechanistic)."""
    r0 = nv.coupled_audit(0.0, 0.0)
    r1 = nv.coupled_audit(0.5, 0.0)
    assert not r1["unstable"]
    assert r1["n_goldstone"] == 2
    assert r1["measured_by"]["lambda_m1_non_goldstone"] is None   # still no drift mode
    assert r1["measured_by"]["lambda_m2plus"] > r0["measured_by"]["lambda_m2plus"]  # split destabilised by a
    assert r1["label"] != "spectral_drift_candidate"


def test_c_positive_blows_up_documented_boundary():
    """The c>0 direction blows up at this resolution/scheme -> honest domain boundary (not a drift result)."""
    r = nv.coupled_audit(0.0, 0.3)
    assert r["unstable"] is True
