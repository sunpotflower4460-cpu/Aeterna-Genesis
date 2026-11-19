#!/usr/bin/env python3
"""e060 Phase 1b — DIES/FILLS 境界の追跡（一様Sobolをやめ、境界に沿って密に走る）。

設計方針の転換（Phase 1本番の結果を受けて）:

1. 核生成は r>0（SHの場合、法則を臨界の向こう側へ動かす）ではなく、r を双安定域
   （既定 r<0）に固定したまま**ノイズ振幅**を段1（高）→段2（低）とスケジュールする
   （noise_schedule.py）。これは位置・形・個数・方向を一切与えない「温度」操作であり、
   既存の quench_duration と同格のプロトコルとして第8監査に触れない。

2. 一様Sobolサンプリングではなく、**DIES と FILLS の境界を二分法で挟み込み**、
   境界に沿って密に走る。Phase 1本番で見つかった FRAGMENTS（MC 19件、SH 7件）は
   まさにこの境界の目印であり、単一個体が存在するとすれば最も期待できるのは
   「死ぬ」と「埋まる」の間の薄い遷移帯である。

主軸は「双安定域の法則パラメータ（SH: r、MC: b0）× ノイズ振幅（amp1）」の2軸。
二次パラメータ（SH: b, dx／MC: Da,Db,k0,gamma,delta）は代表値に固定する
（既定値、または少数の代表点）——組み合わせ爆発を避けつつ、まず主軸2つで
境界の形を確定させることを優先する。
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path

import numpy as np

from . import classify as C
from .phase0 import RESULTS, code_sha

# 境界追跡の対象軸（Phase 0 の凍結閾値・判定器はそのまま使う。ここは探索戦略のみ変更）。
BISECT_AXIS = {"swift_hohenberg": "r", "mass_conserved": "b0"}
BISECT_RANGE = {"swift_hohenberg": (-0.8, -0.02), "mass_conserved": (1.05, 5.95)}
# ノイズ振幅（核生成側 amp1）の探索範囲。amp2（保持側）は既定 noise_amplitude 軸の値を使う。
AMP1_RANGE = {"swift_hohenberg": (0.03, 0.6), "mass_conserved": (0.02, 0.5)}
AMP2 = {"swift_hohenberg": 0.02, "mass_conserved": 0.02}
SWITCH_FRAC = 0.3     # 段1（核生成）を settle の30%に固定（Phase 0 相当の代表値）

FIXED_SECONDARY = {
    "swift_hohenberg": {"b": 2.0, "dx": 0.5},
    "mass_conserved": {"Da": 0.1, "Db": 2.0, "k0": 0.067, "gamma": 1.0, "delta": 1.0},
}


def _screen_at(white, axis_value, amp1, seed, N):
    params = dict(FIXED_SECONDARY[white])
    params[BISECT_AXIS[white]] = float(axis_value)
    ns = {"amp1": float(amp1), "amp2": AMP2[white], "switch_frac": SWITCH_FRAC}
    r = C.SCREENS[white](params, seed=seed, N=N, noise_schedule=ns)
    r.update({"white": white, BISECT_AXIS[white]: float(axis_value), "amp1": float(amp1),
              "seed": seed, "N": N, "parameters": params, "noise_schedule": ns})
    return r


def _is_filled_side(label):
    """境界の『埋まる』側とみなすラベル（FRAGMENTS も片側に含める——多スポットは
    DIES より FILLS 寄りの失敗様式であるため、境界探索の向きとしては FILLS 側）。"""
    return label in ("FILLS_DOMAIN", "FRAGMENTS", "OSCILLATORY_CHAOS")


def bisect_axis(white, amp1, seed, N, iters=7):
    """axis（r または b0）についてDIES側からFILLS側への遷移点を二分法で挟む。

    まず既知の両端（DIES側=軸の「死にやすい」端、FILLS側=「埋まりやすい」端）を確認し、
    ブラケットできなければ None を返す（この amp1 では境界が両端の外にある）。
    全中間試行を記録して返す（境界追跡自体もコンパクト台帳の一部）。
    """
    lo, hi = BISECT_RANGE[white]
    # SH: r が大きい（0に近い）ほどFILLS寄り。MC: b0が大きいほどFILLS寄り。両白共通のこの向きを仮定。
    r_dies = _screen_at(white, lo, amp1, seed, N)
    r_fills = _screen_at(white, hi, amp1, seed, N)
    trials = [r_dies, r_fills]
    if r_dies["label"] == "DIES" and _is_filled_side(r_fills["label"]):
        a, b = lo, hi
    elif r_dies["label"] == "DIES" and r_fills["label"] == "DIES":
        return None, trials              # この amp1 では両端ともDIES：境界は範囲外
    elif _is_filled_side(r_dies["label"]) and _is_filled_side(r_fills["label"]):
        return None, trials              # 両端ともFILLS側：境界は範囲外（amp1が強すぎる）
    else:
        a, b = lo, hi                    # 予期しない組み合わせでもとりあえず挟んで二分する

    boundary = None
    for _ in range(iters):
        mid = 0.5 * (a + b)
        r_mid = _screen_at(white, mid, amp1, seed, N)
        trials.append(r_mid)
        if r_mid["label"] == "DIES":
            a = mid
        elif _is_filled_side(r_mid["label"]):
            b = mid
        else:                            # PERSISTENT_SINGLE_CANDIDATE や TRANSIENT_SINGLE
            boundary = mid
            break
        boundary = 0.5 * (a + b)
    return boundary, trials


def _one_amp1(args):
    white, amp1, seed, N, densify = args
    boundary, trials = bisect_axis(white, amp1, seed, N)
    extra = []
    if boundary is not None and densify > 0:
        # 境界の周辺を複数 seed・微小オフセットで密に走る（単発の当たりを弁別）
        span = 0.03 * (BISECT_RANGE[white][1] - BISECT_RANGE[white][0])
        offsets = np.linspace(-span, span, densify)
        for off in offsets:
            for s2 in (seed, seed + 1, seed + 2):
                extra.append(_screen_at(white, boundary + off, amp1, s2, N))
    return {"amp1": amp1, "boundary": boundary, "bisection_trials": trials, "densify_trials": extra}


def run(white, n_amp1=16, N=64, workers=4, seed=2000, densify=5):
    lo, hi = AMP1_RANGE[white]
    amp1s = np.exp(np.linspace(np.log(lo), np.log(hi), n_amp1))
    jobs = [(white, float(a), seed, N, densify) for a in amp1s]
    started = time.time()
    if workers > 1:
        with mp.Pool(workers) as pool:
            results = pool.map(_one_amp1, jobs)
    else:
        results = [_one_amp1(j) for j in jobs]
    elapsed = time.time() - started

    all_trials = []
    for r in results:
        all_trials.extend(r["bisection_trials"])
        all_trials.extend(r["densify_trials"])
    from collections import Counter
    labels = Counter(t["label"] for t in all_trials)
    survivors = [t for t in all_trials if t["label"] == C.PASS_LABEL]

    return {
        "phase": "1b_boundary", "white": white, "code_sha": code_sha(),
        "bisect_axis": BISECT_AXIS[white], "bisect_range": BISECT_RANGE[white],
        "amp1_range": AMP1_RANGE[white], "amp2": AMP2[white], "switch_frac": SWITCH_FRAC,
        "fixed_secondary": FIXED_SECONDARY[white],
        "n_amp1": n_amp1, "densify": densify, "N": N, "workers": workers, "seed_base": seed,
        "boundaries": [{"amp1": r["amp1"], "boundary": r["boundary"]} for r in results],
        "n_total_trials": len(all_trials), "label_counts": dict(labels),
        "n_survivors": len(survivors), "survivors": survivors,
        "seconds_wall": round(elapsed, 1),
        "registry": all_trials,
    }


def main():
    ap = argparse.ArgumentParser(description="e060 Phase 1b: DIES/FILLS boundary tracing")
    ap.add_argument("--white", choices=sorted(BISECT_AXIS), required=True)
    ap.add_argument("--n-amp1", type=int, default=16)
    ap.add_argument("-N", "--grid", type=int, default=64)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=2000)
    ap.add_argument("--densify", type=int, default=5)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    res = run(args.white, n_amp1=args.n_amp1, N=args.grid, workers=args.workers,
              seed=args.seed, densify=args.densify)
    path = Path(args.out or (RESULTS / f"phase1b_boundary_{args.white}.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"white={res['white']}  axis={res['bisect_axis']}  n_amp1={res['n_amp1']}  "
          f"wall={res['seconds_wall']}s  total_trials={res['n_total_trials']}")
    for label, cnt in sorted(res["label_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {label:30} {cnt:5}")
    print(f"survivors ({C.PASS_LABEL}): {res['n_survivors']}")
    bfound = [b for b in res["boundaries"] if b["boundary"] is not None]
    print(f"boundary found for {len(bfound)}/{res['n_amp1']} amp1 values")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
