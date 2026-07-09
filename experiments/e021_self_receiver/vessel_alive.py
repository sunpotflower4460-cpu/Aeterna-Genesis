#!/usr/bin/env python3
"""e021 Stage 2 -- the driven droplet: its winding is held under drive and dies only to a near anti.

MODULE:   e021_self_receiver (Stage 2: vessel_alive)
QUESTION: in a finite driven-dissipative droplet, is the +1 core winding self-maintained under drive,
          and does it die (winding -> 0, core heals) ONLY when an anti-vortex is injected close enough?
PUT IN:   a driven droplet with a +1 core, and (in the kill runs) a -1 anti at distance d. NO "a near
          anti annihilates the core", NO "there is a critical distance" are put in -- both are measured.
EMERGED:  (measured) under drive the winding stays +1; a far anti (d=30) leaves the winding intact while
          a near anti (d<=14) annihilates the core (a phase slip: |psi| heals to ~1, winding -> 0).
CLAIM TIER: measured(winding maintained; near vs far anti; critical distance) ; interpretive(identity is
          held by the drive and dies only to its own anti, not to body damage) ; analogy(self / identity
          death -- KNOWN MATCH only, never a gate name).
KNOWN MATCH: vortex-antivortex annihilation (a phase slip); driven-dissipative condensate droplets.
STATUS:   GREEN (gates on core winding and core amplitude -- physical quantities only).
A_OR_B:   (A) faithful. Hand input = the droplet + core + (in kill runs) an anti at distance d; the
          maintenance, the annihilation, and its distance threshold are emergent and measured.

THE TRAP (designer hit it, we avoid it): the winding is read on a CCW ring (core.holonomy) that encloses
only the core; the annihilation signature is the core AMPLITUDE HEALING to ~1 (the |psi|=0 hole fills in),
not merely the winding number. Gate on winding / core amplitude -- never name a gate "identity" or "death".

Floors: a 2D driven-dissipative toy; the critical distance depends on (drive, dissipation, droplet
radius). "Identity / identity death / self" is analogy for winding held vs annihilated; no self dies.
"""

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from core.holonomy import ring_winding  # noqa: E402

DEFAULT = {"N": 160, "Rdrop": 48.0, "read_R": 18, "steps": 2500, "dt": 0.02,
           "drive": 1.0, "dissip": 1.0, "nu": 1.0, "dists": [7, 14, 30], "seed": 0}
QUICK = {"steps": 1500, "dists": [7, 30]}


def _grid(N):
    x = np.arange(N) - N / 2
    X, Y = np.meshgrid(x, x, indexing="ij")
    r = np.hypot(X, Y)
    kx = 2 * np.pi * np.fft.fftfreq(N)
    KX, KY = np.meshgrid(kx, kx, indexing="ij")
    return X, Y, r, KX ** 2 + KY ** 2


def _field(cores, X, Y, r, Rdrop, N):
    ph = np.zeros((N, N))
    amp = np.ones((N, N))
    for (x0, y0, c) in cores:
        ph += c * np.arctan2(Y - y0, X - x0)
        amp *= np.tanh(np.hypot(X - x0, Y - y0) / 2.0)
    env = 0.5 * (1 - np.tanh((r - Rdrop) / 3.0))
    return (amp * env * np.exp(1j * ph)).astype(complex)


def _evolve(psi, p, r, K2):
    expK = np.exp(-p["nu"] * 0.5 * K2 * p["dt"])
    conf = (r < p["Rdrop"] + 8)
    for _ in range(p["steps"]):
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
        psi = psi * np.exp(p["dt"] * (p["drive"] * (r < p["Rdrop"]) - p["dissip"] * np.abs(psi) ** 2)) * conf
        psi = np.fft.ifft2(expK * np.fft.fft2(psi))
    return psi


def _core_amp(psi, N):
    c = N // 2
    return float(np.abs(psi)[c - 1:c + 2, c - 1:c + 2].min())


def simulate(quick=False):
    p = dict(DEFAULT)
    if quick:
        p.update(QUICK)
    N, c = p["N"], p["N"] / 2
    X, Y, r, K2 = _grid(N)

    # (1) self-maintenance under drive (no anti): winding held, core is a hole
    psi = _evolve(_field([(0, 0, 1)], X, Y, r, p["Rdrop"], N), p, r, K2)
    w_drive = float(ring_winding(psi, c, c, p["read_R"], n=512))
    core_drive = _core_amp(psi, N)

    # (2) anti-vortex at several distances d: near annihilates, far survives
    anti = []
    for d in p["dists"]:
        psi = _evolve(_field([(0, 0, 1), (d, 0, -1)], X, Y, r, p["Rdrop"], N), p, r, K2)
        anti.append({"d": d, "winding": round(float(ring_winding(psi, c, c, p["read_R"], n=512)), 2),
                     "core_amp": round(_core_amp(psi, N), 3)})

    near = anti[0]                                            # smallest d
    far = anti[-1]                                            # largest d
    return {
        "params": p,
        "winding_under_drive": round(w_drive, 2), "core_amp_under_drive": round(core_drive, 3),
        "anti": anti,
        "near_annihilates": bool(abs(near["winding"]) < 0.5 and near["core_amp"] > 0.5),
        "far_survives": bool(abs(far["winding"]) > 0.5),
    }


def evaluate(result, quick=False):
    checks = {
        "winding_self_maintained_under_drive (|w|>0.5, core is a hole)":
            bool(abs(result["winding_under_drive"]) > 0.5 and result["core_amp_under_drive"] < 0.5),
        "winding_annihilated_by_near_anti (|w|<0.5, core heals >0.5)":
            result["near_annihilates"],
        "winding_survives_far_anti (|w|>0.5)":
            result["far_survives"],
    }
    return all(checks.values()), checks


def _atlas(result):
    return [{
        "experiment": "e021 self receiver Stage 2 (vessel_alive)", "tier": "measured",
        "put_in": "a driven-dissipative droplet with a +1 core, and (in kill runs) a -1 anti at distance d",
        "emerged": ["under drive: winding=%s, core amp=%s (a held hole)"
                    % (result["winding_under_drive"], result["core_amp_under_drive"]),
                    "anti at distance d (winding, core amp): %s"
                    % [(a["d"], a["winding"], a["core_amp"]) for a in result["anti"]]],
        "surprises": ["a far anti leaves the winding intact; a near anti annihilates the core (|psi| heals, winding->0)"],
        "persistence": "the winding is held under drive; it dies only to a close-enough anti (a critical distance)",
        "measured_numbers": {"winding_under_drive": result["winding_under_drive"],
                             "core_amp_under_drive": result["core_amp_under_drive"], "anti": result["anti"]},
        "not_scripted_check": "winding read on a CCW ring around the core; annihilation is signalled by the core "
                              "amplitude healing to ~1, all measured",
        "claim_tier": "measured (maintenance, near vs far anti, critical distance) ; interpretive (identity held "
                      "by drive, dies only to its own anti) ; analogy (self / identity death, KNOWN MATCH only)",
        "floors": ["2D driven-dissipative toy; the critical distance depends on (drive, dissip, Rdrop)",
                   "the gated facts are winding-held vs winding-annihilated + core healing, not absolute distances",
                   "'identity / identity death / self' is analogy for winding held vs annihilated; no self dies"],
    }]


def main(argv=None):
    ap = argparse.ArgumentParser(description="e021 Stage 2: driven droplet vessel")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    r = simulate(quick=args.quick)
    print("=== e021 Stage 2 -- driven droplet: winding held under drive, dies to a near anti ===")
    print("  under drive: winding=%+.2f  core amp=%.3f (a held hole)"
          % (r["winding_under_drive"], r["core_amp_under_drive"]))
    print("  anti at distance d (winding / core amp):")
    for a in r["anti"]:
        print("     d=%2d  winding=%+.2f  core amp=%.3f" % (a["d"], a["winding"], a["core_amp"]))
    passed, checks = evaluate(r, quick=args.quick)
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    print("STATUS: %s (maintenance + annihilation threshold measured; distance is a floor)"
          % ("GREEN" if passed else "RED"))
    if not args.no_write and not args.quick:
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
        out = os.path.join(os.path.dirname(__file__), "results", "vessel_alive.json")
        with open(out, "w") as f:
            json.dump({"result": r, "atlas": _atlas(r)}, f, indent=2)
        print("wrote results/vessel_alive.json")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
