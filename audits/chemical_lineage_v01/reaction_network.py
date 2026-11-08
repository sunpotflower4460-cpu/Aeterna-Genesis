"""Reversible association reactions of the abstract test network (v0.1).

Reactions (declared, not chosen to produce any outcome):
    R0: X  + Y  <-> XY
    R1: X  + Z  <-> XZ
    R2: XY + Z  <-> XYZ
    R3: XZ + Y  <-> XYZ

Rate constants: forward k+ = KF for every reaction (declared), reverse k- = k+ / K_r with K_r fixed by the
standard chemical potentials in thermodynamics.py (detailed balance by construction, not randomised).
"""
import numpy as np

from species import IDX, SPECIES, UNITS

REACTIONS = [
    {"name": "X+Y<->XY", "reactants": {"X": 1, "Y": 1}, "products": {"XY": 1}},
    {"name": "X+Z<->XZ", "reactants": {"X": 1, "Z": 1}, "products": {"XZ": 1}},
    {"name": "XY+Z<->XYZ", "reactants": {"XY": 1, "Z": 1}, "products": {"XYZ": 1}},
    {"name": "XZ+Y<->XYZ", "reactants": {"XZ": 1, "Y": 1}, "products": {"XYZ": 1}},
]
KF = 1.0  # forward rate constant of every reaction, in units of 1/time (declared)


def stoichiometry():
    """Net stoichiometric matrix NU[i, r] = nu_{i r} (products positive, reactants negative)."""
    nu = np.zeros((len(SPECIES), len(REACTIONS)))
    for r, rx in enumerate(REACTIONS):
        for s, k in rx["reactants"].items():
            nu[IDX[s], r] -= k
        for s, k in rx["products"].items():
            nu[IDX[s], r] += k
    return nu


NU = stoichiometry()


def order_matrix(side):
    """Matrix M[i, r] = stoichiometric coefficient of species i on side 'reactants' or 'products'."""
    m = np.zeros((len(SPECIES), len(REACTIONS)))
    for r, rx in enumerate(REACTIONS):
        for s, k in rx[side].items():
            m[IDX[s], r] = k
    return m


MR = order_matrix("reactants")
MP = order_matrix("products")


def conservation_residual():
    """Max |sum_i nu_ir UNITS[i,e]| over reactions and elements. Must be exactly 0 (T01)."""
    return float(np.max(np.abs(NU.T @ UNITS)))
