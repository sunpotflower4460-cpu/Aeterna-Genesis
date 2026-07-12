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


def test_replication_level_measure_l7_and_flat_l0():
    l7, det, _ = hl.assess_replication_level([8, 12, 18, 20])
    assert l7 == 7 and det["self_replication"]
    l0, _, _ = hl.assess_replication_level([8, 8, 7, 8])   # no multiplication -> not L7
    assert l0 == 0


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
