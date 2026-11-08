"""External generation-transfer protocol (v0.1). This is an EXPERIMENTAL OPERATION, not a chemical reaction.

Rules (MODEL_CONTRACT.md §6):
  * The protocol reads the CURRENT molecular state of the donor and moves a fraction f of it. It never reads any
    trait label, never copies a parent description into a child, and never sets the child's state toward a target.
  * Fresh material is free monomers X, Y, Z carrying the building units (1 - f) * T that the transfer removed
    from the vessel. So every vessel keeps element totals T.
  * The mixing step is recorded as an external operation in a ledger. It is not treated as dissipation.

Modes (starts of a generation):
  L1  : f * (own parent end state)          + fresh            (lineage)
  LS  : f * (donor end state, independent)  + fresh            (foreign donor)
  LR  : f * reconstitute(own parent end)    + fresh            (units-only counterfactual)
  L0  : fresh only, no transfer (f = 0)                        (untransferred control)
  LN  : as L1, but reaction constants are zero (passive)       (applied in controls.py, not here)
"""
import numpy as np

from species import SPECIES, element_totals, monomers_with_units
import thermodynamics as TH


def fresh_material(f, T=1.0):
    """Free monomers with building-unit totals (1 - f) * T for X, Y, Z."""
    return monomers_with_units((1.0 - f) * np.full(3, T))


def reconstitute(c):
    """Counterfactual: the same building-unit totals as state c, all carried by free monomers (no complexes)."""
    return monomers_with_units(element_totals(c))


def start_of_generation(parent_end, f, mode, donor_end=None, T=1.0):
    """New vessel content at the start of the next generation. Returns (start, ledger_dict)."""
    if mode == "L0":
        start = fresh_material(0.0, T)
        transferred = np.zeros(len(SPECIES))
    elif mode == "L1":
        transferred = f * np.asarray(parent_end, dtype=float)
        start = transferred + fresh_material(f, T)
    elif mode == "LS":
        if donor_end is None:
            raise ValueError("LS needs a donor end state")
        transferred = f * np.asarray(donor_end, dtype=float)
        start = transferred + fresh_material(f, T)
    elif mode == "LR":
        transferred = f * reconstitute(parent_end)
        start = transferred + fresh_material(f, T)
    else:
        raise ValueError(mode)
    ledger = {
        "mode": mode,
        "f": f,
        "transferred_units": element_totals(transferred).tolist(),
        "fresh_units": element_totals(fresh_material(f, T) if mode != "L0" else fresh_material(0.0, T)).tolist(),
        "start_units": element_totals(start).tolist(),
        "removed_units_expected": (f * element_totals(parent_end)).tolist() if mode in ("L1", "LN") else None,
    }
    return start, ledger


def free_energy_or_none(c):
    c = np.asarray(c, dtype=float)
    return TH.free_energy(c) if np.all(c > 0) else None
