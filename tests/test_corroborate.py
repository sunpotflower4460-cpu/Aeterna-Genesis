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


# ---- multi-backend orchestrator: PURE logic (no network) ----
from tools import corroborate as multi  # noqa: E402
import numpy as np  # noqa: E402


def test_parse_vortex_tdgl_markdown():
    md = ("| step | + | - | net charge | total | E |\n|---|---|---|---|---|---|\n"
          "| 0 | 390 | 390 | 0 | 780 | 4616 |\n| 120 | 18 | 18 | 0 | 36 | 311 |\n")
    s = multi.parse_vortex_tdgl(md)
    assert s["net_charge"] == 0 and s["defects_early"] == 780 and s["defects_late"] == 36
    assert s["coarsens"] is True


def test_zero_looper_verdict_structural():
    a2 = {"structural": {"net_charge": 0, "defects_early": 100, "defects_late": 20, "coarsens": True}}
    good = multi.zero_looper_verdict(a2, {"status": "ok", "structural":
                                          {"net_charge": 0, "defects_early": 780, "defects_late": 36,
                                           "coarsens": True}})
    assert good["backed"] is True and good["checks"]["both_coarsen"]
    bad = multi.zero_looper_verdict(a2, {"status": "ok", "structural":
                                         {"net_charge": 5, "defects_early": 10, "defects_late": 40,
                                          "coarsens": False}})
    assert bad["backed"] is False
    off = multi.zero_looper_verdict(a2, {"status": "unavailable"})
    assert off["backed"] is None


def test_genesis_room_verdict_quantitative():
    a3 = {"observables": {"mean_amp": 0.99, "core_frac": 0.0}}
    good = multi.genesis_room_verdict(a3, {"status": "ok", "observables": {"mean_amp": 0.985, "core_frac": 0.0}})
    assert good["backed"] is True
    bad = multi.genesis_room_verdict(a3, {"status": "ok", "observables": {"mean_amp": 0.4, "core_frac": 0.6}})
    assert bad["backed"] is False


def test_plaquette_charge_counts_a_vortex_antivortex_pair():
    """On a periodic torus total winding must cancel, so use a +1/-1 PAIR: net charge 0, >=2 defects."""
    N = 48
    x = np.arange(N)
    X, Y = np.meshgrid(x, x, indexing="ij")
    th = np.arctan2(Y - 16, X - 16) - np.arctan2(Y - 32, X - 32)   # +1 at (16,16), -1 at (32,32)
    A = np.exp(1j * th)
    net, ndef = multi._plaquette_charge(A)
    assert net == 0 and ndef >= 2                          # balanced pair, both cores detected
