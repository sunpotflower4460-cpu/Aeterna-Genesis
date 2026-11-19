#!/usr/bin/env python3
"""e060 Phase 0 — 測定器の校正。

「通すべきものを通し、落とすべきものを落とす」ことを既知の対照で確認してから、
閾値を凍結する。結果を見てから閾値を動かすことは禁止（docs/ANTI_DRIFT.md 精密化⑤）。

対照と事前登録した期待値:

  A. swift_hohenberg + bump   -> L4通過・単一個体（既知の陽性対照。pure_l4 は False）
  B. swift_hohenberg  bumpなし -> pure_l4 にならない（既定パラメータでは核生成しない）
  C. g001 TDGL                -> L4不通過（L2天井。判定器が甘くないことの確認）
  D. mass_conserved + bump    -> 質量保存が厳密（mass_drift ~ 0）

期待が外れた場合は先へ進まない（Phase 1 を実行しない）。

    python -m experiments.e060_l4_monad_frontier.phase0
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from genesis.diagnostics import measures
from genesis.models import ginzburg_landau as gl

from . import classify as C
from . import l4_protocol as P

ROOT = Path(__file__).resolve().parents[2]
RESULTS = Path(__file__).resolve().parent / "results"


def code_sha():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


def control_tdgl(seed=0, N=64, steps=400):
    """陰性対照：TDGL は L2 天井。L4 の4基準を満たさないことを測定で示す。

    TDGL は複素場なので支持領域は |psi| で取る。局在（渦芯）は出るが、
    自己修復・単一個体性は満たさない。
    """
    from scipy import ndimage
    p = dict(gl.DEFAULTS)
    rng = np.random.default_rng(seed)
    psi = gl.make_initial((N, N), p["noise_amplitude"], rng)
    for i in range(steps):
        psi = gl.step(psi, i * p["dt"], p)
        if not np.all(np.isfinite(psi)):
            return {"status": "numerical_failure"}
    amp = np.abs(psi)
    thr = 0.3 * float(amp.max()) if amp.max() > 0 else 0.3
    m = amp > thr
    _, ncomp = ndimage.label(m)
    prev = psi.copy()
    for i in range(200):
        psi = gl.step(psi, (steps + i) * p["dt"], p)
    change = float(np.abs(np.abs(psi) - np.abs(prev)).max())
    return {"status": "ok", "ncomp": int(ncomp),
            "area_fraction": float(m.sum()) / m.size,
            "amax": float(np.abs(psi).max()),
            "persistence_change": change,
            "winding_defects": int(measures.winding_defect_count(psi))}


def run(seeds=(0, 1, 2)):
    started = time.time()
    out = {"phase": 0, "code_sha": code_sha(), "seeds": list(seeds), "controls": {}}

    # A. 陽性対照：SH + bump は L4 に到達し単一個体であること
    a = []
    for s in seeds:
        t = time.time()
        r = P.run_swift_hohenberg({}, seed=s, N=64, seeded_localization=True)
        r["seconds"] = round(time.time() - t, 2)
        r["seed"] = s
        a.append(r)
    out["controls"]["A_sh_with_bump"] = {
        "expectation": "reached_level == 4 and single_component and pure_l4 is False",
        "runs": a,
        "met": all(x.get("reached_level") == 4 and x.get("single_component")
                   and x.get("pure_l4") is False for x in a),
    }

    # B. 主軸の白（bumpなし）：既定パラメータでは pure_l4 にならないこと
    b = []
    for s in seeds:
        t = time.time()
        r = C.screen_swift_hohenberg({}, seed=s, N=64, seeded_localization=False)
        r["seconds"] = round(time.time() - t, 2)
        r["seed"] = s
        b.append(r)
    out["controls"]["B_sh_without_bump"] = {
        "expectation": "label != PERSISTENT_SINGLE_CANDIDATE at default parameters",
        "runs": b,
        "met": all(x.get("label") != C.PASS_LABEL for x in b),
    }

    # C. 陰性対照：TDGL は L4 の4基準を満たさない
    c = []
    for s in seeds:
        t = time.time()
        r = control_tdgl(seed=s)
        r["seconds"] = round(time.time() - t, 2)
        r["seed"] = s
        c.append(r)
    out["controls"]["C_tdgl_negative"] = {
        "expectation": "not a single compact persistent individual (L2 ceiling)",
        "runs": c,
        "met": all(x.get("status") == "ok" and not (
            x.get("ncomp") == 1 and 0.0 < x.get("area_fraction", 1.0) < 0.25
            and x.get("persistence_change", 1.0) < 1e-2) for x in c),
    }

    # D. mass_conserved の保存則が厳密であること（G0）
    d = []
    for s in seeds:
        t = time.time()
        r = C.screen_mass_conserved({}, seed=s, N=64, seeded_localization=True)
        r["seconds"] = round(time.time() - t, 2)
        r["seed"] = s
        d.append(r)
    out["controls"]["D_mass_conserved_conservation"] = {
        "expectation": "mass_drift < 1e-9 (exact conservation)",
        "runs": d,
        "met": all(x.get("status") == "ok" and x.get("mass_drift", 1.0) < 1e-9 for x in d),
    }

    out["all_controls_met"] = all(v["met"] for v in out["controls"].values())
    out["frozen_thresholds"] = dict(C.THRESHOLDS)
    out["support_threshold"] = dict(P.SUPPORT_THR)
    out["seconds_total"] = round(time.time() - started, 1)
    out["verdict"] = ("calibration_passed_thresholds_frozen" if out["all_controls_met"]
                      else "calibration_failed_do_not_proceed")
    return out


def main():
    ap = argparse.ArgumentParser(description="e060 Phase 0 calibration")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default=str(RESULTS / "phase0_calibration.json"))
    args = ap.parse_args()

    res = run(seeds=tuple(args.seeds))
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=2, ensure_ascii=False, sort_keys=True) + "\n")

    for name, ctl in res["controls"].items():
        print(f"{'PASS' if ctl['met'] else 'FAIL'}  {name}: {ctl['expectation']}")
    print(f"\nverdict: {res['verdict']}  ({res['seconds_total']}s)")
    print(f"wrote {path}")
    return 0 if res["all_controls_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
