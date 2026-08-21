# Aeterna-Genesis

**宇宙水槽に前提条件を入れ、世界自身が何を始めるかを、人間とAIが一緒に観察する。**

Aeterna-Genesis は、完成した結果を組み立てるためのシミュレータではありません。
法則・物質・初期状態・seed・境界・持続入力などの **Recipe（前提条件）** を宇宙水槽へ与え、t=0 から走らせたときに何が起こるかを記録し、条件地図を育てる研究環境です。

人間もAIも「こんな系を見たい」「こんなことを実現したい」という **Intent** を持って構いません。AIは人間の指示がなくても新しい水槽アイディアを考えてよい。一方で、見たい結果そのものを初期条件・方程式・発生位置・発生時刻・外部命令として仕込むことは分けます。

> **Intent は自由。結果は仕込まない。**  
> planning layer は Intent を読める。physics solver は Intent 文を読まない。

詳しい中心思想 → [`docs/UNIVERSE_AQUARIUM.md`](docs/UNIVERSE_AQUARIUM.md)  
現在の水槽一覧 → [`aquaria/registry.json`](aquaria/registry.json)  
Human Note × AI Direction Note → [`aquaria/notebook.json`](aquaria/notebook.json)  
AI が最初に読むもの → [`AGENTS.md`](AGENTS.md)

## 今の研究環境

```text
Universe Aquarium
  Idea / Intent
      ↓
  Recipe（前提条件）
      ↓
  Integrity Check
      ↓
  Run from t=0
      ↓
  Observation
      ↓
  Discovery / Negative Evidence
      ↓
  Human Note + AI Direction Note
      ↓
  Next Recipe

Evidence Library ── 過去の物理・測定器・失敗を参照
Genesis Rooms    ── 実際に走った再現可能な宇宙
AI Genesis Lab   ── 人間の水槽もAI自身の水槽も自動探索
Observatory App  ── 人間が宇宙を見て、現在地と方向書を把握
```

Seeded / scaffolded / driven な水槽も正当な研究です。strict minimal-start と上下関係にはせず、**何を前提として入れた水槽なのかを正確に分けます。**
Goal-directed（例：分裂を見たい、トーラス形成を見たい）も禁止しません。目的を見ながら前提条件を探すことと、結果を直接描くことを区別します。

> 🧭 **いま大事な発見・前進だけを先に見る → [`CURRENT_RESEARCH.md`](CURRENT_RESEARCH.md)**  
> 生の失敗・quarantine・全試行は削除せず証拠庫に残し、Current Research Frontでは重要な発見と次の問いを優先表示します。

> **【Research OS / Universe Aquarium 移行中】** 個別実験の研究庫から、**Evidence Library・Genesis Room・AI自律探索・人間AI共有Aquarium・Observatory** を一つの研究環境へ統合している。
> 現在地は [`docs/GENESIS_MAP.md`](docs/GENESIS_MAP.md)、誠実さの憲法は [`docs/PHYSICS_INTEGRITY.md`](docs/PHYSICS_INTEGRITY.md)、創発の深さは [`docs/EMERGENCE_LEVELS.md`](docs/EMERGENCE_LEVELS.md)、移行記録は [`docs/MIGRATION.md`](docs/MIGRATION.md)。
> 既存 `experiments/e001–e045` は**削除せず** Evidence Library（物理辞書）として保存する。

## 「本物の物理」の二つの意味（混ぜると擬似に転ぶ）

- **(A) 忠実な創発**：本物の法則（実在の場の方程式）を入れ、前提条件から現象が結果として出る。法則は "与えられて本物"、結果は "世界に任せる"。
  **これは本物の物理。今すぐ厳密にできる。** ここを厳密に積む。
- **(B) 法則自体を根から導く**：場の方程式さえ 0≠無 から出す。最深の目標。**まだ。**

このリポジトリは **(A) を厳密に積み、その上で (B) へ向かう。**

## 掟の要約（全文は [LAW.md](LAW.md)）

擬似（意図どおりに動かす作り物）と、本物の創発を、**毎回 機械的に区別する。**
各実験は 7 つの監査に Yes/No で答える：

1. 規則は結果に言及していないか（局所か）
2. 忠実な物理か（実在の法則か、無理のない局所動力学か）
3. 結果は初期条件に入っていなかったか
4. 入れていない随伴現象も出るか
5. 現実と **数で** 合うか
6. パラメータを変えても頑健か
7. コードは結論を主張せず、測定して発見しているか

**7 つ全通過 → GREEN。GREEN 以外を「成功」と呼ばない。**
各主張には claim tier（`measured | observed | interpretive | analogy | frontier`）
を必ず付ける（[docs/claim_ledger.md](docs/claim_ledger.md)）。

## モジュール一覧（Evidence Libraryの一部）

| モジュール | 問い | STATUS | tier | A/B |
|---|---|---|---|---|
| [e001 GPE 渦の歳差](experiments/e001_gpe_vortex_precession/) | トラップ中の渦は場の方程式だけから歳差するか | **GREEN** | measured | (A) |
| [e002 GPE 二渦の相互作用](experiments/e002_gpe_two_vortex/) | 二渦は回り合う（同符号）／対で並進する（逆符号）か | **GREEN** | measured / analogy | (A) |
| [e004 オクターブ階層/ホログラフィー](experiments/e004_octave_holography/) | 折り畳み階層は双曲(AdS/MERA的)幾何を持つか／螺旋＝繰り返し＋微小な非対称は進むか | **YELLOW** | measured / analogy | (A↔analogy) |
| [e003 GPE 3D 渦リング](experiments/e003_gpe_vortex_ring/) | 渦リングは場の方程式だけから自己伝播するか（トーラス） | **GREEN** | measured / analogy | (A) |
| e00x 白→形 | 一様＋ノイズから対称が自分で破れるか | 計画 | — | (A) |
| e00x 因果順序→次元 | 座標なしの因果集合から次元が出るか | 計画 | — | (A) |
| e00x 物質⇄重力 | 場の構造が重力を生み幾何が返るか | 計画 | — | (A→B) |
| [e008 同時共創発](experiments/e008_coemergence/) | 白＋GPEだけで物質(KZ渦)・時間(矢/echo)・空間(相関)が同時に出るか | **GREEN** | measured / interpretive | (A) |
| [e009 探索的創発](experiments/e009_exploratory/) | 持続トーラス電流・種から成長・未知の興味深いもの（探索） | A=GREEN / C=frontier-obs | measured / analogy / frontier-observation | (A) |
| [e010 KZ コヒーレンス長](experiments/e010_kz_coherence/) | KZ 欠陥は凍結コヒーレンス長で決まるか（間隔∝ξ, 2σ=b, b vs z） | **GREEN** | measured / interpretive | (A) |
| [e011 欠陥の動的化学](experiments/e011_defect_chemistry/) | 束縛渦対は選択的則(v·d, ω·d²)に従い、有限温度で解離するか | **GREEN** | measured / interpretive / analogy | (A) |
| [e012 Hopf 安定化＝「第三」](experiments/e012_hopf_stabilization/) | 高階微分('第三')はホップ粒子を Derrick 崩壊から救うか（完全PDEで Q_H≈1 保持→L*） | **GREEN**（半陰的で frontier→measured） | measured / analogy | (A) |
| [e013 器＋中身](experiments/e013_vessel_content/) | 循環は器の内部に load-bearing か（自己組織対流が内部を養うか） | **GREEN** | measured / analogy | (A) |
| [e014 因果 → 次元](experiments/e014_causal_dimension/) | 座標を捨て因果順序だけから次元が出るか（Myrheim-Meyer / スペクトル） | **GREEN** | measured / interpretive | (A) |
| [e015 器の閉じ](experiments/e015_vessel_closure/) | 器は開(駆動)＋閉(自己維持)の散逸構造で、駆動を切ると死ぬか（両腕オートポイエーシス） | **GREEN** | measured / interpretive / analogy | (A) |
| e0xx 重力の創発 | 誘導重力をエンタングルメントから | frontier | — | (B) |

> e004 は **YELLOW（measured-structural／示唆）**：数値は測定だが、双曲幾何は手作り
> 階層に内在し ε も手入れ。MERA/AdS の構造再現であり忠実な創発ではない。GREEN とは
> 呼ばない（[AUDIT](experiments/e004_octave_holography/AUDIT.md) 参照）。

## リポジトリ構造（現在）

```text
Aeterna-Genesis/
├── aquaria/               # 人間/AI共有の水槽台帳・方向書（planning only）
├── experiments/           # Evidence Library
├── rooms/                 # 実際に走った公式/候補Universe
├── ai_lab/                # 自律探索・Research Memory・Compass
├── genesis/               # 物理モデル・solver・diagnostics・recording
├── app/                   # Observatory / Universe Aquarium Lab
├── schemas/               # Room / Run / Aquarium等の機械契約
├── docs/                  # 研究原則・現在地・監査
├── tests/                 # 回帰・integrity・schema tests
├── AGENTS.md              # 全AI共通ルール
├── LAW.md                 # 掟の全文
└── CURRENT_RESEARCH.md     # 人間向けの現在地
```

## 使い方

```bash
pip install -r requirements.txt

# 全体テスト
pytest tests/

# 人間/AI共有 Aquarium Compass
python -m ai_lab.aquarium.compass

# Observatory のデータを組み立てる
python tools/build_catalog.py
python tools/collect_app_data.py

cd app
npm ci
npm run typecheck
npm run build
```

## スタック

物理・Research OSは Python（numpy / scipyほか）。Observatoryは React / TypeScript / R3F。

CI が緑であることは「見た目が良い」という意味ではなく、**前提条件・証拠・表示・研究計画を混ぜず、再現・監査できる構造を守っている**ことを意味する。
