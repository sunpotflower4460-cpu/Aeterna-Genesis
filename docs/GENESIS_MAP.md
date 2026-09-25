# GENESIS_MAP.md — 現在地と研究地図

Aeterna-Genesis の現在地。**旧地図（`docs/history/00_grand_map_legacy.md`）は歴史資料として残し、現在地はここで管理する。**

**中心定義：** Aeterna-Genesis は、無数の**宇宙水槽（Universe Aquarium）**へ異なる前提条件を与え、世界自身が何を始めるかを観察し、その条件地図を人間とAIが共同で学び続ける研究環境。人間もAIも「こんな系を見たい」と意図してよい。意図は探索計画に使うが、見たい結果そのものを物理へ書き込まない。詳細は [`docs/UNIVERSE_AQUARIUM.md`](UNIVERSE_AQUARIUM.md)。

より深い創発を目指すときも、途中へ完成機能を追加して結果を作るのではなく、**Aquarium の Recipe（法則・初期状態・境界・持続入力などの前提条件）を変え、t=0 から新しい Run として試す。**

---

## 全体構造

```text
Aeterna-Genesis
├─ Universe Aquaria    … 「何を見たい／何を試したい」という人間・AI共有の研究系列
│   └─ Recipe → Run → Observation → Discovery → Next Recipe
├─ Evidence Library    … 既存 e001–e036（物理辞書・測定器・負の結果）
├─ Genesis Rooms       … 実際に t=0 から走り、保存・再現可能になった宇宙
└─ AI Genesis Lab      … Aquaria と研究記憶を読み、前提条件を探索する自動実験者
```

**Aquarium は科学的成功状態ではない。** planning layer であり、Goal-directed / Open-ended、Minimal / Seeded / Driven など問いの異なる研究列を並列に持てる。Room は実際に走った宇宙の証拠側に属する。

---

## 0. Universe Aquaria — 人間とAIの研究系列

台帳は `aquaria/registry.json`、共有メモは `aquaria/notebook.json`。

Aquarium は次を持つ。

- **Intent**：何を見たいか。人間・AI・共同のどれでもよい。
- **Recipe Space**：何を前提条件として変えてよいか。
- **Observation Focus**：何を測れば前進と言えるか。
- **Human Note / AI Direction Note**：次のアイディア・問い・判断。
- **Evidence refs**：過去のどの証拠を参照しているか。

重要な境界：

```text
planning may read intent = true
physics may read intent text = false
intent is scientific evidence = false
goal-directed == target-encoded = false
```

つまり「分裂を見たい」「トーラス形成を見たい」と目的を持って探索してよいが、分裂命令・分裂位置・トーラス形状を結果として物理へ埋め込まない。

---

## 1. Evidence Library — 既存 e001–e036 の再分類

**生命の部品表として並べない。** 役割（E/V/S/N/F/Q）と、Genesis に対する位置づけで再分類する。**削除・番号変更しない。**

### 1.1 0 からの Genesis 候補（正式 Room へ発展し得る）
- **e008**：一様に近い状態から欠陥形成（解釈を除き、差・欠陥の自然形成を候補化。3D 正式検証が必要）。
- **e010**：Kibble–Zurek 欠陥形成（0→差→欠陥の強い候補。3D では点渦でなく渦線/ループ、別の正式検証）。
- **e013 の自己組織対流部分**：静止場から不安定性で循環（規定流部分と分離）。
- **e017 の対流部分**：自発対流の物理基準（Room の流体監査・臨界値検証に使用）。
- **e033**：一様＋ノイズから相分離・ドメイン形成（質量保存・スペクトル測定・相判定を修正してから使用）。
- **e035**：均衡の不安定化から時間振動（空間 Genesis と別に、時間的自己組織化の候補）。
- ⚠️ **これらを直ちに一つへ接着しない。** まず、どの法則系が単独でどこまで育つかを比較。

### 1.2 遷移と挙動の物理辞書（創発後の構造が何をするか）
e001（局在渦の運動）／ e002（相互作用）／ e003（3D 渦リング自己伝播）／ e011（欠陥対の運動法則）／ e012（3D トポロジカル構造の安定化）／ e016（安定サイズと basin）／ e034（空間フロント伝播）／ e036（分布場の追従と lag）。→ **Room の到達 Level を判定する比較基準。**

### 1.3 測定器・検証器
e014（因果順序から次元）／ e017（対流臨界値）／ e022（ゲージ不変量・地平線量）／ e023（因果順序・時間順位・次元）／ e031（因果作用の数値揺らぎ）／ e032（3D 地平線量の次元依存性）。→ **創発候補を測る計測器として登録。**

### 1.4 設計仮説・閉環プロトタイプ（role=S）
e015 / e018 / e019 / e021 / e024 / e025 / e028 / e029 / e030。→ **失敗ではない。** 「0 から自然にその閉環が形成された証拠」としては扱わない。「そのような関係が成立した場合、何が起きるか」を調べた設計仮説として AI が参照（完成構造をコピーしない。抽出してよいのは：どの物理量の相関が重要か／何を測れば閉環候補か／何を壊すと崩れるか／どの障害が出たか）。

### 1.5 負の結果・制約（role=N）
e020（受動場だけでは自発分裂しない）／ e026（トポロジカル量は単純コピーできない）／ e031（生の因果作用は強く揺らぐ）／ e032（3D 化で係数の普遍性が壊れる可能性）。→ **探索空間を正しく制約する貴重な成果。**

### 1.6 側枝・アナロジー
e004 ／ e009 の一部 ／ e027 のエージェントモデル部分。→ 本流から削除せず、別 modality として保存。正式 Room と混同しない。

### 1.7 H019（e033–e036）＝場化の複数実現
分化=Cahn-Hilliard、協力=Nagumo フロント、Red Queen=Rosenzweig-MacArthur、適応=replicator-mutator。**サンドボックスの場化（morphogen・生態的 PGG・objtrack）と違う物理での独立実現＝複数の忠実実現**（`docs/TRUST_MAP.md`）。

---

## 2. Genesis Rooms — 最初の候補

| Room | 物理 | 期待する到達 |
|---|---|---|
| **G001** | 3D TDGL / 複素 GL / GPE クエンチ | Lv1 分散/構造因子 → Lv2 欠陥/渦線/ループ → Lv3 移動/再結合 |
| **G002** | 3D Boussinesq / 壁付き RB | Lv1 不安定モード → Lv2 局在対流 → Lv3 循環/輸送 |
| **G003** | Model H / CH–NS / 反応性 phase-field hydro | 相分離+界面+流れ+変形+輸送が**一つの全体場**から（統合候補。G001・G002 の後） |

**完成した渦線/roll を初期条件に置かない。** 詳細は `docs/ROOM_MODEL.md`。

---

## 3. AI Genesis Lab

前提条件を探索する自動実験者（`docs/AI_EXPERIMENT_POLICY.md`）。

AI は人間のAquariumを探索してよいし、人間の入力がなくても新しいAquariumを提案・探索してよい。必ずResearch Memoryを参照し、同じ失敗を惰性反復しない。過去Evidenceから関連する成立条件・失敗条件をAquarium Compassへ戻し、人間が現在地を確認できるようにする。

`ai_lab/aquarium/compass.py` は planning-only の共有地図を作る。**compute allocation・physics・Room promotion・scientific truth gateは変更しない。**

**役割分担：** サンドボックス＝2D 探索＋事前計算（Claude）／正式 3D＝リポジトリ（Codex/Claude Code）。

---

## 4. Observatory App

`app/` は最終的に、人間とAIが同じ研究状態を見る場所。

- Universe Lobby：実際に走ったRoomを見る
- Universe Aquarium Lab：研究系列、Intent、Recipe Space、Human Note、AI Direction Noteを見る
- Room Workspace：実測fieldを美しく再生する
- Discovery Inbox：AI候補とジョブを確認する

人間がアプリで作ったAquarium ideaはまずplanning data。Runner接続後もintegrity checkを通し、**新しいRunとしてt=0から実行**する。

---

## 5. 移行完了の最低条件（更新）

- e001–e036 が一つも削除されていない。
- 既存結果へのリンクが壊れていない。
- Type A–D が確信度として分離された。
- E/V/S/N/F（/Q）が導入された。
- 創発 Level が導入された。
- 2D 候補と正式 3D が区別された。
- Room schema が存在する。
- AI の変更可能範囲が schema で固定された。
- 過去 Room を上書きしない仕組みがある。
- 2D→3D 移行監査がある。
- 少なくとも一つの正式 3D Genesis Room がある。
- アプリがハードコードでなく catalog を読む。
- 可視化の各要素が実際の物理量へ対応している。
- AI 発見候補が正式 Room と混同されない。
- **Aquarium Intent と科学Evidenceが機械的に分離される。**
- **Human Note と AI Direction Note を同じ研究地図で確認できる。**
- **Goal-directed と target-encoded を同一視しない。**
- **CI が保存済み JSON の存在確認だけでなく、実際の再計算を行う。**

---

## 6. 移行 PR の順（歴史参照）

PR1 思想と用語 → PR2 Schema と Registry → PR3 既存実験 metadata → PR4 共通 Runner と Manifest → PR5 Dimension Transfer Harness → PR6 正式 Genesis Room → PR7 AI Genesis Lab → PR8 Observatory App。

現在はこれらの上に **Universe Aquarium collaboration layer** を追加している。

**実装上の注意：** 既存コードを大規模に移動しない。既存実験を「間違い」として削除しない。過去の文章を歴史ごと消さない。Aquarium は既存Evidence/Room/AI Labの上に加えるmetadata・planning層であり、科学証拠の意味を後付けで変更しない。
