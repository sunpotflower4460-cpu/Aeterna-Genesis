#!/usr/bin/env python3
"""e060 二段クエンチ — 空間的に一様・時間的にプログラムされた法則パラメータの変更。

Phase 1 パイロットで判明した構造：swift_hohenberg は r<=0 で全滅 DIES（u=0 が線形
安定なのでゼロ平均ノイズが減衰）、r>0 で FILLS_DOMAIN（一様状態が不安定なので模様が
全域で一斉に育つ）。**間に窓がない。** これは探索不足ではなく亜臨界性という法則構造で
あり、Sobol点数を増やしても解消しない。

そこで、単一の固定パラメータではなく**二段クエンチ**を使う：

    段1: 一様状態が不安定な側で保持   -> ゼロ平均ノイズから模様が核生成する
    段2: 局在状態が安定な側へ落とす   -> 粗大化が進み「1つ」に収束するかを見る

## これは「答えを置く」ことにならないか

ならない。判断の根拠：

1. **空間的に一様**である。全格子点に同一のパラメータが同時に適用される。位置・形・
   大きさ・向き・個数の情報を一切含まない。どこに何個残るかは力学が決める。
2. **既存の白が同じ形の操作を持つ**。genesis/models/ginzburg_landau.py は
   `quench_start` / `quench_duration` で eps を時間的に掃引しており、リポジトリは
   これを正当な始原条件（プロトコル）として扱っている。
3. `docs/ANTI_DRIFT.md` 精密化③の区別に照らすと、これは「動ける素地（法則の選択）を
   与える」側であって「動く構造（解）を置く」側ではない。

ただし**正直な格下げが必要**：これは自律的（autonomous）な発展ではなく、
genesis.schema.json の語彙で言う `time_programmed_environment` である。
結果を報告するときは必ずこの区別を明示し、一段クエンチの結果と混ぜない。

## モナド前提との関係

M1（無分割）・M3（内的原理）は破らない——場も項も足しておらず、局在も置いていない。
M2（窓なし）については、二段クエンチは**環境条件の時間変化**であって系への局所介入では
ないが、外部からプログラムされている点で完全な自律ではない。この限定を
`unresolved_audit` に記録する。
"""
from __future__ import annotations


def stages(p, quench, total_steps):
    """一様二段クエンチを (パラメータ, ステップ数) の列に展開する。

    quench = {"param": "r", "value_1": 0.2, "value_2": -0.4, "switch_frac": 0.4}
    quench が None なら一段（従来どおり）。

    返り値の各段は空間的に一様なパラメータ辞書であり、格子位置に依存する情報を持たない。
    """
    if not quench:
        return [(dict(p), int(total_steps))]

    key = quench["param"]
    frac = float(quench.get("switch_frac", 0.5))
    frac = min(max(frac, 0.05), 0.95)
    n1 = int(round(total_steps * frac))
    n2 = int(total_steps) - n1

    p1 = dict(p)
    p1[key] = float(quench["value_1"])
    p2 = dict(p)
    p2[key] = float(quench["value_2"])
    return [(p1, n1), (p2, n2)]


def final_params(p, quench):
    """段2（最終状態）のパラメータ。hold / heal / size はこの法則の下で測る。"""
    if not quench:
        return dict(p)
    p2 = dict(p)
    p2[quench["param"]] = float(quench["value_2"])
    return p2


# 白ごとにクエンチしてよいパラメータ。
#   mass_conserved: 反応レート k0 を掃引する。a+b の保存は f の符号反転構造で保たれるため、
#                   レートを時間変化させても総量は厳密に保存される（テストで固定）。
#                   b0（保存される平均組成）は質量そのものなのでクエンチしない。
#   swift_hohenberg: 線形係数 r。dx はクエンチしない（k2 の再構築が必要になるため）。
QUENCHABLE = {
    "mass_conserved": ("k0",),
    "swift_hohenberg": ("r",),
}
