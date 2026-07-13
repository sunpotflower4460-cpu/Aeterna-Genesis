"""Multiple law classes climb from t=0 to deeper Levels than GL: flow (L3) and self-replication (L7).

Discipline checked: every IC is generic (rest+noise / noise seeds), NEVER the target (第8監査); the
reached Level is MEASURED; the existing scalar measures.assess_level is untouched (no_touch).
"""

import numpy as np

from ai_lab import lab
from genesis.models import gray_scott as gs
from genesis.models import complex_ginzburg_landau as cgl
from genesis.models import swift_hohenberg as sh
from genesis.models import three_component_rd as tcr
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


def _sh_settle(N, steps, seed=0):
    p = dict(sh.DEFAULTS)
    rng = np.random.default_rng(seed)
    u = sh.make_initial((N, N), 1e-3, rng, p)
    k2 = sh._k2(N, p["dx"])
    for _ in range(steps):
        u = sh.step(u, p, k2)
    return u, k2, p


def test_swift_hohenberg_is_a_persistent_self_healing_individual():
    """A NEW white (Swift-Hohenberg localized state) reaches the map's missing rung: a persistent LOCALIZED
    individual that SELF-HEALS after perturbation (the L4 discriminator) -- from a generic symmetric seed,
    NOT a placed boundary. Being variational it does NOT self-move (static individual)."""
    N = 64
    u, k2, p = _sh_settle(N, 2500)
    s0 = sh.individual_stats(u)
    assert s0["area"] > 0 and s0["peaks"] == 1                 # one bounded localized individual formed
    assert s0["area"] < 0.25 * N * N                            # localized (inside/outside), not global
    assert s0["amax"] > 0.5                                     # clear inside contrast vs ~0 background
    c0 = s0["centroid"]
    for _ in range(600):                                        # persistence + no self-motion (variational)
        u = sh.step(u, p, k2)
    s1 = sh.individual_stats(u)
    drift = float(np.hypot(s1["centroid"][0] - c0[0], s1["centroid"][1] - c0[1]))
    assert drift < 0.5                                          # STATIC individual (no spontaneous motion)
    # self-heal: destroy the top half; the white REGROWS the same individual (you cannot PLACE self-healing)
    up = u.copy(); up[:N // 2, :] = 0.0
    assert sh.individual_stats(up)["area"] < s1["area"]         # genuinely damaged
    for _ in range(2500):
        up = sh.step(up, p, k2)
    heal = sh.individual_stats(up)
    assert abs(heal["area"] - s1["area"]) <= 8 and abs(heal["amax"] - s1["amax"]) < 0.12  # recovered
    # size-independence: same individual on a bigger box (not a finite-size effect)
    u2, _, _ = _sh_settle(N + 32, 2500)
    assert abs(sh.individual_stats(u2)["area"] - s1["area"]) <= 10


def test_assess_individuality_level_l4_static_and_below():
    """The additive L4 measure: a persistent, localized, self-healing, size-independent, NON-moving field
    is L4 (static individual); missing self-healing OR localization drops below L4."""
    lvl, det, mb = hl.assess_individuality_level(amax=1.41, area_fraction=0.015, persistence_change=2e-8,
                                                 recovers_after_perturbation=True, size_independent=True,
                                                 centroid_drift=0.0)
    assert lvl == 4 and det["persistent_individual"] and det["static_individual"]
    assert det["self_healing"] and not det["self_moving"]
    assert "STATIC" in mb["emergent_ceiling"]
    # no self-healing -> not a genuine individual (L2-like frozen blob), below L4
    lvl2, det2, _ = hl.assess_individuality_level(1.41, 0.015, 2e-8, False, True, 0.0)
    assert lvl2 == 0 and not det2["persistent_individual"]
    # a self-moving individual would be the missing conjunction (L4 + motion)
    _, det3, mb3 = hl.assess_individuality_level(1.41, 0.015, 2e-8, True, True, 3.0)
    assert det3["self_moving"] and "self-propelled" in mb3["emergent_ceiling"]


def test_lawscan_swift_hohenberg_reaches_L4_static_individual():
    """lawscan: Swift-Hohenberg reaches L4 (persistent individuality) MEASURED, but STATIC -- individuality
    (L4) and self-motion (L3) are independent axes; a self-propelled individual is frontier."""
    rows = {r["law"]: r for r in lab.lawscan(seed=0, quick=True)}
    row = rows["swift_hohenberg"]
    assert row["reached_level"] == 4 and row["tier"] == "measured"
    assert row["detected"]["persistent_individual"] and row["detected"]["self_healing"]
    assert row["detected"]["static_individual"] and not row["detected"]["self_moving"]
    assert row["measured_by"]["centroid_drift"] == 0.0 and row["measured_by"]["size_independent"] is True
    assert "frontier" in row["floor"]                          # self-propelled individual honestly frontier


def test_assess_self_propulsion_single_vs_replication_and_artifact():
    """The self-propulsion measure: a SINGLE compact body moving with EMERGENT (random-direction) drift that
    self-heals is L4+motion; a moving REPLICATING population is the Gray-Scott trap (not self-propelled); a
    fixed-direction drift is an IC/boundary artifact (not emergent); a single static body is L4-static."""
    # single body, random direction across seeds, self-heals -> self-propelled (L4 + emergent motion)
    lvl, det, mb = hl.assess_self_propulsion([1, 1, 1, 1], [0.02] * 4, [(5, 3), (-4, 4), (1, -6)], True)
    assert lvl == 4 and det["self_propelled_individual"] and det["emergent_random_direction"]
    assert mb["direction_resultant"] < 0.6                  # directions point every which way = emergent
    # replicating population that drifts -> trap flagged, NOT a self-propelled individual
    lvl2, det2, _ = hl.assess_self_propulsion([1, 3, 5, 6], [0.05, 0.1, 0.15, 0.2], [(10, 2), (8, 5), (9, -3)], False)
    assert lvl2 == 0 and det2["replication_drift_trap"] and not det2["self_propelled_individual"]
    # fixed-direction drift from symmetric ICs = artifact (not emergent), even if single & self-healing
    lvl3, det3, mb3 = hl.assess_self_propulsion([1, 1, 1, 1], [0.02] * 4, [(6, 0), (6, 0.1), (6, -0.1)], True)
    assert lvl3 == 0 and not det3["emergent_random_direction"] and mb3["direction_resultant"] > 0.9
    # single body but no motion -> L4-static (not self-propelled)
    lvl4, det4, mb4 = hl.assess_self_propulsion([1, 1, 1, 1], [0.02] * 4, [(0.1, 0.0), (0.0, 0.1)], True)
    assert lvl4 == 0 and not det4["self_motion"] and "static" in mb4["emergent_ceiling"]


def test_three_component_rd_self_propulsion_is_frontier():
    """The 3-component RD white (dissipative-soliton attempt) is a DISTINCT white probing self-propelled
    individuality. Honest ceiling: from a symmetric seed the structure dies/fills/splits -- no clean SINGLE
    self-propelled spot at accessible resolution (原則5: attacked, motion NOT placed). Frontier, and the
    stepper stays finite (no NaN)."""
    counts, fracs, vecs = [], [], []
    for s in (1, 2):
        r = tcr.run_traj(s, N=96, steps=3000, snap=500)
        assert not r.get("unstable")                       # semi-implicit spectral stepper stays finite
        traj = [p for p in r["traj"] if p["count"] > 0 and np.isfinite(p["centroid"][0])]
        if len(traj) < 2:
            counts.append(0); fracs.append(0.0); vecs.append((0.0, 0.0)); continue
        counts.append(traj[-1]["count"]); fracs.append(traj[-1]["area_fraction"])
        a, b = traj[len(traj) // 2], traj[-1]
        vecs.append((b["centroid"][0] - a["centroid"][0], b["centroid"][1] - a["centroid"][1]))
    lvl, det, mb = hl.assess_self_propulsion(counts, fracs, vecs, recovers_after_perturbation=False)
    assert lvl == 0                                        # self-propelled single individual NOT reached
    assert not det["self_propelled_individual"]            # frontier: dies/fills/splits (not a clean single body)


def test_lawscan_ic_is_not_the_target_8th_audit():
    """第8監査: the flow starts at REST (KE=0) and the RD starts with only the seed spots -- the climbed
    structure (rolls / replicated spots) is NEVER in the initial condition."""
    rows = {r["law"]: r for r in lab.lawscan(seed=1, quick=True)}
    assert rows["g002"]["measured_by"]["ke_start"] == 0.0                       # starts at rest, no rolls
    assert rows["gray_scott"]["measured_by"]["seed_spots"] <= 12                # only seeds, not the pattern
    assert (rows["gray_scott"]["measured_by"]["final_spots"]
            > rows["gray_scott"]["measured_by"]["seed_spots"])                  # spots EMERGED by division
