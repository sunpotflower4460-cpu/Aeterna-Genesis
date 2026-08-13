"""Small deterministic repeatability smoke audit for the g001 numerical kernel.

This is not a discovery run and is never added to scientific evidence ledgers. It asks a narrower
infrastructure question: under one installed numerical environment, does the same explicit diagnostic
initial array and the same TDGL parameters produce the same finite summary twice?

The diagnostic intentionally uses a fixed seed and tiny grid because reproducibility tests need a known
input. That fixed seed is *not* evidence about natural emergence and never enters production search.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any

import numpy as np

from genesis.models import ginzburg_landau as gl

_DIAGNOSTIC_SEED = 20260813
_SHAPE = (16, 16)
_STEPS = 48


def _canonical_number(value: float) -> float:
    return float(f"{float(value):.12g}")


def run_probe(*, seed: int = _DIAGNOSTIC_SEED) -> dict[str, Any]:
    p = dict(gl.DEFAULTS)
    rng = np.random.default_rng(int(seed))
    noise = float(p.get("noise_amplitude", 1e-4))
    psi = noise * (rng.normal(size=_SHAPE) + 1j * rng.normal(size=_SHAPE))
    dt = float(p["dt"])
    finite = True
    for step in range(_STEPS):
        psi = gl.step(psi, step * dt, p)
        if not np.all(np.isfinite(psi)):
            finite = False
            break
    amp = np.abs(psi)
    gx = np.roll(psi, -1, axis=1) - psi
    gy = np.roll(psi, -1, axis=0) - psi
    observables = {
        "mean_amp": _canonical_number(float(amp.mean())),
        "amp_std": _canonical_number(float(amp.std())),
        "l2": _canonical_number(float(np.sqrt(np.mean(np.abs(psi) ** 2)))),
        "gradient_rms": _canonical_number(float(np.sqrt(np.mean(np.abs(gx) ** 2 + np.abs(gy) ** 2)))),
        "real_mean": _canonical_number(float(np.real(psi).mean())),
        "imag_mean": _canonical_number(float(np.imag(psi).mean())),
    }
    if not all(math.isfinite(float(x)) for x in observables.values()):
        finite = False
    canonical = json.dumps(observables, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "version": 1,
        "mode": "numerical-repeatability-smoke-audit",
        "model": "g001-tdgl",
        "diagnostic_seed": int(seed),
        "shape": list(_SHAPE),
        "steps": _STEPS,
        "finite": finite,
        "observables": observables,
        "digest_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "semantics": {
            "diagnostic_seed_is_production_seed": False,
            "diagnostic_is_scientific_emergence_evidence": False,
            "same_digest_proves_physical_model_true": False,
            "different_digest_is_new_physics": False,
            "different_digest_requires_numerical_environment_or_code_investigation": True,
        },
    }


def self_check(*, seed: int = _DIAGNOSTIC_SEED) -> dict[str, Any]:
    first = run_probe(seed=seed)
    second = run_probe(seed=seed)
    return {
        "version": 1,
        "mode": "same-environment-deterministic-repeatability-self-check",
        "same_digest": first["digest_sha256"] == second["digest_sha256"],
        "both_finite": bool(first["finite"] and second["finite"]),
        "first": first,
        "second": second,
        "scientific_evidence": False,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run tiny deterministic g001 repeatability smoke audit")
    p.add_argument("--seed", type=int, default=_DIAGNOSTIC_SEED)
    p.add_argument("--json", action="store_true")
    p.add_argument("--self-check", action="store_true", help="run the same probe twice and fail on mismatch")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_check:
        result = self_check(seed=args.seed)
        if args.json:
            print(json.dumps(result, sort_keys=True, ensure_ascii=True))
        else:
            print(
                f"Numerical Repeatability Self-Check: finite={result['both_finite']} "
                f"same_digest={result['same_digest']} digest={result['first']['digest_sha256']}"
            )
        return 0 if result["both_finite"] and result["same_digest"] else 2
    result = run_probe(seed=args.seed)
    if args.json:
        print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    else:
        print(
            f"Numerical Repeatability Probe: finite={result['finite']} "
            f"digest={result['digest_sha256']} seed={result['diagnostic_seed']}"
        )
    return 0 if result["finite"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
