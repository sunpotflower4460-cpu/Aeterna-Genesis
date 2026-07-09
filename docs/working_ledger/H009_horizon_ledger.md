# H009–H010 — 地平線の台帳（受信としてのループ・DS 面積則）

- **状態**: **resolved (promoted)**（`experiments/e022_horizon_ledger/` 実装済み・全 GREEN。3D 係数は FLOOR）
- **起票者**: Claude / 2026-07-09（指示書 §3 より）
- **狙う Type**: B（床つき measured）。**2D は SOLID、3D DS 係数は FLOOR**。
- **依拠する既知事実**: Dou-Sorkin 因果集合分子、Benincasa-Dowker 作用、地平線エントロピー∝面積。

## 仮説（H009–H010）
- **H009**: ループのスペクトル/電流が隠れフラックスで決まる＝**受信**（ループ数のみ通過）。
- **H010**: DS 分子 T(β)=Li₂(1)−Li₂(1/(1+β))→π²/6（密度不変）、切り口 Σ∩H に局在、**2+1 面積則**。
  二計器：BD 作用が曲率符号を読む（要スミアリング）、台帳は一様曲率に剛（地平線プロファイル汎関数、7/7）。

## repo 実装（予定）
`experiments/e022_horizon_ledger/`（Stage1 DS 分子＋Stage2 台帳）。`core/causet.py`（ds_molecules）を使用。
**罠**: numpy 2.x は trapz→trapezoid、箱周回 CCW、π²/6 は β→∞。

## 床（必須）
- **3D DS 係数は DS d>2 病理で FLOOR（frontier、GREEN ゲートに入れない）**。Barton = frontier。
- 2D 面積則・T(β)→π²/6 のみ SOLID。

## 結果（GREEN・物理量ゲートのみ、`experiments/e022_horizon_ledger/`）
**Stage1 ab_gap**（AB 受信）：ギャップは一つの量子化数のみ渡す＝ゲージ不変（dE≈9e-16）・周期性 mod 1・局所平坦。
ゲート：`gauge_invariant` / `periodic_mod_one_quantum` / `locally_flat`。
**Stage2 ledger**（DS 分子）：⟨n⟩ が β とともに π²/6 プラトーへ近づき T(β) を追従／密度不変（spread<0.15、1200 seed）／
台帳は地平線プロファイル w(u,0) のみ読む（spot==ridge）。ゲート：`ds_rises_to_pi2_plateau` /
`ds_density_independent` / `ledger_reads_horizon_profile`。
**床**：2D は SOLID、**3D（2+1）DS 係数は DS d>2 IR 病理で FLOOR（GREEN に入れない）**。DS 数は Monte-Carlo で
高分散（多 seed で収束）。ゲート名は物理量（spectrum/count）。「エントロピー/受信/地平線」は analogy。

## verdict
- [x] **promoted**（e022 実装・全 GREEN、`claim_ledger` e022 §）。3D 係数は frontier。
