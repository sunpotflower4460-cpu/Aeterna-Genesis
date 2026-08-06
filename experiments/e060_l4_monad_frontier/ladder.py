#!/usr/bin/env python3
"""e060 段階ゲート — Level 4 を主張する前に下位 Level を測って記録する。

`docs/EVIDENCE_CONTRACT_V2.md` §2.1:

  「`reached_level` は、連続した下位 gate を全て満たした範囲の保守的要約とする。
    能力が高次軸で true でも、**途中 gate が未通過なら reached_level を飛び越えさせない**」

本モジュールはこの規定を e060 に適用する。L4判定器を直接呼ぶだけでは下位ゲートの
確認を飛ばすことになるため、L1・L2 を独立に測ってから保守的に要約する。

## 各Levelの扱い

**Level 1（差・不安定性・模様）** — `measures.assess_level` と同一の閾値を使う：
`mean_amplitude` の成長率 > 5.0 かつ 構造因子ピークの卓越度 > 1.5。
一様＋ノイズから出発するので、これは「差が生まれたか」の直接の測定である。

**Level 2（局在構造・欠陥）** — ここに正直な限定がある。
`docs/EMERGENCE_LEVELS.md` の L2 判定は
`localized_components > 0 AND winding_defects_detected AND persistence > τ_min`
であり、「密度欠損**と**位相巻きの同時検出（片方だけは弱い）」と明記されている。

しかし本実験の主軸白（swift_hohenberg: 実スカラー u、mass_conserved: 実場 a,b）には
**位相が存在しない**。位相巻き欠陥は複素場に固有の自由度であり、実場では定義できない。
`measures.winding_defect_count` は `np.angle` を使うため、これらの白には適用不能である。

したがって本実験は L2 を **partial（局在と持続のみ・位相巻きは not_applicable）** として
記録する。これは測定の限界であって、白の否定でも、通過の底上げでもない。

**Level 3（自発運動）** — **独立軸であり、L4 の前提条件ではない。**
`docs/EMERGENCE_LEVELS.md` 冒頭：「Level は一本道ではない（個体性と自発運動は独立軸など）」。
`higher_levels.assess_individuality_level` docstring：「Self-MOTION (L3 in a body) is a
SEPARATE axis: an individual may be persistent yet STATIC.」
実際リポジトリは swift_hohenberg を **L4-static（重心ドリフト 0.0）** として記録しており、
L3 を通過しない L4 が既に存在する。よって L3 未通過は L4 主張の障害にならないが、
**飛ばしたことを黙らせない**ため centroid_drift を常に測って記録する。
"""
from __future__ import annotations

import numpy as np

from genesis.diagnostics import measures

# measures.assess_level と同一の閾値（独自に緩めない）
L1_AMP_GROWTH = 5.0
L1_SK_PROMINENCE = 1.5


def measure_l1(field_t0, field_late):
    """Level 1：一様＋ノイズから差が生まれたか。measures と同じ量・同じ閾値で測る。"""
    amp0 = measures.mean_amplitude(field_t0)
    amp1 = measures.mean_amplitude(field_late)
    growth = float(amp1 / amp0) if amp0 > 0 else 0.0
    peak_k, prom = measures.structure_factor_peak(field_late)
    passed = bool(growth > L1_AMP_GROWTH and prom > L1_SK_PROMINENCE)
    return {
        "level1_passed": passed,
        "mean_amplitude_t0": float(amp0),
        "mean_amplitude_late": float(amp1),
        "mean_amplitude_growth": growth,
        "structure_factor_peak_k": float(peak_k),
        "structure_factor_prominence": float(prom),
    }


def measure_l2(ncomp, area_fraction, persistence_change, complex_field=False, defects=None):
    """Level 2：局在と持続。実場では位相巻きが定義できないので partial として記録する。"""
    localized = bool(int(ncomp) > 0 and 0.0 < float(area_fraction) < 1.0)
    persistent = bool(float(persistence_change) < 1e-2)
    if complex_field:
        winding = "detected" if (defects or 0) > 0 else "absent"
        passed = bool(localized and persistent and (defects or 0) > 0)
        partial = False
    else:
        winding = "not_applicable_real_field"
        passed = bool(localized and persistent)      # 位相巻きは測れない
        partial = True
    return {
        "level2_passed": passed,
        "level2_partial": partial,
        "level2_localized": localized,
        "level2_persistent": persistent,
        "level2_winding_defects": winding,
        "level2_note": ("実スカラー場には位相がないため位相巻き欠陥を測定できない。"
                        "局在＋持続のみで判定した partial 記録である。"
                        if partial else ""),
    }


def conservative_reached_level(l1, l2, individual_level4, centroid_drift):
    """下位ゲートを飛び越えさせない保守的要約（EVIDENCE_CONTRACT_V2 §2.1）。

    L3（自発運動）は独立軸なので L4 の前提にしない。ただし測って記録する。
    """
    if not l1["level1_passed"]:
        return 0, "level1_not_passed"
    if not l2["level2_passed"]:
        return 1, "level1_only_no_persistent_localization"
    if not individual_level4:
        return 2, "level2_localized_persistent_but_not_an_individual"
    moving = float(centroid_drift) > 0.5
    return 4, ("level4_with_self_motion" if moving
               else "level4_static_motion_is_a_separate_axis_not_a_skipped_gate")


def summarize(field_t0, field_late, ncomp, area_fraction, persistence_change,
              individual_level4, centroid_drift, complex_field=False, defects=None):
    """L1/L2 を測り、保守的な reached_level と根拠をまとめて返す。"""
    l1 = measure_l1(field_t0, field_late)
    l2 = measure_l2(ncomp, area_fraction, persistence_change,
                    complex_field=complex_field, defects=defects)
    level, reason = conservative_reached_level(l1, l2, individual_level4, centroid_drift)
    out = {"ladder_reached_level": int(level), "ladder_reason": reason,
           "level3_axis": "independent_of_level4",
           "level3_centroid_drift": float(centroid_drift)}
    out.update(l1)
    out.update(l2)
    return out
