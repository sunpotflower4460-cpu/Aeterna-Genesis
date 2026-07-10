#!/usr/bin/env python3
"""Common Genesis Runner: evolve one genesis.yaml from t=0 and produce a reproducible run.

Given a genesis condition (fields, initial_state, protocol, seed) and a mode, the Runner:
  - starts from a UNIFORM near-zero disordered state + tiny noise (NO structure seeded),
  - evolves the reference field law (genesis/models/) with NO runtime intervention,
  - measures emergence by NUMBERS (genesis/diagnostics/measures.py),
  - writes manifest.json / summary.json / emergence.json / checksum.json under runs/seed-XXXX/.

`--no-write` performs the FULL computation and prints diagnostics but writes nothing (so CI can verify
that no-write actually simulates). The field checksum makes runs reproducible: same genesis + seed +
mode -> identical checksum.

Mode -> resolution/steps (2D exploration vs 3D). A mode never changes the physics, only grid/steps.
The official 3D Room (PR6) uses `full-3d`; `2d-screen`/`local-3d` are exploration/pre-computation
(DIMENSION_POLICY.md): a 2D or thin-slab success is a CANDIDATE, not a full-3D result.
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import ginzburg_landau as gl  # noqa: E402
from genesis.diagnostics import measures  # noqa: E402

CODE_VERSION = "runner-1"

MODELS = {gl.MODEL_ID: gl}

# mode -> (dimension, grid_edge, steps, snapshots)
MODES = {
    "2d-screen": (2, 96, 400, 12),
    "local-3d": (3, 32, 300, 10),
    "coarse-global-3d": (3, 48, 400, 10),
    "full-3d": (3, 96, 800, 16),
}
QUICK_MODES = {
    "2d-screen": (2, 48, 260, 10),
    "local-3d": (3, 20, 220, 8),
    "coarse-global-3d": (3, 24, 240, 8),
    "full-3d": (3, 28, 260, 8),
}


def _checksum(psi):
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(psi.real).tobytes())
    h.update(np.ascontiguousarray(psi.imag).tobytes())
    return h.hexdigest()


def _genesis_checksum(genesis):
    return hashlib.sha256(json.dumps(genesis, sort_keys=True).encode()).hexdigest()[:16]


def run(genesis, mode="2d-screen", quick=False):
    """Run one genesis condition; return a result dict (manifest/summary/emergence/checksum + traj)."""
    model = MODELS[genesis["model"]]
    dim, edge, steps, nsnap = (QUICK_MODES if quick else MODES)[mode]
    shape = tuple([edge] * dim)
    p = dict(model.DEFAULTS)
    ist = genesis.get("initial_state", {})
    if "noise_amplitude" in ist:
        p["noise_amplitude"] = ist["noise_amplitude"]
    proto = (genesis.get("protocol") or {}).get("quench")
    if proto:
        p["quench_start"] = proto.get("start", p["quench_start"])
        p["quench_duration"] = proto.get("duration", p["quench_duration"])
    rng = np.random.default_rng(genesis.get("seed", 0))
    psi = model.make_initial(shape, p["noise_amplitude"], rng)

    traj = []
    snap_every = max(1, steps // nsnap)
    f0 = model.free_energy(psi, p)
    for t in range(steps):
        psi = model.step(psi, t * p["dt"], p)
        if t % snap_every == 0 or t == steps - 1:
            skk, skprom = measures.structure_factor_peak(psi)
            traj.append({"step": t,
                         "mean_amp": measures.mean_amplitude(psi),
                         "var": measures.amplitude_variance(psi),
                         "sk_prom": skprom,
                         "defects": measures.winding_defect_count(psi)})
    f1 = model.free_energy(psi, p)

    reached, detected, measured_by = measures.assess_level(traj)
    manifest = {
        "run_id": "%s-%s-seed%04d" % (genesis["model"], mode, genesis.get("seed", 0)),
        "room_id": genesis.get("room_id", "room-scratch"),
        "seed": int(genesis.get("seed", 0)),
        "dimension": dim,
        "mode": mode,
        "manifest": {"genesis": _genesis_checksum(genesis), "solver": genesis["model"],
                     "steps": steps, "dt": p["dt"], "grid": list(shape), "code_version": CODE_VERSION},
        "summary": {"reached_level": reached,
                    "conservation_drift": round(float(f1 - f0), 6),
                    "final_mean_amplitude": round(traj[-1]["mean_amp"], 6)},
        "checksum": {"final_field_sha256": _checksum(psi)},
    }
    emergence = {
        "reached_level": reached,
        "candidate_level": min(reached + 1, 8),
        "uninterrupted_from_zero": True,
        "level_detected_by_measurement": True,
        "detected": detected,
        "measured_by": {k: float(v) if isinstance(v, bool) else v for k, v in measured_by.items()},
        "purity": {"per_object_labels": False, "external_optimum": False,
                   "role": "E" if reached >= 1 else "F"},
        "natural_emergence": {"started_from_time_zero": True, "target_shape_seeded": False,
                              "runtime_interventions": 0, "target_dependent_rules": False,
                              "target_dependent_stopping": False, "target_dependent_clipping": False,
                              "level_detected_by_measurement": True},
    }
    return {"manifest": manifest, "emergence": emergence, "traj": traj}


def write_run(result, out_root):
    seed = result["manifest"]["seed"]
    run_dir = os.path.join(out_root, "runs", "seed-%04d" % seed)
    os.makedirs(run_dir, exist_ok=True)
    m = dict(result["manifest"])
    checksum = m.pop("checksum")
    summary = m.pop("summary")
    with open(os.path.join(run_dir, "manifest.json"), "w") as f:
        json.dump({**m, "checksum": checksum}, f, indent=2)
    with open(os.path.join(run_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(run_dir, "checksum.json"), "w") as f:
        json.dump(checksum, f, indent=2)
    with open(os.path.join(run_dir, "emergence.json"), "w") as f:
        json.dump(result["emergence"], f, indent=2)
    return run_dir


_DEMO_GENESIS = {
    "schema_version": 1, "model": gl.MODEL_ID, "dimension": 2,
    "domain": {"size": [96, 96], "spacing": 1.0, "boundary": "periodic"},
    "fields": {"psi": {"type": "complex_scalar"}},
    "initial_state": {"type": "uniform_plus_noise", "mean_amplitude": 0.0,
                      "noise_amplitude": 1.0e-2, "correlation_length": 1.0},
    "protocol": {"quench": {"start": 0.0, "duration": 8.0}}, "seed": 0,
}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Common Genesis Runner (reference: TDGL quench)")
    ap.add_argument("--mode", default="2d-screen", choices=list(MODES))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    genesis = dict(_DEMO_GENESIS)
    genesis["seed"] = args.seed
    r = run(genesis, mode=args.mode, quick=args.quick)
    m, e = r["manifest"], r["emergence"]
    print("=== Genesis Runner: %s [%s] ===" % (genesis["model"], args.mode))
    print("  grid=%s steps=%s seed=%s" % (m["manifest"]["grid"], m["manifest"]["steps"], m["seed"]))
    print("  measured: amp_growth=%s sk_prom=%s defects=%s"
          % (e["measured_by"]["mean_amplitude_growth"], e["measured_by"]["structure_factor_prominence"],
             e["measured_by"]["defect_count"]))
    print("  reached_level=%s (difference=%s, localization=%s) conservation_drift=%s"
          % (m["summary"]["reached_level"], e["detected"]["difference"], e["detected"]["localization"],
             m["summary"]["conservation_drift"]))
    print("  checksum=%s" % m["checksum"]["final_field_sha256"][:16])
    if not args.no_write:
        out_root = args.out_root or os.path.join(_REPO, "genesis", "runners", "_demo_run")
        run_dir = write_run(r, out_root)
        print("  wrote %s" % os.path.relpath(run_dir, _REPO))
    # emergence is a measured outcome, not a pass/fail gate; exit 0 if it computed a Level.
    return 0


if __name__ == "__main__":
    sys.exit(main())
