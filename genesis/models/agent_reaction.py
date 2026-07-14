#!/usr/bin/env python3
"""Agent-based, LOCAL, PARALLEL, controller-free chemistry -- a DISTINCT white that computes the way reality
does: there is NO central solver deciding each particle's role. Species-A and species-B particles each take
a LOCAL random hop (nearest-neighbour only) simultaneously (parallel), and when an A and a B land on the SAME
site they react locally (A + B -> nothing). No global operation (no FFT, no implicit solve, no oracle): a
particle only ever touches its own site and its four neighbours. Macroscopic laws are then MEASURED to emerge,
not imposed:

  * with no reaction, the local parallel hops make the mean-squared displacement grow LINEARLY in time
    (the diffusion law emerges: MSD = t for the unit ±1 hop) -- a continuum law from purely local events;
  * the local A+B->0 reaction EXACTLY conserves (N_A - N_B) -- a conservation law that emerges from the rule,
    never placed.

This is the honest-physics answer to "why compute one by one?" -- we do not; A and B just interact locally and
"what happens becomes measurable". no_touch: measures.py untouched. spots/particles != life. Deterministic
given a seed (np.random.default_rng). 同じ数学 != 同じもの.
"""

import numpy as np

MODEL_ID = "agent_reaction_local"

# nA/nB particles of each species on an N x N periodic lattice; p_react = local reaction probability per
# shared site per step. Purely local: the update reads only a particle's site and its 4 neighbours.
DEFAULTS = {"N": 96, "nA": 1500, "nB": 1500, "p_react": 1.0}


def _hop_delta(m, rng):
    """The LOCAL rule: each of m particles steps +-1 along one axis (4-neighbour), chosen independently."""
    d = rng.integers(0, 4, m)
    dx = np.where(d == 0, 1, np.where(d == 1, -1, 0))
    dy = np.where(d == 2, 1, np.where(d == 3, -1, 0))
    return dx, dy


def make_initial(N, nA, nB, rng):
    """Two clouds of point particles at random sites (structureless start). Returns (A, B) int arrays (n,2)."""
    A = np.stack([rng.integers(0, N, nA), rng.integers(0, N, nA)], axis=1)
    B = np.stack([rng.integers(0, N, nB), rng.integers(0, N, nB)], axis=1)
    return A, B


def _react(A, B, N, rng, p_react):
    """Local A+B->0 on shared sites: remove (at most) one A and one B per co-occupied site. Conserves
    (N_A - N_B) exactly. Only neighbours-of-nobody logic: a site reacts using only what sits on it."""
    if len(A) == 0 or len(B) == 0:
        return A, B, 0
    sa = A[:, 0] * N + A[:, 1]
    sb = B[:, 0] * N + B[:, 1]
    first_b = {}
    for j in range(len(sb)):
        s = int(sb[j])
        if s not in first_b:
            first_b[s] = j
    rem_a, rem_b, used = [], [], set()
    for i in range(len(sa)):
        s = int(sa[i])
        jb = first_b.get(s)
        if jb is not None and s not in used and rng.random() <= p_react:
            rem_a.append(i)
            rem_b.append(jb)
            used.add(s)
    if not rem_a:
        return A, B, 0
    keep_a = np.ones(len(A), bool); keep_a[rem_a] = False
    keep_b = np.ones(len(B), bool); keep_b[rem_b] = False
    return A[keep_a], B[keep_b], len(rem_a)


def step(A, B, N, rng, p_react=1.0):
    """One PARALLEL local step: every particle hops locally at once, then co-located A,B react locally.
    Returns (A, B, n_reacted). No global/collective operation is used."""
    if len(A):
        dxa, dya = _hop_delta(len(A), rng)
        A = np.stack([(A[:, 0] + dxa) % N, (A[:, 1] + dya) % N], axis=1)
    if len(B):
        dxb, dyb = _hop_delta(len(B), rng)
        B = np.stack([(B[:, 0] + dxb) % N, (B[:, 1] + dyb) % N], axis=1)
    A, B, nr = _react(A, B, N, rng, p_react)
    return A, B, nr


def msd_walk(nP, steps, seed=0):
    """Measure the emergent diffusion law from the SAME local hop rule, tracking UNBOUNDED displacement (no
    wrap). Returns msd[t] = mean_particles |x(t)-x(0)|^2. For the unit +-1 hop, |dr|^2 = 1 each step, so the
    local parallel rule yields MSD(t) = t -- the diffusion equation emerging from purely local events."""
    rng = np.random.default_rng(seed)
    pos = np.zeros((nP, 2), float)
    msd = np.zeros(steps + 1)
    for t in range(1, steps + 1):
        dx, dy = _hop_delta(nP, rng)
        pos[:, 0] += dx; pos[:, 1] += dy
        msd[t] = float(np.mean(pos[:, 0] ** 2 + pos[:, 1] ** 2))
    return msd


def counts(A, B):
    return {"nA": int(len(A)), "nB": int(len(B)), "diff": int(len(A) - len(B))}


def density_grid(P, N):
    """Coarse occupancy count per site (for visualisation / macroscopic-field comparison)."""
    g = np.zeros((N, N))
    if len(P):
        np.add.at(g, (P[:, 0], P[:, 1]), 1.0)
    return g
