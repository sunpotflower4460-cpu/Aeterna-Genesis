"""Frontier Campaign M2-C: re-measure the three-component RD with the FULL coupled state (u,v,w bundled),
not the u-only proxy. The honest measured finding for the scanned region: NO compact localized STATIONARY
single individual exists to linearise around -- the state either DIES (count 0), stays a diffuse DRIFTING
blob (not stationary), or the "+" state INVADES and FILLS the domain. So the coupled measurement instrument,
guarded by an EXISTENCE gate, correctly REFUSES to report a drift spectrum: the frontier here is UPSTREAM of
drift (existence), an N0 no-go, not a drift measurement. A SH #40 individual is the POSITIVE CONTROL that the
SAME gate accepts. no_touch: measures.py untouched. Physical quantity (residual/localization) FIRST.
"""

import numpy as np

from genesis.models import three_component_rd as rd
from genesis.models import swift_hohenberg as sh
from genesis.models.adapters.state_layout import StateLayout
from genesis.diagnostics import coupled_spectrum as cs


def _sh_gate():
    """Settle the variational SH #40 individual and run it through the SAME existence gate (positive control)."""
    p = dict(sh.DEFAULTS)
    rng = np.random.default_rng(0)
    u = sh.make_initial((64, 64), 1e-3, rng, p)
    k2 = sh._k2(64, p["dx"])
    for _ in range(2500):
        u = sh.step(u, p, k2)
    from scipy import ndimage
    lay = StateLayout(("u",), ((64, 64),))
    _, count = ndimage.label(np.abs(u) > 0.3)
    area_frac = int((np.abs(u) > 0.3).sum()) / float(64 * 64)
    ok, info = cs.existence_gate(u.ravel(), sh.step(u, p, k2).ravel(), lay, count, area_frac)
    return ok, info, u, p, k2, lay


def test_positive_control_sh_individual_passes_gate_and_has_goldstone():
    """The SAME existence gate that refuses the 3-comp RD ACCEPTS the SH #40 individual: it is compact,
    single, and a genuine stationary fixed point -> the coupled spectrum has translation Goldstones."""
    ok, info, u, p, k2, lay = _sh_gate()
    assert ok is True
    assert info["localized"] and info["stationary"]
    assert info["count"] == 1 and 0.0 < info["area_frac"] < 0.5
    assert info["reason"] is None

    def step_T(vec):
        w = vec.reshape(64, 64)
        for _ in range(50):
            w = sh.step(w, p, k2)
        return w.ravel()

    spec = cs.coupled_spectrum(u.ravel(), step_T, lay, dx=p["dx"], T_dt=50 * p["dt"], k=8)
    assert sum(1 for s in spec if s["is_goldstone"]) >= 1     # a genuine localized individual has Goldstones


def test_rd_dead_branch_refused_no_localized_individual():
    """k1 too negative -> the activator spot DIES (count 0). The gate refuses: no individual to linearise."""
    r = rd.coupled_audit(k1=-0.05)
    assert r["gate"] == "REFUSED"
    assert r["reason"] == "no_localized_individual"
    assert r["count"] == 0
    assert "measured_by" not in r                            # NO spectrum reported around a non-individual


def test_rd_diffuse_branch_refused_not_stationary():
    """k1=0 -> a large diffuse blob that keeps evolving: localized-ish but NOT a stationary fixed point
    (rel_res above gate). The gate refuses on the stationarity criterion -> no drift claim."""
    r = rd.coupled_audit(k1=0.0)
    assert r["gate"] == "REFUSED"
    assert r["reason"] == "not_stationary"
    assert r["rel_res"] > 1e-2
    assert "measured_by" not in r


def test_rd_filled_branch_refused_no_localized_individual():
    """k1 positive -> the "+" state INVADES and fills the domain (area_frac ~ 1): not a localized individual.
    The gate refuses -> the coupled instrument does not hallucinate a spectrum around a uniform state."""
    r = rd.coupled_audit(k1=0.05)
    assert r["gate"] == "REFUSED"
    assert r["reason"] == "no_localized_individual"
    assert r["area_frac"] > 0.9
    assert "measured_by" not in r
