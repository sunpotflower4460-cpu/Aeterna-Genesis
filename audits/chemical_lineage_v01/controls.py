"""Seeded initial states and the arms of the lineage experiment (v0.1).

Seeded initial state (gen 0): an EXTERNAL preparation, declared, not emerged. Each series has a different
molecular distribution with the same building-unit totals T. It is not a mutation and carries no trait.

Arms (MODEL_CONTRACT.md §7):
  L1  own-parent lineage; protocol mode L1; reactions on
  LR  units-only counterfactual; protocol mode LR; reactions on (parent's transferred part reconstituted)
  L0  untransferred control; fresh monomers each generation (protocol mode L0); reactions on
  LN  passive; protocol mode L1 with reaction constants zero
  LS  foreign donor; protocol mode LS; donor = L1 end state of series (s + donor_offset) mod S, same generation
"""
import numpy as np

import solver as S
import thermodynamics as TH
import transfer_protocol as P
from species import IDX


def seed_state(seed, T=1.0, max_complex_fraction=0.3):
    """Deterministic seeded state (gen 0) with element totals T for X, Y, Z."""
    rng = np.random.default_rng(10_000 + seed)
    nXY, nXZ, nXYZ = rng.uniform(0.0, max_complex_fraction, size=3) * T
    c = np.zeros(6)
    c[IDX["XY"]], c[IDX["XZ"]], c[IDX["XYZ"]] = nXY, nXZ, nXYZ
    c[IDX["X"]] = T - nXY - nXZ - nXYZ
    c[IDX["Y"]] = T - nXY - nXYZ
    c[IDX["Z"]] = T - nXZ - nXYZ
    if np.any(c < 0):
        raise ValueError("seed state has negative species")
    return c


def run_arm(arm, n_series, tau, f, n_gen, kf_scale=1.0, donor_ends=None, T=1.0, seed_offset=0):
    """Run one arm for all series. Returns ends[s, g, :] for g = 0..n_gen (g=0 is the seeded/fresh start).

    donor_ends: array (n_series, n_gen+1, 6) of the L1 arm, used only by LS.
    """
    kf0, kr0 = TH.forward_reverse_rates()
    kf, kr = kf0 * kf_scale, kr0 * kf_scale
    if arm == "LN":
        kf, kr = 0.0, 0.0
    ends = np.zeros((n_series, n_gen + 1, 6))
    for s in range(n_series):
        if arm == "L0":
            ends[s, 0] = P.fresh_material(0.0, T)
        else:
            ends[s, 0] = seed_state(s + seed_offset, T)
        for g in range(1, n_gen + 1):
            if arm == "L0":
                start, _ = P.start_of_generation(None, 0.0, "L0", T=T)
            elif arm == "LS":
                donor_index = (s + n_series // 2) % n_series   # declared: offset n/2, never the series itself
                if donor_index == s:
                    raise ValueError("donor must be an independent series")
                d = donor_ends[donor_index, g - 1]
                start, _ = P.start_of_generation(ends[s, g - 1], f, "LS", donor_end=d, T=T)
            elif arm == "LR":
                start, _ = P.start_of_generation(ends[s, g - 1], f, "LR", T=T)
            else:  # L1 and LN
                start, _ = P.start_of_generation(ends[s, g - 1], f, "L1", T=T)
            ends[s, g] = S.end_state(start, tau, kf, kr)
    return ends
