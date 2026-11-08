"""Determinism: the same scenario run twice in-process, and in two separate interpreter processes, gives
bit-identical arrays (no randomness is used in the transport runs)."""
import hashlib
import os
import subprocess
import sys

import numpy as np

import _setup  # noqa: F401
import model
import solver

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SNIPPET = (
    "import sys, hashlib, numpy as np; sys.path.insert(0, %r)\n"
    "import model, solver\n"
    "dx, x = model.grid(64); phi = model.phi_profile(x)\n"
    "s = solver.make_setup(64, phi, model.D_field(phi, 1.0, 'linear'), 0.5, dx, 'mu')\n"
    "r = solver.run_bdf(s, 1.0 + 0.5*np.cos(2*np.pi*x), [0.0, 0.5, 2.0], rtol=1e-9, atol=1e-12)\n"
    "print(hashlib.sha256(np.ascontiguousarray(r['C']).tobytes()).hexdigest())\n"
) % HERE


def _once():
    dx, x = model.grid(64)
    phi = model.phi_profile(x)
    s = solver.make_setup(64, phi, model.D_field(phi, 1.0, "linear"), 0.5, dx, "mu")
    return solver.run_bdf(s, 1.0 + 0.5 * np.cos(2 * np.pi * x), [0.0, 0.5, 2.0], rtol=1e-9, atol=1e-12)["C"]


def test_same_process_bit_identical():
    a, b = _once(), _once()
    assert np.array_equal(a, b)


def test_separate_processes_bit_identical():
    h1 = subprocess.run([sys.executable, "-c", SNIPPET], capture_output=True, text=True).stdout.strip()
    h2 = subprocess.run([sys.executable, "-c", SNIPPET], capture_output=True, text=True).stdout.strip()
    assert h1 and h1 == h2
    assert h1 == hashlib.sha256(np.ascontiguousarray(_once()).tobytes()).hexdigest()
