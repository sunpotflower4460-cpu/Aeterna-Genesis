"""G002 test: the walled Rayleigh-Bénard model (2D) convects ONLY above the critical Rayleigh number,
is bounded, conserves heat (two independent Nusselt estimators agree), and is reproducible.

Fast, small-grid runs -- the committed Room (tools/build_room_g002.py) uses the same solver at higher
resolution. The physics claim rests on the ONSET CONTRAST (sub- vs super-critical), which proves the
convection pattern is emergent, not seeded (第8監査)."""

import os
import sys

import numpy as np

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import boussinesq_rb as rb  # noqa: E402


def _run(Ra, N, t_end, seed=0):
    s = rb.Bouss(N, N, Ra, seed=seed)
    t = 0.0
    while t < t_end:
        dt = s.cfl_dt()
        s.step(dt)
        t += dt
        assert s.finite(), "solver went non-finite (Ra=%g, N=%d)" % (Ra, N)
    return s


def test_critical_rayleigh_constant():
    assert abs(rb.RA_C - 27 * np.pi ** 4 / 4.0) < 1e-9
    assert abs(rb.KC - np.pi / np.sqrt(2.0)) < 1e-9


def test_subcritical_stays_conductive():
    # Ra < Ra_c: the quiescent conductive state is stable -> noise decays -> Nu -> 1 (no convection).
    s = _run(300.0, 32, t_end=5.0)
    assert s.nusselt_flux() < 1.02
    assert s.kinetic_energy() < 1e-3


def test_supercritical_convects():
    # Ra > Ra_c: translational symmetry breaks spontaneously -> convection -> Nu > 1.
    s = _run(1000.0, 32, t_end=7.0)
    assert s.nusselt_flux() > 1.1
    assert s.kinetic_energy() > 1.0


def test_onset_contrast():
    # The emergence proof: identical law + walls, only Ra changes across Ra_c.
    sub = _run(300.0, 24, t_end=5.0)
    sup = _run(1000.0, 24, t_end=7.0)
    assert sub.nusselt_flux() < 1.02
    assert sup.nusselt_flux() > 1.1


def test_heat_conservation_two_estimators_agree():
    # Steady RB obeys the exact relation Nu = <|grad T|^2> = 1 + <w theta>. Two independently coded
    # estimators must agree -> a genuine conservation audit (not a tautology).
    s = _run(1000.0, 48, t_end=8.0)
    nf, nd = s.nusselt_flux(), s.nusselt_dissipation()
    assert nf > 1.1
    assert abs(nf - nd) / nf < 0.10


def test_reproducible_same_seed():
    a = _run(1000.0, 24, t_end=4.0, seed=0)
    b = _run(1000.0, 24, t_end=4.0, seed=0)
    assert np.allclose(a.om, b.om) and np.allclose(a.th, b.th)
    c = _run(1000.0, 24, t_end=4.0, seed=1)
    assert not np.allclose(a.th, c.th)          # different seed -> different microstate


def test_bounded_walls_keep_it_finite():
    # Walls make convection BOUNDED (the triperiodic version diverges via elevator modes).
    r = rb.run_to_steady(1000.0, 32, 32, t_end=8.0)
    assert r["finite"] and r["converged"]
    assert np.isfinite(r["kinetic_energy"]) and r["convecting"]
