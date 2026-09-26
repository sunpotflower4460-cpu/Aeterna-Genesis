"""First look at the light-and-phase white (lattice Abelian Higgs): do quantized flux vortices grow from the hill?

    python tools/higgs_first_look.py --out /tmp/higgs              # β = 0.5 / 2 / 8, closed and cooled, seeds 1-3
    python tools/higgs_first_look.py --out /tmp/higgs --quick

From t = 0 (φ ≈ 0 + noise 0.01, no gauge field, at rest; e = 0.3, v = 1, dt = 0.2, 128²) up to T:
* the number of vortices (gauge-invariant winding per plaquette) over time -- meaningful only once the field
  has fallen off the hill (mean |φ| > v/2): on the hill the phase of the tiny noise winds everywhere,
* Gauss's law residual and energy,
* at the end, for every vortex farther than 2R from any other: the magnetic flux inside radius R, in units of 2π
  (quantization), and the total Σ|flux| / (2π · number of vortices).
Cooling (uniform friction γ > 0) is PUT IN; so are the law (λ, e) and the t = 0 noise. Writes summary.json + PNGs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import abelian_higgs as ah
from tools.snapshot import render_field


def isolated_flux(phi, th, R: float) -> tuple[int, list[float]]:
    w = ah.winding(phi, th)
    ys, xs = np.nonzero(w)
    N, M = w.shape
    out = []
    for k, f, (y, x) in ah.flux_around(th, w, R):
        d = [np.hypot(min(abs(y - a), N - abs(y - a)), min(abs(x - b), M - abs(x - b)))
             for a, b in zip(ys, xs) if (a, b) != (y, x)]
        if not d or min(d) > 2 * R:
            out.append(round(f / (2 * np.pi) / k, 4))
    return int((w != 0).sum()), out


def run(lam: float, gamma: float, seed: int, T: float, n: int, out: Path, snap: bool) -> dict:
    p = dict(ah.DEFAULTS, lam=lam, gamma=gamma)
    s = ah.make_initial((n, n), np.random.default_rng(seed), p)
    series, steps = [], int(round(T / p["dt"]))
    for k in range(steps + 1):
        if k % int(round(10 / p["dt"])) == 0:
            w = ah.winding(s[0], s[2])
            series.append({"t": round(k * p["dt"], 1), "vortices": int((w != 0).sum()), "net": int(w.sum()),
                           "E": round(ah.energy(*s, p), 3), "gauss": float(np.abs(ah.gauss_residual(s[0], s[1], s[3])).max()),
                           "mean_amp": round(float(np.abs(s[0]).mean()), 4)})
        if k < steps:
            s = ah.step(*s, p)
    total, iso = isolated_flux(s[0], s[2], 12)
    F = ah.flux(s[2])
    tag = f"lam{lam}_g{gamma}_s{seed}"
    if snap:
        render_field(np.abs(s[0]), str(out / f"{tag}_amp.png"))
        render_field(F, str(out / f"{tag}_flux.png"))
    return {"lam": lam, "e": p["e"], "beta": round(lam / (2 * p["e"] ** 2), 3), "gamma": gamma, "seed": seed, "T": T,
            "series": series, "vortices_end": total, "isolated_flux_over_2pi": iso,
            "sum_abs_flux_per_vortex": round(float(np.abs(F).sum() / (2 * np.pi) / total), 4) if total else None,
            "max_abs_plaquette": round(float(np.abs(F).max()), 4)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, help="subset like 0.36/0.01")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds, T, n = ([1], 300.0, 96) if a.quick else ([1, 2, 3], 1500.0, 128)
    res = []
    for lam in (0.09, 0.36, 1.44):                    # β = λ / (2e²) = 0.5, 2, 8 at e = 0.3
        for gamma in (0.0, 0.01):
            for seed in seeds:
                if a.only and f"{lam}/{gamma}" not in a.only:
                    continue
                r = run(lam, gamma, seed, T, n, out, snap=(seed == seeds[0]))
                res.append(r)
                fallen = [x for x in r["series"] if x["mean_amp"] > 0.5 * 1.0]
                peak = max([x["vortices"] for x in fallen] or [0])
                print(f"β={r['beta']:<4} γ={gamma:<5} seed={seed}: peak {peak} vortices → end {r['vortices_end']}"
                      f" | isolated flux/2π {r['isolated_flux_over_2pi'][:6]} | Σ|flux|/2π per vortex {r['sum_abs_flux_per_vortex']}"
                      f" | max gauss {max(x['gauss'] for x in r['series']):.1e} | max|F| {r['max_abs_plaquette']}", flush=True)
    name = "summary.json" if not a.only else "summary_" + "_".join(x.replace("/", "-") for x in a.only) + ".json"
    (out / name).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
