# genesis/registry/ — 機械可読レジストリ

AI（Claude / Codex）が自由形式のファイルを作らず、**ここで許可されたモデル・solver・診断器・保存量・
パラメータ範囲だけを使う**ための機械可読レジストリ（設計書 §19, `docs/AI_EXPERIMENT_POLICY.md`）。

| ファイル | 内容 | schema |
|---|---|---|
| `models.yaml` | 利用可能な物理モデル（G001–G003 候補＋Evidence 物理） | `schemas/registry.schema.json` (kind: models) |
| `solvers.yaml` | 利用可能な数値法（FFT/差分/射影/arrested-Newton） | `schemas/registry.schema.json` (kind: solvers) |
| `diagnostics.yaml` | 創発 Level を測る診断器（Level 1–8） | `schemas/registry.schema.json` (kind: diagnostics) |
| `invariants.yaml` | 保存量・収支 | `schemas/registry.schema.json` (kind: invariants) |
| `param_ranges.yaml` | AI が変更してよい始原側パラメータの探索範囲 + 変更禁止項目 | （search_space 形式） |

**検証**：`python tools/validate_schemas.py`（CI-B）が、全 schema の妥当性・registry の schema 適合・
`related_experiments` の参照先が `experiments/e0xx` に実在するか・model/solver/diagnostic id の重複を機械チェックする。

**不変条件**：既存の物理コード・結果は動かさない。レジストリは Evidence Library を**参照**するのみ。
