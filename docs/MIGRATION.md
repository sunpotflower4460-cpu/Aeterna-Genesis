# MIGRATION.md — Aeterna-Genesis 三層移行の記録

**この文書は、個別実験の研究リポジトリから「0 から立ち上がる 3D 物理・Genesis Room・AI 始原条件探索」の
三層研究環境への段階移行を、PR 単位で記録する。** 設計の全文は GptA/GptB 統合設計指示書に基づき、
`docs/GENESIS_MAP.md`（現在地）・`AGENTS.md`（共通規則）・`docs/PHYSICS_INTEGRITY.md`（誠実さ）へ集約した。

> **不変条件（全 PR 共通）**：既存 `experiments/e001–e045`・各 `run.py`/`AUDIT.md`/`results/`/`robustness.py`・
> `docs/working_ledger/`・`docs/TRUST_MAP.md`・`docs/claim_ledger.md`・Git 履歴・PR 履歴を**削除・移動・番号変更しない**。
> 新思想に合わせて過去の文章を**無断で書き換えない**。まず metadata 層を足し、その後に物理コードを整理する。

---

## 現況（実装時点）

- **Evidence Library**：`experiments/e001–e045`（41 ディレクトリ）。役割 E/V/S/N/F/Q の一次分類は
  `docs/TRUST_MAP.md`（**44 実験・E=20 / V=2 / S=5 / N=2 / F=11 / Q=0**）が保持。GptA/B 起草の
  `docs/GENESIS_MAP.md §1` は e001–e036＋H019 を例示するが、**H020（e037–e045：生態的 PGG・場化 wave2・
  統合 capstone・内生ニッチの負の結果）も Evidence Library に含まれ、分類は TRUST_MAP が一次情報**。
- **LAW.md**：二値 GREEN を廃し役割 E/V/S/N/F/Q＋第8監査へ拡張済み（2026-07 改訂）。本移行で新 docs 群への案内を追加。
- **Genesis Rooms / AI Lab / App**：未実装（後続 PR）。

---

## PR 順（設計書 §22 / GENESIS_MAP §5）

| PR | 内容 | 状態 |
|---|---|---|
| **PR1** | 思想と用語を固定（本 docs 群＋AGENTS.md＋LAW 多軸案内＋旧地図保存＋legacy 明示） | **完了 (#21)** |
| **PR2** | Schema と Registry（`schemas/`・`genesis/registry/`＋CI-B 検証） | **本 PR** |
| PR3 | 既存 e001–e045 へ `experiment.yaml` metadata | 予定 |
| PR4 | 共通 Runner と Manifest（manifest/checkpoint/summary/checksum/no-write 正実装） | 予定 |
| PR5 | Dimension Transfer Harness（薄い 3D スラブ・面外摂動・局所 3D・低解像度全体 3D） | 予定 |
| PR6 | 最初の正式 3D Genesis Room（G001 or G002） | 予定 |
| PR7 | AI Genesis Lab 最小版（許可パラメータのみ探索・既存 Room 非破壊） | 予定 |
| PR8 | Observatory App（catalog 駆動・Physics Integrity Panel） | 予定 |

---

## PR1 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/`・`core/`・`tools/`・`tests/`・`docs/TRUST_MAP.md`・
`docs/claim_ledger.md`・`docs/working_ledger/`・`docs/00_grand_map.md` 本体・`room/中心実験室.html` 本体・
`docs/*harvest*.md`・LAW.md の既存本文。

**追加した**：
- `AGENTS.md`（ルート・全 AI 共通規則）
- `docs/PHYSICS_INTEGRITY.md`・`docs/EMERGENCE_LEVELS.md`・`docs/ROOM_MODEL.md`・
  `docs/DIMENSION_POLICY.md`・`docs/AI_EXPERIMENT_POLICY.md`・`docs/GENESIS_MAP.md`
- `docs/MIGRATION.md`（本ファイル）
- `docs/history/00_grand_map_legacy.md`（旧地図への案内スタブ。本体は移動しない）
- `room/README.md`（`中心実験室.html` が **JS 簡易デモであり Python 実験と別物**である明示）

**軽微に変更した（案内の追加のみ・削除なし）**：
- `README.md`：新三層構造と AGENTS.md への案内を追記。
- `LAW.md`：新 docs 群（PHYSICS_INTEGRITY / EMERGENCE_LEVELS / GENESIS_MAP）への案内を追記。
- `docs/00_grand_map.md`：冒頭に「現在地は GENESIS_MAP.md」の案内バナーを追記（本文は歴史資料として保存）。

**物理コードは一切動かしていない**（設計書 §24-1「既存コードを大規模に移動しない」）。

---

## PR2 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/`・`core/`・`tools/`（既存）・`tests/`・全 docs・LAW.md・全 results。
**物理コードは一切動かしていない。** schema/registry は Evidence Library を**参照するのみ**。

**追加した**：
- `schemas/`：`experiment` / `genesis` / `room` / `run` / `emergence` / `dimension-transfer` / `render` の
  7 スキーマ（設計書 §22 PR2）＋ `registry.schema.json`（registry 検証用）。すべて JSON Schema draft 2020-12。
- `genesis/registry/`：`models.yaml`（G001–G003 候補＋Evidence 物理）・`solvers.yaml`・`diagnostics.yaml`
  （創発 Level 診断器）・`invariants.yaml`（保存量）・`param_ranges.yaml`（AI の探索範囲＋変更禁止項目）・`README.md`。
- `tools/validate_schemas.py`（**CI-B**）：全 schema の妥当性・registry の schema 適合・`related_experiments`
  参照先の実在・id 重複を機械チェック。

**軽微に変更した（追加のみ）**：
- `requirements.txt`：`PyYAML>=6.0`・`jsonschema>=4.18`（純 Python・schema/registry の検証に使用）。
- `.github/workflows/ci.yml`：**CI-B**（`tools/validate_schemas.py`）を追加。

**まだやらない**：`experiment.yaml` を各実験に付与するのは **PR3**。room/run/emergence の実体は正式 Room（PR6）から。
schema は「置いただけ」で既存実験を再検証しない（設計書 §24-5「まず metadata 層」）。
