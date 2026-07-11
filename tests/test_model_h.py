"""G003 test: Model H (2D) phase-separates from a uniform mixture, conserves mass exactly, decreases
its free energy (relaxational H-theorem), stays bounded, is reproducible, and CO-EVOLVES a flow from
the SAME field (the Model H point): coupling generates flow from rest and accelerates coarsening.

Fast, small-grid runs; the committed Room (tools/build_room_g003.py) uses the same solver at higher
resolution. The emergence claim rests on separation growing from the noise floor (not seeded)."""

import os
import sys

import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import model_h as mh  # noqa: E402


def _run(N, steps, seed=0, coupling=1.0):
    s = mh.ModelH(N, seed=seed, coupling=coupling)
    F0, m0 = s.free_energy(), s.mass()
    amp0, sc0 = s.phase_amplitude(), s.structure_scale()
    Fmax_increase, mass_drift = 0.0, 0.0
    Fprev = F0
    for _ in range(steps):
        s.step(mh.DEFAULTS["dt"])
        assert s.finite()
        F = s.free_energy()
        Fmax_increase = max(Fmax_increase, F - Fprev)
        Fprev = F
        mass_drift = max(mass_drift, abs(s.mass() - m0))
    return {"s": s, "F0": F0, "amp0": amp0, "sc0": sc0, "amp": s.phase_amplitude(),
            "sc": s.structure_scale(), "F": s.free_energy(), "ke": s.kinetic_energy(),
            "mass_drift": mass_drift, "F_max_increase": Fmax_increase}


def test_mass_conserved_to_machine_precision():
    r = _run(64, 400, seed=0)
    assert r["mass_drift"] < 1e-9        # Cahn-Hilliard flux form conserves the composition integral


def test_free_energy_decreases():
    r = _run(64, 400, seed=0)
    assert r["F"] < r["F0"]              # net relaxation
    assert r["F_max_increase"] < 1e-6    # monotone (no per-step increase) -> H-theorem


def test_phase_separation_emerges_from_noise():
    r = _run(64, 600, seed=0)
    assert r["amp0"] < 0.1               # start: uniform + tiny noise
    assert r["amp"] > 0.4                # end: separated toward the binodal
    assert r["sc"] > 1.5 * r["sc0"]      # domains coarsen (structure scale grows)


def test_flow_is_generated_from_the_field():
    coupled = _run(64, 500, seed=0, coupling=1.0)
    noflow = _run(64, 500, seed=0, coupling=0.0)
    assert noflow["ke"] < 1e-10          # C=0: no flow
    assert coupled["ke"] > 1e-5          # C>0: capillary forces generate flow from the SAME field


def test_hydrodynamic_coarsening():
    coupled = _run(64, 600, seed=0, coupling=1.0)
    noflow = _run(64, 600, seed=0, coupling=0.0)
    assert coupled["sc"] > noflow["sc"]  # co-evolution: the emergent flow accelerates coarsening


def test_reproducible_same_seed():
    a = _run(64, 300, seed=0)["s"]
    b = _run(64, 300, seed=0)["s"]
    assert np.allclose(a.phih, b.phih) and np.allclose(a.omh, b.omh)
    c = _run(64, 300, seed=1)["s"]
    assert not np.allclose(a.phih, c.phih)
