"""Stationary contact of two conforming particles on a periodic 3D lattice."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import expm_multiply, spsolve

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Rates:
    epsilon: float
    df: float
    mu: float
    driven: float
    passive: float
    ts_fraction: float
    D_B: float
    D_I: float
    z_total: float | None = None

    def driven_factors(self, b_neighbors, macro_neighbors):
        """Factors in the two flip rates after factoring out the common energy ratio."""
        saddle = self.epsilon * self.ts_fraction
        common = self.driven * math.exp(-saddle * b_neighbors)
        if self.z_total is None:
            return common * math.exp(self.mu / 2), common * math.exp(-self.mu / 2)
        available = (6 - macro_neighbors) / 6
        occupied = self.z_total / (1 + self.z_total)
        return (
            common * available * occupied / (1 + math.exp(-self.mu)),
            common * available * occupied / (1 + math.exp(self.mu)),
        )

    def flip(self, state, b_neighbors, macro_neighbors):
        bf, ib = self.driven_factors(b_neighbors, macro_neighbors)
        if state == 1:
            return math.exp(self.df + self.epsilon * b_neighbors) * (self.passive + bf)
        return self.passive + ib

    def hop(self, a, b, adjacent):
        dz = sum(self.D_B if state else self.D_I for state in (a, b)) / 6
        empty = 1.0 if self.z_total is None else 1.0 / (1.0 + self.z_total)
        return dz * math.exp(self.epsilon * (a == b == 1 and adjacent)) * empty

    def reaction_log_bias(self, b_neighbors, macro_neighbors):
        bf, ib = self.driven_factors(b_neighbors, macro_neighbors)
        return math.log((self.passive + bf) / (self.passive + ib))

    def analytic_affinity(self, neighbor=1):
        return self.reaction_log_bias(neighbor, 1) - self.reaction_log_bias(0, 0)


def adjacent(r, n):
    return sum(min(value, n - value) for value in r) == 1


def neighbors(r, n):
    for axis, sign in product(range(3), (-1, 1)):
        yield tuple((value + (sign if i == axis else 0)) % n for i, value in enumerate(r))


def generator(n, rates):
    """Translation-exact reduction to relative positions and two conformations."""
    sites = list(product(range(n), repeat=3))
    states = [(r, a, b) for r in sites[1:] for a, b in product((0, 1), repeat=2)]
    index = {state: i for i, state in enumerate(states)}
    values, rows, cols = [], [], []
    for state, i in index.items():
        r, a, b = state
        contact = adjacent(r, n)
        hop = rates.hop(a, b, contact)
        transitions = [((x, a, b), hop) for x in neighbors(r, n) if x != (0, 0, 0)]
        transitions.extend([
            ((r, 1 - a, b), rates.flip(a, b * contact, contact)),
            ((r, a, 1 - b), rates.flip(b, a * contact, contact)),
        ])
        for target, value in transitions:
            rows.append(i)
            cols.append(index[target])
            values.append(value)
        rows.append(i)
        cols.append(i)
        values.append(-math.fsum(value for _, value in transitions))
    matrix = coo_matrix((values, (rows, cols)), shape=(len(states),) * 2).tocsr()
    return matrix, states, index


def stationary(matrix):
    linear = matrix.T.tolil()
    linear[-1, :] = 1.0
    target = np.zeros(matrix.shape[0])
    target[-1] = 1.0
    population = spsolve(linear.tocsc(), target)
    if np.any(population <= 0) or abs(float(population.sum()) - 1.0) > 1e-12:
        raise ArithmeticError("Invalid stationary probabilities")
    return population


def canon_population(states, n, epsilon, effective_df):
    energy = [effective_df * (a + b) + epsilon * (a == b == 1 and adjacent(r, n)) for r, a, b in states]
    weights = np.exp(-np.asarray(energy))
    return weights / weights.sum()


def measured_affinity(matrix, index, neighbor):
    apart, together = (2, 0, 0), (1, 0, 0)
    cycle = [(apart, 1, neighbor), (together, 1, neighbor),
             (together, 0, neighbor), (apart, 0, neighbor)]
    ids = [index[state] for state in cycle]
    return math.fsum(math.log(matrix[i, j] / matrix[j, i])
                    for i, j in zip(ids, ids[1:] + ids[:1]))


def expected_effective_df(rates):
    if rates.driven == 0 or rates.mu == 0:
        return rates.df
    if rates.passive == 0:
        return rates.df + rates.mu
    if rates.z_total is None and rates.ts_fraction == 0:
        return rates.df + rates.reaction_log_bias(0, 0)
    return None


def measure(n, rates, integrate=False):
    matrix, states, index = generator(n, rates)
    population = stationary(matrix)
    row_residual = float(abs(np.asarray(matrix.sum(axis=1))).max())
    residual = float(abs(matrix.T @ population).max())
    if row_residual > 1e-11 or residual > 1e-11:
        raise ArithmeticError("Invalid row generator or stationary solution")

    both = np.array([a == b == 1 for _, a, b in states])
    contact = np.array([adjacent(r, n) for r, _, _ in states])
    frequency = float(population[both & contact].sum() / population[both].sum())
    p_eq = 6 * math.exp(-rates.epsilon) / (n**3 - 7 + 6 * math.exp(-rates.epsilon))

    affinities = [measured_affinity(matrix, index, neighbor) for neighbor in (0, 1)]
    for neighbor, affinity in enumerate(affinities):
        if abs(affinity - rates.analytic_affinity(neighbor)) > 1e-12:
            raise ArithmeticError("Cycle ratio disagrees with the rate formula")

    stationary_flow = diags(population) @ matrix
    flux = stationary_flow.tocoo()
    mask = flux.row < flux.col
    forward = flux.data[mask]
    backward = np.asarray(stationary_flow[flux.col[mask], flux.row[mask]]).ravel()
    epr = float(np.sum((forward - backward) * (np.log(forward) - np.log(backward))))
    observed = {
        "n": n, "states": len(states), "probability_both_B": float(population[both].sum()),
        "conditional_contact": frequency, "canonical_conditional_contact": p_eq,
        "relative_contact_shift": frequency / p_eq - 1,
        "cycle_log_ratio": affinities[1], "cycle_log_ratio_I_neighbor": affinities[0],
        "projected_entropy_production_rate": epr,
        "maximum_net_edge_flux": float(abs(forward - backward).max()),
        "max_row_residual": row_residual, "max_stationary_residual": residual,
    }

    df = expected_effective_df(rates)
    if df is not None:
        difference = float(abs(canon_population(states, n, rates.epsilon, df) - population).max())
        if difference > 1e-12 or max(map(abs, affinities)) > 1e-12:
            raise ArithmeticError("Reversible control does not reproduce its canonical distribution")
        observed.update(effective_df=df, max_canonical_error=difference)
    else:
        reference_df = rates.df + rates.reaction_log_bias(0, 0)
        reference = canon_population(states, n, rates.epsilon, reference_df)
        observed["max_separated_bias_distribution_difference"] = float(abs(reference - population).max())
    if integrate:
        initial = np.array([float(a + b == 1) for _, a, b in states])
        initial /= initial.sum()
        final = expm_multiply(matrix.T * 120.0, initial)
        difference = float(abs(final - population).max())
        if difference > 2e-8:
            raise ArithmeticError(f"Time evolution has not approached the stationary solve: {difference}")
        observed["max_time_evolution_difference_at_120"] = difference
    return observed


def case_matrix(registration, root):
    implicit = registration["models"][0]
    explicit = registration["models"][1]
    old = root / "20261108-local-reactive-lattice-v02/PRE_REGISTRATION.json"
    fuel = root / "20261108-local-reactive-fuel/PRE_REGISTRATION.json"
    protocols = [(implicit, old, False), (explicit, fuel, True)]
    for (label, source, has_fuel), d_i in product(protocols, registration["D_I"]):
        values = json.loads(source.read_text(encoding="utf-8"))["defaults"]
        p = values["passive_rate"] if has_fuel else values["rate"]
        eta = values["eta"] if has_fuel else values["eta"] * p
        z_total = values["z_total"] if has_fuel else None
        parameters = Rates(
            epsilon=values["epsilon"], df=values["df"], mu=values["mu"],
            driven=eta, passive=p, ts_fraction=.5 if has_fuel else values["ts_fraction"],
            D_B=registration["D_B"], D_I=d_i, z_total=z_total,
        )
        controls = {
            "both_driven": parameters,
            "both_zero_affinity": replace(parameters, mu=0.0),
            "passive_only": replace(parameters, driven=0.0),
            "driven_only": replace(parameters, passive=0.0),
        }
        if not has_fuel:
            controls["common_saddle"] = replace(parameters, ts_fraction=0.0)
        for n, (case, rates) in product(registration["sizes"], controls.items()):
            yield label, n, d_i, case, rates


def saddle_control(cases, control):
    for model, n, d_i, case, rates in cases:
        if model != control["model"] or case != control["reference_case"]:
            continue
        if n not in control["sizes"] or d_i not in control["D_I"]:
            continue
        cancellation = math.log(6 / 5) / -rates.epsilon
        for value in control["saddles"]:
            analytic_point = value == "log(6/5)/(-epsilon)"
            saddle = cancellation if analytic_point else float(value)
            varied = replace(rates, ts_fraction=saddle)
            observed = measure(n, varied)
            if analytic_point and abs(observed["cycle_log_ratio"]) > 1e-12:
                raise ArithmeticError("Analytic cancellation does not close the B-neighbor cycle")
            yield {"model": model, "D_I": d_i, "saddle": saddle, "analytic_point": analytic_point,
                   "parameters": vars(varied), **observed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--saddle-control", action="store_true")
    args = parser.parse_args()
    # SciPy's exponential action estimates a matrix norm with random probe vectors.
    np.random.seed(0)
    reg_file = HERE / "PRE_REGISTRATION.json"
    reg = json.loads(reg_file.read_text())["stationary"]
    cases = case_matrix(reg, HERE.parent)
    result = {"registration_sha256": hashlib.sha256(reg_file.read_bytes()).hexdigest()}
    if args.saddle_control:
        control_file = HERE / "SADDLE_CONTROL.json"
        control = json.loads(control_file.read_text())
        result["saddle_control_sha256"] = hashlib.sha256(control_file.read_bytes()).hexdigest()
        rows = list(saddle_control(cases, control))
        if len(rows) != len(control["sizes"]) * len(control["D_I"]) * len(control["saddles"]):
            raise ArithmeticError("Incomplete saddle control")
    else:
        rows = [{"model": model, "D_I": d_i, "case": case,
                 "parameters": vars(rates), **measure(n, rates, integrate=n == 4)}
                for model, n, d_i, case, rates in cases]
    result["rows"] = rows
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(f"Solved and audited {len(rows)} stationary worlds.")


if __name__ == "__main__":
    main()
