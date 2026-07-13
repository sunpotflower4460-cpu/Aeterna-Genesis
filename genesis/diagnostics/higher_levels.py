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


def assess_individuality_level(amax, area_fraction, persistence_change,
                               recovers_after_perturbation, size_independent, centroid_drift):
    """Level 4 (persistent individuality) per EMERGENCE_LEVELS.md, measured HONESTLY.

    L4 judgment there = `inside_outside_contrast > θ AND tracked_id_lifetime > τ AND
    recovers_after_perturbation` AND size-independent (not a finite-size effect). The DISCRIMINATOR that
    separates a genuine L4 individual from an L2 frozen defect is **recovery after perturbation**
    (self-healing) -- you cannot PLACE self-healing (ANTI_DRIFT). Self-MOTION (L3 in a body) is a SEPARATE
    axis: an individual may be persistent yet STATIC. A self-propelled individual (L4 AND self-motion) is
    the map's true missing conjunction and is frontier.

    amax                       : peak |field| inside the structure (inside/outside contrast vs ~0 background).
    area_fraction              : support area / domain area (localized => small; ~1 => global, not an individual).
    persistence_change         : late-time max |u_{t+dt}-u_t| (small => settled to a stable attractor).
    recovers_after_perturbation: True if, after destroying part of it, the structure REGREW (self-healing).
    size_independent           : True if the same individual forms on a larger domain (not finite-size).
    centroid_drift             : centroid displacement over a long window (>0 => self-moving; ~0 => static).
    Returns (reached_level, detected, measured_by).
    """
    localized = 0.0 < float(area_fraction) < 0.25          # bounded support, not the whole domain
    contrast = float(amax) > 0.5                            # clear inside signal vs ~0 outside
    persistent = float(persistence_change) < 1e-2          # settled to a stable attractor (tracked id persists)
    recovers = bool(recovers_after_perturbation)           # self-heals after a cut -> genuine individual (not L2)
    size_indep = bool(size_independent)
    self_moving = float(centroid_drift) > 0.5              # spontaneous motion of the individual (L3 in a body)
    individual = bool(localized and contrast and persistent and recovers and size_indep)
    reached = 4 if individual else 0                       # L4 individuality criteria (motion is a separate axis)
    if not individual:
        ceiling = "below L4 (no persistent self-healing localized individual)"
    elif self_moving:
        ceiling = "L4 + self-motion (self-propelled individual)"   # the missing conjunction (not expected here)
    else:
        ceiling = ("L4 persistent individuality, STATIC: inside/outside + self-healing + size-independent, "
                   "but VARIATIONAL -> no self-motion (self-propelled individual = frontier)")
    detected = {"persistent_individual": individual, "self_healing": recovers, "localized": localized,
                "size_independent": size_indep, "self_moving": self_moving,
                "static_individual": bool(individual and not self_moving)}
    measured_by = {"amax": round(float(amax), 3), "area_fraction": round(float(area_fraction), 4),
                   "persistence_change": float(persistence_change), "centroid_drift": round(float(centroid_drift), 4),
                   "recovers_after_perturbation": recovers, "size_independent": size_indep,
                   "emergent_ceiling": ceiling}
    return reached, detected, measured_by


def assess_self_propulsion(count_series, area_fraction_series, seed_displacement_vectors,
                           recovers_after_perturbation):
    """A SELF-PROPELLED individual (L4 individuality AND emergent self-motion), measured HONESTLY, with the
    anti-trap that separates a single moving BODY from a moving POPULATION (the Gray-Scott replication trap:
    a replicating cluster's centroid wanders, which is NOT one individual self-propelling).

    The decisive 3-check (docs: self_propelled_individual_white_search):
      1. SINGLE body        : spot count stays 1 (not replication / splitting).
      2. motion EMERGENT     : from symmetric ICs the drift direction is RANDOM across seeds (spontaneous
                               symmetry breaking). A FIXED direction => IC/boundary artifact, not emergence.
      3. SELF-HEALING (L4)   : recovers its form after a perturbation.
    Also COMPACT (not domain-filling) so a "single body" is genuinely localized.

    count_series             : spot counts over time (late half should be all 1 for a single body).
    area_fraction_series     : support-area / domain-area over time (compact => small; ~1 => filled).
    seed_displacement_vectors: list of (dy,dx) net centroid displacements, ONE PER SEED (>=2 seeds).
    recovers_after_perturbation: True if the body recovers after a cut (self-healing, L4).
    Returns (reached_level, detected, measured_by). reached_level is 4 only if a SINGLE COMPACT body moves
    with an EMERGENT (random-direction) drift AND self-heals; else 0 (frontier), with replication_drift_trap
    flagged when motion comes from a non-single (replicating/splitting) structure.
    """
    import numpy as np
    late = slice(max(1, len(count_series) // 2), None)
    single_body = bool(len(count_series) and all(int(c) == 1 for c in count_series[late]))
    compact = bool(len(area_fraction_series) and max(area_fraction_series[late]) < 0.25)
    vecs = [np.asarray(v, dtype=float) for v in (seed_displacement_vectors or [])]
    speeds = [float(np.hypot(v[0], v[1])) for v in vecs]
    moves = bool(speeds and float(np.mean(speeds)) > 1.0)     # net displacement well above measurement noise
    # emergent = random direction across seeds: normalized resultant length ~0 (vectors point every which way)
    if len(vecs) >= 2 and all(s > 1e-9 for s in speeds):
        units = np.array([v / (np.hypot(v[0], v[1]) + 1e-12) for v in vecs])
        resultant = float(np.hypot(*units.mean(axis=0)))      # ~1 => aligned (artifact); ~0 => random (emergent)
        emergent_random = bool(resultant < 0.6)
    else:
        resultant, emergent_random = 1.0, False
    recovers = bool(recovers_after_perturbation)
    self_propelled = bool(single_body and compact and moves and emergent_random and recovers)
    replication_drift_trap = bool(moves and not single_body)   # motion from a replicating population (not one body)
    reached = 4 if self_propelled else 0
    if self_propelled:
        ceiling = "L4 + self-motion: a SINGLE compact body self-propels with emergent (random) direction and self-heals"
    elif replication_drift_trap:
        ceiling = "NOT self-propelled: motion is a REPLICATING population's centroid wander (Gray-Scott trap), not one body"
    elif single_body and not moves:
        ceiling = "static single individual (L4-static): a single body but no self-motion emerged"
    else:
        ceiling = "self-propelled single individual NOT reached (dies/fills/splits) -> frontier"
    detected = {"self_propelled_individual": self_propelled, "single_body": single_body, "compact": compact,
                "self_motion": moves, "emergent_random_direction": emergent_random, "self_healing": recovers,
                "replication_drift_trap": replication_drift_trap}
    measured_by = {"n_seeds": len(vecs), "mean_speed_disp": round(float(np.mean(speeds)) if speeds else 0.0, 3),
                   "direction_resultant": round(resultant, 3), "max_area_fraction": round(
                       float(max(area_fraction_series[late])) if len(area_fraction_series) else 0.0, 3),
                   "late_counts": [int(c) for c in count_series[late]], "emergent_ceiling": ceiling}
    return reached, detected, measured_by
