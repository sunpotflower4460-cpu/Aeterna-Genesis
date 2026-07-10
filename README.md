# Aeterna-Genesis

**本物の場から、最小条件で、構造が勝手に出るのを、掟つきで一個ずつ積む。**

> **【三層移行 進行中】** 個別実験の研究庫から、**0 から立ち上がる 3D 物理・Genesis Room・
> AI 始原条件探索**の三層研究環境へ段階移行している。
> **AI が最初に読むもの → [`AGENTS.md`](AGENTS.md)**。現在地は [`docs/GENESIS_MAP.md`](docs/GENESIS_MAP.md)、
> 誠実さの憲法は [`docs/PHYSICS_INTEGRITY.md`](docs/PHYSICS_INTEGRITY.md)、創発の深さは
> [`docs/EMERGENCE_LEVELS.md`](docs/EMERGENCE_LEVELS.md)、移行記録は [`docs/MIGRATION.md`](docs/MIGRATION.md)。
> 既存 `experiments/e001–e045` は**削除せず** Evidence Library（物理辞書）として保存する。

宇宙が始まるとき、おそらく最小条件しかない。その条件から、意図せずに——石が
水に作る波紋、雨が降り雷が鳴るのと同じように——構造が "勝手に" 生まれた。
それを、この場で、本物としてやる。観測されている要素（幾何・物質・渦・トーラス・
重力…）が、作為なく、最小条件から創発するのを、一個ずつ確かめて積む。

## 「本物の物理」の二つの意味（混ぜると擬似に転ぶ）

- **(A) 忠実な創発**：本物の法則（実在の場の方程式）を入れ、最小条件から現象が
  勝手に出る。法則は "与えられて本物"、結果は "勝手に出る"。
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

## モジュール一覧

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

剥がす順番の全体地図は [docs/00_grand_map.md](docs/00_grand_map.md)。

## リポジトリ構造

```
Aeterna-Genesis/
├── README.md              # マニフェスト + 掟の要約 + モジュール一覧
├── LAW.md                 # 掟の全文（7監査・claim tier・忠実な場の規則）
├── core/                  # 共有の数値道具（再利用。実験ごとに再実装しない）
│   ├── fft.py             # 2D FFT・波数格子（split-step 用）
│   ├── field.py           # 複素場の初期化・規格化・トラップ・split-step 伝播
│   ├── vortex.py          # 渦検出（位相巻き数＋密度極小）、循環の量子化チェック
│   └── measure.py         # 保存量・累積回転・（後で）次元/相関/スペクトル
├── experiments/
│   ├── e001_gpe_vortex_precession/
│   │   ├── run.py         # 監査ヘッダ＋測定を表示、result.json を保存
│   │   ├── robustness.py  # 監査6：R0×Ω スイープ
│   │   ├── AUDIT.md       # 7監査の結果（人間可読）
│   │   ├── result.json    # 基準測定値（再現確認用）
│   │   └── robustness.json
│   └── e002_gpe_two_vortex/
│       ├── run.py         # 同符号＝共回転／逆符号＝並進、result.json を保存
│       ├── robustness.py  # 監査6：間隔 d スイープ
│       ├── AUDIT.md       # 7監査＋正直な注記（クリーン窓）
│       ├── result.json
│       └── robustness.json
├── docs/
│   ├── 00_grand_map.md    # 全体地図（背骨と剥がす順番）
│   └── claim_ledger.md    # 全主張の claim tier 台帳
├── tests/                 # core 単体テスト＋e001 回帰テスト
└── .github/workflows/ci.yml
```

## 使い方

```bash
pip install -r requirements.txt

# e001 を基準パラメータで再現（result.json を生成）
python experiments/e001_gpe_vortex_precession/run.py

# 監査6（頑健性スイープ）
python experiments/e001_gpe_vortex_precession/robustness.py

# core 単体テスト＋e001 回帰テスト
pytest tests/
```

**期待される結果（e001）**：渦が中心の周りを半径ほぼ一定（≈10）で回り、累積
回転角は 8000 步で 360° を超える（≈462°）。循環は +1 に量子化、エネルギー・
ノルムは保存。詳細は [AUDIT.md](experiments/e001_gpe_vortex_precession/AUDIT.md)。

## スタック

Python（numpy / scipy）。FFT・線形代数・将来の誘導重力（実線形代数）が速く
標準的なため。CI が緑＝「掟つきで再現可能」——擬似でない構造的保証。
