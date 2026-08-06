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
