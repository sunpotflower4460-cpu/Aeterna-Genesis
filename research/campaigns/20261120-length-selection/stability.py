"""Linear stability of the independent-site approximation to the local rates."""
from __future__ import annotations

import argparse
from itertools import product
import math
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from simulate import FUEL, HERE, PLAN, SUPPLY_PLAN, read_json, sha256, supply_trials, trials_for
from run import json_text

STABILITY_PLAN = HERE / "STABILITY_REGISTRATION.json"
DIRECTIONS = tuple(product(range(3), (-1, 1)))


def activities(params):
    mu = params["mu"]
    total = params["z_total"]
    return total / (1 + math.exp(-mu)), total / (1 + math.exp(mu))


def homogeneous_roots(params, material=0.18):
    eps, df = params["epsilon"], params["df"]
    passive, linked, exchange = params["passive_rate"], params["eta"], params["exchange"]
    z_f, z_w = activities(params)
    empty = (1 - material) / (1 + z_f + z_w)
    resource = (z_f + z_w) * empty

    def product_factor(b, energy):
        return (1 + b * math.expm1(energy))

    def state_and_balance(b):
        i = material - b
        forward = linked * i * product_factor(b, -eps / 2)**5
        reverse = linked * math.exp(df) * b * product_factor(b, eps / 2)**5
        f = (exchange * z_f * empty + forward * resource) / (exchange + forward + reverse)
        w = resource - f
        net = passive * (i - math.exp(df) * b * product_factor(b, eps)**6) + forward * w - reverse * f
        return np.array([i, b, f, w]), net

    def balance(b):
        return state_and_balance(b)[1]

    points = np.linspace(0, material, 4097)
    values = np.asarray([balance(b) for b in points])
    roots = list(points[values == 0])
    for pos in np.flatnonzero(values[:-1] * values[1:] < 0):
        roots.append(brentq(balance, points[pos], points[pos + 1], xtol=1e-15))
    if not roots:
        raise ArithmeticError("No homogeneous root bracketed")
    return [state_and_balance(b)[0] for b in sorted(roots)]


def rhs(state, params):
    """Evaluate the product closure on a periodic grid of site probabilities."""
    i, b, f, w = state
    vacancy = 1 - state.sum(axis=0)
    eps, df = params["epsilon"], params["df"]
    p, eta, exchange = params["passive_rate"], params["eta"], params["exchange"]
    rates = np.array([params[name] for name in ("D_I", "D_B", "D_F", "D_W")])
    z_f, z_w = activities(params)
    output = np.zeros_like(state)
    surrounding_b = [np.roll(b, -step, axis=axis) for axis, step in DIRECTIONS]
    factors = {e: [1 + math.expm1(e) * neighbor for neighbor in surrounding_b]
               for e in (eps, eps / 2, -eps / 2)}
    passive = p * (i - math.exp(df) * b * np.prod(factors[eps], axis=0))
    output[0] -= passive
    output[1] += passive
    output[2] += exchange * (z_f * vacancy - f)
    output[3] += exchange * (z_w * vacancy - w)
    for index, (axis, step) in enumerate(DIRECTIONS):
        eligible_products = {e: np.prod(products[:index] + products[index + 1:], axis=0)
                             for e, products in factors.items()}
        open_target = np.roll(vacancy, -step, axis=axis)
        hops = rates[:, None, None, None] * state * open_target / 6
        hops[1] *= eligible_products[eps]
        output += np.roll(hops, step, axis=axis + 1) - hops
        fuel_target = np.roll(f, -step, axis=axis)
        waste_target = np.roll(w, -step, axis=axis)
        linked = eta * (i * waste_target * eligible_products[-eps / 2]
                        - math.exp(df) * b * fuel_target * eligible_products[eps / 2]) / 6
        output[0] -= linked
        output[1] += linked
        exchanged = np.roll(linked, step, axis=axis)
        output[2] += exchanged
        output[3] -= exchanged
    return output


def jacobian_stencil(state, params):
    n = 7
    base = np.broadcast_to(state[:, None, None, None], (4, n, n, n)).astype(complex)
    stencil = np.zeros((4, 4, n, n, n))
    for index in range(4):
        trial = base.copy()
        trial[index, 0, 0, 0] += 1e-25j
        stencil[:, index] = rhs(trial, params).imag / 1e-25
    offsets = np.indices((n,)*3).reshape(3, -1).T
    offsets[offsets > n // 2] -= n
    return offsets, stencil.reshape(4, 4, -1)


def fourier_jacobian(offsets, stencil, wavevectors):
    phase = np.exp(-1j * (wavevectors @ offsets.T))
    matrices = np.einsum("abx,kx->kab", stencil, phase, optimize=True)
    if abs(matrices.imag).max() > 1e-10:
        raise ArithmeticError("Fourier linearization loses spatial reflection symmetry")
    return matrices.real


def measure_branch(state, params):
    magnitudes = np.linspace(0, np.pi, 193)
    offsets, stencil = jacobian_stencil(state, params)
    absent = np.abs(offsets).sum(axis=1) > 2
    if abs(stencil[:, :, absent]).max() > 1e-11:
        raise ArithmeticError("Linearization extends beyond the local stencil")
    base = rhs(np.broadcast_to(state[:, None, None, None], (4, 3, 3, 3)), params)
    residual = float(abs(base).max())
    conserved = float(abs((stencil[0] + stencil[1]).sum(axis=-1)).max())
    if max(residual, conserved) > 1e-10:
        raise ArithmeticError("Homogeneous balance or conservation validation failed")

    spectra = {}
    for name, vector in (("axis", (1, 0, 0)), ("face_diagonal", (1, 1, 0)), ("body_diagonal", (1, 1, 1))):
        direction = np.asarray(vector) / math.sqrt(sum(vector))
        jac = fourier_jacobian(offsets, stencil, magnitudes[:, None] * direction)
        eigenvalues, vectors = np.linalg.eig(jac)
        error = float(abs(jac @ vectors - vectors * eigenvalues[:, None, :]).max())
        if error > 1e-10:
            raise ArithmeticError("Fourier eigenvalue residual exceeds numerical tolerance")
        indexes = eigenvalues.real.argmax(axis=1)
        leading = eigenvalues[np.arange(len(magnitudes)), indexes]
        top = int(leading[1:].real.argmax()) + 1
        spectra[name] = {
            "max_eigenpair_residual": error,
            "zero_mode_eigenvalues_real": eigenvalues[0].real.tolist(),
            "longest_nonzero_growth_rate": float(leading[1].real),
            "max_nonzero_growth_rate": float(leading[top].real),
            "wave_number_at_maximum": float(magnitudes[top]),
            "length_at_maximum": float(2 * np.pi / magnitudes[top]),
            "positive_modes": int(np.count_nonzero(leading[1:].real > 1e-9)),
            "leading_real": leading.real.tolist(),
            "leading_imaginary_magnitude": abs(leading.imag).tolist(),
        }
    return {
        "site_fractions": dict(zip(("I", "B", "F", "W"), state.tolist(), strict=True)),
        "max_stationary_residual": residual,
        "conserved_material_zero_mode_error": conserved,
        "spectra": spectra,
    }


def model_cases():
    plan = read_json(PLAN)
    defaults = read_json(FUEL / "PRE_REGISTRATION.json")["defaults"]
    trials = [*trials_for(plan, "extent"), *trials_for(plan, "clock"),
              *supply_trials(plan, read_json(SUPPLY_PLAN))]
    base = {job.case["id"]: defaults | job.case for job in trials if job.n == 32}
    for name, parameters in sorted(base.items()):
        yield name, {**parameters, "exchange": parameters["kex"] / 32}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {"registration_sha256": sha256(STABILITY_PLAN),
              "wave_numbers": np.linspace(0, np.pi, 193).tolist(), "cases": {}}
    for name, parameters in model_cases():
        result["cases"][name] = [measure_branch(state, parameters) for state in homogeneous_roots(parameters)]
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json_text(result))
    print(f"Measured the homogeneous dispersion curves for {len(result['cases'])} registered cases.")


if __name__ == "__main__":
    main()
