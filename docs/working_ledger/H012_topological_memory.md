# H012–H013 — トポロジカル記憶（巻きが保護された受信・記憶）

- **状態**: proposed（サンドボックス検証済み・**repo 実装予定** `experiments/e020_topological_memory/`）
- **起票者**: Claude / 2026-07-09（指示書 §3 より）
- **狙う Type**: B（床つき measured）。
- **依拠する既知事実**: 巻き数（トポロジカル電荷）保護、GL リング、Aharonov-Bohm 位相、スペクトル ETD。

## 仮説（H012–H013）
- **H012（静的）**: 非局所（囲まぬ環=0・全環同値）／保護（局所擾乱 0→4π で巻き不変）／
  容量（小受信機 dof≈48 が M=121 保護ビット 100% 回復＝MC≫N）／力学バンプは対照で劣化。
- **H013（動的リング）**: 自律量子化（n=round(Φ)・エネルギー周期1・電流鋸歯）／ゲージ不変（dE<1e-4）／
  位相スリップ障壁（Φ=0.5 で強制ノード E≫基底 E）。

## repo 実装（予定）
`experiments/e020_topological_memory/`（Stage1 静的＋Stage2 リング）。`core/holonomy.py`（**実装済み**：
winding_around[CCW]）を使用。
**罠**: 巻きは**反時計回り**（時計回りだと巻き反転→ノイズ0でも "0%"）。
リング Laplacian は**スペクトル ETD** `exp(−(k−Φ)²dt)`（陽解法は overflow→NaN）。
GREEN ゲート名は物理量のみ（winding / energy / current）。「記憶」は analogy（docstring/AUDIT）。

## 番号メモ（衝突・要確認）
現 repo には別セッションの `experiments/e020_vesicle_division/`（H002+ の分裂・負の結果、PR #10）が既存。
指示書 §8.8 は e020 を空きと想定していたため**番号衝突**。実装時に再採番（この記憶弧を空き番号へ）
または vesicle_division の扱いと合わせて調整する。**この判断は e020 系実装の着手時に確定する**。

## verdict
- [ ] proposed → e020 実装で判定（番号衝突を先に解決）。
