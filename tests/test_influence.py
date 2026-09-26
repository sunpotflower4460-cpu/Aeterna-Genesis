"""Twin-universe influence: a poke spreads like light in the wave white, like diffusion in a diffusive one."""
import numpy as np

from genesis.diagnostics.influence import kind, twin_influence
from genesis.models import wave_klein_gordon as kg


def test_wave_spreads_at_the_speed_of_light():
    p = dict(kg.DEFAULTS)
    n = 101
    state = {"phi": np.ones((n, n)), "pi": np.zeros((n, n))}           # vacuum

    def adv(s, k):
        phi, pi = s["phi"], s["pi"]
        for _ in range(k):
            phi, pi = kg.step(phi, pi, p)
        return {"phi": phi, "pi": pi}

    r = twin_influence(state, adv, "phi", (50, 50), 1e-6, 8, 25, p["dt"])
    assert all(x["front"] <= x["t"] + 3 for x in r["rows"])            # the front (0.1% of max) stays in the light cone
    # the lattice itself can only move a signal one cell per step (5c at dt = 0.2): a strict bound even for the
    # far, ~1e-6-relative numerical fringe that `reach` sees
    assert all(x["reach"] <= x["t"] / p["dt"] + 1 for x in r["rows"])
    assert r["lin_over_sqrt"] < 1.5 and kind(r, 25) == "steady"          # a steady front (massive: v < c)
    assert 0.5 < r["front_speed"] <= 1.0


def test_diffusion_spreads_like_sqrt_t():
    n, D, dt = 101, 0.2, 1.0
    state = {"u": np.zeros((n, n))}

    def adv(s, k):
        u = s["u"]
        for _ in range(k):
            u = u + D * dt * (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u)
        return {"u": u}

    r = twin_influence(state, adv, "u", (50, 50), 1e-6, 8, 40, dt, rel=1e-2)
    assert 0.35 < r["alpha"] < 0.65 and r["lin_over_sqrt"] > 2 and kind(r, 40) == "slowing"   # like sqrt(t)
