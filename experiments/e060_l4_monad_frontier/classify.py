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

from . import ladder
from . import noise_schedule as NS
from . import quench as Q
from . import whites

# --- 凍結閾値（Phase 0 で確定・以後変更しない） --------------------------------
THRESHOLDS = {
    "amax_floor": 0.5,        # higher_levels の contrast 条件と同値
    "area_max": 0.25,         # higher_levels の localized 条件と同値
    "fill_fraction": 0.5,     # これ以上を FILLS_DOMAIN とみなす
    "steady_change": 1e-2,    # higher_levels の persistent 条件と同値
}

PASS_LABEL = "PERSISTENT_SINGLE_CANDIDATE"


def _sh_substeps(b, dt, cap=8):
    """swift_hohenberg の非線形項 b*u^3-u^5 は明示的（陰的なのは線形項 (1+lap)^2 のみ）。
    NUMERICAL_FAILURE の実測分布は b>2.5 に強く集中し（b<=2.5では失敗率0.2%、b>2.9では
    ほぼ100%）、r の符号にはほとんど依存しなかった——臨界を越える操作をやめた今も、
    大きな b では素朴な陽的オイラーの安定限界に触れる。

    ai_lab/lab.py の `_cfl_substeps`（GL拡散の陽的安定限界に対する既存パターン）に倣い、
    物理時間を変えず（steps*dtを一定に保ち）dtだけ細分化する——数値的正しさの修正で
    あって物理やICの変更ではない。genesis/models/swift_hohenberg.py 自体は書き換えない
    （既存の他実験がその厳密な数値挙動に依存し得るため）。
    """
    # 係数はPhase1本番の実測（b<=2.5で失敗率0.2%・b>2.9でほぼ100%）に合わせて校正：
    # 既定 dt=0.2 のとき b<=2.5 では nsub=1（無変更）、それ以上でだけ細分化する。
    safe_dt = 0.5 / max(float(b), 1e-9)
    return int(min(cap, max(1, np.ceil(dt / safe_dt))))


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
                          noise_amp=1e-3, seeded_localization=False, dt=None, thr=0.3,
                          quench=None, noise_schedule=None):
    """noise_schedule が与えられたら quench（法則パラメータの跨ぎ越え）は使わない。
    法則パラメータ（b0,Da,Db,k0,gamma,delta）は settle 全体で固定し、ノイズ振幅
    だけを段1（高）→段2（低）とスケジュールする（noise_schedule.py 参照）。
    """
    p = dict(whites.WHITES["mass_conserved"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    dt = float(dt if dt is not None else whites.mc.stable_dt(p, ndim=2))
    init = whites.mc_initial_bump if seeded_localization else whites.mc_initial_uniform
    rng = np.random.default_rng(seed)
    a, b = init((N, N), p, noise_amp, rng)
    a0 = a.copy()                                       # L1（差の成長）の基準となる t=0
    mass0 = float((a + b).sum())
    p_final = p if noise_schedule else Q.final_params(p, quench)

    def evolve(a, b, steps, params_at, inject_amp=None):
        for _ in range(steps):
            a, b = whites.mc.step(a, b, dt, params_at)
            if inject_amp:                               # 熱浴ノイズ（a+bの厳密保存を壊さないよう両方に対称に加算）
                da = NS.kick(a.shape, inject_amp, rng, dt=dt)
                a = a + da; b = b - da
            if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
                return None, None
        return a, b

    if noise_schedule:
        n1, n2 = NS.stage_lengths(settle, noise_schedule["switch_frac"])
        a, b = evolve(a, b, n1, p, inject_amp=noise_schedule["amp1"])
        if a is not None:
            a, b = evolve(a, b, n2, p, inject_amp=noise_schedule["amp2"])
    else:
        for stage_p, n in Q.stages(p, quench, settle):  # 段1（核生成）→ 段2（局在安定）
            a, b = evolve(a, b, n, stage_p)
            if a is None:
                break
    if a is None:
        return _fail("settle")
    s0 = whites.mc_support_stats(a, thr)
    prev = a.copy()
    a, b = evolve(a, b, hold, p_final)                  # hold は最終法則の下で測る
    if a is None:
        return _fail("hold")
    s1 = whites.mc_support_stats(a, thr)
    change = float(np.abs(a - prev).max())
    mass_drift = abs(float((a + b).sum()) - mass0) / (abs(mass0) + 1e-30)
    return _ok(s0, s1, change, field_t0=a0, field_late=a,
               extra={"mass_drift": mass_drift, "dt": dt})


def screen_swift_hohenberg(params, *, seed, N=64, settle=2500, hold=800,
                           noise_amp=1e-3, seeded_localization=False, thr=0.3,
                           quench=None, noise_schedule=None):
    """noise_schedule が与えられたら quench（r を臨界を越えて動かす操作）は使わない。
    r は settle 全体で（サンプルされた双安定域の値に）固定し、ノイズ振幅だけを
    段1（高）→段2（低）とスケジュールする（noise_schedule.py 参照）。
    """
    from .l4_protocol import _sh_stats
    p = dict(whites.WHITES["swift_hohenberg"]["defaults"])
    p.update({k: float(v) for k, v in params.items()})
    nsub = _sh_substeps(p["b"], p["dt"])                 # b依存の陽的安定サブステップ（物理時間は不変）
    if nsub > 1:
        p["dt"] = p["dt"] / nsub
        settle, hold = settle * nsub, hold * nsub
    init = whites.sh_initial_bump if seeded_localization else whites.sh_initial_uniform
    rng = np.random.default_rng(seed)
    u = init((N, N), p, noise_amp, rng)
    u0 = u.copy()                                       # L1（差の成長）の基準となる t=0
    k2 = whites.sh._k2(N, p["dx"])       # dx はクエンチしないので k2 は不変
    p_final = p if noise_schedule else Q.final_params(p, quench)

    def evolve(u, steps, params_at, inject_amp=None):
        for _ in range(steps):
            u = whites.sh.step(u, params_at, k2)
            if inject_amp:
                u = u + NS.kick(u.shape, inject_amp, rng, dt=params_at["dt"])
            if not np.all(np.isfinite(u)):
                return None
        return u

    if noise_schedule:
        n1, n2 = NS.stage_lengths(settle, noise_schedule["switch_frac"])
        u = evolve(u, n1, p, inject_amp=noise_schedule["amp1"])
        if u is not None:
            u = evolve(u, n2, p, inject_amp=noise_schedule["amp2"])
    else:
        for stage_p, n in Q.stages(p, quench, settle):  # 段1（核生成）→ 段2（局在安定）
            u = evolve(u, n, stage_p)
            if u is None:
                break
    if u is None:
        return _fail("settle")
    s0 = _sh_stats(u, thr)
    prev = u.copy()
    u = evolve(u, hold, p_final)                        # hold は最終法則の下で測る
    if u is None:
        return _fail("hold")
    s1 = _sh_stats(u, thr)
    change = float(np.abs(u - prev).max())
    return _ok(s0, s1, change, field_t0=u0, field_late=u)


def _fail(stage):
    return {"status": "numerical_failure", "stage": stage,
            "label": "NUMERICAL_FAILURE", "ncomp": None, "area_fraction": None,
            "amax": None, "persistence_change": None}


def _ok(s0, s1, change, field_t0=None, field_late=None, extra=None):
    label = classify("ok", s0, s1, change)
    out = {"status": "ok", "label": label,
           "ncomp_settle": int(s0["ncomp"]), "ncomp": int(s1["ncomp"]),
           "area_fraction": float(s1["area_fraction"]), "amax": float(s1["amax"]),
           "persistence_change": float(change)}
    if field_t0 is not None:
        # 下位ゲート（L1/L2）を測って記録する。Phase 1 の段階では L4 判定はまだ
        # 行わないので individual_level4=False とし、reached_level は最大2に留まる。
        out.update(ladder.summarize(
            field_t0, field_late, ncomp=s1["ncomp"],
            area_fraction=s1["area_fraction"], persistence_change=change,
            individual_level4=False, centroid_drift=0.0, complex_field=False))
    if extra:
        out.update(extra)
    return out


SCREENS = {"mass_conserved": screen_mass_conserved,
           "swift_hohenberg": screen_swift_hohenberg}
