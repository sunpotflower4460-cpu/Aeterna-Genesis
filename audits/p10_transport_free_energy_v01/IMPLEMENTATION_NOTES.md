# IMPLEMENTATION_NOTES — 実装の選択と、既存 V0 との違い（v0.1）

## 1. 数値モデル（独立に書いた）
- **流束**：`J_{j+1/2} = −M_face c_face (μ_{j+1} − μ_j)/dx`。`M_face`＝M の算術平均（M = D/RT）、`c_face`＝c の算術平均。`μ = RT ln(c/c_ref) + χφ`。
- **空間**：N 個のセル、中心値。壁の面は `J_0 = J_N = 0`（無流束）。
- **離散の性質**：Δμ = 0 が離散の定常。よって離散の平衡は `c_j ∝ exp(−βφ_j)` が**厳密**に成り立つ（T3 の相対誤差 1e−15）。
- **正値性**：`μ` が `ln c` を含むため、c→0 では流入の駆動が無限に大きくなる（対数障壁）。正値性は解析的に保たれる想定で、数値的にも確認した（クリップはしていない）。
- **散逸**：離散でも `dF/dt = −Σ M_face c_face (Δμ)²/dx` が厳密に成り立つ（T8b の根拠）。

## 2. 既存 V0 の Scharfetter–Gummel と何が違うか
- V0 は面流束を `J = D[B(Δψ)c_i − B(−Δψ)c_{i+1}]`（B はベルヌーイ関数）で与える。本監査は使わない（依頼 §5.3）。
- 本監査は化学ポテンシャル差の形を使い、面の c は算術平均。両者は連続極限で同じ式に収束するはずで、離散の平衡はどちらも Boltzmann（T9 の平面スラブで相対 7.8e−12 一致）。
- 時間積分：V0 は明示的 Euler（dt = 0.1）。本監査は BDF（scipy）。T9 の過渡の差（1.8e−3）は時間積分の違いによるもので、判定には使わない（情報のみ）。

## 3. 関数の依存関係（独立性の確認）
- `model.py`、`solver.py`、`metrics.py`：`vessel_permeability` を import しない。
- `scenarios.py::T9` のみが `genesis.diagnostics.vessel_permeability` を import し、**読み取り比較**に使う（`relax_step` の結果を比べるが、独立モデルの計算には入れない）。

## 4. 閾値と設定の出所
- 全ての数値は `PRE_REGISTRATION.json` から読む（`scenarios.py` は JSON を読む。数値を直接書いたのは `D0=1`、`L=1`、`x0=0.5` の定義だけ）。
- 数値フィールド `rtol_primary` 等は JSON の文字列と同じ値を数値化したもの（値は変えていない）。

## 5. 事前登録からの逸脱（すべて記録）
- AMD-1：T10c の雑音床規則（本実行の前、コミット `52b87a009`）。
- AMD-2：T8b の求積の格子（本実行の前、閾値は不変）。診断は `results/AMD-2_quadrature_diagnostic.txt`。
- 数値エンコード：`integrators` の rtol/atol を数値で追加（値は不変）。
- 図の縦軸を修正（本実行の後。計算は不変。CSV は一致）。
- 既存 V0 の pytest 行の壁時計文字列を除く（本実行の後。数値は不変）。
- 詳細は `INDEPENDENT_AUDIT.md` §I。

## 6. 補足（判定の対象外）
- `results/SUPPLEMENTARY_NOT_IN_VERDICTS.txt`：Fick の F_ref 増加の解像度依存性（a–c）、同じ初期値での Fick と μ の比較（e）、RK4 の自己収束と BDF の床（d）。判定には入れていない。

## 7. 実行環境
- Python（本環境）、numpy 2.5.3、scipy 1.18.1、pytest 9.1.1、matplotlib 3.11.2（本環境で pip 導入。requirements には無い）。
- 実行時間：本実行 約 90 秒。単体テスト 約 7 秒。

## 8. v0.1.1 の形式修正（FMT-1）
- 旧 `summary.json` は `NaN`（標準 JSON ではない）を含んでいた。`strict_json.py` で非有限値を `null` にし、理由を `json_null_fields` に記録する。
- 出力は `allow_nan=False` で書く。NaN が残れば例外になる。
- 旧ファイルは `results/corrections/summary.pre-json-fix.json` に SHA-256 付きで保存（非標準のまま。テストで SHA を照合）。
- `json_correction.py` は一回限りの適用。他の全フィールドが元と一致することを検証してから書く。
- 採点済みの CSV、manifest、test_results は変更していない。本実行は繰り返していない（数値と判定を保つため）。
- `run_audit.py` のコードは形式部分だけ変わった。manifest のコードハッシュは採点時のコードを指す（`CORRECTIONS.json` に両方のハッシュ）。
