# H005–H008 — 順序から時空へ（因果作用が多様体を選ぶ）

- **状態**: **resolved (部分 promoted)**（`experiments/e023_causal_action/` の順序→時空は GREEN。曲率治癒/経路積分は frontier）
- **起票者**: Claude / 2026-07-09（指示書 §3 より）
- **狙う Type**: B（床つき measured）＋ established の統合。e014（因果次元）に隣接。
- **依拠する既知事実**: 因果集合（causal set）＝局所有限な半順序。Benincasa-Dowker 作用、CDT/因果集合プログラム。

## 仮説（H005–H008）
- **H005/H006**: 純粋な順序（関係のみ）から**時間**が創発（rank=最長鎖）するが、**空間は非多様体**（次元発散）。
- **H007**: 曲率治癒がアトラクター＝BD 作用降下（|mean Ricci| 0.06 ≪ 0.95 ≪ 4.19、普遍性・恒常性）。
- **H008**: 実重み経路積分は多様体を選べない（内点・要スミアリング）＝作用の役割の床。

## repo 実装（予定）
`experiments/e023_causal_action/`（3 Stage）。`core/causet.py`（**本セッションで実装済み**：
sprinkle / causal_relation / transitive_percolation[bitmask] / rank / interval_dimension[Myrheim-Meyer] /
bd_action_2d）を使用。**罠**：推移閉包は bitmask、sprinkle は Poisson。
GREEN ゲートは物理量のみ（dimension / action / |mean Ricci|）。

## 床
- 2D は Gauss-Bonnet で作用が位相的＝曲率選択は要スミアリング（床）。z_earlier_uncertain/ の中間物には依拠せず、
  指示書 H005–H008 仕様＋core/causet から実装する。

## 結果（GREEN・物理量ゲートのみ、`experiments/e023_causal_action/`）
**Stage1 order_time**：純粋な因果順序から時間が創発＝rank が隠れ時刻を回復（Spearman 0.99）／中間 rank の反鎖が
空間を充填／interval 次元が有限（≈2）。ゲート：`rank_recovers_hidden_time` / `spatial_slice_fills_space` /
`interval_dimension_finite`。
**Stage2 directed_vs_undirected**：**向きが時空を作る**＝有向は有限次元＋時間、同じ対を対称化すると
スモールワールド mush（~全 N に 2 hop 到達＝次元発散）＋サイクル（非巡回順序が壊れ時間なし）。ゲート：
`directed_dimension_finite` / `undirected_collapses_smallworld` / `undirected_has_cycles`。
core/causet（e014 で検証済み）を使用。ゲート名は物理量/組合せ量。「時間/時空」は analogy。

**frontier（GREEN にしない・正直に保留）**: 曲率治癒＝BD 作用降下（H007）／実重み経路積分は多様体を選べない（H008）
——サンドボックス参照（z_earlier_uncertain）が本セッションで未検証のため、検証済み数値がなく昇格しない。

## verdict
- [x] **部分 promoted**（順序→時空 e023 GREEN、`claim_ledger` e023 §）。曲率治癒/経路積分は frontier（次段）。
