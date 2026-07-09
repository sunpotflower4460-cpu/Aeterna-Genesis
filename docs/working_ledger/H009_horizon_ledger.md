# H009–H010 — 地平線の台帳（受信としてのループ・DS 面積則）

- **状態**: proposed（サンドボックス検証済み・**repo 実装予定** `experiments/e022_horizon_ledger/`）
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

## verdict
- [ ] proposed → e022 実装で判定（2D SOLID / 3D floor を厳守）。
