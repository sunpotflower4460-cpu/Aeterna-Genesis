"""Multiple law classes climb from t=0 to deeper Levels than GL: flow (L3) and self-replication (L7).

Discipline checked: every IC is generic (rest+noise / noise seeds), NEVER the target (第8監査); the
reached Level is MEASURED; the existing scalar measures.assess_level is untouched (no_touch).
"""

import numpy as np

from ai_lab import lab
from genesis.models import gray_scott as gs
from genesis.models import complex_ginzburg_landau as cgl
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


def test_gray_scott_ceiling_is_L7partial_heredity_is_placed():
    """ANTI_DRIFT: the HONEST emergent ceiling of the Gray-Scott U,V white is L7-partial (division only).
    Heredity does NOT emerge from U,V; a tag field is PLACED, so no full-L7 EMERGENCE is claimed."""
    # division from the U,V white (no tag) -> L7-partial (emergent), NEVER a full-L7 claim
    lp, det, mb = hl.assess_replication_level([8, 12, 18, 20])
    assert lp == 0 and det["division_not_seeded"] and det["l7_partial"]
    assert det["full_l7_emergence"] is False and det["inheritance_placed"] is False
    assert "L7-partial" in mb["emergent_ceiling"]
    # a PLACED tag field is measured but flagged inheritance_placed=True -- still NOT full-L7 emergence
    spots = [{"tag": t, "purity": 0.95, "size": 30} for t in ([0] * 10 + [1] * 10)]
    lpl, detpl, mbpl = hl.assess_replication_level([8, 12, 18, 20], spots=spots)
    assert lpl == 0                                        # heredity was PLACED, not born -> no full L7
    assert detpl["inheritance_placed"] is True and detpl["full_l7_emergence"] is False
    assert "PLACED" in mbpl["note"]
    # no division -> below L7
    l0, det0, _ = hl.assess_replication_level([8, 8, 7, 8])
    assert l0 == 0 and not det0["division_not_seeded"]


def test_placed_tag_is_carried_but_labeled_placed_not_emergent():
    """The tag field (U,V->U,V,T) is a PLACED heritable degree of freedom. We may still measure that the
    placed tag is carried cleanly through division, but it is labeled placed -- never sold as emergence."""
    p = dict(gs.DEFAULTS)
    rng = np.random.default_rng(1)
    U, V, T, founder_tags = gs.make_initial_tagged((96, 96), 8, rng, seed_radius=p["seed_radius"], mix=0.5)
    assert set(int(t) for t in founder_tags) <= {0, 1}
    for i in range(12000):
        U, V, T = gs.step_tagged(U, V, T, p)
    spots = gs.spot_tags(V, T)
    assert len(spots) >= 2 * 8                              # divided (self-replication EMERGES from U,V)
    _, det, mb = hl.assess_replication_level([8] + [len(spots)], spots=spots)
    assert det["inheritance_placed"] is True               # the tag was PLACED, not born
    assert det["full_l7_emergence"] is False               # so NO full-L7 emergence is claimed
    assert "PLACED" in mb["note"]


def test_lawscan_gray_scott_is_L7partial_not_full_l7():
    """GL caps at L2, flow reaches L3, and Gray-Scott's HONEST ceiling is L7-partial (division only) --
    a full L7 would require PLACING heredity (docs/ANTI_DRIFT.md). Deeper Level needs a different LAW."""
    rows = {r["law"]: r for r in lab.lawscan(seed=0, quick=True)}
    assert rows["g001"]["reached_level"] == 2          # Ginzburg-Landau: winding defects (L2) cap in 2D
    assert rows["g002"]["reached_level"] == 3          # Boussinesq: rest+noise -> coherent circulation (L3)
    assert rows["g002"]["measured_by"]["ke_start"] == 0.0 and rows["g002"]["measured_by"]["ke_final"] > 1.0
    gs_row = rows["gray_scott"]
    assert gs_row["reached_level"] == 0                 # NOT full L7 (retracted); division only
    assert "L7-partial" in gs_row["l7_status"] and "PLACED" in gs_row["l7_status"]
    assert gs_row["detected"]["l7_partial"] and gs_row["detected"]["full_l7_emergence"] is False
    assert gs_row["measured_by"]["final_spots"] >= 2 * gs_row["measured_by"]["seed_spots"]  # division real


def test_cgl_is_a_distinct_white_no_velocity_field_seeded():
    """CGL is a SINGLE complex oscillatory field: IC = uniform + tiny complex noise (no spiral/defect
    seeded). Deterministic per seed, amplitude-preserving (|A|~1 is set by the IC, not grown from a floor)."""
    rng = np.random.default_rng(0)
    A = cgl.make_initial((32, 32), 1e-2, rng)
    assert A.dtype == np.complex128
    assert abs(float(np.abs(A).mean()) - 1.0) < 0.05        # |A|~1 from the IC (NOT growth-from-floor)
    p = dict(cgl.DEFAULTS)
    k2 = cgl._k2(A.shape)
    A1 = cgl.step(A.copy(), p, k2)
    A2 = cgl.step(cgl.make_initial((32, 32), 1e-2, np.random.default_rng(0)), p, k2)
    assert np.allclose(A1, A2)                              # deterministic for a fixed seed
    for _ in range(200):
        A1 = cgl.step(A1, p, k2)
    assert np.all(np.isfinite(A1))                          # spectral integrating-factor stays finite


def test_lawscan_cgl_ceiling_is_turbulence_below_L4():
    """The CGL white climbs to L1 patterns + L2 moving cores, but the motion is TURBULENT (not coherent)
    and makes no persistent individual -> honest ceiling BELOW L4 (turbulent != coherent). reached_level
    is None (not a clean integer Level), amplitude does NOT grow from a floor, and we record the
    measurement floor that winding_defect_count undercounts CGL cores."""
    rows = {r["law"]: r for r in lab.lawscan(seed=0, quick=True)}
    cg = rows["cgl"]
    assert cg["reached_level"] is None                      # not a clean L; it is turbulence, honestly
    assert cg["kind"] == "complex_oscillatory" and cg["tier"] == "measured"
    assert cg["detected"]["turbulent_motion"] is True       # cores MOVE (amp autocorrelation decays)
    assert cg["detected"]["coherent"] is False              # but turbulent, NOT coherent
    assert cg["detected"]["persistent_individuals"] is False
    assert cg["measured_by"]["growth_from_floor"] is False  # |A|~1 is the IC, not born from L0
    assert cg["measured_by"]["amp_autocorr_tail"] < 0.6     # genuine decorrelation = turbulent motion
    assert "UNDERCOUNTS" in cg["floor"]                     # honest measurement floor recorded


def test_lawscan_ic_is_not_the_target_8th_audit():
    """第8監査: the flow starts at REST (KE=0) and the RD starts with only the seed spots -- the climbed
    structure (rolls / replicated spots) is NEVER in the initial condition."""
    rows = {r["law"]: r for r in lab.lawscan(seed=1, quick=True)}
    assert rows["g002"]["measured_by"]["ke_start"] == 0.0                       # starts at rest, no rolls
    assert rows["gray_scott"]["measured_by"]["seed_spots"] <= 12                # only seeds, not the pattern
    assert (rows["gray_scott"]["measured_by"]["final_spots"]
            > rows["gray_scott"]["measured_by"]["seed_spots"])                  # spots EMERGED by division
