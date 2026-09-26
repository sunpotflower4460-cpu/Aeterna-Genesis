"""Does a vortex have its own rhythm? (P9-Q1, complex Ginzburg–Landau, local, 2D)

    python tools/vortex_rhythm.py --out /tmp/rhythm

dA/dt = A + (1 + ib)∇²A − (1 + ic)|A|²A with b = 0 (put in: the law, c). A plane wave of wavenumber k turns its
phase at ω = c(1 − k²); with no vortex at all the medium beats at ω₀ = c. From noise (t = 0: A ≈ 0 + noise,
128², seeds 1–3) spirals grow around vortex cores. Measured over the last 100 t of 800: ω at every site where
|A| > 0.5, the spread across the whole box, the most common local wavenumber k, the number of vortices.
Control (put in, to compare): the same law started from the uniform oscillation A = 1 + tiny noise, which has no
vortex; the explicit time step shifts its ω a little above c, so spirals are compared with the control
(ω / ω_control = 1 − k² for a plane wave). PNGs: the phase of seed 1 and its ω map.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.diagnostics import measures
from genesis.diagnostics import rhythm as rh
from genesis.models import cgl_local as cl
from tools.snapshot import render_field

DT = 0.05


def run(c: float, seed: int, n: int = 128, T: float = 800.0, win: float = 100.0, uniform: bool = False) -> dict:
    p = {"b": 0.0, "c": c}
    rng = np.random.default_rng(seed)
    A = (1.0 + 0j + cl.make_initial((n, n), 0.01, rng)) if uniform else cl.make_initial((n, n), 0.01, rng)
    steps, w0, every = int(round(T / DT)), int(round((T - win) / DT)), 10
    stack = []
    for k in range(steps):
        A = cl.step(A, DT, p)
        if k >= w0 and (k - w0) % every == 0:
            stack.append(np.angle(A))
    om = rh.frequencies(np.array(stack), every * DT)
    kk = rh.local_wavenumber(A)
    good = np.abs(A) > 0.5
    k_mode = rh.mode(kk[good & (kk < 1.0)])
    q = np.percentile(om[good], [5, 50, 95])
    return {"c": c, "seed": seed, "uniform_start": uniform, "vortices": int(measures.winding_defect_count(A)),
            "omega_p5_50_95": [round(float(x), 5) for x in q], "omega_uniform": c,
            "k_mode": round(k_mode, 4), "omega_from_k": round(c * (1 - k_mode ** 2), 5),
            "k_from_omega": round(float(np.sqrt(max(0.0, 1 - q[1] / c))), 4), "A": A, "om": om}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = []
    for c in (0.5, 0.8, 1.2):
        ctrl = None
        for seed, uniform in ((1, True), (1, False), (2, False), (3, False)):
            r = run(c, seed, uniform=uniform)
            if seed == 1 and not uniform:
                render_field(np.angle(r["A"]), str(out / f"phase_c{c}.png"))
                render_field(r["om"], str(out / f"omega_c{c}.png"))
            r.pop("A"), r.pop("om")
            if uniform:
                ctrl = r["omega_p5_50_95"][1]
            # the explicit time step shifts every frequency a little (the control shows it); compare like with like
            r["omega_over_control"] = round(r["omega_p5_50_95"][1] / ctrl, 5)
            r["k_from_ratio"] = round(float(np.sqrt(max(0.0, 1 - r["omega_over_control"]))), 4)
            res.append(r)
            tag = "uniform start (control)" if uniform else f"seed {seed}"
            print(f"c={c} {tag}: vortices {r['vortices']} | ω p5/50/95 {r['omega_p5_50_95']} (no-vortex ω₀ = {c})"
                  f" | ω / control {r['omega_over_control']} → k {r['k_from_ratio']} vs most common k {r['k_mode']}", flush=True)
    (out / "summary.json").write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
