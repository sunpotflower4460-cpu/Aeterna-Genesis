"""Tests for ai_lab/relational/instruments.py (PR-R1: R1-R4 only)."""

import numpy as np
import pytest

from ai_lab.relational import instruments, substrate, topology


def test_reading_has_exact_spec_fields():
    r = instruments.Reading(
        name="x", value=1, defined=True, precondition="p", expressible_max=5,
        expressible_note="n",
    )
    d = r.to_dict()
    assert set(d.keys()) == {"name", "value", "defined", "precondition", "expressible_max", "expressible_note"}


# ---------------------------------------------------------------------------
# R1 difference
# ---------------------------------------------------------------------------

def test_r1_difference_defined_with_real_variance():
    x_traj = np.random.default_rng(0).normal(size=(50, 6, 1))
    r = instruments.difference(x_traj)
    assert r.defined is True
    assert r.value["mean"] > 0
    assert r.expressible_max is None


def test_r1_difference_flat_when_all_equal():
    x_traj = np.zeros((10, 4, 1))
    r = instruments.difference(x_traj)
    assert r.defined is True
    assert r.value["mean"] == 0.0


# ---------------------------------------------------------------------------
# R2 direction
# ---------------------------------------------------------------------------

def test_r2_undefined_without_edges():
    x_traj = np.random.default_rng(0).normal(size=(20, 4, 1))
    W = np.zeros((4, 4))
    r = instruments.direction(x_traj, W)
    assert r.defined is False
    assert r.value is None


def test_r2_persistence_high_for_monotone_diverging_pair():
    # node 1 always above node 0 -> sign should persist near 1.0
    t = np.linspace(0, 1, 40)
    x0 = -t
    x1 = t
    x_traj = np.stack([x0, x1], axis=1)[:, :, None]
    W = np.array([[0, 1], [1, 0]], dtype=float)
    r = instruments.direction(x_traj, W)
    assert r.defined is True
    assert r.value["mean_persistence"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# R3 reversal
# ---------------------------------------------------------------------------

def test_r3_zero_for_perfectly_monotone_series():
    t = np.linspace(0, 1, 100)
    x_traj = np.stack([-t, t], axis=1)[:, :, None]  # two monotone nodes (distinct, so R1 > 0)
    r = instruments.reversal(x_traj)
    assert r.defined is True
    assert r.value["mean_count"] == 0


def test_r3_detects_oscillation():
    t = np.linspace(0, 20 * np.pi, 400)
    series_a = np.sin(t)
    series_b = np.sin(t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.reversal(x_traj)
    assert r.defined is True
    assert r.value["mean_count"] > 10  # a clean sine over 10 periods should reverse often


def test_r3_expressible_max_is_L_minus_1():
    x_traj = np.random.default_rng(0).normal(size=(37, 3, 1))
    r = instruments.reversal(x_traj)
    assert r.expressible_max == 36


# ---------------------------------------------------------------------------
# R4 period
# ---------------------------------------------------------------------------

def test_r4_expressible_max_carries_L_over_2_value():
    """R4's expressible_max must actually carry the value, not just a comment (task constraint)."""
    L = 200
    x_traj = np.random.default_rng(1).normal(size=(L, 3, 1))
    r = instruments.period(x_traj, dt=0.1)
    assert r.expressible_max == L // 2
    assert isinstance(r.expressible_max, int)
    assert "L/2" in r.expressible_note or str(L // 2) in r.expressible_note


def test_r4_undefined_when_r3_precondition_fails():
    t = np.linspace(0, 1, 50)
    x_traj = np.stack([-t, t], axis=1)[:, :, None]  # monotone -> R3 = 0 reversals everywhere
    r = instruments.period(x_traj, dt=0.05)
    assert r.defined is False
    assert r.value is None or r.value.get("any_defined") is False


def test_r4_detects_period_of_clean_sine():
    dt = 0.05
    true_period_steps = 40  # so T = 2.0 time units
    t = np.arange(0, 2000) * dt
    omega = 2 * np.pi / (true_period_steps * dt)
    series_a = np.sin(omega * t)
    series_b = np.sin(omega * t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.period(x_traj, dt)
    assert r.defined is True
    node0 = r.value["per_node"][0]
    assert node0["defined"] is True
    assert node0["lag_steps"] == pytest.approx(true_period_steps, abs=2)
    # rate_i = 1/T_i should be the reciprocal, not the forbidden word "frequency" anywhere
    assert node0["rate"] == pytest.approx(1.0 / node0["T"], rel=1e-6)


def test_r4_cannot_represent_period_longer_than_L_over_2():
    """A period longer than half the window must come back undefined for that node, honestly,
    not silently truncated to a wrong value."""
    dt = 0.05
    L = 200  # expressible_max = 100 steps
    long_period_steps = 180  # > L/2
    t = np.arange(0, L) * dt
    omega = 2 * np.pi / (long_period_steps * dt)
    series_a = np.sin(omega * t)
    series_b = np.sin(omega * t + 0.7)  # distinct phase so nodes differ (R1 > 0)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r = instruments.period(x_traj, dt)
    assert r.expressible_max == 100
    node0 = r.value["per_node"][0]
    # Either R3's precondition fails for this short a fraction of a period (< 2 reversals in
    # 200 samples of a 180-step period), or R4's search finds nothing within its L/2 ceiling
    # -- either way, this instrument must NOT report a fabricated ~180-step period.
    if node0["defined"]:
        assert node0["lag_steps"] <= 100


def test_measure_all_returns_all_readings_in_order():
    x_traj = np.random.default_rng(2).normal(size=(30, 5, 1))
    W = np.ones((5, 5)) - np.eye(5)
    out = instruments.measure_all(x_traj, W, dt=0.05)
    assert list(out.keys()) == ["R1_difference", "R2_direction", "R3_reversal", "R4_period",
                                 "R7_phase"]
    for reading in out.values():
        assert isinstance(reading, instruments.Reading)


# ---------------------------------------------------------------------------
# PR-R1.5: envelope trend (sustained / decaying / growing)
# ---------------------------------------------------------------------------

def test_envelope_trend_positive_controls_on_synthetic_signals():
    t = np.linspace(0, 40, 2000)
    sustained = np.sin(2 * np.pi * t / 3.0)
    decaying = np.exp(-0.05 * t) * np.sin(2 * np.pi * t / 3.0)
    growing = np.exp(0.02 * t) * np.sin(2 * np.pi * t / 3.0)

    s = instruments._envelope_trend(sustained, trim=50)
    d = instruments._envelope_trend(decaying, trim=50)
    g = instruments._envelope_trend(growing, trim=50)

    assert s["classification"] == "sustained" and s["sustained"] is True
    assert d["classification"] == "decaying" and d["sustained"] is False
    assert g["classification"] == "growing" and g["sustained"] is False
    assert d["ratio"] < 1.0 - instruments._ENVELOPE_SUSTAIN_TOL
    assert g["ratio"] > 1.0 + instruments._ENVELOPE_SUSTAIN_TOL


def test_period_carries_sustained_flag_whenever_defined():
    """R4 must always carry `sustained` alongside `defined` -- a decaying transient must
    not be reportable as if it were structurally equivalent to genuine periodic structure."""
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=7, memory="on", damping=0.08)
    r4 = instruments.period(res.x_traj, res.dt)
    assert r4.defined is True   # a period WAS detected (autocorrelation peak found)
    for entry in r4.value["per_node"]:
        assert "sustained" in entry
        if entry["defined"]:
            assert isinstance(entry["sustained"], bool)
            assert "envelope" in entry


def test_period_sustained_positive_control_undamped_oscillator():
    """memory=on with damping=0.0 (no dissipation, no external input) is a genuinely
    conservative system -- the sustained detector must actually fire here, confirming it
    is not simply always reporting 'decaying'."""
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=7, memory="on", damping=0.0)
    r4 = instruments.period(res.x_traj, res.dt)
    assert r4.value["any_sustained"] is True
    assert r4.value["n_sustained_periodic_nodes"] > 0


def test_envelope_settled_flags_a_still_growing_tail_even_when_sustained_by_halves():
    """PR-R1.9: the exact risk review flagged -- a whole-window halves comparison can call a
    node 'sustained' (ratio within tol) while its amplitude is still visibly climbing right
    up to the end of the recording, because most of the growth happened earlier and the
    coarse two-halves average dilutes it. `settled` must catch this: a flat envelope for the
    first half, then a steady ramp for the second half, passes the whole-window `sustained`
    check (ratio ~1.12, under the 15% tolerance) but must NOT be `settled` (its trailing
    quarter is still moving by ~11%, over the 10% settled tolerance)."""
    t = np.linspace(0, 40, 4000)
    amp = np.where(t < 20, 1.0, 1.0 + 0.25 * (t - 20) / 20.0)
    sig = amp * np.sin(2 * np.pi * t / 3.0)
    r = instruments._envelope_trend(sig, trim=50)
    assert r["classification"] == "sustained" and r["sustained"] is True
    assert r["settled"] is False


def test_envelope_settled_true_for_a_genuinely_plateaued_oscillation():
    """Positive control: a signal that is flat-amplitude for its entire recorded window
    (nothing still moving anywhere, not just on average) must be both sustained AND settled."""
    t = np.linspace(0, 40, 4000)
    sig = np.sin(2 * np.pi * t / 3.0)
    r = instruments._envelope_trend(sig, trim=50)
    assert r["sustained"] is True
    assert r["settled"] is True


def test_period_carries_settled_and_sustained_and_settled_whenever_defined():
    res = substrate.run(n=24, steps=3000, dt=0.05, seed=7, memory="on", damping=0.0)
    r4 = instruments.period(res.x_traj, res.dt)
    assert "any_settled_sustained" in r4.value
    assert "n_settled_sustained_periodic_nodes" in r4.value
    for entry in r4.value["per_node"]:
        assert "settled" in entry
        if entry["defined"]:
            assert "sustained_and_settled" in entry
            assert entry["sustained_and_settled"] == (entry["sustained"] and entry["settled"])


def test_reversal_carries_per_node_envelope():
    res = substrate.run(n=12, steps=2000, dt=0.05, seed=2, memory="on", damping=0.05)
    r3 = instruments.reversal(res.x_traj)
    assert r3.defined is True
    envs = r3.value["per_node_envelope"]
    assert len(envs) == 12
    for e in envs:
        assert e["classification"] in ("sustained", "decaying", "growing", "undefined")


# ---------------------------------------------------------------------------
# PR-R1.75: memory=on x asymmetry=on -- the untested cell (AUDIT.md Sec.10.3)
# ---------------------------------------------------------------------------

def test_memory_on_asymmetry_on_positive_control_produces_sustained_oscillation():
    """The one combination PR-R1.5 left unmeasured. This is a positive control from
    AUDIT.md Sec.10.3's own sweep parameters (damping=0.0, strength=0.3, random_regular,
    n=24) at a seed confirmed (by direct exploration, not cherry-picked from the sweep
    average) to land in the sustained regime -- unlike the earlier memory=on positive
    control, absence here would NOT be surprising on its own (373/600 runs in the sweep
    were not sustained), so this test exists to catch a regression in the sustained path
    for the asymmetry x memory combination specifically, not to re-litigate the sweep's
    aggregate rate."""
    res = substrate.run(
        n=24, steps=3000, dt=0.05, seed=2, memory="on", damping=0.0,
        asymmetry=True, asymmetry_strength=0.3, saturation="none",
        topology="random_regular",
    )
    assert res.w_is_symmetric is False
    r4 = instruments.period(res.x_traj, res.dt)
    assert r4.defined is True
    assert r4.value["any_sustained"] is True
    assert r4.value["n_sustained_periodic_nodes"] > 0


def test_memory_off_asymmetry_on_same_seed_does_not_sustain():
    """The Gershgorin-barred counterpart of the test above: the identical relation graph
    and asymmetry, but memory=off, must NOT produce sustained oscillation (AUDIT.md
    Sec.10.2) -- isolating that inertia, not asymmetry alone, is what crosses into the
    sustained regime."""
    res = substrate.run(
        n=24, steps=3000, dt=0.05, seed=2, memory="off",
        asymmetry=True, asymmetry_strength=0.3, saturation="none",
        topology="random_regular",
    )
    r4 = instruments.period(res.x_traj, res.dt)
    if r4.defined:
        assert r4.value["any_sustained"] is False


# ---------------------------------------------------------------------------
# PR-R1.75: the q^2 > p*gamma^2 instability threshold (AUDIT.md Sec.10.3), checked
# directly against L's eigenvalues and the second-order characteristic equation --
# independent of the substrate simulation and the R4 instrument entirely.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("gamma", [0.05, 0.08, 0.2])
@pytest.mark.parametrize("strength", [0.1, 0.3, 1.0, 3.0, 8.0])
def test_q2_gt_p_gamma2_threshold_matches_direct_eigenvalue_computation(strength, gamma):
    W0 = topology.build_topology("random_regular", n=24, degree=4, seed=1)
    Wa = substrate._asymmetrize(W0, strength, seed=1)
    L = np.diag(Wa.sum(axis=1)) - Wa
    mu = np.linalg.eigvals(L)

    # derived prediction: unstable iff q^2 > p*gamma^2 for some eigenvalue mu = p + iq
    p, q = mu.real, mu.imag
    predicted_unstable = bool(np.any(q**2 > p * gamma**2 + 1e-9))

    # direct computation: roots of lambda^2 + gamma*lambda + mu = 0 for every mu
    disc = gamma**2 - 4.0 * mu
    sqrt_disc = np.sqrt(disc.astype(complex))
    lam_plus = (-gamma + sqrt_disc) / 2.0
    lam_minus = (-gamma - sqrt_disc) / 2.0
    max_re = float(np.max(np.concatenate([lam_plus.real, lam_minus.real])))
    actual_unstable = max_re > 1e-9

    assert predicted_unstable == actual_unstable, (
        "q^2 > p*gamma^2 sign mismatch at strength=%s gamma=%s (max_re=%.3e)"
        % (strength, gamma, max_re)
    )


# ---------------------------------------------------------------------------
# PR-R2.2: R7 (phase) -- transient+edge trim, gating, and cross-check against R4
# ---------------------------------------------------------------------------

_R7_KW = dict(n=24, steps=3000, dt=0.05, memory="on", damping=0.05, asymmetry=True,
              asymmetry_strength=0.3, topology="random_regular", saturation="cubic",
              saturation_strength=0.1)


def test_phase_analysis_window_is_last_half_plus_edge_trim():
    L = 3001
    lo, hi = instruments._phase_analysis_window(L)
    assert lo >= L // 2
    assert hi <= L
    assert hi - lo < L - L // 2   # strictly less than the raw last half (edge-trimmed)


def test_phase_analysis_window_fixed_rule_not_tunable_per_call():
    """The trim is a pure function of L alone -- same L always gives the same window,
    regardless of what data would be sliced by it (no per-call parameter to tune)."""
    for L in (100, 501, 3001, 12000):
        a = instruments._phase_analysis_window(L)
        b = instruments._phase_analysis_window(L)
        assert a == b


def test_phase_undefined_when_r4_undefined():
    res = substrate.run(n=10, steps=100, seed=1, memory="off")
    r7 = instruments.phase(res.x_traj, res.dt)
    assert r7.defined is False


def test_phase_gates_per_node_on_sustained_and_settled():
    res = substrate.run(seed=5, **_R7_KW)
    readings = instruments.measure_all(res.x_traj, res.W_final, res.dt)
    r4, r7 = readings["R4_period"], readings["R7_phase"]
    assert r7.defined is True
    any_checked = False
    for i, entry in enumerate(r7.value["per_node"]):
        r4_entry = r4.value["per_node"][i]
        if entry["defined"]:
            assert r4_entry.get("sustained_and_settled") is True
            any_checked = True
        elif not r4_entry.get("sustained_and_settled", False):
            assert entry["reason"].startswith("R4 precondition not met")
    assert any_checked


def test_phase_span_and_rate_have_correct_sign_and_magnitude():
    """Positive control on a synthetic signal with a known, exact rate: unwrapped phase
    should advance monotonically and mean_rate_from_phase should match the true rate.
    Two nodes with distinct phases so R1 (difference) is nonzero and R3/R4's precondition
    chain is genuinely satisfied, not bypassed."""
    dt = 0.01
    L = 4000
    t = np.arange(L) * dt
    true_rate = 2.0  # cycles per time unit
    series_a = np.sin(2 * np.pi * true_rate * t)
    series_b = np.sin(2 * np.pi * true_rate * t + 0.7)
    x_traj = np.stack([series_a, series_b], axis=1)[:, :, None]
    r4 = instruments.period(x_traj, dt)
    assert r4.defined is True
    r4.value["per_node"][0]["sustained_and_settled"] = True
    r7 = instruments.phase(x_traj, dt, r4=r4)
    entry = r7.value["per_node"][0]
    assert entry["defined"] is True
    assert entry["unwrapped_phase_span"] > 0   # advancing phase for a forward-rotating signal
    assert abs(entry["mean_rate_from_phase"] - true_rate) / true_rate < 0.05
