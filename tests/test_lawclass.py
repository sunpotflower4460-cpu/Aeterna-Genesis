"""Multiple law classes climb from t=0 to deeper Levels than GL: flow (L3) and self-replication (L7).

Discipline checked: every IC is generic (rest+noise / noise seeds), NEVER the target (第8監査); the
reached Level is MEASURED; the existing scalar measures.assess_level is untouched (no_touch).
"""

import numpy as np

from ai_lab import lab
from genesis.models import gray_scott as gs
from genesis.diagnostics import higher_levels as hl


def test_gray_scott_self_replicates_from_seeds():
    """From a FEW noise seeds, reaction-diffusion spots multiply by division (not seeded as the pattern)."""
    p = dict(gs.DEFAULTS)
    rng = np.random.default_rng(0)
    U, V = gs.make_initial((96, 96), p["n_seeds"], rng, seed_radius=p["seed_radius"])
    c0 = gs.spot_count(V)
    assert c0 <= p["n_seeds"] + 1                       # start = the seeds only, NOT a replicated pattern
    for i in range(12000):
        U, V = gs.step(U, V, p)
    assert np.all(np.isfinite(V))
    cN = gs.spot_count(V)
    assert cN >= 2 * c0                                 # population multiplied by division (self-replication)


def test_flow_level_measure_l3_and_rest_l0():
    l3, det, _ = hl.assess_flow_level([0.0, 50.0, 112.0, 112.0], circulation=50.0, late_fluct=0.0)
    assert l3 == 3 and det["self_organized_flow"] and det["coherent_rolls"]
    l0, _, _ = hl.assess_flow_level([0.0, 0.0, 0.0], circulation=0.0, late_fluct=0.0)
    assert l0 == 0
    # turbulent churn is still flow (L3) but flagged NOT coherent (turbulent != coherent)
    lt, dt, _ = hl.assess_flow_level([0.0, 1000.0, 3000.0, 2000.0], circulation=80.0, late_fluct=0.4)
    assert lt == 3 and dt["turbulent_churn"] and not dt["coherent_rolls"]


def test_full_l7_needs_division_AND_inheritance():
    """FULL L7 = division AND state_inherited AND accounting_consistent. Division ALONE is only L7-partial."""
    # division only (no tag info) -> L7-partial, NOT full L7
    lp, det, _ = hl.assess_replication_level([8, 12, 18, 20])
    assert lp == 0 and det["division_not_seeded"] and det["l7_partial"] and not det["full_l7"]
    # division + clean inherited bistable tags + uniform spots -> FULL L7
    spots = [{"tag": t, "purity": 0.95, "size": 30} for t in ([0] * 10 + [1] * 10)]
    lf, detf, mbf = hl.assess_replication_level([8, 12, 18, 20], spots=spots)
    assert lf == 7 and detf["full_l7"] and detf["state_inherited"] and detf["accounting_consistent"]
    assert detf["both_lineages_survive"] and mbf["mean_purity"] > 0.9
    # division but SMEARED tags (purity ~0, no clean heredity) -> not full L7, stays partial
    smeared = [{"tag": 0, "purity": 0.1, "size": 30} for _ in range(20)]
    ls, dets, _ = hl.assess_replication_level([8, 12, 18, 20], spots=smeared)
    assert ls == 0 and not dets["state_inherited"] and dets["l7_partial"]
    # no division -> not L7 at all
    l0, det0, _ = hl.assess_replication_level([8, 8, 7, 8])
    assert l0 == 0 and not det0["division_not_seeded"]


def test_tagged_gray_scott_inherits_parent_tag():
    """The heritable bistable tag is CLEAN (0/1) and BOTH founder lineages persist through division
    (daughters carry the parent's tag; it is not a global switch and it is not commanded)."""
    p = dict(gs.DEFAULTS)
    rng = np.random.default_rng(1)
    U, V, T, founder_tags = gs.make_initial_tagged((96, 96), 8, rng, seed_radius=p["seed_radius"], mix=0.5)
    assert set(int(t) for t in founder_tags) <= {0, 1}
    for i in range(12000):
        U, V, T = gs.step_tagged(U, V, T, p)
    spots = gs.spot_tags(V, T)
    assert len(spots) >= 2 * 8                              # divided (self-replication)
    purities = [s["purity"] for s in spots]
    assert np.mean([pu > 0.6 for pu in purities]) > 0.7     # clean bistable tags (heritable state)
    tags = [s["tag"] for s in spots]
    assert 0 in tags and 1 in tags                          # BOTH lineages survive = real inheritance


def test_lawscan_climbs_deeper_with_different_law():
    """The headline: GL caps at L2, flow reaches L3, self-replication reaches L7 -- a deeper Level needs
    a DIFFERENT LAW, not a different score. All from t=0, measured."""
    rows = {r["law"]: r for r in lab.lawscan(seed=0, quick=True)}
    assert rows["g001"]["reached_level"] == 2          # Ginzburg-Landau: winding defects (L2) is the cap in 2D
    assert rows["g002"]["reached_level"] == 3          # Boussinesq: rest+noise -> coherent circulation (L3)
    assert rows["g002"]["measured_by"]["ke_start"] == 0.0 and rows["g002"]["measured_by"]["ke_final"] > 1.0
    assert rows["gray_scott"]["reached_level"] == 7    # Gray-Scott: noise seeds -> self-replication (L7)
    assert rows["gray_scott"]["measured_by"]["final_spots"] >= 2 * rows["gray_scott"]["measured_by"]["seed_spots"]
    assert "NOT life" in rows["gray_scott"]["floor"]   # 同じ数学 != 同じもの


def test_lawscan_ic_is_not_the_target_8th_audit():
    """第8監査: the flow starts at REST (KE=0) and the RD starts with only the seed spots -- the climbed
    structure (rolls / replicated spots) is NEVER in the initial condition."""
    rows = {r["law"]: r for r in lab.lawscan(seed=1, quick=True)}
    assert rows["g002"]["measured_by"]["ke_start"] == 0.0                       # starts at rest, no rolls
    assert rows["gray_scott"]["measured_by"]["seed_spots"] <= 12                # only seeds, not the pattern
    assert (rows["gray_scott"]["measured_by"]["final_spots"]
            > rows["gray_scott"]["measured_by"]["seed_spots"])                  # spots EMERGED by division
