# AUDIT — e046 topological_state_capacity (role V)

## 主張と tier
- **主張**：固定した閉じた向き付け可能曲面の胞複体上で、独立な非可縮 **ホロノミーチャネル**の数 = 第一ベッチ数
  `b₁ = 2g`。指定した巻きは (a) 正確に読み戻せ、(b) 局所ゲージ変換で不変、(c) 可縮サイクルで 0、(d) 同じ
  ホモロジー類の別ループで同じ整数。
- **tier**：measured / established（胞体コホモロジーの定理を、本 repo の測定器で数値的に検証した）。
- **role**：**V（primary）／N（secondary）**。トポロジーと巻きは**人が置く**ので創発ではない。これは
  「与えたトポロジーが何個の独立な保護巻き座標を許すか」の**測定器検証**であり、将来の 3D トポロジー測定器の
  **陽性対照**である。

## PUT IN / MEASURED
- **PUT IN**：曲面の胞複体 (V,E,F)、辺上の U(1) 位相（接続）、H₁ 基底、一部の試験で整数巻き。
- **MEASURED**：`rank H₁ = b₁ = 2g`（境界 b 本で `b₁ = 2g+b−1`）；正確な読み戻し；ゲージ不変；可縮=0；
  同ホモロジー同値。`b₀/b₁/b₂/genus/boundary` を**別 field** で記録。

## ゲート（物理量名のみ）
`rank_h1_equals_betti1` / `sphere_zero_channels` / `holonomy_readback_exact` / `contractible_cycle_zero` /
`holonomy_gauge_invariant` / `same_homology_same_readout`。**すべて PASS（GREEN）。**

## 再現性（C12 遵守）
独立実装（`betti_numbers` は境界作用素のランクから b₀,b₁,b₂ を計算）が、元サンドボックス `Hgamma_out.json` と
**数値一致**（球面 b₀,b₁,b₂=1,0,1／トーラス=1,2,1／トーラス+3穴 b₁=4／genus 2g）。図からの再構成ではない。

## 用語の規律（conflict register）
- **C02**：`b₁` を「bit / 情報容量」と呼ばない。**independent noncontractible holonomy channels（保護巻き座標
  空間のランク）**。実際の情報容量は alphabet・障壁・ノイズ・読み出し精度・保持時間を要する。
- **C03**：handle 数 g・境界数 b・`b₁=2g(+b−1)` を混同せず別 field。
- **C09**：Hopf 不変量（3D 写像の preimage linking）と H₁ ホロノミーは**別の不変量**。本実験は後者のみ。
- 「記憶」はゲート名に使わない（analogy）。**同じ数学 ≠ 同じもの**。

## 正直な床
- 固定した有限胞複体上の定理検証（**空間そのものの創発ではない**）。トポロジーも巻きも置いた＝role V。
- b₁ の**メッシュ非依存性**はトーラス 2 解像度で確認。高種数は標準 CW 複体（1頂点・2g辺・1面）で厳密。
- **創発の問い**（未分化 3D 場から穴と非ゼロ巻きが自然に生じ、局所摂動に耐えるか）は**別の将来 frontier**
  （one-handle selection / emergent holonomy）であり、本実験では主張しない。

## A_OR_B
(A) 忠実。手入力＝胞複体＋基底＋指定巻き。`capacity=b₁` の法則・ゲージ保護・非局所性は測定で確認（置いていない）。
