"""G002 3D frontier solver test: assert ONLY what is verified.

The 3D free-slip walled Rayleigh-Bénard solver (genesis/models/boussinesq_rb_3d.py) is EXPERIMENTAL
and not wired to any official Room (the official G002 is the validated 2D convection). These tests pin
down exactly what is trustworthy about it:
  1. its 3/2 dealiased spectral transforms round-trip to machine precision (products are truly dealiased);
  2. it reproduces the SUBCRITICAL regime correctly and boundedly (Ra < Ra_c -> Nu -> 1).

Its supercritical convection is under-resolved at affordable N and is documented as a frontier in the
module docstring -- deliberately NOT asserted here (it would not pass without N >= ~32)."""

import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from genesis.models import boussinesq_rb_3d as rb3  # noqa: E402


def test_status_is_experimental():
    # guard: this solver must never be mistaken for an official-Room solver
    assert rb3.STATUS == "experimental"


def test_dealiased_transforms_round_trip_exact():
    s = rb3.RB3D(16, 16, 1000.0, seed=1)
    assert s.transform_roundtrip_error() < 1e-10      # exact 3/2 dealiasing machinery


def test_subcritical_decays_to_conduction_and_stays_bounded():
    # Ra < Ra_c = 27 pi^4/4 ~ 657.5: quiescent state stable -> noise decays -> Nu -> 1, bounded.
    r = rb3.run_subcritical_check(300.0, 12, 12, t_end=3.0, cfl=0.3)
    assert r["finite"]
    assert abs(r["nusselt_flux"] - 1.0) < 0.02
    assert r["kinetic_energy"] < 1e-3
