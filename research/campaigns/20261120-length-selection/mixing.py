"""Evaluate reaction rates under uniform permutations at exactly fixed counts."""
from __future__ import annotations

import argparse
import csv
import io
import math
from pathlib import Path
import zipfile

import numpy as np

from simulate import HERE, read_json, sha256
from observe import time_mean
from run import json_text

MIXING_PLAN = HERE / "MIXING_REGISTRATION.json"
REACTIONS = ("passive_B_to_I", "passive_I_to_B", "linked_B_to_I", "linked_I_to_B")


def mean_exponential(population, b, neighbors, energy):
    denominator = math.comb(population, neighbors)
    powers = [math.exp(energy * k) for k in range(neighbors + 1)]
    expectation = []
    for tagged in map(int, b):
        numerators = [math.comb(tagged, k) * math.comb(population - tagged, neighbors - k)
                      for k in range(neighbors + 1)]
        if sum(numerators) != denominator:
            raise ArithmeticError("Invalid hypergeometric counts")
        expectation.append(math.fsum(count / denominator * rate
                                     for count, rate in zip(numerators, powers, strict=True)))
    return np.asarray(expectation)


def permutation_rates(volume, i, b, f, w, params):
    p, eta = params["passive_rate"], params["eta"]
    eps, energy = params["epsilon"], math.exp(params["df"])
    weights_bp = mean_exponential(volume - 1, np.maximum(0, b - 1), 6, eps)
    weights_bd = mean_exponential(volume - 2, np.maximum(0, b - 1), 5, eps / 2)
    weights_id = mean_exponential(volume - 2, b, 5, -eps / 2)
    return np.stack((p * energy * b * weights_bp, p * i,
                     eta * energy * b * f / (volume - 1) * weights_bd,
                     eta * i * w / (volume - 1) * weights_id), axis=1)


def summarize(archive, row):
    if sha256(archive) != row["archive_sha256"]:
        raise ValueError("Mixing calculation input archive digest differs")
    with zipfile.ZipFile(archive) as bundle:
        ledger = list(csv.DictReader(io.StringIO(bundle.read("series.csv").decode())))
    times = np.asarray([int(r["time"]) for r in ledger])
    stocks = np.asarray([[int(r[k]) for k in ("I", "B", "F", "W")] for r in ledger])
    counts = np.asarray([[sum(int(r[f"rxn_{kind}_{n}"]) for n in range(7)) for kind in range(4)]
                         for r in ledger])
    recipe = row["recipe"]
    volume, material = recipe["N"]**3, recipe["molecules"]
    mixing = permutation_rates(volume, *stocks.T, recipe["parameters"]) / material
    output = {}
    for end, block in row["windows"].items():
        start, finish = block["window"]
        a, b = np.searchsorted(times, [start, finish])
        if [int(times[a]), int(times[b])] != [start, finish]:
            raise ValueError("Mixing calculation window is missing from the ledger")
        actual = (counts[b] - counts[a]) / ((finish - start) * material)
        counterfactual = [time_mean(times, values, start, finish) for values in mixing.T]
        differences = [float(x - y) for x, y in zip(actual, counterfactual, strict=True)]
        output[end] = {
            "window": [start, finish],
            "observed": dict(zip(REACTIONS, actual.tolist(), strict=True)),
            "uniform_mixing": dict(zip(REACTIONS, counterfactual, strict=True)),
            "observed_minus_mixing": dict(zip(REACTIONS, differences, strict=True)),
            "observed_net_B": math.fsum((actual[1], -actual[0], actual[3], -actual[2])),
            "uniform_mixing_net_B": math.fsum((counterfactual[1], -counterfactual[0],
                                               counterfactual[3], -counterfactual[2])),
        }
    return {"N": recipe["N"], "seed": recipe["seed"], "case": recipe["case"]["id"],
            "archive": row["archive"], "windows": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--measurements", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    data = read_json(args.measurements)
    records = [summarize(args.evidence / row["archive"], row) for row in data["archives"]]
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json_text({"registration_sha256": sha256(MIXING_PLAN), "records": records}))
    print(f"Calculated fixed-count permutation references for {len(records)} histories.", flush=True)


if __name__ == "__main__":
    main()
