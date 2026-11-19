#!/usr/bin/env python3
"""e060 Phase 1 — 広域存在探索（Sobol・1条件1 seed・settle+hold のみ）。

「そもそも単一の持続個体が存在するか」を安価に判定して足切りする段。
raw field は保存せず、全条件のコンパクトな台帳だけを残す（前回の1.4GB問題の回避）。

通過ラベルは PERSISTENT_SINGLE_CANDIDATE ただ一つ。前回の
gl-haiku-1000-robustness では min_reached_level=1 が緩すぎて200条件すべてが通過し
条件間を弁別できなかった——その反省に基づく設計である。

探索軸は Phase 0 で凍結済みの範囲。解像度・領域サイズ・摂動強度は探索軸に混ぜない
（それらは Phase 3/4 の検証軸）。

    python -m experiments.e060_l4_monad_frontier.phase1 --white mass_conserved -n 256
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import qmc

from . import classify as C
from . import quench as Q
from .phase0 import RESULTS, code_sha

# --- 探索軸（Phase 1 開始前に凍結する） ----------------------------------------
# 解像度 N・領域サイズ・摂動強度は含めない（検証軸として後段で使う）。
# 各白のクエンチ対象パラメータ（quench.QUENCHABLE）の軸は「段2（最終・保持）」の
# 値を表す。段1（核生成）の値は QUENCH_AXES 側で別に探索する。
AXES = {
    "mass_conserved": {
        # b0 = 保存される平均組成。3D既知: b0>=3.0 で単一球・2.5 で分裂。2D窓は未知。
        "b0":     {"min": 1.0,   "max": 6.0,   "scale": "linear"},
        "Da":     {"min": 0.02,  "max": 0.5,   "scale": "log"},
        "Db":     {"min": 0.5,   "max": 8.0,   "scale": "log"},
        "k0":     {"min": 0.01,  "max": 0.20,  "scale": "log"},   # 段2（保持）の反応レート
        "gamma":  {"min": 0.5,   "max": 2.0,   "scale": "linear"},
        "delta":  {"min": 0.5,   "max": 2.0,   "scale": "linear"},
        "noise_amplitude": {"min": 1e-4, "max": 1e-1, "scale": "log"},
    },
    "swift_hohenberg": {
        # r<0 は u=0 が線形安定（Phase 0 の B 対照で DIES を確認）。r>0 側も掃く。
        "r":      {"min": -0.8,  "max": 0.4,   "scale": "linear"},   # 段2（保持）の線形係数
        "b":      {"min": 0.5,   "max": 3.5,   "scale": "linear"},
        "dx":     {"min": 0.35,  "max": 0.9,   "scale": "linear"},
        "noise_amplitude": {"min": 1e-4, "max": 5e-1, "scale": "log"},
    },
}

# 二段クエンチの追加軸（空間一様・時間プログラムのみ。quench.py 参照）。
# value1 = 段1（核生成側）の値、switch_frac = 総ステップ中の段1割合。
# mass_conserved: k0 を高レート側（核生成しやすい）へ一時的に上げてから既定域へ落とす。
# swift_hohenberg: r を正側（一様状態が不安定）から負側（既定域=局在双安定）へ落とす。
QUENCH_AXES = {
    "mass_conserved": {
        "value1":       {"min": 0.05, "max": 0.6,  "scale": "log"},
        "switch_frac":  {"min": 0.05, "max": 0.5,  "scale": "linear"},
    },
    "swift_hohenberg": {
        "value1":       {"min": 0.05, "max": 0.6,  "scale": "linear"},
        "switch_frac":  {"min": 0.05, "max": 0.5,  "scale": "linear"},
    },
}

# 各白の探索専用 seed（Phase 3-6 の検証用 seed とは重ならないよう分離する。
# docs/ANTI_DRIFT.md 精密化⑤「発見AIが同seedで自己検証しない」）。
DISCOVERY_SEED = 1000
VERIFICATION_SEED_BASE = 5000


def _scale(spec, u):
    lo, hi = float(spec["min"]), float(spec["max"])
    if spec["scale"] == "log":
        return float(np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo))))
    return float(lo + u * (hi - lo))


def sample(white, n, sobol_seed=0, with_quench=True):
    """Sobol列で条件を生成。n は2の冪が望ましい（qmc の均一性のため）。

    with_quench=True なら QUENCH_AXES の value1/switch_frac も同じ Sobol 列に含める
    （物理軸とクエンチ軸を独立にランダムサンプルすると相関構造が失われるため）。
    """
    axes = dict(AXES[white])
    qaxes = QUENCH_AXES[white] if with_quench else {}
    keys = sorted(axes) + [f"__quench_{k}" for k in sorted(qaxes)]
    sob = qmc.Sobol(d=len(keys), scramble=True, seed=sobol_seed)
    pts = sob.random(n)
    out = []
    for row in pts:
        cond = {}
        for k, u in zip(keys, row):
            if k.startswith("__quench_"):
                cond[k] = _scale(qaxes[k[len("__quench_"):]], u)
            else:
                cond[k] = _scale(axes[k], u)
        out.append(cond)
    return out


def _build_quench(white, cond):
    """cond の __quench_value1 / __quench_switch_frac から quench.py の辞書を組む。

    段2（保持）の値は該当パラメータの通常軸（例: mass_conserved の k0, swift_hohenberg
    の r）をそのまま使う——二重に定義しない。
    """
    if "__quench_value1" not in cond:
        return None
    param = Q.QUENCHABLE[white][0]
    return {"param": param, "value_1": float(cond["__quench_value1"]),
            "value_2": float(cond[param]), "switch_frac": float(cond["__quench_switch_frac"])}


def _one(job):
    white, idx, cond, seed, N = job
    quench = _build_quench(white, cond)
    params = {k: v for k, v in cond.items()
              if k != "noise_amplitude" and not k.startswith("__quench_")}
    noise = float(cond["noise_amplitude"])
    t = time.time()
    try:
        r = C.SCREENS[white](params, seed=seed, N=N, noise_amp=noise,
                             seeded_localization=False, quench=quench)
    except Exception as exc:                       # 失敗も記録して先へ進む（消さない）
        r = {"status": "error", "label": "NUMERICAL_FAILURE", "error": f"{type(exc).__name__}: {exc}"}
    r.update({"white": white, "trial_index": idx, "seed": seed, "N": N,
              "parameters": cond, "quench": quench, "seconds": round(time.time() - t, 3),
              "seeded_localization": False})
    return r


def run(white, n=256, N=64, workers=4, sobol_seed=0, seed=DISCOVERY_SEED, with_quench=True):
    conds = sample(white, n, sobol_seed=sobol_seed, with_quench=with_quench)
    jobs = [(white, i, c, seed, N) for i, c in enumerate(conds)]
    started = time.time()
    if workers > 1:
        with mp.Pool(workers) as pool:
            rows = pool.map(_one, jobs, chunksize=4)
    else:
        rows = [_one(j) for j in jobs]
    elapsed = time.time() - started

    labels = Counter(r["label"] for r in rows)
    survivors = [r for r in rows if r["label"] == C.PASS_LABEL]
    per_trial = [r["seconds"] for r in rows]
    return {
        "phase": 1, "white": white, "code_sha": code_sha(),
        "n_conditions": n, "N": N, "workers": workers,
        "discovery_seed": seed, "sobol_seed": sobol_seed, "with_quench": with_quench,
        "axes": AXES[white],
        "quench_axes": QUENCH_AXES[white] if with_quench else None,
        "frozen_thresholds": dict(C.THRESHOLDS),
        "label_counts": dict(labels),
        "n_survivors": len(survivors),
        "survivors": sorted(survivors, key=lambda r: r["area_fraction"]),
        "seconds_wall": round(elapsed, 1),
        "seconds_per_trial_mean": round(float(np.mean(per_trial)), 3),
        "seconds_per_trial_max": round(float(np.max(per_trial)), 3),
        "registry": [{k: v for k, v in r.items() if k != "parameters"} | {"parameters": r["parameters"]}
                     for r in rows],
    }


def main():
    ap = argparse.ArgumentParser(description="e060 Phase 1 broad existence search")
    ap.add_argument("--white", choices=sorted(AXES), required=True)
    ap.add_argument("-n", "--n-conditions", type=int, default=256)
    ap.add_argument("-N", "--grid", type=int, default=64)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sobol-seed", type=int, default=0)
    ap.add_argument("--no-quench", action="store_true", help="1段（従来）ICのみで走らせる")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    res = run(args.white, n=args.n_conditions, N=args.grid,
              workers=args.workers, sobol_seed=args.sobol_seed,
              with_quench=not args.no_quench)
    path = Path(args.out or (RESULTS / f"phase1_{args.white}.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"white={res['white']}  n={res['n_conditions']}  N={res['N']}  "
          f"wall={res['seconds_wall']}s  mean/trial={res['seconds_per_trial_mean']}s")
    for label, cnt in sorted(res["label_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {label:30} {cnt:5}  ({100.0*cnt/res['n_conditions']:.1f}%)")
    print(f"survivors ({C.PASS_LABEL}): {res['n_survivors']}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
