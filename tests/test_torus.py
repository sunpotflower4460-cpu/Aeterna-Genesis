"""The torus (P10): a flux quantum through the hole gathers into one string that cannot vanish; its tension;
and the two-arm line on a torus that closes (fraction) or keeps filling (π, φ+1)."""
import numpy as np

from genesis.models import abelian_higgs_nd as an
from tools.torus_flux import t1, t2, twisted_links
from tools.torus_lines import coverage_curve


def test_twisted_links_thread_one_even_quantum():
    for shape in ((16, 16), (12, 10, 4)):
        th = twisted_links(shape)
        P = an.wrap(an.plaquette(th, 0, 1))
        B = 2 * np.pi / (shape[0] * shape[1])
        assert np.allclose(P, -B, atol=1e-12)                       # every plaquette the same, seam included
        assert np.allclose(P.sum(axis=(0, 1)) / (2 * np.pi), -1.0)
        for i, j in an.planes(len(shape)):
            if (i, j) != (0, 1):
                assert np.abs(an.wrap(an.plaquette(th, i, j))).max() < 1e-12


def test_the_spread_flux_gathers_into_one_straight_quantized_string():
    r = t1(24, 8, 0.01, 1, 300.0)
    assert r["net_per_slice_ever"] == [-1]                           # conserved from t = 0 on
    assert r["end_length"] == 8 and r["end_wrapped"] == [2]          # one straight string around the torus
    f = r["end_flux"][2]
    assert f["piercings"] == 8 and f["worst"] < 0.02
    assert r["max_gauss"] < 1e-12


def test_tension_is_2pi_at_the_bps_point_lower_below_higher_above():
    T = {b: t2(b, n=24, T=300.0) for b in (0.5, 1.0, 2.0)}
    assert all(r["vortices"] == 1 and abs(r["net"]) == 1 for r in T.values())
    assert abs(T[1.0]["ratio_to_bps"] - 1.0) < 0.01                 # Bogomolny bound, exact at β = 1
    assert T[0.5]["ratio_to_bps"] < 0.95 and T[2.0]["ratio_to_bps"] > 1.05


def test_a_fraction_closes_and_stops_an_irrational_keeps_filling():
    c227 = coverage_curve(22 / 7, [7, 50], G=256)
    # closed after 7 turns: later passes retrace it (only a few corner-clipped cells are added)
    assert c227[0]["coverage"] < 0.15 and c227[1]["coverage"] - c227[0]["coverage"] < 0.01
    gold = coverage_curve((1 + 5 ** 0.5) / 2 + 1, [7, 500], G=256)
    assert gold[1]["coverage"] > 0.99
    rat, pi = coverage_curve(355 / 113, [113, 1000], G=2048), coverage_curve(np.pi, [113, 1000], G=2048)
    assert abs(rat[0]["coverage"] - pi[0]["coverage"]) < 0.01      # indistinguishable until 113 turns
    assert pi[1]["coverage"] - rat[1]["coverage"] > 0.01            # then π keeps creeping, 355/113 does not
