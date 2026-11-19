"""Replay the registered e060 settings at fixed times and finer time steps."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
from pathlib import Path
import subprocess
import sys

import numpy as np

from run import HERE, json_text, read_json, sha256

REPO = HERE.parents[2]
REGISTRATION = HERE / "E060_DIAGNOSTIC_REGISTRATION.json"
sys.path.insert(0, str(REPO))
from genesis.models import swift_hohenberg as sh


def load_archived_instruments(source):
    root = source.parents[1]
    name = "e060_archived_instruments"
    spec = importlib.util.spec_from_file_location(name, root / "__init__.py",
                                                    submodule_search_locations=[str(root)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return tuple(importlib.import_module(f"{name}.{part}")
                 for part in ("whites", "quench", "classify", "l4_protocol"))


def replay(row, factor, instruments):
    whites, quench, classifier, protocol = instruments
    changes = {k: value for k, value in row["parameters"].items() if k in ("r", "b", "dx")}
    params = dict(sh.DEFAULTS) | changes
    base_dt = params["dt"]
    n = row["N"]
    initial = whites.sh_initial_uniform((n, n), params, row["parameters"]["noise_amplitude"],
                                        np.random.default_rng(row["seed"]))
    u = initial
    k2 = sh._k2(n, params["dx"])
    stages = [(p, count, "settle") for p, count in quench.stages(params, row["quench"], 2500)]
    stages.append((quench.final_params(params, row["quench"]), 800, "hold"))
    completed_steps = 0
    after_settle = None
    with np.errstate(over="ignore", invalid="ignore"):
        for stage, count, period in stages:
            dt = base_dt / factor
            settings = stage | {"dt": dt}
            for _ in range(count * factor):
                candidate = sh.step(u, settings, k2)
                if not np.isfinite(candidate).all():
                    return {
                        "factor": factor, "dt": dt,
                        "label": "NUMERICAL_FAILURE",
                        "failed_at_time": (completed_steps + 1) * dt, "stage": period,
                    }, {"initial": initial, "last_finite": u}
                u = candidate
                completed_steps += 1
            if period == "settle":
                after_settle = u
    s0 = protocol._sh_stats(after_settle, 0.3)
    s1 = protocol._sh_stats(u, 0.3)
    persistence = float(np.max(np.abs(u - after_settle)))
    label = classifier.classify("ok", s0, s1, persistence)
    return {
        "factor": factor, "dt": base_dt / factor, "label": label, "observed_time": 660.0,
        "amplitude_maximum": float(s1["amax"]), "area_fraction": float(s1["area_fraction"]),
        "components": int(s1["ncomp"]), "persistence_change": persistence,
    }, {"initial": initial, "settle": after_settle, "final": u}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reg = read_json(REGISTRATION)
    source = (HERE / reg["source_result"]).resolve()
    old = read_json(source)
    solver = Path(sh.__file__).relative_to(REPO).as_posix()
    content = subprocess.check_output(["git", "show", f"{reg['original_commit']}:{solver}"], cwd=REPO)
    if content != (REPO / solver).read_bytes() or old["code_sha"] != reg["original_commit"]:
        raise ValueError("Historical solver source differs")
    instruments = load_archived_instruments(source)
    if old["frozen_thresholds"] != instruments[2].THRESHOLDS:
        raise ValueError("Historical observation thresholds differ")
    args.out.mkdir(parents=True, exist_ok=False)
    selection = []
    population = []
    edges = reg["selection"]["b_bin_edges"]
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        pool = [row for row in old["registry"] if lo <= row["parameters"]["b"] < hi
                or (i == len(edges) - 2 and row["parameters"]["b"] == hi)]
        numerical = [row for row in pool if row["status"] == "numerical_failure"]
        valid = [row for row in pool if row["status"] == "ok"]
        population.append({"b_range": [lo, hi], "total": len(pool), "numerical_failure": len(numerical),
                           "selected": [group[0]["trial_index"] if group else None for group in (numerical, valid)]})
        selection.extend(group[0] for group in (numerical, valid) if group)

    results = []
    fields = {}
    for row in selection:
        runs = []
        prior_final = None
        trial = row["trial_index"]
        for factor in reg["procedure"]["refinement_factors"]:
            measured, states = replay(row, factor, instruments)
            final = states.get("final")
            if final is not None and prior_final is not None:
                measured["rms_from_previous_step"] = float(np.sqrt(np.mean((final - prior_final)**2)))
            prior_final = final
            fields.setdefault(f"trial_{trial}_initial", states["initial"])
            for key, values in states.items():
                if key != "initial":
                    fields[f"trial_{trial}_factor_{factor}_{key}"] = values
            runs.append(measured)
            print(f"Trial {trial}, dt={measured['dt']:g}, {measured['label']}", flush=True)
        results.append({"trial": trial, "old_label": row["label"], "seed": row["seed"],
                        "parameters": row["parameters"], "quench": row["quench"], "runs": runs})
    np.savez_compressed(args.out / "fields.npz", **fields)
    report = {
        "registration_sha256": sha256(REGISTRATION), "archived_result_sha256": sha256(source),
        "solver_sha256": hashlib.sha256(content).hexdigest(), "selection_population": population,
        "historical_baseline_labels_matching": sum(r["runs"][0]["label"] == r["old_label"] for r in results),
        "results": results, "fields_sha256": sha256(args.out / "fields.npz"),
    }
    (args.out / "diagnostic.json").write_text(json_text(report), encoding="utf-8")


if __name__ == "__main__":
    main()
