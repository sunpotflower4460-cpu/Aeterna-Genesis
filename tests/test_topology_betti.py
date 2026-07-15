"""Topology Instrument v1 (scalar): Betti numbers b0/b1/b2, Euler chi, and boundary genus of a 3D binary
region, validated on analytically-known synthetic shapes. This is the 3D-volume analog whose SURFACE facts
e046 validates; it is the prerequisite measurement tool for the sphere->torus (genus 0->1) frontier. no_touch:
measures.py untouched (new module)."""
import numpy as np

from genesis.diagnostics import topology_betti as tb


def test_solid_ball_is_contractible():
    r = tb.betti3d(tb.ball())
    assert (r["b0"], r["b1"], r["b2"], r["chi"], r["genus"]) == (1, 0, 0, 1, 0)


def test_two_balls_two_components():
    r = tb.betti3d(tb.two_balls())
    assert r["b0"] == 2 and r["b1"] == 0 and r["b2"] == 0 and r["chi"] == 2


def test_hollow_shell_has_one_cavity():
    r = tb.betti3d(tb.shell())
    assert r["b0"] == 1 and r["b1"] == 0 and r["b2"] == 1 and r["chi"] == 2


def test_solid_torus_has_one_tunnel_genus_one():
    r = tb.betti3d(tb.solid_torus())
    assert r["b0"] == 1 and r["b1"] == 1 and r["b2"] == 0 and r["chi"] == 0 and r["genus"] == 1


def test_double_torus_genus_two():
    r = tb.betti3d(tb.double_torus())
    assert r["b0"] == 1 and r["b1"] == 2 and r["chi"] == -1 and r["genus"] == 2


def test_euler_identity_b0_minus_b1_plus_b2():
    for fn in (tb.ball, tb.two_balls, tb.shell, tb.solid_torus, tb.double_torus):
        r = tb.betti3d(fn())
        assert r["chi"] == r["b0"] - r["b1"] + r["b2"]           # cubical chi consistent with Betti numbers


def test_translation_and_rotation_invariance_of_genus():
    """A solid torus keeps b1=1 under a lattice translation and a 90-degree rotation (topology, not placement)."""
    t = tb.solid_torus()
    assert tb.betti3d(np.roll(t, 5, axis=0))["b1"] == 1
    assert tb.betti3d(np.rot90(t, 1, axes=(0, 2)))["b1"] == 1
