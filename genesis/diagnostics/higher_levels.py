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


def assess_replication_level(spot_counts, spots=None):
    """Level 7 (reproduction). FULL L7 needs THREE things, not just division:

        reached_L7 = division_not_seeded AND state_inherited AND accounting_consistent

      - division_not_seeded : spots MULTIPLY by division from the seed count (growth, doubling).
      - state_inherited     : each spot carries a CLEAN bistable heritable tag (0/1) -- daughters inherit
                              the parent's tag (measured, not commanded). frac_clean>0.7 AND mean_purity>0.6.
      - accounting_consistent: the spots are genuine similar-sized separate components (guards the
                              "static division accounting" trap where one static region is miscounted).

    spot_counts : spot count sampled over time (starts at the seed/founder count).
    spots       : final per-spot list of {tag, purity, size} (from gray_scott.spot_tags). If omitted,
                  only DIVISION is measurable -> the result is L7-PARTIAL (honest), never full L7.
    Returns (reached_level, detected, measured_by): reached_level == 7 ONLY for full L7; otherwise 0 with
    detected['l7_partial'] flagging division-without-heredity.
    """
    import numpy as np
    c0, cN, cmax = int(spot_counts[0]), int(spot_counts[-1]), int(max(spot_counts))
    division = bool(cN >= max(2, c0 + 3) and cmax >= 2 * max(c0, 1))
    detected = {"division_not_seeded": division}
    mb = {"seed_spots": c0, "final_spots": cN, "peak_spots": cmax, "growth_factor": round(cN / max(c0, 1), 3)}
    if not spots:                                          # no tag info -> division only -> L7-partial
        detected["state_inherited"] = None
        detected["full_l7"] = False
        detected["l7_partial"] = division
        return 0, detected, mb
    purities = [s["purity"] for s in spots]
    sizes = [s["size"] for s in spots]
    tags = [s["tag"] for s in spots]
    frac_clean = float(np.mean([p > 0.6 for p in purities]))
    mean_purity = float(np.mean(purities))
    state_inherited = bool(frac_clean > 0.7 and mean_purity > 0.6)
    cv = float(np.std(sizes) / (np.mean(sizes) + 1e-9))    # size uniformity -> genuine separate spots
    accounting_consistent = bool(len(spots) == cN and cv < 1.2)
    full = bool(division and state_inherited and accounting_consistent)
    detected.update({"state_inherited": state_inherited, "accounting_consistent": accounting_consistent,
                     "full_l7": full, "l7_partial": bool(division and not full),
                     "both_lineages_survive": bool(0 in tags and 1 in tags)})
    mb.update({"frac_clean_bistable": round(frac_clean, 3), "mean_purity": round(mean_purity, 3),
               "spot_size_cv": round(cv, 3), "tag0": tags.count(0), "tag1": tags.count(1)})
    return (7 if full else 0), detected, mb
