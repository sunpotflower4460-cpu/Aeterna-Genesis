#!/usr/bin/env python3
"""AI Genesis Lab (minimal): an automated experimenter that searches START CONDITIONS, not designs.

AI's job (AGENTS.md / AI_EXPERIMENT_POLICY.md): NOT to build a finished shape, but to find start
conditions that grow deeper on their own. This minimal Lab:

  1. reads a PARENT room (rooms/official/room-g001-a) and the allowed search space
     (genesis/registry/param_ranges.yaml) -- it may change ONLY start-side parameters,
  2. proposes a CHILD genesis with ONE parameter changed within the allowed range,
  3. runs it FROM t=0 (2D screen) with the SAME Runner + diagnostics the Room uses (it does NOT
     redefine success criteria / thresholds -- those are imported, not copied),
  4. measures the reached Level and compares to the parent baseline,
  5. registers a dimension-transfer RISK (harness) for any 2D candidate,
  6. saves a NON-DESTRUCTIVE proposal (never touches rooms/official, parent Room, or thresholds).

Determinism: no Math.random for the search -- parameter values come from a fixed grid indexed by the
proposal number, so runs are reproducible. Promotion to full-3D is GATED (2d_screened only here).
"""

import argparse
import json
import os
import sys

import yaml

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import ginzburg_landau as gl  # noqa: E402
from genesis.runners import runner  # noqa: E402
from genesis.dimension import harness  # noqa: E402

# start-side knobs the Lab may vary (subset of param_ranges.yaml search_space) -> (path, grid of values)
KNOBS = {
    "noise_amplitude": [1.0e-4, 3.0e-4, 1.0e-3, 3.0e-3, 1.0e-2],
    "quench_duration": [4.0, 6.0, 8.0, 12.0, 16.0],
}


def _load_search_space():
    p = os.path.join(_REPO, "genesis", "registry", "param_ranges.yaml")
    return yaml.safe_load(open(p))["search_space"]


def _parent_baseline(quick=True):
    """Screen the parent genesis (room-g001-a defaults) in 2D from t=0 for a fair comparison."""
    g = dict(runner._DEMO_GENESIS)
    r = runner.run(g, mode="2d-screen", quick=quick)
    return r["manifest"]["summary"]["reached_level"], r["emergence"]["measured_by"]


def propose(index):
    """Deterministically pick ONE knob + value from the grid (indexed), return a child genesis + mutation."""
    knobs = sorted(KNOBS)
    knob = knobs[index % len(knobs)]
    grid = KNOBS[knob]
    val = grid[(index // len(knobs)) % len(grid)]
    g = dict(runner._DEMO_GENESIS)
    g["initial_state"] = dict(g["initial_state"])
    g["protocol"] = {"quench": dict(g["protocol"]["quench"])}
    frm = None
    if knob == "noise_amplitude":
        frm = g["initial_state"]["noise_amplitude"]
        g["initial_state"]["noise_amplitude"] = val
    elif knob == "quench_duration":
        frm = g["protocol"]["quench"]["duration"]
        g["protocol"]["quench"]["duration"] = val
    g["seed"] = 0
    mutation = {"type": "initial_state_change" if knob == "noise_amplitude" else "parameter_change",
                "param": knob, "from": frm, "to": val}
    return g, mutation


def _within_allowed(mutation, search_space):
    """Verify the proposed value is inside the allowed search-space range (AI cannot exceed it)."""
    if mutation["param"] == "noise_amplitude":
        rng = search_space["initial_state"]["noise_amplitude"]
        return rng["min"] <= mutation["to"] <= rng["max"]
    if mutation["param"] == "quench_duration":
        return 0.0 < mutation["to"] <= 40.0     # protocol duration: physical, bounded
    return False


def screen(genesis, quick=True):
    r = runner.run(genesis, mode="2d-screen", quick=quick)
    return r["manifest"]["summary"]["reached_level"], r["emergence"]["measured_by"], r["manifest"]["checksum"]


def run_lab(n=4, quick=True):
    search_space = _load_search_space()
    base_level, base_mb = _parent_baseline(quick=quick)
    dtrans, _ = harness.report(quick=quick)
    dim_risk = dtrans["dimension_risk"]["expected_transferability"]
    proposals = []
    for i in range(n):
        g, mut = propose(i)
        allowed = _within_allowed(mut, search_space)
        if not allowed:
            proposals.append({"proposal_id": "prop-%04d" % i, "mutation": mut,
                              "status": "rejected", "reason": "outside_allowed_search_space"})
            continue
        level, mb, checksum = screen(g, quick=quick)
        prop = {
            "proposal_id": "prop-%04d" % i,
            "parent_room": "room-g001-a",
            "mutation": mut,
            "genesis": g,
            "screen_2d": {"reached_level": level,
                          "mean_amplitude_growth": mb["mean_amplitude_growth"],
                          "defect_count": mb["defect_count"]},
            "vs_parent": {"parent_level": base_level, "delta_level": level - base_level},
            "dimension_transfer_risk": dim_risk,
            "checksum": checksum["final_field_sha256"][:16],
            # promotion is GATED: the Lab only 2D-screens; full-3D + Room registration is a separate,
            # human/promote-command step (AI cannot self-promote or write rooms/official).
            "status": "2d_screened",
            "promotion": {"stage": "2d_screened",
                          "next": "dimension_audit -> local_3d -> coarse_global_3d -> full_3d"},
        }
        proposals.append(prop)
    return {"parent_baseline_level": base_level, "n": n, "proposals": proposals}


def write_out(result, out_root):
    d = os.path.join(out_root, "ai_lab", "proposals")
    os.makedirs(d, exist_ok=True)
    for p in result["proposals"]:
        with open(os.path.join(d, p["proposal_id"] + ".json"), "w") as f:
            json.dump(p, f, indent=2)
    with open(os.path.join(out_root, "ai_lab", "discoveries", "summary.json"), "w") as f:
        os.makedirs(os.path.dirname(f.name), exist_ok=True)
        json.dump({"parent_baseline_level": result["parent_baseline_level"],
                   "n": result["n"],
                   "screened": [{"id": p["proposal_id"], "mutation": p.get("mutation"),
                                 "level": p.get("screen_2d", {}).get("reached_level"),
                                 "status": p["status"]} for p in result["proposals"]]}, f, indent=2)
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description="AI Genesis Lab (minimal start-condition searcher)")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out-root", default=None)
    args = ap.parse_args(argv)
    res = run_lab(n=args.n, quick=args.quick)
    print("=== AI Genesis Lab: %d proposals (parent room-g001-a, 2D-screened from t=0) ===" % args.n)
    print("  parent baseline 2D level = %d" % res["parent_baseline_level"])
    for p in res["proposals"]:
        if p["status"] == "2d_screened":
            print("  %s: %s %s->%s | level=%d (delta %+d) | risk=%s | %s"
                  % (p["proposal_id"], p["mutation"]["param"], p["mutation"]["from"], p["mutation"]["to"],
                     p["screen_2d"]["reached_level"], p["vs_parent"]["delta_level"],
                     p["dimension_transfer_risk"], p["status"]))
        else:
            print("  %s: %s -> %s (%s)" % (p["proposal_id"], p["mutation"]["param"], p["status"],
                                           p.get("reason", "")))
    print("  NOTE: 2D-screened candidates only. AI cannot self-promote to full-3D or write rooms/official.")
    if not args.no_write:
        out_root = args.out_root or os.path.join(_REPO, "ai_lab", "_demo_out")
        d = write_out(res, out_root)
        print("  wrote proposals under %s" % os.path.relpath(d, _REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
