"""Live lab universes: same physics as the model code, and every universe replays from t=0 bit for bit."""
import numpy as np
import pytest

from tools.lab.universe import Universe, replay


def test_gray_scott_is_the_unchanged_model():
    from genesis.models import gray_scott as gs
    p = dict(gs.DEFAULTS)
    rng = np.random.default_rng(0)
    U, V = gs.make_initial((96, 96), p["n_seeds"], rng, seed_radius=p["seed_radius"])
    for _ in range(150):
        U, V = gs.step(U, V, p)
    u = Universe("gray-scott", 0)
    u.advance(150)
    assert np.array_equal(u.state["U"], U) and np.array_equal(u.state["V"], V)


def test_tdgl_is_the_unchanged_model():
    from genesis.models import ginzburg_landau as gl
    p = dict(gl.DEFAULTS)
    rng = np.random.default_rng(2)
    psi = gl.make_initial((48,) * 3, p["noise_amplitude"], rng)
    for s in range(12):
        psi = gl.step(psi, s * p["dt"], p)
    u = Universe("tdgl-3d", 2)
    u.advance(12)
    assert np.array_equal(u.state["psi"], psi)


def test_three_component_is_the_unchanged_model():
    from genesis.models import three_component_rd as t3
    p = dict(t3.DEFAULTS)
    k2 = t3._k2(96)
    rng = np.random.default_rng(1)
    a, b, c = t3.make_initial((96, 96), 1e-3, rng, p)
    for _ in range(40):
        a, b, c = t3.step(a, b, c, p, k2)
    u = Universe("three-component", 1)
    u.advance(40)
    assert np.array_equal(u.state["u"], a) and np.array_equal(u.state["w"], c)


@pytest.mark.parametrize("wid,law,perturb", [
    ("gray-scott", {"F": 0.04}, ("drop_seed", {"y": 0.2, "x": 0.8})),
    ("cgl", {"c": -0.5}, ("kick", {"amp": 0.05})),
    ("sh", {"r": -0.3}, ("cut_half", {})),
    ("three-component", {"Dw": 30.0}, ("kick", {"amp": 0.01})),
])
def test_replay_with_events_is_bit_identical(wid, law, perturb):
    u = Universe(wid, 5)
    u.advance(30)
    u.set_law(law)
    u.advance(20)
    u.perturb(*perturb)
    u.perturb("kick", {"amp": 0.02})          # two events at one step keep their order
    u.advance(25)
    assert replay(u.recipe(), u.step_index).sha256() == u.sha256()


def test_branch_is_parent_recipe_plus_one_event():
    parent = Universe("gray-scott", 1)
    parent.advance(60)
    child = parent.clone()
    child.set_law({"k": 0.06})
    parent.advance(40)
    child.advance(40)
    assert parent.sha256() != child.sha256()
    assert child.recipe()["events"] == [{"step": 60, "kind": "set", "values": {"k": 0.06}}]
    assert replay(child.recipe(), child.step_index).sha256() == child.sha256()
    assert replay(parent.recipe(), parent.step_index).sha256() == parent.sha256()


def test_frames_are_display_only():
    u = Universe("cgl", 0)
    u.advance(10)
    before = u.sha256()
    f = u.frame("amplitude")
    assert len(f["data"]) == 96 * 96 and f["lo"] <= f["hi"]
    u.frame("phase")
    u.metrics()
    assert u.sha256() == before
