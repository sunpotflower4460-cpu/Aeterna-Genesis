"""Which rotation lasts longest? The last torus of the standard map (P16, H7).

    python tools/golden_torus.py --out /tmp/gt

For every kick strength K on a grid: the rotational invariant circles (tori of the kicked rotor) that still exist
(genesis/models/standard_map.py). For each target rotation number -- the golden ratio 1/φ, 1/π, 1/e, 1/√2,
√2 − 1 -- the largest K at which a circle within `delta` of it still exists ("its last K"). Known: the golden circle
is the last of all, at K ≈ 0.971635 (Greene 1979). Image: rotation number of the surviving circles against K.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from genesis.models import standard_map as sm
from tools.snapshot import render_field

TARGETS = {"1/phi": (np.sqrt(5.0) - 1.0) / 2.0, "1/pi": 1.0 / np.pi, "1/e": 1.0 / np.e,
           "1/sqrt2": 1.0 / np.sqrt(2.0), "sqrt2-1": np.sqrt(2.0) - 1.0}
K_GRID = [round(k, 3) for k in list(np.arange(0.5, 0.95, 0.05)) + list(np.arange(0.95, 0.9801, 0.0025))]


def run(K_grid=K_GRID, delta: float = 1e-3, n: int = 4001, N: int = 20000):
    rows, last = [], {k: None for k in TARGETS}
    for K in K_grid:
        c = sm.circles(K, n, N)
        near = {name: (float(np.min(np.abs(c - v))) if c.size else None) for name, v in TARGETS.items()}
        for name, d in near.items():
            if d is not None and d < delta:
                last[name] = K
        rows.append({"K": K, "circles": int(c.size), "omegas": [round(float(w), 6) for w in c][:: max(1, c.size // 400)],
                     "nearest": {k: (round(v, 6) if v is not None else None) for k, v in near.items()}})
    survivors = next((r for r in reversed(rows) if r["circles"]), None)
    return {"delta": delta, "rows": rows, "last_K": last,
            "last_circles": {"K": survivors["K"], "omegas": survivors["omegas"]} if survivors else None,
            "first_K_without_circles": next((r["K"] for r in rows if r["circles"] == 0), None)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    r = run()
    img = np.zeros((300, len(r["rows"])))
    for j, row in enumerate(r["rows"]):
        for w in row["omegas"]:
            img[299 - int(w * 299), j] = 1.0
    render_field(img, str(out / "golden_torus.png"), px=720)
    for row in r["rows"]:
        print(f"K={row['K']}: circles {row['circles']} | nearest circle to "
              + ", ".join(f"{k} {v}" for k, v in row["nearest"].items()), flush=True)
    print(f"last K with a circle within {r['delta']}: {r['last_K']} | last circles {r['last_circles']}"
          f" | first K without any: {r['first_K_without_circles']}", flush=True)
    (out / "golden_torus.json").write_text(json.dumps(r, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
