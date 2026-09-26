"""H7: rotations that never meet -- from the two-arm π picture (Infinite-Lab) to a many-mode universe.

    python tools/two_arm_recurrence.py --out /tmp/h7

1. Two arms, z(t) = e^{it} + e^{ict} (sunpotflower4460-cpu/-infinite-lab, Experiment 04): for c = π, 22/7, 355/113,
   φ+1 and √10, the record near returns up to q = 40000 (distance of the second arm when the first is home),
   compared with the continued fraction convergents of c. π is computed here to 60 digits (Machin, Decimal).
2. The same question for a wave white: the linear modes of the φ⁴ vacuum on a ring of N cells,
   ω_k = sqrt(m² + 4 sin²(π k / N)), m² = 2 (the white's own mass gap), each started at phase 0.
   D(t) = rms_k |e^{iω_k t} − 1| for N = 2, 4, 16, 64 modes, 50 < t ≤ 10⁵: how close does the state come back?
Nothing here is fitted; everything is computed from the law and the numbers.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np

from genesis.diagnostics.recurrence import continued_fraction, convergents, mode_returns, two_arm_returns


def machin_pi(digits: int = 60) -> Decimal:
    getcontext().prec = digits + 10

    def arctan_inv(x: int) -> Decimal:
        x = Decimal(x)
        total, term, n, sign = Decimal(0), 1 / x, 1, 1
        x2 = x * x
        while term > Decimal(10) ** -(digits + 5):
            total += sign * term / n
            term /= x2
            n += 2
            sign = -sign
        return total

    return 4 * (4 * arctan_inv(5) - arctan_inv(239))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--qmax", type=int, default=40000)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pi = machin_pi()
    phi1 = (1 + Decimal(5).sqrt()) / 2 + 1
    cases = {"π": pi, "22/7": Decimal(22) / 7, "355/113": Decimal(355) / 113, "φ+1": phi1, "√10": Decimal(10).sqrt()}
    res = {"pi_60": str(pi)[:62], "two_arm": {}, "modes": {}}
    for name, c in cases.items():
        cf = continued_fraction(c, 8)
        conv = [f"{f.numerator}/{f.denominator}" for f in convergents(cf)]
        rows = two_arm_returns(float(c), a.qmax)
        res["two_arm"][name] = {"continued_fraction": cf, "convergents": conv, "record_returns": rows}
        print(f"{name:8s} cf {cf}  convergents {conv[:6]}")
        print("         record returns (q: distance, petals): " +
              ", ".join(f"{r['q']}: {r['distance']:.2e}, {r['petals']}" for r in rows[-6:]))
    m = np.sqrt(2.0)
    times = np.linspace(0.0, 1e5, 2_000_001)
    times = times[times > 50.0]                    # "coming back" means after having left: skip the start
    for n_modes in (2, 4, 16, 64):
        k = np.arange(n_modes)
        om = np.sqrt(m * m + 4 * np.sin(np.pi * k / n_modes) ** 2)
        d = mode_returns(om, times)
        i = int(np.argmin(d))
        res["modes"][n_modes] = {"omegas": [round(x, 6) for x in om], "min_D": float(d[i]), "t_at_min": float(times[i]),
                                 "mean_D": float(d.mean()), "fraction_below_0.1": float((d < 0.1).mean())}
        print(f"{n_modes:3d} modes: closest return D = {d[i]:.4f} at t = {times[i]:.1f} (mean D {d.mean():.3f},"
              f" time below 0.1: {100 * (d < 0.1).mean():.4f} %)")
    (out / "summary.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
