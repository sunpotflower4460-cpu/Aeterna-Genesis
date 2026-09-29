"""The census counts what formed without naming it. Checked on hand-made fields whose answer is known."""
import numpy as np

from genesis.diagnostics import emergence_census as ec
from genesis.models import sb_universe as sb


def _state(spec, shape, r=None, c=None):
    R, N = spec["real"], spec["complex"]
    r = np.zeros((R,) + shape) if r is None else r
    c = np.zeros((N,) + shape, complex) if c is None else c
    d = len(shape)
    return {"r": r, "pr": np.zeros_like(r), "c": c, "pc": np.zeros_like(c), "th": np.zeros((d,) + shape),
            "E": np.zeros((d,) + shape), "tau": 0.0}


def test_two_valleys_two_regions_and_where_they_meet():
    s = sb.spec_from("yinyang")
    x = np.arange(32)
    f = np.sqrt(2.0) * np.tanh((x - 8) / 2.0) * np.tanh((24 - x) / 2.0)      # +, then −, then +: two walls
    st = _state(s, (32, 16), r=np.broadcast_to(f[:, None], (32, 16))[None].copy())
    lab, groups = ec.label_sites(s, st)
    assert len(groups) == 2 and all(g["flat_dirs"] == 0 for g in groups)
    d = ec.domains(lab)
    assert d["regions"] == 2 and d["plaquettes_3plus"] == 0
    assert d["bonds_between_total"] == 0 and d["between_fraction"] > 0     # the walls themselves are between


def test_the_middle_valley_is_a_valley_not_a_top():
    s = sb.spec_from("yinyang_middle")
    st = _state(s, (16, 16), r=1e-3 * np.random.default_rng(0).standard_normal((1, 16, 16)))
    lab, groups = ec.label_sites(s, st)
    assert len(groups) == 1 and ec.domains(lab)["between_fraction"] == 0.0


def test_three_valleys_meet_at_points():
    s = sb.spec_from("three_equal")
    y, x = np.mgrid[0:48, 0:48]
    ang = np.angle((x - 24) + 1j * (y - 24))                              # three wedges around the centre
    k = np.floor(((ang + np.pi / 3) % (2 * np.pi)) / (2 * np.pi / 3))
    rad = 2.245
    c = rad * np.exp(2j * np.pi * k / 3)[None]
    lab, groups = ec.label_sites(s, _state(s, (48, 48), c=c))
    assert len(groups) == 3
    d = ec.domains(lab)
    assert d["plaquettes_3plus"] >= 1 and len(d["bonds_between"]) == 3


def test_a_continuous_valley_is_one_group_with_a_flat_direction():
    s = sb.spec_from("continuous", e=0.0)
    ph = np.random.default_rng(1).uniform(-np.pi, np.pi, (16, 16))
    lab, groups = ec.label_sites(s, _state(s, (16, 16), c=np.exp(1j * ph)[None]))
    assert len(groups) == 1 and groups[0]["flat_dirs"] == 1


def test_windings_are_counted_where_the_phase_turns():
    s = sb.spec_from("continuous", e=0.0)
    y, x = np.mgrid[0:32, 0:32]
    z = ((x - 8.5) + 1j * (y - 16.5)) * np.conj((x - 24.5) + 1j * (y - 16.5))   # a + and a − winding
    w = ec.windings(s, _state(s, (32, 32), c=(z / np.abs(z))[None]))
    assert w["per_field"] == [2]


def _blob(shape, centre, r0):
    g = np.indices(shape)
    d2 = sum((g[i] - centre[i]) ** 2 for i in range(len(shape)))
    return np.exp(-d2 / (2 * r0 ** 2))


def test_lumps_and_whether_two_are_the_same():
    s = sb.spec_from("yinyang")
    r = np.full((1, 40, 40), np.sqrt(2.0))
    st = _state(s, (40, 40), r=r)
    st["pr"] = (_blob((40, 40), (10, 10), 2.0) + _blob((40, 40), (30, 25), 2.0))[None]
    L = ec.lumps(s, st)["lumps"]
    assert len(L) == 2
    same = ec.sameness([x["descr"] for x in L], [0, 0])
    assert same["kinds"]["0"]["identical_pairs"] == 1                     # the same shape, placed twice
    st["pr"] = (_blob((40, 40), (10, 10), 2.0) + _blob((40, 40), (30, 25), 3.0))[None]
    L = ec.lumps(s, st, thr_sigma=2.0)["lumps"]
    assert len(L) == 2 and ec.sameness([x["descr"] for x in L], [0, 0])["kinds"]["0"]["identical_pairs"] == 0


def test_the_spectrum_finds_the_free_wave_frequency():
    """A free massive wave ω² = m² + 4 sin²(k/2) (lattice): the census finds its branch at that k."""
    s = sb.spec_from(None, real=1, terms=[{"kind": "mass", "on": "real", "m2": 0.25}], dt=0.05)
    n = 16
    k1 = 2 * np.pi / n
    x = np.arange(n)
    r = (0.1 * np.cos(k1 * x))[None, :, None, None] * np.ones((1, n, n, n))
    st = _state(s, (n, n, n), r=r)
    spec_ = ec.Spectrum(s)
    for _ in range(1024):
        spec_.add(st)
        st = sb.run(s, st, 0.05, 4)
    res = spec_.result()
    ch = res["channels"]["real0"]
    want = np.sqrt(0.25 + 4 * np.sin(k1 / 2) ** 2)
    assert ch["peaks"][1] and abs(ch["peaks"][1][0] - want) < 2 * np.pi / (1024 * 0.2)


def test_energy_parts_add_up():
    s = sb.spec_from("continuous", hbar=1e-2)
    st = sb.run(s, sb.make_initial(s, (8, 8, 8), np.random.default_rng(1)), 0.2, 50)
    e = ec.energy_parts(s, st)
    assert abs(e["total"] - sb.energy(s, st)) < 1e-9 * abs(e["total"])
    assert e["electric"] > 0 and e["magnetic"] > 0


def test_two_scales_give_two_circles():
    """cascade: a circle of valleys for A times ± for B -- two groups, each with one flat direction."""
    s = sb.spec_from("cascade")
    rng = np.random.default_rng(2)
    shape = (24, 24)
    c = np.exp(1j * rng.uniform(-np.pi, np.pi, shape))[None]
    r = np.where(rng.random(shape) < 0.5, -1.0, 1.0)[None] * 0.5
    lab, groups = ec.label_sites(s, _state(s, shape, r=r, c=c))
    assert len(groups) == 2 and [g["flat_dirs"] for g in groups] == [1, 1]
