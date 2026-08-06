#!/usr/bin/env python3
"""e060 Phase 1 の失敗様式分類器と、その安価なスクリーン。

Phase 1 は settle + hold だけを回す（heal / size は回さない）。これは L4 フル
プロトコルの約1/2のコストで「そもそも単一の持続個体が存在するか」を判定するため。

分類ラベル（前回の gl-haiku-1000 の反省：「Level 1 以上なら通過」にしない）:

    DIES                        構造が消える（支持領域が空になる）
    FILLS_DOMAIN                「+」状態が侵入して全域を埋める
    FRAGMENTS                   多スポット／迷路状に分裂（連結成分 >= 2）
    OSCILLATORY_CHAOS           単一化しないまま late-time で揺れ続ける
    TRANSIENT_SINGLE            settle では単一だが hold で失われる
    PERSISTENT_SINGLE_CANDIDATE 単一・コンパクト・定常（Phase 2 へ進む唯一のラベル）
    NUMERICAL_FAILURE           NaN / 発散

⚠️ 下の閾値は Phase 0 終了時に凍結する。結果を見て緩めてはならない。
   PERSISTENT_SINGLE_CANDIDATE の area_fraction 上限 0.25 は、既存判定器
   higher_levels.assess_individuality_level の `localized` 条件と同じ値を使う
   （独自の甘いゲートを作らないため）。
"""
from __future__ import annotations

import numpy as np

from . import whites

# --- 凍結閾値（Phase 0 で確定・以後変更しない） --------------------------------
THRESHOLDS = {
    "amax_floor": 0.5,        # higher_levels の contrast 条件と同値
    "area_max": 0.25,         # higher_levels の localized 条件と同値
    "fill_fraction": 0.5,     # これ以上を FILLS_DOMAIN とみなす
    "steady_change": 1e-2,    # higher_levels の persistent 条件と同値
}

PASS_LABEL = "PERSISTENT_SINGLE_CANDIDATE"


def classify(status, s_settle, s_hold, persistence_change, thresholds=None):
    """settle/hold の支持領域統計から失敗様式を決める。純関数（副作用なし）。"""
    t = dict(THRESHOLDS if thresholds is None else thresholds)
    if status != "ok":
        return "NUMERICAL_FAILURE"

    af_hold = float(s_hold["area_fraction"])
    amax_hold = float(s_hold["amax"])
    n_hold = int(s_hold["ncomp"])
    n_settle = int(s_settle["ncomp"])

    if n_hold == 0 or amax_hold < t["amax_floor"]:
        return "DIES"
    if af_hold >= t["fill_fraction"]:
        return "FILLS_DOMAIN"
    if n_hold >= 2:
        return "FRAGMENTS"
    # ここから n_hold == 1
    if af_hold >= t["area_max"]:
        return "FILLS_DOMAIN"
    if float(persistence_change) >= t["steady_change"]:
        return "OSCILLATORY_CHAOS"
    if n_settle != 1:
        return "TRANSIENT_SINGLE"
    return PASS_LABEL


# --- 安価なスクリーン（settle + hold のみ） ------------------------------------

def screen_mass_conserved(params, *, seed, N=64, settle=4000, hold=1200,
                          noise_amp=1e-3, seeded_localization=False, dt=None, thr=0.3):
    p = dict(whites.WHITES["mass_conserved"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    dt = float(dt if dt is not None else whites.mc.stable_dt(p, ndim=2))
    init = whites.mc_initial_bump if seeded_localization else whites.mc_initial_uniform
    rng = np.random.default_rng(seed)
    a, b = init((N, N), p, noise_amp, rng)
    mass0 = float((a + b).sum())

    def evolve(a, b, steps):
        for _ in range(steps):
            a, b = whites.mc.step(a, b, dt, p)
            if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
                return None, None
        return a, b

    a, b = evolve(a, b, settle)
    if a is None:
        return _fail("settle")
    s0 = whites.mc_support_stats(a, thr)
    prev = a.copy()
    a, b = evolve(a, b, hold)
    if a is None:
        return _fail("hold")
    s1 = whites.mc_support_stats(a, thr)
    change = float(np.abs(a - prev).max())
    mass_drift = abs(float((a + b).sum()) - mass0) / (abs(mass0) + 1e-30)
    return _ok(s0, s1, change, extra={"mass_drift": mass_drift, "dt": dt})


def screen_swift_hohenberg(params, *, seed, N=64, settle=2500, hold=800,
                           noise_amp=1e-3, seeded_localization=False, thr=0.3):
    from .l4_protocol import _sh_stats
    p = dict(whites.WHITES["swift_hohenberg"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    init = whites.sh_initial_bump if seeded_localization else whites.sh_initial_uniform
    rng = np.random.default_rng(seed)
    u = init((N, N), p, noise_amp, rng)
    k2 = whites.sh._k2(N, p["dx"])

    def evolve(u, steps):
        for _ in range(steps):
            u = whites.sh.step(u, p, k2)
            if not np.all(np.isfinite(u)):
                return None
        return u

    u = evolve(u, settle)
    if u is None:
        return _fail("settle")
    s0 = _sh_stats(u, thr)
    prev = u.copy()
    u = evolve(u, hold)
    if u is None:
        return _fail("hold")
    s1 = _sh_stats(u, thr)
    change = float(np.abs(u - prev).max())
    return _ok(s0, s1, change)


def _fail(stage):
    return {"status": "numerical_failure", "stage": stage,
            "label": "NUMERICAL_FAILURE", "ncomp": None, "area_fraction": None,
            "amax": None, "persistence_change": None}


def _ok(s0, s1, change, extra=None):
    label = classify("ok", s0, s1, change)
    out = {"status": "ok", "label": label,
           "ncomp_settle": int(s0["ncomp"]), "ncomp": int(s1["ncomp"]),
           "area_fraction": float(s1["area_fraction"]), "amax": float(s1["amax"]),
           "persistence_change": float(change)}
    if extra:
        out.update(extra)
    return out


SCREENS = {"mass_conserved": screen_mass_conserved,
           "swift_hohenberg": screen_swift_hohenberg}
