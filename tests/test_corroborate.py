"""Corroboration (hermetic layer): the same white under two DIFFERENT spatial discretisations -- the local
nearest-neighbour stencil and a spectral FFT Laplacian -- must agree on physical observables. Agreement =>
the emergent result is solver-independent, not a finite-difference artefact. no_touch: measures.py untouched.
(The cross-repo Genesis-Room- layer is network-dependent and lives in tools/corroborate.py, not here.)"""
from genesis.diagnostics import corroborate as cor


def test_local_vs_spectral_agree_2d():
    v = cor.corroborate_local_vs_spectral((48, 48), t_final=40.0, seed=1)
    assert v["corroborated"] is True
    assert v["rel_diff"]["mean_amp"] < 0.05          # amplitude saturation agrees tightly
    assert v["method_a"] == "local_stencil" and v["method_b"] == "spectral_fft"


def test_local_vs_spectral_agree_3d():
    v = cor.corroborate_local_vs_spectral((24, 24, 24), t_final=30.0, seed=1)
    assert v["corroborated"] is True
    assert v["rel_diff"]["mean_amp"] < 0.05


def test_agree_helper_flags_disagreement():
    ok, rel = cor.agree({"mean_amp": 1.0, "core_frac": 0.1}, {"mean_amp": 1.0, "core_frac": 0.1})
    assert ok is True
    bad, _ = cor.agree({"mean_amp": 1.0, "core_frac": 0.1}, {"mean_amp": 0.5, "core_frac": 0.5})
    assert bad is False
