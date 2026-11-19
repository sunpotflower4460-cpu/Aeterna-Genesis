"""Test two-particle conditional contact in the original explicit-fuel simulator."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stdout
import csv
import io
from itertools import product, repeat
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import zipfile

import numpy as np

from longtime import HERE, check_initial_matching, inspect_history
from run import Trial, archive_history, build_binary, json_text, load_engine, read_json, sha256, valid_archive
from stationary import Rates, measure

PLAN = HERE / "FINITE_PAIR_CONTROL.json"
PHASE = "finite_pair"


def projected_rates(plan):
    historical = read_json((HERE / plan["source_parameters"]).resolve())
    case = next(case for case in historical["cases"] if case["id"] == plan["case"])
    p = historical["defaults"] | case
    projected = Rates(p["epsilon"], p["df"], p["mu"], p["eta"], p["passive_rate"], 0.5,
                      D_B=plan.get("D_B", p["D_B"]), D_I=plan["D_I"], z_total=p["z_total"])
    return case, projected


def trials_for(plan):
    case, projected = projected_rates(plan)
    if "D_B" in plan:
        case = {**case, "D_B": plan["D_B"]}
    reference_df = projected.df + projected.reaction_log_bias(0, 0)
    n = plan["N"]
    cases = {"driven": {}, "reversible": {"df": reference_df, "eta": 0.0}}
    trials = [
        Trial(plan.get("phase", PHASE), "sparse", n, plan["T"], seed,
              {**case, **cases[label], "D_I": plan["D_I"], "id": f"{label}_k{exchange:g}", "kex": n * exchange})
        for exchange, seed, label in product(reversed(plan["exchange_per_site"]), plan["seeds"], plan["conditions"])
    ]
    if len(trials) != plan["count"] or len({trial.key for trial in trials}) != len(trials):
        raise ValueError("Incomplete finite-pair matrix")
    return trials


def run_pair(trial, evidence, scratch, binary, execution, molecules):
    destination = evidence / trial.relative_archive
    if valid_archive(destination, trial, execution["registration_sha256"]):
        return trial.key
    directory = Path(tempfile.mkdtemp(dir=scratch, prefix="pair-"))
    raw = directory / "history" / trial.key
    model = load_engine(trial.engine)
    model.binary = lambda: binary
    try:
        with redirect_stdout(io.StringIO()):
            model.run(directory, "history", trial.case, n=trial.n, d=3, T=trial.duration,
                      seed=trial.seed, molecules=molecules)
    except Exception:
        if raw.is_dir():
            archive_history(raw, evidence / "failures" / trial.phase / f"{trial.key}-{directory.name}.zip",
                            execution)
            shutil.rmtree(directory)
        raise
    archive_history(raw, destination, execution)
    shutil.rmtree(directory)
    return trial.key


def run(trials, plan, registration_path, evidence, scratch, jobs):
    scratch.mkdir(parents=True, exist_ok=True)
    binary = build_binary("sparse", scratch)
    execution = {
        "engine": "sparse", "registration_sha256": sha256(registration_path),
        "binary_sha256": sha256(binary), "platform": platform.platform(),
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "runner_sha256": sha256(Path(__file__)),
    }
    with ProcessPoolExecutor(max_workers=jobs) as executor:
        completed = executor.map(run_pair, trials, repeat(evidence), repeat(scratch), repeat(binary),
                                 repeat(execution), repeat(plan["molecules"]))
        for count, key in enumerate(completed, 1):
            print(f"{count}/{len(trials)} finite pair histories archived ({key})", flush=True)


def pipeline(trials, plan, registration_path, evidence):
    histories = []
    for trial in trials:
        path = evidence / trial.relative_archive
        observed = inspect_history(path, trial, {"observations": {"windows": []}}, registration_path=registration_path)
        if observed["recipe"]["molecules"] != plan["molecules"]:
            raise ValueError(f"Wrong material count in {path}")
        with zipfile.ZipFile(path) as bundle:
            rows = list(csv.DictReader(io.StringIO(bundle.read("series.csv").decode())))
        times = np.asarray([float(row["time"]) for row in rows])
        both = np.asarray([int(row["B"]) == 2 for row in rows])
        contacts = np.asarray([int(row["pairs"]) for row in rows])
        if np.any((contacts < 0) | (contacts > both.astype(int))):
            raise ValueError(f"Impossible two-particle contact ledger in {path}")
        windows = {}
        for start, end in plan["windows"]:
            window = (start < times) & (times <= end)
            windows[f"{start}-{end}"] = {
                "samples": int(window.sum()), "both_B": int(both[window].sum()),
                "contact": int(contacts[window].sum()),
            }
        histories.append({
            "archive": observed["archive"], "archive_sha256": observed["archive_sha256"],
            "recipe": observed["recipe"], "initial_hashes": observed["initial_hashes"],
            "engine": observed["engine"], "windows": windows,
            "max_relative_medium_error": observed["max_relative_medium_error"],
        })
    return histories


def compare(histories, plan):
    draws = np.random.default_rng(1729).integers(len(plan["seeds"]), size=(8192, len(plan["seeds"])))
    lookup = {(row["recipe"]["case"]["id"], row["recipe"]["seed"]): row for row in histories}
    _, parameters = projected_rates(plan)
    fast = measure(plan["N"], parameters)
    comparisons = []
    for exchange, (start, end) in product(plan["exchange_per_site"], plan["windows"]):
        group = {}
        for label in plan["conditions"]:
            windows = [lookup[f"{label}_k{exchange:g}", seed]["windows"][f"{start}-{end}"]
                       for seed in plan["seeds"]]
            contacts = np.asarray([row["contact"] for row in windows])
            both = np.asarray([row["both_B"] for row in windows])
            if np.any(both <= 0):
                raise ValueError("Insufficient both-B observations for a paired interval")
            group[label] = {"fraction": float(contacts.sum() / both.sum()),
                            "contact": int(contacts.sum()), "both_B": int(both.sum()),
                            "resampled": contacts[draws].sum(axis=1) / both[draws].sum(axis=1)}
        driven = group["driven"]
        control = group["reversible"]
        bootstrap = driven.pop("resampled") - control.pop("resampled")
        comparisons.append({
            "exchange_per_site": exchange, "window": [start, end],
            "conditional_contact": group, "driven_minus_reversible": driven["fraction"] - control["fraction"],
            "paired_seed_bootstrap_interval": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
            "driven_minus_fast_limit": driven["fraction"] - fast["conditional_contact"],
            "reversible_minus_canonical": control["fraction"] - fast["canonical_conditional_contact"],
        })
    return {"D_B": parameters.D_B, "D_I": parameters.D_I, "fast_limit": fast, "windows": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--plan", default=PLAN, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    simulate = commands.add_parser("simulate")
    simulate.add_argument("--scratch", required=True, type=Path)
    simulate.add_argument("--jobs", type=int, default=4)
    analyse = commands.add_parser("analyse")
    analyse.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    plan = read_json(args.plan)
    trials = trials_for(plan)
    evidence = args.evidence.resolve()
    if args.command == "simulate":
        run(trials, plan, args.plan, evidence, args.scratch.resolve(), args.jobs)
        return
    histories = pipeline(trials, plan, args.plan, evidence)
    result = {
        "registration_sha256": sha256(args.plan), "count": len(histories),
        "matched_initial_groups": check_initial_matching(histories),
        "maximum_relative_medium_error": max(row["max_relative_medium_error"] for row in histories),
        "comparisons": compare(histories, plan), "archives": histories,
        "partial_attempts": [{"path": p.relative_to(evidence).as_posix(), "sha256": sha256(p)}
                             for p in sorted((evidence / "failures" / trials[0].phase).glob("*.zip"))],
    }
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json_text(result))
    print(f"Independently audited {len(histories)} finite pair histories", flush=True)


if __name__ == "__main__":
    main()
