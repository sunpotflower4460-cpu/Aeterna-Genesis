# docs/ の目次

2026-09 の再始動（P0〜P5）の後、どの文書が「いま使う正本」で、どれが「記録（歴史）」かを分けた目次。
ファイルは動かしていない（既存リンクを壊さないため）。**迷ったら上から順に読む。**

## 1. まず読む（規律と定義）

1. [`../AGENTS.md`](../AGENTS.md)：AI も人も守る共通規則
2. [PHYSICS_INTEGRITY.md](PHYSICS_INTEGRITY.md)：誠実さの規律、claim tier、第8監査
3. [EMERGENCE_LEVELS.md](EMERGENCE_LEVELS.md)：Level 0–8 と測定指標
4. [ANTI_DRIFT.md](ANTI_DRIFT.md)：「それは育ったのか、置いたのか？」
5. [ROOM_MODEL.md](ROOM_MODEL.md)：Genesis Room
6. [DIMENSION_POLICY.md](DIMENSION_POLICY.md)、[3D_NATIVE_POLICY.md](3D_NATIVE_POLICY.md)：2D は候補、3D が本線
7. [AI_EXPERIMENT_POLICY.md](AI_EXPERIMENT_POLICY.md)：AI が変えてよいもの

## 2. 現在地（いまの地図）

- [`../RESEARCH_COMPASS.md`](../RESEARCH_COMPASS.md)：羅針盤（`research/index.json` から自動生成）
- [WHITE_CEILINGS.md](WHITE_CEILINGS.md)：白ごとの天井地図（最重要）
- [TREASURE_AUDIT.md](TREASURE_AUDIT.md)：2026-08〜09 の自動研究の監査
- [X_PATTERN_AUDIT.md](X_PATTERN_AUDIT.md)：「名無し変化 X」の監査
- [INVENTORY_2026-09.md](INVENTORY_2026-09.md)：凍結点の棚卸し
- [ANGULAR_MODES.md](ANGULAR_MODES.md)：自走個体の frontier（M1/M2）
- [TRUST_MAP.md](TRUST_MAP.md)、[PIECES.md](PIECES.md)、[claim_ledger.md](claim_ledger.md)、[honest_floors.md](honest_floors.md)、[traps_museum.md](traps_museum.md)：証拠庫の索引・信頼度・失敗の記録
- [GENESIS_PROVENANCE.md](GENESIS_PROVENANCE.md)、[CAUSAL_CLOSURE.md](CAUSAL_CLOSURE.md)、[PREPARATION_PROTOCOLS.md](PREPARATION_PROTOCOLS.md)、[PERIODIC_TABLE.md](PERIODIC_TABLE.md)、[VERTICAL_EMERGENCE_CONTRACT.md](VERTICAL_EMERGENCE_CONTRACT.md)：主張を支える枠組み
- [HUMAN_REPORTING.md](HUMAN_REPORTING.md)：人向け報告のルール
- [generated/evidence_index.md](generated/evidence_index.md)：実験と公式 Room の自動索引

## 3. 記録（歴史）：2026-08〜09 の自動研究 bot 期

bot は P0 で停止した（`.github/workflows/*` の該当 6 本は手動実行のみ）。
次の文書は、当時の仕組みを記録として残しているもので、**いまの運用や結論の根拠にはしない**。
結論は P2 の監査（上の 2.）を通すこと。

- 自動研究ループ：[DREAM_LOOP.md](DREAM_LOOP.md)、[ADAPTIVE_DREAM_CYCLE.md](ADAPTIVE_DREAM_CYCLE.md)、[ADAPTIVE_DREAM_V7.md](ADAPTIVE_DREAM_V7.md)、[ADAPTIVE_RESEARCH_YIELD.md](ADAPTIVE_RESEARCH_YIELD.md)、[PROGRESS_RATCHET.md](PROGRESS_RATCHET.md)、[GENESIS_AUTOPILOT.md](GENESIS_AUTOPILOT.md)
- 群・拡張：[AUTONOMOUS_EXPLORATION_SWARM.md](AUTONOMOUS_EXPLORATION_SWARM.md)、[AUTONOMOUS_FRONTIER_EXPANSION.md](AUTONOMOUS_FRONTIER_EXPANSION.md)、[FREE_HYPOTHESIS_LAB.md](FREE_HYPOTHESIS_LAB.md)、[SCIENCE_BRIDGE_CONTINUITY_MAINTENANCE.md](SCIENCE_BRIDGE_CONTINUITY_MAINTENANCE.md)、[EMERGENT_FIELD_FRONTIER.md](EMERGENT_FIELD_FRONTIER.md)
- 研究基盤：[RESEARCH_INFRASTRUCTURE.md](RESEARCH_INFRASTRUCTURE.md)、[RESEARCH_COMPASS.md](RESEARCH_COMPASS.md)（bot 版の羅針盤。現行はルートの `RESEARCH_COMPASS.md`）、[INSTRUMENT_CONTRACTS.md](INSTRUMENT_CONTRACTS.md)、[REPRODUCIBILITY.md](REPRODUCIBILITY.md)、[PORTABLE_CI.md](PORTABLE_CI.md)
- 始原の試み：[GENESIS_ROOT.md](GENESIS_ROOT.md)、[GENESIS_NOTHING.md](GENESIS_NOTHING.md)、[MULTIWORLD_GENESIS.md](MULTIWORLD_GENESIS.md)、[ZERO_TO_FISSION_PATH.md](ZERO_TO_FISSION_PATH.md)
- 証拠契約：[EVIDENCE_CONTRACT_V2.md](EVIDENCE_CONTRACT_V2.md)、[EVIDENCE_CONTRACT_V2_AUDIT.md](EVIDENCE_CONTRACT_V2_AUDIT.md)
- 初期の地図・移行・収穫メモ：[00_grand_map.md](00_grand_map.md)、[GENESIS_MAP.md](GENESIS_MAP.md)、[MIGRATION.md](MIGRATION.md)、[現在地と方向性_TypeABCD.md](現在地と方向性_TypeABCD.md)、`e0xx_harvest.md`、[claude_code_instructions_H001-H004.md](claude_code_instructions_H001-H004.md)
- サブフォルダ：`history/`、`working_ledger/`、`frontier/`、`integration/`
