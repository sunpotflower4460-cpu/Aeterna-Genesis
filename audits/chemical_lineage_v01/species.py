"""Abstract species of the chemical lineage audit (v0.1).

These are ABSTRACT molecules defined only by their counts of three conserved building units X, Y, Z.
They are not specific real molecules, and the reaction set is a test network, not a reproduction of
any measured chemistry (see MODEL_CONTRACT.md).
"""
import numpy as np

SPECIES = ["X", "Y", "Z", "XY", "XZ", "XYZ"]
IDX = {s: i for i, s in enumerate(SPECIES)}

# UNITS[i, e] = number of building unit e (0:X, 1:Y, 2:Z) in species i
UNITS = np.array([
    [1, 0, 0],   # X
    [0, 1, 0],   # Y
    [0, 0, 1],   # Z
    [1, 1, 0],   # XY
    [1, 0, 1],   # XZ
    [1, 1, 1],   # XYZ
], dtype=float)


def element_totals(c):
    """Building-unit totals sum_i UNITS[i,e] c_i for concentrations c (volume V = 1)."""
    return UNITS.T @ np.asarray(c, dtype=float)


def monomers_with_units(units):
    """A state made only of free monomers X, Y, Z carrying the given building-unit totals."""
    c = np.zeros(len(SPECIES))
    c[IDX["X"]], c[IDX["Y"]], c[IDX["Z"]] = units
    return c
