#!/usr/bin/env python3
"""e060 Level 4 プロトコル — settle / hold / heal / size の4本立て。

ai_lab/lab.py::_screen_swift_hohenberg（839-881行）で実証済みの手順を、白に依存しない
形へ抽出したもの。元の関数は残す（no_touch）。

判定は **既存の genesis/diagnostics/higher_levels.assess_individuality_level に丸ごと委ねる**。
本モジュールは測定量を作るだけで、合否の閾値を一切持たない——これは「結果を見て閾値を
緩める」ことを構造的に不可能にするための設計である（docs/ANTI_DRIFT.md 精密化⑤）。

4本立て:
  1. settle : t=0 から緩和させ、構造が落ち着くのを待つ
  2. hold   : さらに進めて persistence_change（持続）と centroid_drift（運動）を測る
  3. heal   : 構造の一部を壊し、controlの状態へ再接近するかを測る（L4の決定的判別子）
  4. size   : 一回り大きい箱で同じ条件を回し、有限サイズ効果でないことを確かめる

摂動（heal）は M2「窓なし」に対する認識論的プローブであり、無摂動controlとは別runとして
runtime_interventions を正直に記録する（monad_audit.yaml: perturbation_policy）。
"""
from __future__ import annotations

import numpy as np

from genesis.diagnostics import higher_levels as hl

from . import whites

# 支持領域の閾値。白ごとに一度だけ決め、Phase 0 で凍結する（結果を見て動かさない）。
SUPPORT_THR = {"mass_conserved": 0.3, "swift_hohenberg": 0.3}


def _finite(*arrays):
    return all(np.all(np.isfinite(a)) for a in arrays)


# --- mass_conserved の1試行 ----------------------------------------------------

def run_mass_conserved(params, *, seed, N=64, settle=4000, hold=1200, heal=4000,
                       noise_amp=1e-3, seeded_localization=False, dt=None,
                       size_delta=32, thr=None):
    """mass_conserved 白の L4 4本立て。seeded_localization=False なら bump を置かない。"""
    p = dict(whites.WHITES["mass_conserved"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    thr = SUPPORT_THR["mass_conserved"] if thr is None else float(thr)
    dt = float(dt if dt is not None else whites.mc.stable_dt(p, ndim=2))
    init = whites.mc_initial_bump if seeded_localization else whites.mc_initial_uniform

    def evolve(a, b, steps):
        for _ in range(steps):
            a, b = whites.mc.step(a, b, dt, p)
            if not _finite(a, b):
                return None, None
        return a, b

    rng = np.random.default_rng(seed)
    a, b = init((N, N), p, noise_amp, rng)
    mass0 = float((a + b).sum())

    a, b = evolve(a, b, settle)                      # 1. settle
    if a is None:
        return {"status": "numerical_failure", "stage": "settle"}
    s0 = whites.mc_support_stats(a, thr)

    prev = a.copy()
    a, b = evolve(a, b, hold)                        # 2. hold
    if a is None:
        return {"status": "numerical_failure", "stage": "hold"}
    s1 = whites.mc_support_stats(a, thr)
    persistence_change = float(np.abs(a - prev).max())
    drift = _drift(s0["centroid"], s1["centroid"])
    mass_drift = abs(float((a + b).sum()) - mass0) / (abs(mass0) + 1e-30)

    # 3. heal: 支持領域の上半分を消し、白自身に再成長させる
    ah, bh = a.copy(), b.copy()
    ah[: N // 2, :] = 0.0
    ah, bh = evolve(ah, bh, heal)
    if ah is None:
        return {"status": "numerical_failure", "stage": "heal"}
    sh_ = whites.mc_support_stats(ah, thr)
    recovers = bool(abs(sh_["area"] - s1["area"]) <= max(8, 0.1 * max(s1["area"], 1))
                    and abs(sh_["amax"] - s1["amax"]) < 0.12
                    and sh_["ncomp"] == s1["ncomp"])

    # 4. size: 一回り大きい箱（同じ物理・同じ seed）
    N2 = N + int(size_delta)
    rng2 = np.random.default_rng(seed)
    a2, b2 = init((N2, N2), p, noise_amp, rng2)
    a2, b2 = evolve(a2, b2, settle)
    if a2 is None:
        return {"status": "numerical_failure", "stage": "size"}
    s2 = whites.mc_support_stats(a2, thr)
    size_independent = bool(abs(s2["area"] - s1["area"]) <= max(10, 0.15 * max(s1["area"], 1))
                            and s2["ncomp"] == s1["ncomp"])

    return _judge(s1, persistence_change, recovers, size_independent, drift,
                  seeded_localization, extra={
                      "mass_drift": mass_drift, "ncomp_settle": s0["ncomp"],
                      "ncomp_hold": s1["ncomp"], "ncomp_heal": sh_["ncomp"],
                      "ncomp_size": s2["ncomp"], "area_hold": s1["area"],
                      "area_size": s2["area"], "dt": dt})


# --- swift_hohenberg の1試行 ---------------------------------------------------

def run_swift_hohenberg(params, *, seed, N=64, settle=2500, hold=800, heal=2500,
                        noise_amp=1e-3, seeded_localization=False,
                        size_delta=32, thr=None):
    """swift_hohenberg 白の L4 4本立て。seeded_localization=False なら bump を置かない。"""
    p = dict(whites.WHITES["swift_hohenberg"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    thr = SUPPORT_THR["swift_hohenberg"] if thr is None else float(thr)
    init = whites.sh_initial_bump if seeded_localization else whites.sh_initial_uniform

    def evolve(u, steps, k2):
        for _ in range(steps):
            u = whites.sh.step(u, p, k2)
            if not np.all(np.isfinite(u)):
                return None
        return u

    rng = np.random.default_rng(seed)
    u = init((N, N), p, noise_amp, rng)
    k2 = whites.sh._k2(N, p["dx"])

    u = evolve(u, settle, k2)                        # 1. settle
    if u is None:
        return {"status": "numerical_failure", "stage": "settle"}
    s0 = _sh_stats(u, thr)

    prev = u.copy()
    u = evolve(u, hold, k2)                          # 2. hold
    if u is None:
        return {"status": "numerical_failure", "stage": "hold"}
    s1 = _sh_stats(u, thr)
    persistence_change = float(np.abs(u - prev).max())
    drift = _drift(s0["centroid"], s1["centroid"])

    up = u.copy()                                    # 3. heal
    up[: N // 2, :] = 0.0
    up = evolve(up, heal, k2)
    if up is None:
        return {"status": "numerical_failure", "stage": "heal"}
    sh_ = _sh_stats(up, thr)
    recovers = bool(abs(sh_["area"] - s1["area"]) <= max(8, 0.1 * max(s1["area"], 1))
                    and abs(sh_["amax"] - s1["amax"]) < 0.12
                    and sh_["ncomp"] == s1["ncomp"])

    N2 = N + int(size_delta)                         # 4. size
    u2 = init((N2, N2), p, noise_amp, np.random.default_rng(seed))
    u2 = evolve(u2, settle, whites.sh._k2(N2, p["dx"]))
    if u2 is None:
        return {"status": "numerical_failure", "stage": "size"}
    s2 = _sh_stats(u2, thr)
    size_independent = bool(abs(s2["area"] - s1["area"]) <= max(10, 0.15 * max(s1["area"], 1))
                            and s2["ncomp"] == s1["ncomp"])

    return _judge(s1, persistence_change, recovers, size_independent, drift,
                  seeded_localization, extra={
                      "ncomp_settle": s0["ncomp"], "ncomp_hold": s1["ncomp"],
                      "ncomp_heal": sh_["ncomp"], "ncomp_size": s2["ncomp"],
                      "area_hold": s1["area"], "area_size": s2["area"]})


def _sh_stats(u, thr):
    """swift_hohenberg.individual_stats を使いつつ、連結成分数を |u|>thr で数え直す。

    individual_stats の `peaks` は |u|>0.6 固定なので、支持領域と同じ閾値で数えた
    ncomp を G1 用に別に取る。
    """
    from scipy import ndimage
    st = whites.sh.individual_stats(u, thr)
    m = np.abs(np.asarray(u)) > float(thr)
    _, ncomp = ndimage.label(m)
    return {"area": st["area"], "amax": st["amax"], "centroid": st["centroid"],
            "ncomp": int(ncomp), "area_fraction": st["area"] / float(u.size)}


def _drift(c0, c1):
    if any(np.isnan(v) for v in (*c0, *c1)):
        return 0.0
    return float(np.hypot(c1[0] - c0[0], c1[1] - c0[1]))


def _judge(s1, persistence_change, recovers, size_independent, drift,
           seeded_localization, extra=None):
    """G1（連結成分1個）を前置してから、既存判定器へ丸ごと委ねる。

    assess_individuality_level は改変しない。G1 はこのキャンペーン固有の
    「純粋Level 4」要件（局在も創発）であり、判定器の閾値ではない。
    """
    area_fraction = float(s1["area_fraction"])
    single_component = bool(s1["ncomp"] == 1)

    reached, detected, mb = hl.assess_individuality_level(
        amax=s1["amax"], area_fraction=area_fraction,
        persistence_change=persistence_change,
        recovers_after_perturbation=recovers,
        size_independent=size_independent,
        centroid_drift=drift,
        localization_seeded=bool(seeded_localization))

    # 純粋Level 4 = 判定器のL4 かつ 単一連結成分（モナドから切り出していない個体）
    pure_l4 = bool(reached == 4 and single_component and not seeded_localization)
    out = {"status": "ok", "reached_level": int(reached),
           "single_component": single_component, "pure_l4": pure_l4,
           "seeded_localization": bool(seeded_localization),
           "detected": detected, "measured_by": mb,
           "area_fraction": area_fraction, "amax": float(s1["amax"]),
           "persistence_change": float(persistence_change),
           "centroid_drift": float(drift), "recovers": bool(recovers),
           "size_independent": bool(size_independent), "ncomp": int(s1["ncomp"])}
    if extra:
        out.update({k: v for k, v in extra.items()})
    return out


RUNNERS = {"mass_conserved": run_mass_conserved, "swift_hohenberg": run_swift_hohenberg}
