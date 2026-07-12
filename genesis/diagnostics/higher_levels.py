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
    """Reproduction, measured HONESTLY per docs/ANTI_DRIFT.md (「答えを置くな」).

    Self-replication (division) EMERGES from the Gray-Scott U,V white (spots come from the U,V
    concentrations already in the white) -> the honest EMERGENT ceiling of this white is **L7-partial**
    (division only). Heredity does NOT emerge from U,V: to get it you must ADD a heritable field (a tag T)
    -- that is PLACING the answer (原則1: tying a bought apple to the tree), NOT emergence. So:

      * division alone  -> L7-partial (emergent, real).
      * tag info given  -> the inheritance is measured but flagged inheritance_placed=True; a full-L7
                           EMERGENCE is NOT claimed (the heritable degree of freedom was placed, not born).

    Returns (reached_level, detected, measured_by). reached_level is 0 (no clean higher Level EMERGED
    beyond the partial); detected carries l7_partial (division) and, if a tag field was placed,
    inheritance_placed=True with the placed-tag metrics. `emergent_ceiling` labels the honest ceiling.
    """
    import numpy as np
    c0, cN, cmax = int(spot_counts[0]), int(spot_counts[-1]), int(max(spot_counts))
    division = bool(cN >= max(2, c0 + 3) and cmax >= 2 * max(c0, 1))
    detected = {"division_not_seeded": division, "l7_partial": division, "full_l7_emergence": False}
    mb = {"seed_spots": c0, "final_spots": cN, "peak_spots": cmax, "growth_factor": round(cN / max(c0, 1), 3),
          "emergent_ceiling": "L7-partial (self-replication/division only)" if division else "below L7"}
    if not spots:
        detected["inheritance_placed"] = False
        return 0, detected, mb
    # A tag field was PLACED (U,V -> U,V,T). We still measure how cleanly the placed tag is carried through
    # division, but this is NOT emergence of heredity from the U,V white (ANTI_DRIFT 原則1/原則4).
    purities = [s["purity"] for s in spots]
    sizes = [s["size"] for s in spots]
    tags = [s["tag"] for s in spots]
    frac_clean = float(np.mean([p > 0.6 for p in purities]))
    mean_purity = float(np.mean(purities))
    cv = float(np.std(sizes) / (np.mean(sizes) + 1e-9))
    detected.update({"inheritance_placed": True,
                     "placed_tag_carried_cleanly": bool(frac_clean > 0.7 and mean_purity > 0.6),
                     "accounting_consistent": bool(len(spots) == cN and cv < 1.2),
                     "both_lineages_survive": bool(0 in tags and 1 in tags)})
    mb.update({"placed_frac_clean": round(frac_clean, 3), "placed_mean_purity": round(mean_purity, 3),
               "spot_size_cv": round(cv, 3), "tag0": tags.count(0), "tag1": tags.count(1),
               "note": "tag field PLACED (U,V->U,V,T): inheritance is placed, not emergent (docs/ANTI_DRIFT.md)"})
    return 0, detected, mb                                 # no full-L7 EMERGENCE claim; heredity was placed
