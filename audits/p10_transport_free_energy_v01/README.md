# P10 輸送・自由エネルギー独立監査 v0.1

**役割：V（Validation）。** 固定・平面・手で置いた界面の上で、既知の平衡分配則と数式の整合を、既存検証器とは独立に検算する。
器の生成、膜の自発形成、生命、選択透過の創発は**主張しない**。Room でも experiments/eNNN でもない。

- 対象：`docs/frontier/F0_P10_active_vessel.md` §2（F0 は変更しない）。
- 比較（読み取りのみ）：`genesis/diagnostics/vessel_permeability.py`（既存 V0・3D 固定球）。
- 基準：`649fd7e0de259a30048684ba98480739be1edcd9`。ブランチ：`audit/p10-transport-free-energy-v01`。main は未変更。

## 結論（一行）
- 総合判定 **INCONCLUSIVE**。原因は T10c（RK4 の次数）だけで、事前登録の「参照解の誤差の床」の規則による。その他は全て PASS。
- F0 本文の輸送式（χ を含まない）は分配を生まず（T2）、一部の初期条件で F_ref を増やす（補足 J）。書かれた式からは選択性を導けない。
- 化学ポテンシャル流（μ = RT ln c + χφ、共有の D）では、平衡が exp(−χφ/RT) になり、選択性は χ の差だけから出る（T3–T6）。

## 読む順
1. `INDEPENDENT_AUDIT.md`（技術報告・判定の正本）
2. `FORMULA_AUDIT.md`（導出と不一致 D-1〜D-7）
3. `PRE_REGISTRATION.json`（条件・閾値・AMD）
4. `IMPLEMENTATION_NOTES.md`（実装の選択）
5. `ASSUMPTIONS.md`、`SOURCE_INVENTORY.md`

## 実行
```bash
python -m pytest audits/p10_transport_free_energy_v01/tests -q      # 単体テスト 22 件
python audits/p10_transport_free_energy_v01/run_audit.py            # 本実行（results/ を書き換える）
```
図の作成には matplotlib が必要（requirements には無い）。

## ファイル
| ファイル | 中身 |
|---|---|
| `model.py` | 独立の 1-D 方程式（F_ref、μ、流束、散逸、μ_φ、μ_m） |
| `solver.py` | BDF（scipy）と固定刻み RK4 |
| `metrics.py` | 測定（質量、CV、分配比、次数、緩和時間、L1 誤差） |
| `scenarios.py` | T1–T10 とその判定（閾値は PRE_REGISTRATION.json から読む） |
| `run_audit.py` | 全体の実行と results/ の出力 |
| `visualize.py` | 3 枚の図（結果の表示のみ。計算の入力にしない） |
| `tests/` | 単体テスト（変分・保存・分配・散逸・決定性） |
| `results/` | 判定・数値・図・マニフェスト・補足（`SUPPLEMENTARY_NOT_IN_VERDICTS.txt`、`AMD-2_quadrature_diagnostic.txt`） |

## 禁止事項の確認
- 既存ファイル（F0、V0、V0 テスト、docs、experiments、genesis、rooms、ai_lab、research、tests、schemas、pyproject、CI）は無変更（INDEPENDENT_AUDIT.md §E）。
- 独立モデルは `vessel_permeability` を import しない。
- 負の濃度をクリップしていない。閾値を結果の後に変えていない（AMD は本実行の前に記録）。
