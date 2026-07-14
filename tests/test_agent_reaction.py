"""agent_reaction: a LOCAL, PARALLEL, controller-free white. Tests that macroscopic laws EMERGE from purely
local particle rules (no global operation): the diffusion law (MSD linear in t) and an exactly-conserved
(N_A - N_B) from local A+B->0. Answers 'why compute one by one?' -- we don't; local interactions suffice.
no_touch: measures.py untouched. Deterministic (seeded)."""
import numpy as np

from genesis.models import agent_reaction as ar


def test_diffusion_law_emerges_from_local_hops():
    """Purely local parallel +-1 hops -> MSD(t) = t (the continuum diffusion law), measured not imposed."""
    steps = 400
    msd = ar.msd_walk(nP=4000, steps=steps, seed=0)
    # slope of MSD vs t is ~1 for the unit hop (|dr|^2 = 1 each step)
    t = np.arange(steps + 1)
    slope = float(np.polyfit(t, msd, 1)[0])
    assert 0.9 < slope < 1.1                         # linear growth = diffusion emerged
    assert msd[steps] > msd[steps // 2] > msd[1]     # monotone spreading


def test_local_reaction_conserves_A_minus_B_exactly():
    """Local A+B->0 removes one A and one B per shared site -> (N_A - N_B) is an exact invariant that
    EMERGES from the rule (never placed). Also N_A, N_B are non-increasing."""
    rng = np.random.default_rng(1)
    N = 48
    A, B = ar.make_initial(N, 1200, 900, rng)        # start with a deliberate imbalance
    diff0 = len(A) - len(B)
    prev_a, prev_b = len(A), len(B)
    total_reacted = 0
    for _ in range(60):
        A, B, nr = ar.step(A, B, N, rng, p_react=1.0)
        assert (len(A) - len(B)) == diff0            # exact conservation of N_A - N_B
        assert len(A) <= prev_a and len(B) <= prev_b  # annihilation only removes
        prev_a, prev_b = len(A), len(B)
        total_reacted += nr
    assert total_reacted > 0                         # reactions actually happened (local contact occurred)
    assert len(B) < 900                              # the minority species is being consumed


def test_deterministic_given_seed():
    """Same seed -> identical trajectory counts (reproducible; no hidden global state)."""
    def run():
        rng = np.random.default_rng(7)
        A, B = ar.make_initial(40, 500, 500, rng)
        seq = []
        for _ in range(20):
            A, B, nr = ar.step(A, B, 40, rng, p_react=1.0)
            seq.append((len(A), len(B), nr))
        return seq
    assert run() == run()


def test_step_is_local_only_no_global_field():
    """A particle only ever moves to a 4-neighbour site (displacement <= 1 per axis under min-image):
    the update is local, never a global/collective operation."""
    rng = np.random.default_rng(3)
    N = 64
    A, B = ar.make_initial(N, 300, 300, rng)
    A0 = A.copy()
    A1, _, _ = ar.step(A, B, N, rng, p_react=0.0)    # no reaction so A particles persist 1:1
    d = np.abs(A1 - A0)
    d = np.minimum(d, N - d)                          # minimum-image distance
    assert d.max() <= 1                              # moved at most one lattice step (purely local)
    assert d.sum(axis=1).max() <= 1                  # 4-neighbour: at most one axis changes
