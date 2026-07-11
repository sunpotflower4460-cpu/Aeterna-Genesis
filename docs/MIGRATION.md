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
| **PR2** | Schema と Registry（`schemas/`・`genesis/registry/`＋CI-B 検証） | **完了 (#22)** |
| **PR3** | 既存 e001–e045 へ `experiment.yaml` metadata（41件・schema 検証・8監査整合） | **完了 (#23)** |
| **PR4** | 共通 Runner と Manifest（gl2d/gl3d 参照モデル・manifest/summary/checksum/emergence・no-write 正実装） | **完了 (#24)** |
| **PR5** | Dimension Transfer Harness（薄い 3D スラブ・面外摂動・渦線安定性・リスク報告） | **完了 (#25)** |
| **PR6** | 最初の正式 3D Genesis Room（G001・64³・Level 2・格子収束・複数 seed） | **完了 (#26)** |
| **PR7** | AI Genesis Lab 最小版（許可パラメータのみ探索・2D screen・既存 Room 非破壊・自己昇格しない） | **完了 (#27)** |
| **PR8** | Observatory App（catalog 駆動・Universe Lobby・Physics Integrity Panel） | **本 PR（移行 第一段階 完了）** |

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

---

## PR3 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/e0xx/` の物理コード・`results/`・`AUDIT.md`・`robustness.py`・`tests/`・
全 docs 本文・`docs/TRUST_MAP.md`・`docs/claim_ledger.md`・LAW.md。**物理コードは一切動かしていない。**

**追加した**：
- 各 `experiments/e0xx/experiment.yaml`（**41 件**）：`id/title/role{primary,secondary}/confidence(Type A–D)/
  claim_tier/put_in/emerged/seeded_structure/dimension{computed,official_3d,transfer_risk}/genesis_role/
  target_encoded/known_match/unresolved_audit/results`。**一次情報は `docs/TRUST_MAP.md`（役割・target_encoded）・
  `docs/現在地と方向性_TypeABCD.md`（確信度）・`docs/GENESIS_MAP.md §1`（genesis_role）**。
- `tools/gen_experiment_yaml.py`：experiment.yaml の再現可能な生成器（ハンド authored データ表）。
- `tools/validate_schemas.py`（CI-B 拡張）：全 experiment.yaml を `experiment.schema.json` で検証・
  id とディレクトリ名の一致・**第8監査整合**（target_encoded=true → 主役割は E/V でない）を機械チェック。

**genesis_role（GENESIS_MAP §1 の位置づけ）の内訳**：
genesis_candidate=e008/e010/e013/e033/e035、behavior_dictionary=e001/e002/e003/e011/e012/e016/e034/e036/
e037/e038/e039/e040/e043/e044、measurement_tool=e014/e017/e022/e023/e031/e032、
design_hypothesis=e015/e018/e019/e021/e024/e025/e028/e029/e030/e041、negative_constraint=e020/e026/e045、
sidebranch_analogy=e004/e009/e027。

**まだやらない**：room/run/emergence の実体は正式 Room（PR6）から。experiment.yaml は metadata であり、
既存の `AUDIT.md`/YAML ヘッダ/TRUST_MAP を置換しない（並存する集約ビュー）。

---

## PR4 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/`・既存 `tools/`・全 docs 本文・`schemas/`・`genesis/registry/`。既存物理コード不変更。

**追加した**：
- `genesis/models/ginzburg_landau.py`：次元非依存の複素 TDGL クエンチ参照モデル（2D/3D 同一コード）。
  一様に近い無秩序＋微小ノイズから出発し、対称性破れ（Level 1）と位相巻き欠陥（2D 点渦/3D 渦線, Level 2）が
  **入れずに**創発（Kibble-Zurek）。**欠陥・パターン・波長は一切 seeded していない**。
- `genesis/diagnostics/measures.py`：測定量で Level 判定（秩序変数の成長・構造因子ピーク・巻き欠陥数。
  欠陥は**無秩序ノイズを除外**して秩序バルクのみ計数）。
- `genesis/runners/runner.py`：共通 Runner。genesis 条件を t=0 から**途中介入なし**で発展させ、
  `manifest.json`/`summary.json`/`emergence.json`/`checksum.json` を `runs/seed-XXXX/` に生成。
  **`--no-write` は完全計算して書き込まないだけ**（no-write が実計算することを CI で検証）。
  **field checksum で再現性**（同 genesis+seed+mode → 同一 checksum）。mode は物理でなく格子/step のみ変える。
- `tests/test_genesis_runner.py`：2D で Level≥1・再現 checksum・run/emergence が schema 準拠・3D smoke。

**軽微な追加のみ**：`.github/workflows/ci.yml` に Runner の 2D/3D smoke（--no-write が実計算する検証）。

**まだやらない**：正式 3D Room 登録（`rooms/`）は **PR6**。次元移行監査は **PR5**。
PR4 の Runner は「2D は探索・3D 正式」の枠を実装するが、**正式 Room の到達 Level 判定は full-3d から**
（DIMENSION_POLICY.md）。`_demo_run` は成果物でなく Runner の動作確認用（コミットしない）。

---

## PR5 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/`・`genesis/models/`・`genesis/runners/`・`genesis/diagnostics/`・
`schemas/`・全 docs 本文。既存物理コード不変更。

**追加した**：
- `genesis/dimension/harness.py`：**次元移行監査**（DIMENSION_POLICY.md §2）。2D 成功を 3D へ自動外挿しない。
  - **薄い 3D スラブ試験**：2D で秩序化した渦場（残存渦あり・edge≥48）を nz 層の薄いスラブに積み、**面外摂動**を
    加えて 3D 発展させ、渦が**面外へ逃げるか（z 分散成長）／渦線が切れるか／新モードが育つか／構造が保たれるか**を測定。
  - a-priori 次元リスク（2D 点渦→3D 渦線＝**トポロジー余次元変化 high**・reconnection high）＋線形代理（面外モード成長率）。
  - `dimension-transfer.yaml`（`schemas/dimension-transfer.schema.json` 準拠）を出力する**リスク報告**（合否ゲートでない）。
- `tests/test_dimension_harness.py`：報告が schema 準拠・スラブ試験が非退化（残存渦>0）・面外成長を数で測る・リスク報告である。

**測定結果（ローカル）**：edge=64 スラブで 8 本の渦線・面外摂動は減衰（z 分散成長 0・log-rate<0）→ この規模では
渦線は面外に**安定**（escaped=False）。ただし a-priori 余次元変化リスクは残るので **full-3D（PR6）が必須**という規律的結論。

**軽微な追加のみ**：`.github/workflows/ci.yml` に harness smoke。`.gitignore` に `_demo_transfer.yaml`。

**まだやらない**：正式 3D Room（`rooms/room-g001-a/`）と full-3d 実行は **PR6**。

---

## PR6 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`experiments/`・`genesis/models,runners,diagnostics,dimension/`・`schemas/`・全 docs 本文。

**追加した（最初の正式 3D Genesis Room）**：
- `rooms/official/room-g001-a/`：**3D 複素 TDGL クエンチ**を t=0 から途中介入なしで full-3D 実行した正式 Room。
  `genesis.yaml`/`room.yaml`/`solver.yaml`/`diagnostics.yaml`/`emergence.json`/`dimension-transfer.yaml`/
  `lineage.yaml`/`render.yaml`/`convergence.json`/`README.md` ＋ `runs/seed-000{0,1,2}/{manifest,summary,checksum,emergence}.json`。
- `rooms/catalog.json`：Room カタログ（Python 生成の一次情報。Observatory App（PR8）が読む＝ハードコードしない）。
- `tools/build_room_g001.py`：Room を再現可能に生成するビルダ（多 seed＋格子収束＋物理監査＋schema 検証）。
- `tests/test_room_g001.py`：committed Room が schema 準拠・Level 2・physics_status 全 passed・多 seed。

**測定（full-3D, 64³, 700 steps, seeds 0/1/2）**：
- **reached_level=2**（全 seed）＝対称性破れ（秩序変数創発）＋**位相巻き渦線**（入れずに創発・Kibble-Zurek）。
- **格子収束**：Level 2 が 48³/64³/80³ で一致、欠陥密度 11.3→9.2→8.1（×10⁻⁴）で収束傾向。
- **再現性**：同 seed → 同一 field checksum。**保存**：post-quench 自由エネルギー単調減少。**第8監査**：目標構造 seeded なし・t=0 から・runtime 介入 0。

**拡張のみ**：`tools/validate_schemas.py`（CI-B）が `rooms/official/*/` の全 Room 成果物（room/genesis/emergence/
run/dimension-transfer/render）を schema 検証。`.github/workflows/ci.yml` にビルダの quick full-3D pipeline smoke。

**床（正直に）**：role E（純粋創発・ラベル/外的最適なし）。「渦線 Genesis」は測定量で判定した名（強い語を使わない）。
Level 3+（渦線の運動・再結合の循環）は candidate＝frontier。**移行完了の最低条件「少なくとも一つの正式 3D Room」を充足。**

**まだやらない**：AI Genesis Lab（許可 param 探索）は **PR7**、Observatory App（catalog 駆動）は **PR8**。

---

## PR7 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`genesis/`・`rooms/`・`experiments/`・`schemas/`・全 docs 本文。**Runner/diagnostics/監査閾値は不変更**。

**追加した**：
- `ai_lab/lab.py`：始原条件の自動探索者。親 Room（room-g001-a）の始原側 knob を**一つだけ**許可範囲内で変え、
  t=0 から **2D screen**（Runner/diagnostics を**import**＝成功判定を再定義しない）、到達 Level を測定し親と比較、
  次元リスクを付し、候補を**非破壊**に保存。**決定的**（固定グリッド・Math.random 不使用）。
- `ai_lab/policies/search_policy.yaml`（許可 knob・昇格段階・no-touch）・`ai_lab/README.md`・`tests/test_ai_lab.py`。

**不変条件（AI がやってはいけないこと・実装で強制）**：成功判定/保存則/監査閾値を変えない（import）・始原側のみ・
一度に一つ・親 Room/`rooms/official/`/過去結果を上書きしない・**自己昇格しない**（`2d_screened` まで。full-3D 判定・
Room 登録は別段階）・許可 search_space を超えた提案は reject。

**軽微な追加のみ**：`.github/workflows/ci.yml` に Lab smoke。`.gitignore` に `ai_lab/{_demo_out,proposals,discoveries}/`。

**まだやらない**：Observatory App（catalog 駆動）は **PR8**。

---

## PR8 で「何を残し・何を追加し・何を変更しなかったか」

**残した（変更なし）**：`genesis/`・`rooms/`・`experiments/`・`ai_lab/`・`schemas/`・全 docs 本文・
`room/中心実験室.html`（legacy デモは削除せず・`room/README.md` で明示済み）。

**追加した**：
- `tools/build_catalog.py`：**唯一の表示元** `app/generated/catalog.{json,js}` を Python 側で生成
  （`experiments/*/experiment.yaml` + `rooms/official/*/` + `rooms/catalog.json` から）。App はハードコードしない。
- `app/index.html`：静的 Observatory。**Universe Lobby**（正式 3D Room・**AI 候補と区別**・Evidence Library 役割別集計）、
  **Room View / Physics Integrity Panel**（入れたもの・自然に出たもの・到達 Level・保存/収束/再現/第8監査・
  格子収束表・複数 seed checksum・**可視化対応 表示→実測物理量**）。`catalog.js`（`window.CATALOG`）を読むので file:// でも動く。
- `app/generated/catalog.{json,js}`（生成物）・`app/README.md`・`tests/test_catalog.py`。

**軽微な追加のみ**：`.github/workflows/ci.yml` に catalog 再生成チェック（**CI が保存済み JSON でなく実際に再計算**）。

**誠実さ（PHYSICS_INTEGRITY §18）**：表示要素は実測物理量に対応・存在しない流線/粒子を描かない・
official 3D Room と 2D/AI 候補を混同しない・強い語を使わない。役割別集計は `experiment.yaml` 由来。

---

## 移行 第一段階 完了チェック（GENESIS_MAP §4 / 設計書 §23）

| 最低条件 | 状態 |
|---|---|
| e001–e045 が一つも削除されていない | ✅（全て保存・Evidence Library） |
| 既存結果へのリンクが壊れていない | ✅（案内追記のみ・旧地図も保存） |
| Type A–D が確信度として分離 | ✅（experiment.yaml `confidence`） |
| E/V/S/N/F(/Q) が導入 | ✅（LAW.md §6・experiment.yaml `role`） |
| 創発 Level が導入 | ✅（EMERGENCE_LEVELS.md・emergence schema・測定判定） |
| 2D 候補と正式 3D が区別 | ✅（DIMENSION_POLICY・mode・catalog で区別） |
| Room schema が存在 | ✅（schemas/room.schema.json） |
| AI の変更範囲が schema で固定 | ✅（param_ranges・AI_EXPERIMENT_POLICY・lab が強制） |
| 過去 Room を上書きしない仕組み | ✅（ROOM_MODEL パラレル宇宙・lab 非破壊） |
| 2D→3D 移行監査 | ✅（dimension harness・dimension-transfer schema） |
| **少なくとも一つの正式 3D Genesis Room** | ✅（**room-g001-a**・Level 2・格子収束・多 seed） |
| アプリが catalog を読む（ハードコードでない） | ✅（build_catalog → catalog.json → app） |
| 可視化の各要素が実測物理量へ対応 | ✅（render schema・app の対応表示） |
| AI 発見候補が正式 Room と混同されない | ✅（catalog で kind 区別・lab は 2d_screened のみ） |
| **CI が保存済み JSON の存在確認だけでなく実際に再計算** | ✅（experiments quick 再実行・room builder smoke・catalog 再生成・validate_schemas） |

**三層移行 第一段階 完了。** 次段：G002/G003 Room、Level 3+ frontier、次元監査の実 3D 昇格、App の Parallel/Lineage View。

---

## 移行後の follow-up（第一段階の後に積んだもの）

| PR | 内容 | 状態 |
|----|------|------|
| **PR-A** | AI 探索の永続化：発見台帳 `ai_lab/discoveries/ledger.json`（append-only by key・冪等）＋ `--review`＋local-3D 昇格した候補 Room（`rooms/candidates/`・非公式）＋ App の Discovery Inbox。 | **完了 (#30)** |
| **PR-B** | **二番目の正式 Genesis Room（G002・自発対流・2D）**：壁付き Rayleigh-Bénard の忠実 2D DNS（`genesis/models/boussinesq_rb.py`）を t=0・静止＋微小ノイズから途中介入なしで実行。 | 本 PR |

**G002（room-g002-a）で入れたもの / 出たもの：**
- **入れた**：Boussinesq 場方程式・上下の壁（自由すべり）・固定温度差（環境）・静止＋微小ノイズ。対流セルも波長も入れていない。
- **出た**：臨界 Ra_c = 27π⁴/4 ≈ 657.5 を境に、亜臨界 Ra=300 は熱伝導のまま（Nu≈1.000）、超臨界 Ra*=1000 で**自発的**に並進対称性が破れて定常対流（Nu≈1.75・循環）。これが「seeded でない」＝第8監査の証拠（onset control）。
- **数値が本物である理由**：壁があるため対流は**有界**（三重周期版は elevator mode で発散する）。渦度-流れ関数形で非圧縮を厳密に満たし（圧力を消去）、自由すべり壁の sine 基底で鉛直ラプラシアンが対角化され拡散は**積分因子で厳密**。移流のみ陽的（適応 CFL・2/3 de-alias）。
- **物理監査（測定・主張でない・4つとも passed）**：保存＝独立な二つの Nu 推定（対流フラックス `1+<wθ>` vs 熱散逸 `<|∇T|²>`）が定常で一致／収束＝定常 Nu が格子 32/48/64 で一致（1.762→1.754→1.750）／再現＝同 seed → 同一 checksum／第8監査＝onset control（亜臨界 vs 超臨界）。
- **床（正直に）**：role E（外部**駆動**＝熱は環境として許容、外部**目標**なし）。reached_level=1（差・模様）。循環（Level 3 物理）は測定済みだが定常セルは並進しないため candidate=3（frontier）。
- **次元（正直に）**：これは**検証済み 2D** Room。3D 昇格は別段階の監査（DIMENSION_POLICY）＝2D 成功を自動外挿しない。剛体壁・高 Ra 時間依存対流も別 Room。

**G002 3D 昇格の試み（frontier・正直な記録）：** 本物の 3D 壁付き RB を作り込むべく、`genesis/models/boussinesq_rb_3d.py`（**experimental**）に完全スペクトル自由すべり 3D ソルバ＋**3/2 ゼロ詰め de-aliasing**を実装。検証できたこと＝(1) de-aliasing 変換が厳密（roundtrip 誤差 ~3e-14）で非線形項が真に de-alias される、(2) **亜臨界**（Ra=300）は Nu→1.0000 で有界（伝導が正しく再現）。未達＝**超臨界**対流は入手可能な解像度（N≤24）で飽和近傍に崩れる。崩壊時刻は解像度/Ra で決まり（Ra=1000,N=16→t≈2.3／Ra=800,N=20→t≈5.2）**dt 非依存**（cfl 0.4 と 0.12 が同じ物理時刻で崩壊）＝aliasing でも CFL でもなく**純粋な解像度不足**。有界・格子収束の 3D DNS には N≳32〜40 とより頑健な時間積分（半陰的移流など）が必要＝バグでなく**計算資源/数値 R&D の段階**。ソルバとテスト（`tests/test_boussinesq_rb_3d.py`：変換厳密＋亜臨界有界のみを主張）を再現可能に保存し、正式 Room には未接続のまま frontier とする。

| **PR-C** | **三番目の正式 Genesis Room（G003・相分離＋流体の共発展・2D）**：Model H（Cahn-Hilliard × Navier-Stokes）の忠実 2D 擬スペクトル DNS（`genesis/models/model_h.py`）を t=0・一様＋微小ノイズから途中介入なしで実行。 | 本 PR |

**G003（room-g003-a）で入れたもの / 出たもの：**
- **入れた**：一つの自由エネルギー `F=∫(-φ²/2+φ⁴/4+κ|∇φ|²/2)`・化学ポテンシャル μ=δF/δφ・Cahn-Hilliard・Navier-Stokes・Korteweg 応力・一様＋微小ノイズ。ドメインも界面も波長も流れも入れていない。
- **出た**：一様混合が**自発的に相分離**（amp 0.05→0.73、ドメインが粗大化）＝Level 1、界面が**局在**（interface fraction 1.0→0.33）＝Level 2。同じ μ の界面応力が**流れを生み**（KE 0→4.9e-3）、その流れが φ を移流して**粗大化を加速**（L1 13.3 vs 無流体 11.5）＝流体力学的共発展。
- **共発展の証拠（coupling contrast）**：C=0（純 Cahn-Hilliard）は KE=0・L1=11.5、C=1（Model H）は KE>0・L1=13.3。流れは**場から生まれ**粗大化を加速する＝入れていない（第8監査に相当）。
- **数値が本物である理由**：Model H は**緩和系**（自由エネルギーが Lyapunov 関数として単調減少）ゆえ二重周期でも**有界**（駆動 RB と違い壁不要）。剛性の 4次 Cahn-Hilliard 項は陰的（無条件安定）、粘性は積分因子で厳密、移流は陽的・2/3 de-alias。
- **物理監査（測定・主張でない・4つとも passed）**：保存＝質量 ∫φ 機械精度＋自由エネルギー単調減少（H定理）／収束＝飽和コントラストが 96/128/160 で一致（0.741/0.731/0.739）／再現＝同 seed → 同一 checksum／第8監査＝一様＋ノイズから binodal へ・seeded なし。
- **床（正直に）**：role E（自律・外部駆動なし）。reached_level=2（相分離＋界面局在）。界面＋流れ＋輸送の**共分化（Level 5）は candidate**：流れが場から生まれ粗大化を加速することは測定済みだが厳密ゲートは別段階。**検証済み 2D**（3D は逆カスケード・液滴/双連続トポロジが異なるため別段階の監査）。
