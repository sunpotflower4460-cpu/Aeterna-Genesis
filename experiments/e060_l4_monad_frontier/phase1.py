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
from .phase0 import RESULTS, code_sha

# --- 探索軸（Phase 1 開始前に凍結する） ----------------------------------------
# 解像度 N・領域サイズ・摂動強度は含めない（検証軸として後段で使う）。
AXES = {
    "mass_conserved": {
        # b0 = 保存される平均組成。3D既知: b0>=3.0 で単一球・2.5 で分裂。2D窓は未知。
        "b0":     {"min": 1.0,   "max": 6.0,   "scale": "linear"},
        "Da":     {"min": 0.02,  "max": 0.5,   "scale": "log"},
        "Db":     {"min": 0.5,   "max": 8.0,   "scale": "log"},
        "k0":     {"min": 0.01,  "max": 0.20,  "scale": "log"},
        "gamma":  {"min": 0.5,   "max": 2.0,   "scale": "linear"},
        "delta":  {"min": 0.5,   "max": 2.0,   "scale": "linear"},
        "noise_amplitude": {"min": 1e-4, "max": 1e-1, "scale": "log"},
    },
    "swift_hohenberg": {
        # r<0 は u=0 が線形安定（Phase 0 の B 対照で DIES を確認）。r>0 側も掃く。
        "r":      {"min": -0.8,  "max": 0.4,   "scale": "linear"},
        "b":      {"min": 0.5,   "max": 3.5,   "scale": "linear"},
        "dx":     {"min": 0.35,  "max": 0.9,   "scale": "linear"},
        "noise_amplitude": {"min": 1e-4, "max": 5e-1, "scale": "log"},
    },
}

# 各白の探索専用 seed（Phase 3-6 の検証用 seed とは重ならないよう分離する。
# docs/ANTI_DRIFT.md 精密化⑤「発見AIが同seedで自己検証しない」）。
DISCOVERY_SEED = 1000
VERIFICATION_SEED_BASE = 5000


def sample(white, n, sobol_seed=0):
    """Sobol列で条件を生成。n は2の冪が望ましい（qmc の均一性のため）。"""
    axes = AXES[white]
    keys = sorted(axes)
    sob = qmc.Sobol(d=len(keys), scramble=True, seed=sobol_seed)
    pts = sob.random(n)
    out = []
    for row in pts:
        cond = {}
        for k, u in zip(keys, row):
            spec = axes[k]
            lo, hi = float(spec["min"]), float(spec["max"])
            if spec["scale"] == "log":
                cond[k] = float(np.exp(np.log(lo) + u * (np.log(hi) - np.log(lo))))
            else:
                cond[k] = float(lo + u * (hi - lo))
        out.append(cond)
    return out


def _one(job):
    white, idx, cond, seed, N = job
    params = {k: v for k, v in cond.items() if k != "noise_amplitude"}
    noise = float(cond["noise_amplitude"])
    t = time.time()
    try:
        r = C.SCREENS[white](params, seed=seed, N=N, noise_amp=noise,
                             seeded_localization=False)
    except Exception as exc:                       # 失敗も記録して先へ進む（消さない）
        r = {"status": "error", "label": "NUMERICAL_FAILURE", "error": f"{type(exc).__name__}: {exc}"}
    r.update({"white": white, "trial_index": idx, "seed": seed, "N": N,
              "parameters": cond, "seconds": round(time.time() - t, 3),
              "seeded_localization": False})
    return r


def run(white, n=256, N=64, workers=4, sobol_seed=0, seed=DISCOVERY_SEED):
    conds = sample(white, n, sobol_seed=sobol_seed)
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
        "discovery_seed": seed, "sobol_seed": sobol_seed,
        "axes": AXES[white], "frozen_thresholds": dict(C.THRESHOLDS),
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
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    res = run(args.white, n=args.n_conditions, N=args.grid,
              workers=args.workers, sobol_seed=args.sobol_seed)
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
