# H012–H013 — トポロジカル記憶（巻きが保護された受信・記憶）

- **状態**: **resolved (promoted)**（`experiments/e028_topological_memory/` 実装済み・全 GREEN）
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

## 番号衝突の解決（確定）
e020 は `e020_vesicle_division`（H002+ 負の結果、PR #10 でマージ済み）が占めるため、
この記憶弧は**空き番号 `e028` へ再採番**して実装した（合意どおり）。

## 結果（GREEN・物理量ゲートのみ、`experiments/e028_topological_memory/`）
**Stage1 memory**（静的）：固定 h=6 受信機（dof≈48）が M=121 保護ビットを **100%** 回復（容量>dof＝
storage-in-loop 反証）／巻きは局所ノイズ下で不変（動的バンプは劣化）／穴を囲まぬループ=0・全穴の箱ループ=Σビット。
**Stage2 ring**（動的 GL リング・**スペクトル ETD**）：受信巻き n＝round(Φ)（\|n−Φ\|≤0.5）／ゲージ不変 dE≈2e-6／
位相スリップ障壁（**床**：基底 0.79 vs 強制ノード 3.81）。
ゲート名は物理量（winding/capacity/energy/gauge）。「記憶・受信」は analogy（docstring/AUDIT）。

## verdict
- [x] **promoted**（e028 実装・全 GREEN、`claim_ledger` e028 §）。
