# H005–H008 — 順序から時空へ（因果作用が多様体を選ぶ）

- **状態**: proposed（サンドボックス検証済み・**repo 実装予定** `experiments/e023_causal_action/`）
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

## verdict
- [ ] proposed → e023 実装で promoted/dead-end を判定。
