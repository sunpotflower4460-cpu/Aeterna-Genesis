"""e046 topological state capacity (role V): the number of independent noncontractible holonomy channels on a
fixed closed orientable surface = b_1 = 2g. Rigorous cell-complex holonomy; gates on physical quantities only
(rank_h1=betti1 / holonomy read-back / gauge invariance / contractible=0 / same-class same readout / sphere=0).
Topology + windings are PLACED -> this validates the instrument, it is NOT an emergence claim."""
import numpy as np

from experiments.e046_topological_state_capacity import topological_state_capacity as tc


def test_sphere_carries_zero_channels():
    b0, b1, b2 = tc.betti_numbers(*[tc.octahedron()[k] for k in ("V", "edges", "faces")])
    assert (b0, b1, b2) == (1, 0, 1)                              # chi=2, no protected winding coordinate


def test_torus_has_two_channels_at_two_resolutions():
    for n in (4, 6):
        T = tc.torus_grid(n)
        assert tc.betti_numbers(T["V"], T["edges"], T["faces"]) == (1, 2, 1)


def test_genus_g_has_2g_channels():
    for g in range(5):
        C = tc.genus_cw(g)
        _, b1, _ = tc.betti_numbers(C["V"], C["edges"], C["faces"])
        assert b1 == 2 * g


def test_flat_connection_reads_back_windings_and_is_gauge_invariant():
    T = tc.torus_grid(6)
    theta = tc._uniform_torus_connection(T, (3, -2))
    assert tc.face_flux(theta, T["faces"]) < 1e-12                # genuinely flat
    assert abs(tc.holonomy(theta, T["cyc"]["a"]) - 3) < 1e-9
    assert abs(tc.holonomy(theta, T["cyc"]["b"]) + 2) < 1e-9
    assert abs(tc.holonomy(theta, T["faces"][0])) < 1e-12         # contractible reads 0
    rng = np.random.default_rng(0)
    lam = rng.normal(0, 1, T["V"])
    tg = theta.copy()
    for e, (t, h) in enumerate(T["edges"]):
        tg[e] += lam[h] - lam[t]                                  # gauge transform
    assert abs(tc.holonomy(tg, T["cyc"]["a"]) - 3) < 1e-9
    assert abs(tc.holonomy(tg, T["cyc"]["b"]) + 2) < 1e-9


def test_same_homology_class_same_readout():
    T = tc.torus_grid(6)
    theta = tc._uniform_torus_connection(T, (2, 0))
    assert abs(tc.holonomy(theta, T["cyc"]["a"]) - tc.holonomy(theta, T["cyc"]["a2"])) < 1e-9


def test_surface_record_reports_separate_topology_fields():
    rec = tc.surface_record(tc.torus_grid(4))
    for k in ("b0", "b1", "b2", "genus", "boundary", "independent_holonomy_channels"):
        assert k in rec
    assert rec["independent_holonomy_channels"] == rec["b1"]      # channels == b1 (NOT information capacity)


def test_all_gates_pass():
    passed, checks = tc.evaluate(tc.simulate(seed=0))
    assert passed, checks
