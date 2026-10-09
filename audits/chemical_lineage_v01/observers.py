"""Observers for the lineage experiment (v0.1). Read-only: they never modify the state they receive (T11).

M1  composition distance: half L1 distance between concentration vectors (absolute units, V = 1, T = 1).
    The absolute form is used because mixing with fresh material is then exactly linear (passive baseline).
M1b molecule-fraction distance, reported alongside (not used for the verdicts).
M3  parent-specific dispersion of a set of lineages at one generation: each series' distance to the mean state
    of all series in the same arm and generation (per-series quantity, so the statistical unit is the series).
M4  transfer-induced offset: distance between an L1 lineage and its units-only counterfactual LR at the same
    generation.
M6  building-unit totals and complexed-unit fraction (ledger quantities).
M7  reaction usage: mean absolute net rate of each reaction (diagnostic only).
"""
import numpy as np

import reaction_network as RN
import species as SP
import thermodynamics as TH


def dist_abs(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(0.5 * np.sum(np.abs(a - b)))


def dist_fraction(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    pa = a / np.sum(a)
    pb = b / np.sum(b)
    return float(0.5 * np.sum(np.abs(pa - pb)))


def per_series_dispersion(states):
    """states: array (n_series, 6) at one generation of one arm. Returns per-series distance to the mean state."""
    states = np.asarray(states, dtype=float)
    mean = states.mean(axis=0)
    return np.array([dist_abs(s, mean) for s in states])


def per_series_offset(lineage_states, counterfactual_states):
    """Per-series distance between a lineage and its paired counterfactual at one generation (M4)."""
    a = np.asarray(lineage_states, dtype=float)
    b = np.asarray(counterfactual_states, dtype=float)
    return np.array([dist_abs(x, y) for x, y in zip(a, b)])


def complexed_unit_fraction(c):
    """Fraction of building units bound in complexes (M6). Total units are 3T for T = 1 per element."""
    c = np.asarray(c, dtype=float)
    units_total = float(np.sum(SP.UNITS.sum(axis=1) * c))
    units_free = float(c[SP.IDX["X"]] + c[SP.IDX["Y"]] + c[SP.IDX["Z"]])
    return 0.0 if units_total == 0 else 1.0 - units_free / units_total


def element_units(c):
    return SP.element_totals(c)


def reaction_usage(c, kf=None, kr=None):
    """M7: |net rate| of each reaction at state c (diagnostic)."""
    if kf is None or kr is None:
        kf, kr = TH.forward_reverse_rates()
    return np.abs(TH.reaction_rates(np.asarray(c, dtype=float), kf, kr))
