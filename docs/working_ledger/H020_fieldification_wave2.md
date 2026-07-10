# H020 — 場化プログラム wave 2（H019 深化：進化・発生・協力・幾何を場から）

- **状態**: **進行中（e038/e039/e040/e041 GREEN・e043/e044 GREEN・e045 は負の結果 N；e042 保留）**。H019（e033–e037）で
  「エージェント→場」の最初の波を示した。ここは同じ規律で**進化・発生・協力・幾何**の各機構をさらに場から出し、
  capstone で**一つの場に統合**する（参照サンドボックス `fieldification_bundle`）。
- **起票者**: Claude Code / 2026-07-10
- **狙う Type**: A（忠実な場の創発）。role E を基本に、hybrid/幾何は正直に床/役割を明示。

## 対象（参照スクリプト → 実験）
| 参照 script | 概念 | Claude Code 実験 | role |
|---|---|---|---|
| efieldobj.py | per-object 連続形質進化（de novo・均質化回避） | **e038 field objtrack** | **E（hybrid 床）** |
| efielddiff.py | 分化（French-flag モルフォゲン＋Turing） | **e039 field differentiation** | **E** |
| eco_rps.py | 協力＝C-D-L 循環スパイラル波 | **e040 field rps_cooperation** | **E** |
| efieldbottle.py | ボトルネック（ネック幾何→創設者数） | **e041 field bottleneck** | **S（幾何サンプリング）** |
| efieldboundary.py | 離散↔連続 境界地図（競争半径 R） | e042（保留） | E |
| efielduniverse.py | ONE 場に 6 過程統合（分化ボディ） | **e043 field universe** | **E（hybrid）** |
| efield_oneuniverse.py | 協力が同じ場に参加（局所公共財） | **e044 field unification** | **E（hybrid）** |
| efield_endogenous.py | 内生ニッチ構築（自己生成景観） | **e045 field endogenous** | **N（負の結果）** |

## e038（連続形質進化＝object tracking）— GREEN
- **入れたもの**: Gray-Scott 場＋tissue ごとの連続形質 τ、成長端で継承＋変異、fitness→kill 結合、低い一様 τ=0.2 播種。
- **出たもの**: de novo で平均形質 0.2→0.90（standing variation なし）、連続分布維持、移動最適点追跡（lag 0.24）。
- **床**: HYBRID（動力学は純場だが形質は追跡ラベル）。e036（replicator-mutator 密度場）の per-object 版。

## e039（分化＝モルフォゲン＋Turing）— GREEN
- **入れたもの**: モルフォゲン源＋拡散分解＋一つの閾値則（French flag）／Gierer-Meinhardt 活性化-抑制系（Turing）。
- **出たもの**: 指数勾配（入れていない）＋3 空間順序ドメイン、Turing が一様から対称性を破りパターン（std 0.02→1.19）。
- **床**: 閾値はモデル選択。「分化/同じゲノム」は analogy。e033（分業）の「同一細胞→異なる型」機構。

## e040（協力＝RPS スパイラル波）— GREEN
- **入れたもの**: 三密度場 C-D-L の循環抑制（D>C, C>L, L>D）＋拡散／well-mixed 対照（拡散なし）。
- **出たもの**: スパイラル波に自己組織し三者共存（C=0.31, D=0.29, L=0.26, std 0.35）、well-mixed は一種へ崩壊。
- **床**: spiral は regime 依存・確率的（N>~180・D<~0.8・4/5 seed）＝正直な床。「協力/RPS」は analogy。

## e041（ボトルネック＝幾何）— GREEN（role S）
- **入れたもの**: タグ付き体＋ピンチネック（幅 w）、娘はネック通過者から再成長。
- **出たもの**: 狭ネック→~1 創設者→clonal（relatedness~0.8）／広→mixed（0.001）＝単一細胞ボトルネックはネック幅から。
- **床**: **role S**＝幾何サンプリング模型（連続場でない・ピンチ抽象）。

## e043（統合＝ONE 場に 6 過程）— GREEN（role E, hybrid）
- **入れたもの**: ONE GS 場＋per-tissue 形質（継承+変異）＋空間変化するモルフォゲン最適点への fitness 結合、一様 τ=0.5 始点。
- **出たもの**: 分裂で場を満たし（occupied~0.4）、局所最適点へ適応（corr~0.8）、順序ある空間形質ドメイン（分化ボディ、contrast~0.47）。
- **床**: HYBRID。e038(object tracking)+e039(morphogen) の**統合**（新機構でなく同時共起の実証）。最適点は環境入力。

## e044（統一＝協力が同じ場に参加）— GREEN（role E, hybrid）
- **入れたもの**: e043 の場＋coop 形質、cooperators が局所公共財（隣人の減衰↓）を生産・コスト負担、便益ゼロの決定的対照。
- **出たもの**: clonal 同類化で協力持続（~0.6）／便益ゼロ対照は崩壊（~0.3）＝空間同類化が公共財を成立、体はなお適応・分化。
- **床**: **param は事前固定**（参照の best-of 掃引＝結果に合わせたチューニングを回避）。robust は「公共財>対照」（絶対値は床）。

## e045（内生ニッチ構築）— 負の結果（role N）
- **入れたもの**: 外部最適点なし・負の頻度依存だけで適応度（locally-common trait を罰）、中立対照・強罰run。
- **出たもの（負）**: 生存窓の内では中立を超えない（local-var excess~-0.001≤0）／罰を効かせると場は絶滅（occupied→0）。
- **床**: 参照の内生多様性主張を**忠実に反証**。GREEN が出るまでチューニングせず（禁止）負を公表（cf e020）。
  内生 open-endedness が**不可能とは示さない**（別の場/結合なら成功しうる＝frontier）。「ニッチ/open-endedness」は analogy。

## メモ
「進化/発生/協力を場に翻訳した」でなく「同じ創発事実が本物の場の法則から出る」を数で。
role は E を基本に、hybrid（e038/e043/e044）・幾何サンプリング（e041）は正直に床/役割を分け、
内生 open-endedness は忠実に試して**負の結果 N**（e045）＝frontier のまま。「結果に合わせたチューニング禁止」を e044（param 事前固定）・
e045（GREEN が出るまで回さない）で厳守。
第8監査：低播種で standing variation を排除（e038）、順序は勾配から創発・パターンは自己組織（e039）、
対比でゲート（e040/e044）、中立帰無と比較（e045）＝全 target_encoded=false。
「同じ数学≠同じもの」。禁止語（生命/協力/同一性/open-endedness）は docs の analogy のみ。ゲート名は物理量。
