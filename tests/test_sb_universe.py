"""P19: a universe built from a spec. These tests check known properties of the law (conservation, gauge symmetry,
locality, the quantum vacuum at t = 0) -- they are tests of the tool, not findings."""
import numpy as np
import pytest

from genesis.models import abelian_higgs_nd as ah
from genesis.models import sb_universe as sb


def _run(spec, st, n, dt=None):
    dt = dt or sb.auto_dt(spec, st["th"].shape[0])
    for _ in range(n):
        st = sb.step(spec, st, dt)
    return st


def _two_flavours(e=0.3, **over):
    over.setdefault("terms", [{"kind": "mexican", "on": "complex", "lam": 0.36, "v": 1.0}])
    return sb.spec_from(None, complex=2, e=e, hbar=1e-2, **over)


def test_every_preset_is_a_valid_universe():
    for name in sb.PRESETS:
        s = sb.spec_from(name)
        assert 0.05 < sb.auto_dt(s, 3) < 0.5


@pytest.mark.parametrize("bad", [
    {"real": 1, "terms": [{"kind": "mass", "on": "real", "m2": -1.0}]},                 # runs away
    {"complex": 1, "e": 0.3, "terms": [{"kind": "mexican", "on": "complex", "lam": 0.5, "v": 1.0},
                                       {"kind": "z3", "on": "complex:0", "g": 0.3, "v": 1.0}]},  # not gauge invariant
    {"real": 1, "e": 0.3, "terms": []},                                                  # light with nothing charged
    {"real": 0, "complex": 0},
    {"real": 1, "terms": [{"kind": "mexican", "on": "complex:0", "lam": 0.5, "v": 1.0}]},  # no such field
])
def test_bad_universes_are_refused(bad):
    with pytest.raises(ValueError):
        sb.spec_from(None, **bad)


def test_one_charged_field_is_the_abelian_higgs_white_bit_for_bit():
    s = sb.spec_from(None, complex=1, e=0.3, dt=0.2,
                     terms=[{"kind": "mexican", "on": "complex", "lam": 0.36, "v": 1.0}])
    p = dict(ah.DEFAULTS)
    phi, pi, th, E = ah.make_initial((10, 10, 10), np.random.default_rng(3), p)
    pi = 0.01 * np.random.default_rng(4).standard_normal(phi.shape) * (1 + 1j)
    st = {"r": np.zeros((0, 10, 10, 10)), "pr": np.zeros((0, 10, 10, 10)), "c": phi[None].copy(),
          "pc": pi[None].copy(), "th": th.copy(), "E": E.copy(), "tau": 0.0}
    a = (phi, pi, th, E)
    for _ in range(40):
        a = ah.step(*a, p)
        st = sb.step(s, st, 0.2)
    assert all(np.array_equal(x, y) for x, y in zip(a, (st["c"][0], st["pc"][0], st["th"], st["E"])))


def test_the_quantum_start_keeps_gauss_and_carries_no_net_charge():
    s = _two_flavours()
    st = sb.make_initial(s, (10, 10, 10), np.random.default_rng(1))
    assert abs(sb.charge_density(st).sum()) < 1e-12
    assert np.abs(sb.gauss_residual(s, st)).max() < 1e-12
    assert np.abs(st["E"]).max() > 0 and np.abs(st["th"]).max() > 0          # the photons' own vacuum
    st = _run(s, st, 300)
    assert np.abs(sb.gauss_residual(s, st)).max() < 1e-12


def test_gauge_invariance():
    s = _two_flavours()
    st = sb.make_initial(s, (8, 8, 8), np.random.default_rng(2))
    al = np.random.default_rng(9).uniform(-np.pi, np.pi, (8, 8, 8))
    g = dict(st, c=st["c"] * np.exp(1j * al), pc=st["pc"] * np.exp(1j * al),
             th=np.stack([st["th"][i] + ah._sh(al, i) - al for i in range(3)]))
    a, b = _run(s, st, 100), _run(s, g, 100)
    assert np.allclose(sb.energy_density(s, a), sb.energy_density(s, b), atol=1e-10)
    assert np.allclose(np.abs(a["c"]), np.abs(b["c"]), atol=1e-10)
    for i, j in ah.planes(3):
        assert np.allclose(np.cos(ah.plaquette(a["th"], i, j)), np.cos(ah.plaquette(b["th"], i, j)), atol=1e-10)


@pytest.mark.parametrize("name", ["yinyang", "yinyang_middle", "three_equal", "continuous", "cascade"])
def test_energy_is_conserved_to_second_order(name):
    s = sb.spec_from(name, hbar=1e-2)
    errs = []
    for dt in (0.1, 0.05):
        st = sb.make_initial(s, (8, 8, 8), np.random.default_rng(1))
        E0, worst = sb.energy(s, st), 0.0
        for _ in range(int(round(20.0 / dt))):
            st = sb.step(s, st, dt)
            worst = max(worst, abs(sb.energy(s, st) - E0))
        errs.append(worst)
    assert 3.0 < errs[0] / errs[1] < 5.0                     # ≈ 4: the leapfrog's bounded dt² error, not a leak


def test_time_reversal():
    s = _two_flavours()
    st0 = sb.make_initial(s, (8, 8, 8), np.random.default_rng(3))
    st = _run(s, st0, 100)
    st = dict(st, pr=-st["pr"], pc=-st["pc"], E=-st["E"])
    st = _run(s, st, 100)
    assert np.allclose(st["c"], st0["c"], atol=1e-9) and np.allclose(st["th"], st0["th"], atol=1e-9)


def test_each_flavour_keeps_its_charge_when_the_law_does_not_tell_them_apart():
    s = _two_flavours()
    st = sb.make_initial(s, (8, 8, 8), np.random.default_rng(4))
    q0 = sb.flavor_charges(st)
    assert np.allclose(sb.flavor_charges(_run(s, st, 300)), q0, atol=1e-10)


def test_rotating_the_flavours_at_t0_rotates_the_universe():
    """κ = 0: the law has the U(2) symmetry; a rotated start gives the rotated history."""
    s = _two_flavours()
    st = sb.make_initial(s, (8, 8, 8), np.random.default_rng(5))
    q, _ = np.linalg.qr(np.random.default_rng(6).standard_normal((2, 2)) + 1j * np.random.default_rng(7)
                        .standard_normal((2, 2)))
    rot = dict(st, c=np.einsum("ab,b...->a...", q, st["c"]), pc=np.einsum("ab,b...->a...", q, st["pc"]))
    a, b = _run(s, st, 100), _run(s, rot, 100)
    assert np.allclose(np.einsum("ab,b...->a...", q, a["c"]), b["c"], atol=1e-9)
    assert np.allclose(a["E"], b["E"], atol=1e-9)
    k = _two_flavours(terms=[{"kind": "mexican", "on": "complex", "lam": 0.36, "v": 1.0},
                             {"kind": "aniso", "on": "complex", "kappa": 0.1}])
    a, b = _run(k, st, 100), _run(k, rot, 100)
    assert not np.allclose(np.einsum("ab,b...->a...", q, a["c"]), b["c"], atol=1e-6)   # κ tells them apart


def test_without_light_the_gauge_field_never_moves():
    s = sb.spec_from("three_equal", hbar=1e-2)
    st = _run(s, sb.make_initial(s, (8, 8, 8), np.random.default_rng(1)), 100)
    assert not st["th"].any() and not st["E"].any()


def test_a_massless_free_field_does_not_feel_the_expansion():
    """Radiation era, conformal time: a field with V = 0 is conformal, χ = aφ obeys the flat-space equation."""
    flat = sb.spec_from(None, real=1, complex=1, hbar=1e-2, dt=0.1)
    grow = sb.spec_from(None, real=1, complex=1, hbar=1e-2, dt=0.1, H=0.5)
    st = sb.make_initial(flat, (8, 8, 8), np.random.default_rng(1))
    a, b = _run(flat, st, 100), _run(grow, st, 100)
    assert np.array_equal(a["r"], b["r"]) and np.array_equal(a["c"], b["c"])
    s = sb.spec_from("yinyang", hbar=1e-2, dt=0.1, H=0.5)
    c = _run(s, st, 100)
    assert not np.allclose(c["r"], _run(sb.spec_from("yinyang", hbar=1e-2, dt=0.1), st, 100)["r"])


def test_every_site_only_hears_its_neighbours():
    """One kick–drift–kick step carries a change one site further (nearest neighbours, no FFT in the dynamics)."""
    s = _two_flavours()
    st = sb.make_initial(s, (16, 16, 16), np.random.default_rng(8))
    twin = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in st.items()}
    twin["pc"][0, 8, 8, 8] += 1e-3
    n = 5
    a, b = _run(s, st, n), _run(s, twin, n)
    x = np.indices((16, 16, 16))
    dist = sum(np.abs(x[i] - 8) for i in range(3))
    diff = np.abs(a["c"] - b["c"]).sum(0) + np.abs(a["pc"] - b["pc"]).sum(0)
    assert diff[dist > n + 1].max() == 0.0 and diff[dist <= 1].max() > 0


def test_deterministic():
    s = sb.spec_from("cascade")
    runs = [_run(s, sb.make_initial(s, (8, 8, 8), np.random.default_rng(11)), 50) for _ in range(2)]
    assert all(np.array_equal(runs[0][k], runs[1][k]) for k in ("r", "pr", "c", "pc", "th", "E"))


def test_the_vacuum_carries_half_a_quantum_per_mode():
    """⟨|φ_k|²⟩ = ħ/(2ω_k) for every mode of a free field: the variance of the field is the mean of ħ/(2ω)."""
    shape, hbar, m2 = (24, 24, 24), 0.01, 0.5
    w = np.sqrt(sb._k2_lattice(shape) + m2)
    got = np.mean([np.var(sb._vacuum_real(shape, np.random.default_rng(s), hbar, 0.0, 1.0, m2)[0])
                   for s in range(4)])
    assert abs(got / np.mean(hbar / (2 * w)) - 1) < 0.02
    hot = np.var(sb._vacuum_real(shape, np.random.default_rng(0), hbar, 0.05, 1.0, m2)[0])
    assert hot > got                                                  # a hot start carries more
    # hot and classical (T ≫ ħω): ⟨|φ_k|²⟩ = T/ω², whatever ħ is
    for h in (1e-4, 1e-6):
        cl = np.var(sb._vacuum_real(shape, np.random.default_rng(1), h, 0.05, 1.0, m2)[0])
        assert abs(cl / np.mean(0.05 / w ** 2) - 1) < 0.03
