"""Replay archived histories and directly count reaction events by local density."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

import numpy as np

from simulate import FUEL, HERE, OLD, read_json, sha256
from longtime import trials_for as old_trials
from run import json_text

REGISTRATION = HERE / "EVENT_REGISTRATION.json"
SOURCE = FUEL / "local_kmc_sparse.cpp"
COUNTERS = """
  std::array<std::array<int64_t,65>,4> by_material_density{};
  auto count_material=[&](int site) {
    int corner=site;
    for(int a=0;a<3;++a)corner=neighbor[neighbor[corner][2*a+1]][2*a+1];
    int count=0;
    for(int i=0,x0=corner;i<4;++i,x0=neighbor[x0][0])
      for(int j=0,x1=x0;j<4;++j,x1=neighbor[x1][2])
        for(int k=0,x2=x1;k<4;++k,x2=neighbor[x2][4])
          count+=(cell[x2]==1||cell[x2]==2);
    return count;
  };
  if(d!=3)throw std::runtime_error("reaction-density readout needs 3D");
  std::ofstream chemistry(out/"reaction-density.csv");
  chemistry<<"time";
  for(int kind=0;kind<4;++kind)for(int count=0;count<=64;++count)
    chemistry<<",kind"<<kind<<"_sites"<<count;
  chemistry<<'\\n';
"""
EMIT = """
    chemistry<<sample*10;
    for(const auto &histogram:by_material_density)
      for(auto count:histogram)chemistry<<','<<count;
    chemistry<<'\\n';
    chemistry.flush();
    if(!chemistry)throw std::runtime_error("reaction-density readout write failed");
"""


def instrument_source(text):
    additions = (
        ("  auto measure=[&](int sample){", COUNTERS, True),
        ("    obs<<'\\n';obs.flush();", EMIT, False),
        ("    const int kind=(path?2:0)+(B?0:1);reactions[kind][n]++;rxn_x[kind][x%N]++;",
         "\n    by_material_density[kind][count_material(x)]++;", False),
    )
    for anchor, addition, before in additions:
        if text.count(anchor) != 1:
            raise ValueError("Cannot verify insertion point in the frozen solver")
        text = text.replace(anchor, addition + anchor if before else anchor + addition)
    return text


def compiled_solver(registration, scratch):
    if sha256(SOURCE) != registration["solver_source_sha256"]:
        raise ValueError("Archived solver source digest changed")
    generated = scratch / "observed.cpp"
    content = instrument_source(SOURCE.read_text(encoding="utf-8"))
    if generated.exists() and generated.read_text(encoding="utf-8") != content:
        raise ValueError("Scratch simulation source differs")
    generated.write_text(content, encoding="utf-8")
    binary = scratch / "observed"
    subprocess.run(["g++", "-O3", "-std=c++17", str(generated), "-o", str(binary)], check=True)
    return binary, sha256(generated)


def verify_replay(path, archived):
    reference_members = {name for name in archived.namelist() if name.startswith("state-")}
    emitted = {name.name for name in path.glob("state-*.bin")}
    if emitted != reference_members:
        raise ValueError("Replayed and archived checkpoint names differ")
    for member in sorted(reference_members | {"series.csv"}):
        if (path / member).read_bytes() != archived.read(member):
            raise ValueError(f"Physical replay differs at {member}")
    return len(reference_members)


def read_events(text, ledger_text):
    rows = list(csv.DictReader(io.StringIO(text)))
    ledger = list(csv.DictReader(io.StringIO(ledger_text)))
    times = np.asarray([int(row["time"]) for row in rows])
    counts = np.asarray([[[int(row[f"kind{k}_sites{j}"]) for j in range(65)] for k in range(4)] for row in rows])
    expected = np.asarray([[sum(int(row[f"rxn_{k}_{j}"]) for j in range(7)) for k in range(4)] for row in ledger])
    if not np.array_equal(times, [int(row["time"]) for row in ledger]):
        raise ValueError("Reaction-density trace and physical ledger clocks differ")
    if np.any(counts[0]) or np.any(np.diff(counts, axis=0) < 0) or not np.array_equal(counts.sum(axis=2), expected):
        raise ValueError("Density-resolved events disagree with the physical reaction ledger")
    return times, counts


def window(times, counts, start, end, recipe):
    left, right = np.searchsorted(times, [start, end])
    if [int(times[left]), int(times[right])] != [start, end]:
        raise ValueError("Event window endpoints absent")
    delta = counts[right] - counts[left]
    density = np.arange(65) / 64
    classes = np.searchsorted((0.3, 0.7), density, side="right")
    results = {}
    overall = int(delta[3].sum() - delta[2].sum())
    denominator = (end - start) * recipe["molecules"]
    for index, key in enumerate(("dilute", "intermediate", "dense")):
        accepted = delta[:, classes == index].sum(axis=1)
        passive = int(accepted[1] - accepted[0])
        linked = int(accepted[3] - accepted[2])
        results[key] = {
            "passive_net_B": passive,
            "linked_net_B": linked,
            "linked_gross": int(accepted[2] + accepted[3]),
            "fraction_of_net_linked": linked / overall if overall else None,
            "conversion_work_per_material_time": -recipe["parameters"]["mu"] * linked / denominator,
        }
    return {"interval": [start, end], "linked_net_B": overall, "bins": results,
            "accepted_counts_by_density": delta.tolist()}


def replay(item):
    trial, archive, binary, scratch, output, source_digest = item
    work = Path(tempfile.mkdtemp(prefix=trial.key + "-", dir=scratch))
    with zipfile.ZipFile(archive) as old:
        recipe = json.loads(old.read("recipe.json"))
        p = recipe["parameters"]
        fields = ("epsilon", "df", "passive_rate", "eta", "D_B", "D_I", "D_F", "D_W",
                  "kex", "source", "mu", "z_total", "initial_B_fraction")
        command = [str(x) for x in (binary, trial.n, 3, recipe["molecules"], trial.duration, trial.seed,
                                    *(p[key] for key in fields), work)]
        with (work / "solver.log").open("wb") as log:
            subprocess.run(command, check=True, stdout=log, stderr=log)
        members = verify_replay(work, old)
    raw_events = (work / "reaction-density.csv").read_bytes()
    times, counts = read_events(raw_events.decode(), (work / "series.csv").read_text(encoding="utf-8"))
    trace = output / f"{trial.key}.csv.gz"
    with trace.open("xb") as target:
        target.write(gzip.compress(raw_events, mtime=0))
    record = {"N": trial.n, "seed": trial.seed,
              "reference": trial.relative_archive.as_posix(), "reference_sha256": sha256(archive),
              "instrumented_source_sha256": source_digest,
              "verified_checkpoint_members": members,
              "verified_observation_times": len(times),
              "trace": trace.name, "trace_sha256": sha256(trace),
              "window": window(times, counts, 840, 1200, recipe)}
    shutil.rmtree(work)
    print(f"Verified all physical output and accepted-event counts for {trial.key}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    reg = read_json(REGISTRATION)
    plan_file = (HERE / reg["reference_plan"]).resolve()
    if sha256(plan_file) != reg["reference_plan_sha256"]:
        raise ValueError("Reference registration digest changed")
    plan = read_json(plan_file)["explicit"]
    trials = [trial for trial in old_trials(plan) if trial.n in reg["sizes"] and trial.seed in reg["seeds"]
              and trial.case["id"] == reg["case"] and trial.duration == reg["T"]]
    if len(trials) != reg["count"]:
        raise ValueError("Incomplete event-audit trial matrix")
    args.scratch.mkdir(parents=True, exist_ok=True)
    args.out.mkdir(parents=True, exist_ok=False)
    binary, source = compiled_solver(reg, args.scratch.resolve())
    cases = [(trial, args.reference.resolve() / trial.relative_archive, binary, args.scratch.resolve(),
              args.out.resolve(), source) for trial in trials]
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        records = list(pool.map(replay, cases))
    with (args.out / "results.json").open("x", encoding="utf-8") as stream:
        stream.write(json_text({"registration_sha256": sha256(REGISTRATION), "records": records}))


if __name__ == "__main__":
    main()
