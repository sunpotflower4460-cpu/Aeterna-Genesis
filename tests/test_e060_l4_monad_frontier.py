"""e060 L4 Frontier — モナド前提とゲートが崩れていないことの回帰テスト。

このテストの役割は「L4が出るか」を確かめることではなく、**出たと言ってよい条件が
後から緩んでいないこと**を固定することにある（docs/ANTI_DRIFT.md 精密化⑤）。
"""
import inspect
from pathlib import Path

import numpy as np
import pytest
import yaml

from genesis.diagnostics import higher_levels as hl
from experiments.e060_l4_monad_frontier import classify as C
from experiments.e060_l4_monad_frontier import l4_protocol as P
from experiments.e060_l4_monad_frontier import whites

AUDIT = Path(__file__).resolve().parents[1] / "experiments" / "e060_l4_monad_frontier" / "monad_audit.yaml"


# --- 単子性監査の凍結 ----------------------------------------------------------

def test_monad_audit_is_frozen_before_phase0():
    doc = yaml.safe_load(AUDIT.read_text())
    assert doc["frozen_before_phase0"] is True
    assert doc["frozen_at_commit"]


def test_primary_whites_are_monadic_and_nr_is_excluded():
    """主軸は monadic のみ。非相反w付き（合成白）は主軸から除外されていること。"""
    doc = yaml.safe_load(AUDIT.read_text())
    by_id = {w["id"]: w for w in doc["whites"]}

    for wid in ("mass_conserved", "swift_hohenberg"):
        assert by_id[wid]["monadicity"] == "monadic"
        assert by_id[wid]["m1_indivisible"] is True
        assert by_id[wid]["role"] == "primary"

    nr = by_id["mass_conserved_nr"]
    assert nr["monadicity"] == "composite"       # w は拘束を共有しない独立部品
    assert nr["m1_indivisible"] is False
    assert nr["excluded_from_primary"] is True
    assert nr["role"] == "contrast_only"


def test_perturbation_policy_keeps_the_monad_windowless():
    """主張の土台は無摂動control（介入0）であること。"""
    doc = yaml.safe_load(AUDIT.read_text())
    pol = doc["perturbation_policy"]
    assert pol["claim_base"] == "unperturbed_control"
    assert pol["control_runtime_interventions"] == 0


# --- M3: 初期条件に局在を置いていない ------------------------------------------

def test_zero_mean_noise_is_exactly_zero_mean():
    rng = np.random.default_rng(0)
    n = whites.zero_mean_noise((64, 64), rng)
    assert abs(float(n.mean())) < 1e-12


def test_uniform_ic_places_no_localized_structure():
    """一様IC は『平均＋ゼロ平均ノイズ』のみ。空間構造（bump）を含まない。"""
    rng = np.random.default_rng(0)
    u = whites.uniform_plus_noise((64, 64), 0.0, 1e-3, rng)
    assert abs(float(u.mean())) < 1e-12
    # 中心が周辺より高い＝bumpがある、という構造がないこと
    c = float(np.abs(u[24:40, 24:40]).mean())
    edge = float(np.abs(np.concatenate([u[:8].ravel(), u[-8:].ravel()])).mean())
    assert c == pytest.approx(edge, rel=0.5)
    # ノイズ振幅を超える構造がない
    assert float(np.abs(u).max()) < 1e-2


def test_bump_ic_is_visibly_different_from_uniform_ic():
    """陽性対照（bump入り）と主軸（bumpなし）が本当に別物であること。"""
    p = dict(whites.WHITES["swift_hohenberg"]["defaults"])
    flat = whites.sh_initial_uniform((64, 64), p, 1e-3, np.random.default_rng(0))
    bump = whites.sh_initial_bump((64, 64), p, 1e-3, np.random.default_rng(0))
    assert float(np.abs(bump).max()) > 100 * float(np.abs(flat).max())


def test_mass_conserved_uniform_ic_conserves_total_and_has_no_bump():
    p = dict(whites.WHITES["mass_conserved"]["defaults"])
    a, b = whites.mc_initial_uniform((64, 64), p, 1e-3, np.random.default_rng(0))
    total = float((a + b).sum())
    assert total == pytest.approx(p["b0"] * 64 * 64, rel=1e-9)
    assert float(a.max()) < 1e-2          # 局在核を置いていない


# --- 判定器を改変していない ----------------------------------------------------

def test_l4_judgment_is_delegated_to_untouched_assessor():
    """e060 は自前のL4合格判定を持たず、既存判定器へ委ねていること。"""
    src = inspect.getsource(P._judge)
    assert "hl.assess_individuality_level" in src


def test_existing_l4_thresholds_are_unchanged():
    """higher_levels の L4 閾値が動いていないことを、判定器の挙動で固定する。"""
    # 既知の陽性（SH bump 相当の測定値）
    lvl, _, _ = hl.assess_individuality_level(
        amax=1.41, area_fraction=0.015, persistence_change=2e-8,
        recovers_after_perturbation=True, size_independent=True, centroid_drift=0.0)
    assert lvl == 4
    # 自己修復しなければ L4 ではない（L2 の凍結欠陥との決定的判別子）
    lvl_no_heal, _, _ = hl.assess_individuality_level(
        1.41, 0.015, 2e-8, False, True, 0.0)
    assert lvl_no_heal == 0
    # 全域を埋めたら個体ではない
    lvl_fill, _, _ = hl.assess_individuality_level(
        1.41, 1.0, 2e-8, True, True, 0.0)
    assert lvl_fill == 0


def test_pure_l4_requires_unseeded_localization_and_single_component():
    """seeded な局在は pure_l4 にならない（モナドM3）。"""
    s_single = {"area_fraction": 0.015, "amax": 1.41, "ncomp": 1}
    seeded = P._judge(s_single, 2e-8, True, True, 0.0, seeded_localization=True)
    assert seeded["reached_level"] == 4 and seeded["pure_l4"] is False

    grown = P._judge(s_single, 2e-8, True, True, 0.0, seeded_localization=False)
    assert grown["reached_level"] == 4 and grown["pure_l4"] is True

    s_multi = {"area_fraction": 0.015, "amax": 1.41, "ncomp": 5}
    frag = P._judge(s_multi, 2e-8, True, True, 0.0, seeded_localization=False)
    assert frag["pure_l4"] is False          # 連結成分が1個でなければ「一つのもの」ではない


# --- 分類器の凍結閾値 ----------------------------------------------------------

def test_classifier_thresholds_match_the_existing_assessor():
    """独自の甘いゲートを作っていないこと（判定器と同じ値を使う）。"""
    assert C.THRESHOLDS["area_max"] == 0.25       # higher_levels の localized 条件
    assert C.THRESHOLDS["amax_floor"] == 0.5      # 同 contrast 条件
    assert C.THRESHOLDS["steady_change"] == 1e-2  # 同 persistent 条件


@pytest.mark.parametrize("s_hold, change, expected", [
    ({"area_fraction": 0.0, "amax": 0.0, "ncomp": 0}, 1e-9, "DIES"),
    ({"area_fraction": 1.0, "amax": 1.2, "ncomp": 1}, 1e-9, "FILLS_DOMAIN"),
    ({"area_fraction": 0.10, "amax": 1.2, "ncomp": 7}, 1e-9, "FRAGMENTS"),
    ({"area_fraction": 0.10, "amax": 1.2, "ncomp": 1}, 5e-1, "OSCILLATORY_CHAOS"),
    ({"area_fraction": 0.015, "amax": 1.4, "ncomp": 1}, 1e-9, "PERSISTENT_SINGLE_CANDIDATE"),
])
def test_classify_labels(s_hold, change, expected):
    s_settle = {"area_fraction": 0.015, "amax": 1.4, "ncomp": 1}
    assert C.classify("ok", s_settle, s_hold, change) == expected


def test_classify_transient_single_when_settle_was_not_single():
    s_settle = {"area_fraction": 0.10, "amax": 1.2, "ncomp": 4}
    s_hold = {"area_fraction": 0.015, "amax": 1.4, "ncomp": 1}
    assert C.classify("ok", s_settle, s_hold, 1e-9) == "TRANSIENT_SINGLE"


def test_numerical_failure_short_circuits():
    z = {"area_fraction": 0.0, "amax": 0.0, "ncomp": 0}
    assert C.classify("numerical_failure", z, z, 0.0) == "NUMERICAL_FAILURE"


# --- Phase 0 対照の期待値（実際に物理を回す・やや重い） ------------------------

def test_phase0_positive_control_sh_with_bump_is_a_single_persistent_individual():
    """通すべきものが通ること。既知の陽性対照（SH + bump）。"""
    r = C.screen_swift_hohenberg({}, seed=0, N=64, seeded_localization=True)
    assert r["label"] == C.PASS_LABEL
    assert r["ncomp"] == 1
    assert 0.0 < r["area_fraction"] < 0.25


def test_phase0_mass_conserved_conserves_mass_exactly():
    """G0：質量保存白は保存量を厳密に保つこと（保存が壊れたら結論は無効）。"""
    r = C.screen_mass_conserved({}, seed=0, N=48, settle=800, hold=200)
    assert r["status"] == "ok"
    assert r["mass_drift"] < 1e-9


# --- 下位ゲート（EVIDENCE_CONTRACT_V2 §2.1「途中gateを飛び越えさせない」） ------

def test_ladder_uses_the_same_l1_thresholds_as_measures():
    from experiments.e060_l4_monad_frontier import ladder
    assert ladder.L1_AMP_GROWTH == 5.0
    assert ladder.L1_SK_PROMINENCE == 1.5


def test_reached_level_never_skips_a_lower_gate():
    """L1未通過なら、たとえ個体判定がTrueでもLevel 4を主張しない。"""
    from experiments.e060_l4_monad_frontier import ladder
    l1_fail = {"level1_passed": False}
    l2_ok = {"level2_passed": True}
    lvl, reason = ladder.conservative_reached_level(l1_fail, l2_ok,
                                                    individual_level4=True, centroid_drift=0.0)
    assert lvl == 0 and reason == "level1_not_passed"

    l1_ok = {"level1_passed": True}
    l2_fail = {"level2_passed": False}
    lvl2, _ = ladder.conservative_reached_level(l1_ok, l2_fail,
                                                individual_level4=True, centroid_drift=0.0)
    assert lvl2 == 1                      # 局在・持続が未確認なら L4 を主張しない


def test_level4_static_is_allowed_because_motion_is_a_separate_axis():
    """L3（自発運動）は独立軸。静止した個体でも L4 は成立する（SH の L4-static）。"""
    from experiments.e060_l4_monad_frontier import ladder
    lvl, reason = ladder.conservative_reached_level(
        {"level1_passed": True}, {"level2_passed": True},
        individual_level4=True, centroid_drift=0.0)
    assert lvl == 4
    assert "separate_axis" in reason      # 飛ばしたのではなく別軸であることを明示


def test_level2_is_recorded_as_partial_for_real_scalar_whites():
    """実場には位相がないので位相巻き欠陥は測れない。partial として正直に記録する。"""
    from experiments.e060_l4_monad_frontier import ladder
    l2 = ladder.measure_l2(ncomp=1, area_fraction=0.02, persistence_change=1e-8,
                           complex_field=False)
    assert l2["level2_passed"] is True
    assert l2["level2_partial"] is True
    assert l2["level2_winding_defects"] == "not_applicable_real_field"
    # 複素場なら位相巻きを要求する（緩めない）
    l2c = ladder.measure_l2(1, 0.02, 1e-8, complex_field=True, defects=0)
    assert l2c["level2_passed"] is False and l2c["level2_partial"] is False


def test_l1_growth_is_measured_from_t0(monkeypatch):
    """L1は t=0 の場と後期の場の比で測る（一様＋ノイズから差が育ったか）。"""
    import numpy as np
    from experiments.e060_l4_monad_frontier import ladder
    rng = np.random.default_rng(0)
    t0 = 1e-3 * rng.standard_normal((64, 64))
    late = np.zeros((64, 64)); late[28:36, 28:36] = 1.4      # 局在構造が育った
    l1 = ladder.measure_l1(t0, late)
    assert l1["mean_amplitude_growth"] > 5.0
    assert l1["level1_passed"] is True


# --- 二段クエンチ軸の配線（Phase1本番） -----------------------------------------

def test_phase1_sample_includes_quench_axes_by_default():
    from experiments.e060_l4_monad_frontier import phase1 as P1
    conds = P1.sample("mass_conserved", 4, sobol_seed=0)
    for c in conds:
        assert "__quench_value1" in c and "__quench_switch_frac" in c


def test_phase1_build_quench_reuses_the_base_axis_as_final_value():
    """段2（保持）の値は通常軸と二重定義しない。"""
    from experiments.e060_l4_monad_frontier import phase1 as P1
    from experiments.e060_l4_monad_frontier import quench as Q
    cond = {"k0": 0.05, "__quench_value1": 0.3, "__quench_switch_frac": 0.2}
    q = P1._build_quench("mass_conserved", cond)
    assert q["param"] == Q.QUENCHABLE["mass_conserved"][0] == "k0"
    assert q["value_2"] == cond["k0"]
    assert q["value_1"] == cond["__quench_value1"]


def test_phase1_no_quench_mode_has_no_quench_dict():
    from experiments.e060_l4_monad_frontier import phase1 as P1
    conds = P1.sample("swift_hohenberg", 4, sobol_seed=0, with_quench=False)
    for c in conds:
        assert "__quench_value1" not in c
        assert P1._build_quench("swift_hohenberg", c) is None


def test_quench_stages_conserve_mass_exactly():
    """二段クエンチ下でも a+b の保存が厳密であること（G0）。"""
    from experiments.e060_l4_monad_frontier import classify as C
    r = C.screen_mass_conserved(
        {"b0": 3.0}, seed=0, N=48, settle=600, hold=200,
        quench={"param": "k0", "value_1": 0.15, "value_2": 0.02, "switch_frac": 0.4})
    assert r["status"] == "ok"
    assert r["mass_drift"] < 1e-9
