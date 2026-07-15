# EVIDENCE_CONTRACT_V2_AUDIT.md — 独立技術監査（Phase A1）

本監査は `docs/EVIDENCE_CONTRACT_V2.md`（前登録）が **docs-only** であり、既存の研究資産・物理・数値・
CI を**変えていない**ことを独立に確認し、契約 v2 の主張の**限界**を明示する。

## 監査基準
- 基準コミット（指示書）：`8d8dedc`
- Phase A1 の対象：`main` に対する docs-only 追加。
- 規律：`AGENTS.md` / `docs/ANTI_DRIFT.md`（強い語を測定能力以上に使わない・no_touch）。

## 変更セット（意図）
| ファイル | 種別 | 物理/数値/CI への影響 |
|---|---|---|
| `docs/EVIDENCE_CONTRACT_V2.md` | 新規 | なし（前登録テキスト） |
| `docs/EVIDENCE_CONTRACT_V2_AUDIT.md` | 新規 | なし（本監査） |
| `docs/MIGRATION.md` | 追記のみ | なし（Phase A1 節を追記） |

**触っていない**：`schemas/`・`rooms/`（room.yaml / emergence.json / checksum / field.json / run manifest）・
`genesis/`（物理コード・`measures.py`＝no_touch）・`experiments/*/experiment.yaml`・`app/`・
`.github/workflows/ci.yml`・`tools/`。

## 検証（本 PR で実行）
| コマンド | 期待 | 結果 |
|---|---|---|
| `python tools/validate_schemas.py` | 変更前と同等に pass | （本文で報告） |
| `python tools/audit_roles.py` | 第8監査 GREEN 維持 | （本文で報告） |
| `python tools/build_catalog.py --no-write` | 3 room / 41 experiments 不変 | （本文で報告） |
| `pytest tests/ -q` | 変更前と同等に pass | （本文で報告） |
| `git diff --stat` | docs 3 ファイルのみ | （本文で報告） |

## 契約 v2 が「言えること / まだ言えないこと」
**言える**：
- 現行 metadata に **"official" と "3D 昇格完了" の畳み込み**、**"conservation" 一語への 5 種混在**、
  **Level と能力ベクトルの二重の真実**という具体的な曖昧点が存在する（一次証拠：`room-g00{2,3}-a/room.yaml`・
  `emergence.json`・`measures.py`）。
- それらを二軸＋区別語彙＋機械検証可能な official 不変条件へ分解する**一意な語彙**を前登録した。

**まだ言えない（A1 の限界）**：
- これは **設計契約であって実装ではない**。`room.yaml` / `experiment.yaml` の値はまだ v2 語彙になっていない。
- semantic lint はまだ機械化されていない（§5 は仕様のみ・負の fixture は A2 で実装）。
- 閾値表（§6）は**様式**であり、感度分析の数値は A2 / Phase F で埋める（A1 では値を変えない）。
- G002/G003 の "candidate へ言い換え" は**方針**。実際の badge 変更・folder 互換 alias は A2 で（参照破壊を避ける別 PR 案）。

## 誠実さの確認（ANTI_DRIFT）
- 本契約は G001/G002/G003 の既存結果を**削除・降格・再解釈していない**（validated_2d は価値保持）。
- 強い語を足していない（「証明」等は使わず、G001 は "lower-bound proxy" と明記）。
- 「実装済み」と「前登録のみ」を各節で区別している。

## 既知の限界と次の停止条件
- A2 へ自動で進まない。A1 のレビューを待つ。
- A2 で metadata を書き換える際は、recorded artifact / checksum の**不改変をテストで保証**する（ルール 7）。
- 数え方（TRUST_MAP 44 vs catalog 41）の一本化は A2 §7.3 で行う（本 A1 では触れない）。
