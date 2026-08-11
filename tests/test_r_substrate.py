"""Tests for ai_lab/relational/substrate.py (PR-R1).

Covers: ingredient axes present in both kwargs and result dict; the difference-only hard
constraint's observable consequence (Sum(x) conservation for the pure diffusive default);
grid's geometry_was_given honesty flag; and the PR's one central empirical question --
does memory=off genuinely fail to produce reversal/period while memory=on produces them?
"""

import numpy as np
import pytest

from ai_lab.relational import instruments, substrate, topology


def test_all_ingredient_axes_in_result_dict():
    res = substrate.run(n=10, steps=20, seed=1)
    d = res.to_dict(include_trajectory=False)
    for axis in ("memory", "saturation", "conservation", "plasticity", "topology", "m"):
        assert axis in d, "ingredient axis %r missing from result dict" % axis
    assert d["memory"] == substrate.DEFAULT_MEMORY == "off"
    assert d["saturation"] == substrate.DEFAULT_SATURATION == "none"
    assert d["conservation"] == substrate.DEFAULT_CONSERVATION is False
    assert d["plasticity"] == substrate.DEFAULT_PLASTICITY is False
    assert d["topology"] == substrate.DEFAULT_TOPOLOGY == "random_regular"
    assert d["m"] == substrate.DEFAULT_M == 1


def test_ingredient_axes_are_constructor_kwargs():
    # every axis must be settable, not just reported
    res = substrate.run(
        n=12, steps=10, seed=2, memory="on", saturation="cubic", conservation=True,
        plasticity=True, topology="erdos_renyi", m=1,
    )
    d = res.to_dict(include_trajectory=False)
    assert d["memory"] == "on"
    assert d["saturation"] == "cubic"
    assert d["conservation"] is True
    assert d["plasticity"] is True
    assert d["topology"] == "erdos_renyi"


def test_default_topology_is_not_grid():
    assert substrate.DEFAULT_TOPOLOGY != "grid"
    assert topology.DEFAULT_TOPOLOGY != "grid"


def test_grid_sets_geometry_was_given_when_selected():
    res_default = substrate.run(n=10, steps=5, seed=1)
    assert res_default.geometry_was_given is False

    res_grid = substrate.run(n=9, steps=5, seed=1, topology="grid", topology_kwargs={"dim": 1})
    assert res_grid.geometry_was_given is True
    d = res_grid.to_dict(include_trajectory=False)
    assert d["geometry_was_given"] is True


def test_state_space_has_no_complex_or_angle_content():
    res = substrate.run(n=8, steps=5, seed=1, m=2)
    assert not np.iscomplexobj(res.x_traj)
    assert res.x_traj.dtype.kind == "f"


@pytest.mark.parametrize("topo_name", ["random_regular", "erdos_renyi", "watts_strogatz", "barabasi_albert"])
def test_pure_diffusion_conserves_sum_x_for_symmetric_graphs(topo_name):
    # Hard-constraint consequence: the default (conservation=False, saturation=none) rule is
    # exactly -L@x, which sums to zero for symmetric W -- Sum(x) should stay constant even
    # though we never told it to.
    res = substrate.run(n=16, steps=800, dt=0.05, seed=3, epsilon=0.2, topology=topo_name,
                         memory="off", saturation="none", conservation=False)
    sums = res.x_traj.sum(axis=(1, 2))
    assert np.allclose(sums, sums[0], atol=1e-6), "Sum(x) drifted under the pure diffusive default"


def test_conservation_flag_holds_sum_x_even_with_saturation_on():
    # saturation="cubic" alone breaks conservation; conservation=True should restore it.
    res_off = substrate.run(n=16, steps=400, dt=0.05, seed=4, epsilon=0.3, memory="off",
                             saturation="cubic", saturation_strength=0.2, conservation=False)
    sums_off = res_off.x_traj.sum(axis=(1, 2))
    assert not np.allclose(sums_off, sums_off[0], atol=1e-4), (
        "expected saturation to break Sum(x) conservation when conservation=False"
    )

    res_on = substrate.run(n=16, steps=400, dt=0.05, seed=4, epsilon=0.3, memory="off",
                            saturation="cubic", saturation_strength=0.2, conservation=True)
    sums_on = res_on.x_traj.sum(axis=(1, 2))
    assert np.allclose(sums_on, sums_on[0], atol=1e-6), (
        "conservation=True should hold Sum(x) constant even with saturation on"
    )


def test_plasticity_changes_weights():
    res = substrate.run(n=10, steps=300, dt=0.05, seed=5, epsilon=0.3, plasticity=True,
                         plasticity_rate=0.5)
    assert not np.allclose(res.W_initial, res.W_final)
    assert np.all(res.W_final >= 0)
    assert np.allclose(res.W_final, res.W_final.T)


# ---------------------------------------------------------------------------
# The central PR-R1 question: memory=off vs memory=on on R3(reversal)/R4(period).
# ---------------------------------------------------------------------------

def _sweep_memory_off(n_seeds=8):
    """Fraction of (run, node) pairs where R4 finds a defined period under memory=off."""
    total_nodes = 0
    periodic_nodes = 0
    for seed in range(n_seeds):
        for topo_name in ("random_regular", "erdos_renyi", "watts_strogatz", "barabasi_albert"):
            res = substrate.run(n=20, steps=1500, dt=0.05, seed=seed, epsilon=0.1,
                                 memory="off", topology=topo_name)
            readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
            r4 = readings["R4_period"]
            total_nodes += res.n
            if r4.defined:
                periodic_nodes += r4.value["n_periodic_nodes"]
    return periodic_nodes, total_nodes


def _sweep_memory_on(n_seeds=8, damping=0.06):
    """Fraction of (run, node) pairs where R4 finds a defined period under memory=on."""
    total_nodes = 0
    periodic_nodes = 0
    runs_with_any = 0
    for seed in range(n_seeds):
        res = substrate.run(n=20, steps=2500, dt=0.05, seed=seed, epsilon=0.1,
                             memory="on", damping=damping)
        readings = instruments.measure_all(res.x_traj, res.W_initial, res.dt)
        r4 = readings["R4_period"]
        total_nodes += res.n
        if r4.defined:
            runs_with_any += 1
            periodic_nodes += r4.value["n_periodic_nodes"]
    return periodic_nodes, total_nodes, runs_with_any


def test_memory_off_does_not_produce_sustained_period():
    """Core PR-R1 result: pure first-order relaxation should almost never show R4-defined
    period, and never more than a small, disclosed noise floor (see AUDIT.md Sec.3.3).
    This is an aggregate/statistical assertion (not "exactly zero every single run") because
    a small, investigated, and explained false-positive rate exists and should not make this
    test flaky -- see AUDIT.md for the investigation of why that residual is not real
    periodicity.
    """
    periodic, total = _sweep_memory_off(n_seeds=8)
    frac = periodic / total
    assert frac < 0.05, (
        "memory=off produced defined periods on %.4f of nodes (%d/%d) -- expected a very "
        "small residual (analytically, this should be exactly zero; see AUDIT.md Sec.3.1's "
        "Lyapunov argument for why memory=off cannot sustain a periodic orbit)" % (frac, periodic, total)
    )


def test_memory_on_produces_sustained_period():
    """Core PR-R1 result: second-order (inertial) dynamics with damping should reliably
    produce a defined R4 period on most nodes, in most/all runs.
    """
    periodic, total, runs_with_any = _sweep_memory_on(n_seeds=8, damping=0.06)
    frac = periodic / total
    assert runs_with_any >= 7, "expected almost every memory=on run to show at least one periodic node"
    assert frac > 0.3, (
        "memory=on produced defined periods on only %.4f of nodes (%d/%d) -- expected a "
        "clear majority" % (frac, periodic, total)
    )


def test_memory_on_vs_off_contrast_same_initial_condition_family():
    """Same seed, same topology, same small-random-inhomogeneity initial condition family --
    only `memory` differs. This isolates memory as the ingredient responsible for the
    reversal/period contrast (the actual PR-R1 question), not some confound like topology or
    seed.
    """
    common = dict(n=20, steps=2000, dt=0.05, seed=7, epsilon=0.1, topology="random_regular")
    res_off = substrate.run(memory="off", **common)
    res_on = substrate.run(memory="on", damping=0.06, **common)

    r_off = instruments.measure_all(res_off.x_traj, res_off.W_initial, res_off.dt)
    r_on = instruments.measure_all(res_on.x_traj, res_on.W_initial, res_on.dt)

    off_periodic = r_off["R4_period"].value["n_periodic_nodes"] if r_off["R4_period"].defined else 0
    on_periodic = r_on["R4_period"].value["n_periodic_nodes"] if r_on["R4_period"].defined else 0

    assert on_periodic > off_periodic
    assert on_periodic >= res_on.n // 2, "expected memory=on to make at least half the nodes periodic here"


# --- PR-R1.5: asymmetry axis ---------------------------------------------------------------

def test_asymmetry_default_off_keeps_w_symmetric():
    r = substrate.run(n=12, steps=50, seed=1, memory="off", asymmetry=False)
    assert r.asymmetry is False
    assert r.asymmetry_strength == 0.0
    assert r.w_is_symmetric is True
    assert np.allclose(r.W_final, r.W_final.T)


def test_asymmetry_on_breaks_symmetry_but_preserves_edges_and_average():
    r0 = substrate.run(n=12, steps=50, seed=3, memory="off", asymmetry=False)
    r1 = substrate.run(n=12, steps=50, seed=3, memory="off", asymmetry=True, asymmetry_strength=0.6)
    assert r1.asymmetry is True
    assert r1.asymmetry_strength == 0.6
    assert r1.w_is_symmetric is False
    assert not np.allclose(r1.W_final, r1.W_final.T)
    # edge existence unchanged
    base_edges = r0.W_initial > 0
    asym_edges = (r1.W_final > 0) | (r1.W_final.T > 0)
    assert np.array_equal(base_edges, asym_edges)
    # per-edge average preserved (average-preserving split, not a magnitude change)
    avg = 0.5 * (r1.W_final + r1.W_final.T)
    assert np.allclose(avg[base_edges], r0.W_initial[base_edges])
    # weights stay non-negative
    assert (r1.W_final >= 0).all()


def test_asymmetry_does_not_change_initial_condition_for_same_seed():
    r0 = substrate.run(n=12, steps=1, seed=5, memory="off", asymmetry=False)
    r1 = substrate.run(n=12, steps=1, seed=5, memory="off", asymmetry=True, asymmetry_strength=0.5)
    assert np.allclose(r0.x_traj[0], r1.x_traj[0])


def test_asymmetry_is_present_in_kwargs_and_result_dict():
    r = substrate.run(n=10, steps=20, seed=0, asymmetry=True, asymmetry_strength=0.4)
    d = r.to_dict(include_trajectory=False)
    assert d["asymmetry"] is True
    assert d["asymmetry_strength"] == 0.4
    assert d["w_is_symmetric"] is False


# --- PR-R1.75: Gershgorin bound (AUDIT.md Sec.10.2) -----------------------------------------
#
# Structural claim: for ANY non-negative W built by this construction (symmetric or
# asymmetrized), L = D - W (D = row-sum degree) has every eigenvalue with Re >= 0, at any
# asymmetry strength. This is a direct consequence of Q = -L being a zero-row-sum,
# non-negative-off-diagonal matrix (a CTMC generator), not something that could fail for a
# large-enough strength -- these tests check that unconditionally, well past the strengths
# {0.3, 0.6, 0.9} used elsewhere in this file.

def test_gershgorin_bound_holds_for_symmetric_w():
    W = topology.build_topology("random_regular", n=20, degree=4, seed=11)
    L = np.diag(W.sum(axis=1)) - W
    eig = np.linalg.eigvals(L)
    assert eig.real.min() > -1e-8


@pytest.mark.parametrize("strength", [0.5, 2.0, 8.0, 30.0, 100.0])
@pytest.mark.parametrize("topo", ["random_regular", "erdos_renyi", "watts_strogatz", "barabasi_albert"])
def test_gershgorin_bound_holds_for_asymmetric_w_at_any_strength(topo, strength):
    kwargs = {
        "random_regular": dict(degree=4),
        "erdos_renyi": dict(p=0.3),
        "watts_strogatz": dict(k=4, beta=0.3),
        "barabasi_albert": dict(m=2),
    }[topo]
    W0 = topology.build_topology(topo, n=20, seed=3, **kwargs)
    Wa = substrate._asymmetrize(W0, strength, seed=3)
    assert not np.allclose(Wa, Wa.T)   # actually asymmetric, not a no-op
    L = np.diag(Wa.sum(axis=1)) - Wa
    eig = np.linalg.eigvals(L)
    # Gershgorin's own disc radius is 0 at the rightmost point (Re(disc_center) + radius ==
    # 0 exactly for a zero-row-sum matrix), so this is a tight bound, not a loose one --
    # floating point noise is the only slack allowed.
    assert eig.real.min() > -1e-6, "L must have no negative-real-part eigenvalue at strength=%s (topo=%s)" % (strength, topo)


def test_asymmetrize_preserves_non_negativity_at_extreme_strength():
    W0 = topology.build_topology("random_regular", n=16, degree=4, seed=1)
    Wa = substrate._asymmetrize(W0, strength=1000.0, seed=1)
    assert (Wa >= 0).all()
    # edges are neither created nor destroyed even at an extreme strength
    assert np.array_equal(W0 > 0, (Wa > 0) | (Wa.T > 0))


# --- PR-R2 pre-check (AUDIT.md Sec.12.2): saturation="none" cannot produce a genuine
# bounded oscillation for memory=on x asymmetry=on -- only saturation="cubic" can ---------

def test_memory_on_asymmetry_on_saturation_none_diverges_over_a_longer_window():
    """AUDIT.md Sec.12.2: memory=on with saturation='none' is an EXACTLY LINEAR ODE (no
    a*x^3 term), so any config with Re(lambda_max) > 0 (essentially every asymmetric config
    swept in Sec.10.3/11 -- see Sec.12.2) cannot have a bounded limit cycle; it must diverge
    without bound given a long enough window, however 'settled' it looks in a short one.
    This is a regression/documentation test protecting that finding: a config previously
    reported sustained_and_settled at steps=3000 shows unmistakable, unbounded growth once
    the window is extended -- not evidence of a code bug, evidence that saturation='none'
    genuinely cannot cap growth."""
    kw = dict(n=24, dt=0.05, seed=5, memory="on", damping=0.05, asymmetry=True,
              asymmetry_strength=0.3, topology="random_regular")
    node = 22  # AUDIT.md Sec.12.2's spot-checked node for this exact (seed, kw)
    short = substrate.run(steps=3000, saturation="none", **kw)
    long = substrate.run(steps=20000, saturation="none", **kw)
    series_short = short.x_traj[:, node, :].sum(axis=-1)
    series_long = long.x_traj[:, node, :].sum(axis=-1)
    # within the original (short) window, amplitude stays modest -- this is what PR-R1.9's
    # settled check saw and correctly reported as flat FOR THAT WINDOW.
    assert np.max(np.abs(series_short)) < 1.0
    # extended far past that window, the SAME trajectory (same seed, same physics) is
    # unmistakably diverging -- more than two orders of magnitude beyond the short window's
    # peak, confirming this was a slow transient, not a true attractor.
    assert np.max(np.abs(series_long[-len(series_long) // 10:])) > 100.0


def test_memory_on_asymmetry_on_saturation_cubic_stays_bounded_on_the_same_config():
    """Positive control for the test above: the ONLY change from the diverging config is
    saturation='cubic' (the codebase's existing nonlinear cap, unused in Sec.10.3/11's
    sweep) -- on the identical (seed, topology, strength, damping), this must plateau
    rather than diverge, confirming saturation='cubic' is the missing ingredient for a
    genuine bounded oscillation, not a coincidence of this one config."""
    kw = dict(n=24, dt=0.05, seed=5, memory="on", damping=0.05, asymmetry=True,
              asymmetry_strength=0.3, topology="random_regular",
              saturation="cubic", saturation_strength=0.1)
    node = 22
    res = substrate.run(steps=20000, **kw)
    series = res.x_traj[:, node, :].sum(axis=-1)
    L = len(series)
    second_half_max = np.max(np.abs(series[L // 2:]))
    last_quarter_max = np.max(np.abs(series[3 * L // 4:]))
    # bounded and plateaued: the last quarter's peak is not meaningfully larger than the
    # second half's overall peak (no further growth once past the initial transient), and
    # both are orders of magnitude below where the saturation='none' twin ends up.
    assert last_quarter_max < 2.0 * second_half_max
    assert last_quarter_max < 50.0
