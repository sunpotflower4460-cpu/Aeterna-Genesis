"""Run the registered 3D histories and archive their original solver outputs."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import redirect_stdout
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
REGISTRATION = HERE / "PRE_REGISTRATION.json"
FUEL = HERE.parent / "20261108-local-reactive-fuel"
LATTICE = HERE.parent / "20261108-local-reactive-lattice-v02"
ENGINES = {
    "reference": (FUEL / "experiment.py", FUEL / "local_kmc.cpp"),
    "sparse": (FUEL / "experiment_sparse.py", FUEL / "local_kmc_sparse.cpp"),
    "lattice": (LATTICE / "experiment.py", LATTICE / "local_kmc.cpp"),
}
PHASES = (
    "fuel_discovery", "fuel_grid", "lattice_matched", "lattice_brackets", "fuel_holdout",
)
PREREQUISITES = {"fuel_grid": "fuel_discovery", "lattice_brackets": "lattice_matched"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def sha256(path: Path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Trial:
    phase: str
    engine: str
    n: int
    duration: float
    seed: int
    case: dict

    @property
    def key(self):
        return f"{self.case['id']}-d3-n{self.n}-T{self.duration:g}-s{self.seed}"

    @property
    def relative_archive(self):
        return Path(self.phase) / f"{self.key}.zip"


def plan():
    """Return all unique trials and the 72 slots of the fuel encounter grid."""
    campaign = read_json(REGISTRATION)
    phases = campaign["phases"]
    fuel = read_json(FUEL / "PRE_REGISTRATION.json")
    lattice = read_json(LATTICE / "PRE_REGISTRATION.json")
    bracket = read_json(LATTICE / "COMPOSITION_BRACKET_REGISTRATION.json")["conditions"]
    grid = read_json(FUEL / "ENCOUNTER_GRID_REGISTRATION.json")
    fuels = {case["id"]: case for case in fuel["cases"]}
    lattices = {case["id"]: case for case in lattice["cases"]}
    discovery = fuel["discovery"]
    matched = phases["lattice_matched"]
    holdout = phases["fuel_holdout"]

    trials = {phase: [] for phase in PHASES}
    trials["fuel_discovery"] = [
        Trial("fuel_discovery", "reference", discovery["N"], discovery["T"], seed, case)
        for seed, case in itertools.product(discovery["seeds"], fuels.values())
    ]
    trials["lattice_matched"] = [
        Trial("lattice_matched", "lattice", matched["N"], matched["T"], seed, lattices[case])
        for seed, case in itertools.product(matched["seeds"], matched["cases"])
    ]
    trials["lattice_brackets"] = [
        Trial("lattice_brackets", "lattice", bracket["N"], bracket["T"], seed, {
            "id": f"frozen_B{fraction:g}_DI{mobility:g}",
            "rate": bracket["reaction_rate"], "mu": bracket["mu"], "df": bracket["df"],
            "D": bracket["D_B"], "D_I": mobility, "initial_B_fraction": fraction,
        })
        for seed, fraction, mobility in itertools.product(
            bracket["seeds"], bracket["initial_B_fraction"], bracket["D_I"],
        )
    ]
    trials["fuel_holdout"] = [
        Trial("fuel_holdout", "sparse", n, holdout["T"], seed, fuels[case])
        for n, seed in itertools.product(holdout["N"], holdout["seeds"])
        for case in holdout["cases_both_volumes"] + (holdout["cases_N32_only"] if n == 32 else [])
    ]

    def signature(trial: Trial):
        changes = {key: value for key, value in trial.case.items() if key != "id"}
        return trial.n, trial.duration, trial.seed, tuple(sorted((fuel["defaults"] | changes).items()))

    reference = {signature(trial): trial for trial in trials["fuel_discovery"]}
    grid_slots = []
    g = grid["grid"]
    for seed, eta, mobility, source, df in itertools.product(
        grid["seeds"], g["eta"], g["D_F_and_D_W"], g["source"], g["df"],
    ):
        case = {
            "id": f"enc_eta{eta:g}_D{mobility:g}_{source}_df{df:g}",
            "eta": eta, "D_F": mobility, "D_W": mobility, "source": source, "df": df, "mu": g["mu"],
        }
        trial = Trial("fuel_grid", "sparse", grid["N"], grid["T"], seed, case)
        reused = reference.get(signature(trial))
        if reused is None:
            trials["fuel_grid"].append(trial)
        grid_slots.append({
            "case": case, "seed": seed, "reused": reused is not None,
            "archive": (reused or trial).relative_archive.as_posix(),
        })

    for phase, jobs in trials.items():
        if len(jobs) != phases[phase]["histories"] or len({job.key for job in jobs}) != len(jobs):
            raise ValueError(f"Contradictory registration for {phase}")
    if len(grid_slots) != phases["fuel_grid"]["total_slots"] or sum(
        slot["reused"] for slot in grid_slots
    ) != phases["fuel_grid"]["reused_slots"]:
        raise ValueError("Grid reuse disagrees with registration")
    return trials, grid_slots


def build_binary(engine: str, scratch: Path):
    _, source = ENGINES[engine]
    destination = scratch / f"{engine}-{sha256(source)[:16]}"
    if not destination.exists():
        with tempfile.TemporaryDirectory(dir=scratch, prefix="compile-") as temporary:
            binary = Path(temporary) / "solver"
            subprocess.run(["g++", "-O3", "-std=c++17", str(source), "-o", str(binary)], check=True)
            try:
                os.link(binary, destination)
            except FileExistsError:
                pass
    return destination


@lru_cache
def load_engine(engine: str):
    source, _ = ENGINES[engine]
    spec = importlib.util.spec_from_file_location(f"campaign_engine_{engine}", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_archive(path: Path, trial: Trial, registration_hash: str):
    if not path.is_file():
        return False
    with zipfile.ZipFile(path) as bundle:
        recipe = json.loads(bundle.read("recipe.json"))
        execution = json.loads(bundle.read("execution.json"))
        has_summary = "summary.json" in bundle.namelist()
    if (
        not has_summary or recipe["case"] != trial.case or recipe["seed"] != trial.seed
        or recipe["N"] != trial.n or recipe["T"] != trial.duration
        or recipe["dimension"] != 3 or execution["engine"] != trial.engine
        or execution["registration_sha256"] != registration_hash
    ):
        raise ValueError(f"Existing archive has a different recipe: {path}")
    return True


def archive_history(raw: Path, destination: Path, execution: dict):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=destination.parent, prefix=".packing-")
    os.close(fd)
    temporary = Path(name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=4) as bundle:
            for file in sorted(raw.iterdir()):
                bundle.write(file, arcname=file.name)
            bundle.writestr("execution.json", json_text(execution))
        with zipfile.ZipFile(temporary) as bundle:
            bad_member = bundle.testzip()
            if bad_member is not None:
                raise ValueError(f"Archive verification failed for {bad_member}")
        os.link(temporary, destination)
    finally:
        temporary.unlink()


def run_trial(trial: Trial, out: Path, scratch: Path, binary: Path, execution: dict):
    destination = out / trial.relative_archive
    if valid_archive(destination, trial, execution["registration_sha256"]):
        return trial.key
    directory = Path(tempfile.mkdtemp(dir=scratch, prefix=f"{trial.phase}-"))
    raw = directory / "history" / trial.key
    model = load_engine(trial.engine)
    model.binary = lambda: binary
    scheduler = {"scheduler": 1} if trial.engine == "lattice" else {}
    try:
        with redirect_stdout(io.StringIO()):
            model.run(
                directory, "history", trial.case, n=trial.n, d=3, T=trial.duration,
                seed=trial.seed, **scheduler,
            )
    except Exception:
        if raw.exists():
            failure = out / "failures" / trial.phase / f"{trial.key}-{directory.name}.zip"
            archive_history(raw, failure, execution)
            shutil.rmtree(directory)
        raise
    try:
        archive_history(raw, destination, execution)
    except FileExistsError:
        if not valid_archive(destination, trial, execution["registration_sha256"]):
            raise
    shutil.rmtree(directory)
    return trial.key


def run_phase(phase: str, trials: dict, out: Path, scratch: Path, workers: int, *, registration_path=REGISTRATION):
    jobs = trials[phase]
    source = PREREQUISITES.get(phase)
    registration_hash = sha256(registration_path)
    if source and not all(
        valid_archive(out / trial.relative_archive, trial, registration_hash) for trial in trials[source]
    ):
        raise ValueError(f"Complete {source} before {phase}")
    pending = [
        trial for trial in jobs
        if not valid_archive(out / trial.relative_archive, trial, registration_hash)
    ]
    print(f"{phase}: {len(jobs) - len(pending)}/{len(jobs)} archived", flush=True)
    if not pending:
        return

    engine = jobs[0].engine
    binary = build_binary(engine, scratch)
    execution = {
        "engine": engine, "registration_sha256": registration_hash,
        "binary_sha256": sha256(binary), "platform": platform.platform(),
        "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
        "runner_sha256": sha256(Path(__file__)),
    }
    count = len(jobs) - len(pending)
    failures = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_trial, trial, out, scratch, binary, execution): trial
            for trial in pending
        }
        for future in as_completed(futures):
            job = futures[future]
            try:
                future.result()
            except Exception as error:
                failures.append(job.key)
                print(f"{phase}: {job.key} failed: {error}", flush=True)
            else:
                count += 1
                print(f"{phase}: {count}/{len(jobs)} archived ({job.key})", flush=True)
    if failures:
        raise RuntimeError(f"{phase}: {len(failures)} histories need review: {', '.join(failures)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=(*PHASES, "all"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--seed", type=int, action="append", help="Run only these registered seeds in the selected phase")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    out = args.out.resolve()
    scratch = args.scratch.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    trials, slots = plan()
    if args.seed and args.phase == "all":
        parser.error("--seed requires one registered phase")
    for phase in PHASES if args.phase == "all" else [args.phase]:
        selection = trials
        if args.seed:
            allowed = {job.seed for job in trials[phase]}
            if set(args.seed) - allowed:
                parser.error(f"Requested seeds must belong to {phase}: {sorted(allowed)}")
            selection = trials | {phase: [job for job in trials[phase] if job.seed in args.seed]}
        run_phase(phase, selection, out, scratch, args.jobs)
        if phase == "fuel_grid" and all((out / slot["archive"]).is_file() for slot in slots):
            for slot in slots:
                slot["archive_sha256"] = sha256(out / slot["archive"])
            manifest = json_text(slots)
            path = out / "fuel-grid-slots.json"
            if path.exists() and path.read_text(encoding="utf-8") != manifest:
                raise ValueError(f"Grid manifest differs from the completed run at {path}")
            if not path.exists():
                with path.open("x", encoding="utf-8") as stream:
                    stream.write(manifest)


if __name__ == "__main__":
    main()
