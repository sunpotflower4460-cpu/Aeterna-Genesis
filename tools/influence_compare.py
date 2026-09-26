"""Compare how a tiny poke spreads in each white of the lab (H5: does "an outside not yet reached" exist?).

    python tools/influence_compare.py                  # all lab whites, seed 1, after 5 frames of warm-up
    python tools/influence_compare.py --whites wave-phi4 gray-scott

For each white: copy the universe (twin), poke the first field by 1e-6 at the centre (PUT IN), run both, and
classify the spreading of the difference (genesis/diagnostics/influence.py): steady (finite speed, like light),
slowing (like diffusion), nonlocal (farther than one cell per step from the first sample: global / FFT operators).
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from genesis.diagnostics import influence as inf
from tools.lab import whites
from tools.lab.universe import Universe


def measure(white_id: str, seed: int = 1, warm_frames: int = 5, samples: int = 20) -> dict:
    u = Universe(white_id, seed)
    u.advance(warm_frames * u.white.steps_per_frame)
    key = next(iter(u.state))
    spf = max(2, u.white.steps_per_frame // 4)

    def adv(state, n):
        v = u.clone()
        v.state = {k: np.array(x, copy=True) for k, x in state.items()}
        v.advance(n)
        return v.state

    point = tuple(s // 2 for s in u.state[key].shape)
    res = inf.twin_influence(u.state, adv, key, point, 1e-6, samples, spf, u.dt)
    first = res["rows"][0]
    return {"white": white_id, "field": key, "kind": inf.kind(res, spf), "front_speed": res["front_speed"],
            "speed_ratio": res["speed_ratio"], "lin_over_sqrt": res["lin_over_sqrt"], "alpha": res["alpha"], "first_t": first["t"], "first_front": first["front"],
            "first_touched": first["touched"], "box_max_r": res["box_max_r"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--whites", nargs="*", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = [measure(w) for w in (a.whites or list(whites.registry()))]
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print(f"{r['white']:18s} {r['kind']:8s} lin/sqrt {r['lin_over_sqrt']}  α {r['alpha']}  first t={r['first_t']:g}: front {r['first_front']:g}"
                  f" / box {r['box_max_r']:g}, touched {r['first_touched']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
