#!/usr/bin/env python3
"""Additive emergence measures for LEVELS the scalar-field assess_level does not cover (L3 flow, L7
self-replication). This module is NEW and ADDITIVE -- it does NOT change genesis/diagnostics/measures.py
(the L1/L2 success criteria stay untouched, no_touch). Level is still decided BY NUMBERS.

References: EMERGENCE_LEVELS.md. All measures are honest floors:
  - L3 self-organized flow: circulation != 0 AND kinetic energy grew from rest AND (coherent vs churn).
    「turbulent != coherent」: turbulence is still L3 flow, but we FLAG coherence so churn is not sold as
    coherent steady rolls.
  - L7 self-replication: the number of localized spots GROWS by division over time. 「同じ数学 != 同じもの」:
    these are reaction-diffusion spots, not life; the self-replication is a measured field phenomenon.
"""


def assess_flow_level(ke_traj, circulation, late_fluct):
    """Level 3 (spontaneous motion / circulation) from a flow that started at REST.

    ke_traj      : kinetic-energy samples over time (starts ~0 at rest).
    circulation  : a circulation magnitude (e.g. mean |vorticity|); >0 means rotational flow.
    late_fluct   : late-time relative std of KE (small => coherent steady rolls; large => turbulent churn).
    Returns (reached_level, detected, measured_by).
    """
    ke0 = float(ke_traj[0])
    keN = float(ke_traj[-1])
    grew = keN > max(1e-6, 20.0 * (ke0 + 1e-9))          # KE rose well above the rest floor
    rotational = float(circulation) > 1e-6
    coherent = bool(grew and rotational and late_fluct < 0.05)   # steady rolls, not turbulent churn
    flow = bool(grew and rotational)
    reached = 3 if flow else 0                            # self-organized circulation from rest = L3
    detected = {"self_organized_flow": flow, "coherent_rolls": coherent,
                "turbulent_churn": bool(flow and not coherent)}
    measured_by = {"ke_start": round(ke0, 6), "ke_final": round(keN, 4),
                   "circulation": round(float(circulation), 6), "late_fluctuation": round(float(late_fluct), 4)}
    return reached, detected, measured_by


def assess_replication_level(spot_counts):
    """Level 7 (self-replication) signature: localized spots MULTIPLY by growth/division over time.

    spot_counts : number of spots sampled over time (starts at the seed count).
    Reached L7 when the population grows substantially AND ends well above the seed count (division),
    not merely drifting. Returns (reached_level, detected, measured_by).
    """
    c0 = int(spot_counts[0])
    cN = int(spot_counts[-1])
    cmax = int(max(spot_counts))
    replicated = bool(cN >= max(2, c0 + 3) and cmax >= 2 * max(c0, 1))   # multiplied by division
    reached = 7 if replicated else 0
    detected = {"self_replication": replicated}
    measured_by = {"seed_spots": c0, "final_spots": cN, "peak_spots": cmax,
                   "growth_factor": round(cN / max(c0, 1), 3)}
    return reached, detected, measured_by
