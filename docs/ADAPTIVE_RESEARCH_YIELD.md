# ADAPTIVE_RESEARCH_YIELD — 自動実験を「成功数」ではなく情報量で配分する

## 目的

Aeterna の自動実験は、特定の筋書きを深くすること自体を目的にしない。

> **同じ計算時間なら、いまの仮説を最も強く確かめる／壊す実験へ多く配分する。**

この文書は Adaptive Dream の**追加 frontier 予算**の配分規則を定める。物理方程式、初期条件、科学ゲート、Room、公式 Emergence Level、広域探索の anti-bias floor は変更しない。

## なぜ変更するか

旧 v8 の `frontier_expander` は「F0–F7は人間が書いた参照経路であり自然な正解ルートではない」と明記している一方、F4 以上があると F lane が追加予算のほぼ半分を最初に確保する実装だった。

これは target encoding ではないが、**研究配分の段階で参照経路を暗黙の目的関数にする**危険がある。

同時に、X-pattern は大量反復だけでは意味が増えにくい。たとえば巨大な nonspecific X を同じ方法で何度も再確認するより、contrast=0 の specific candidate の成立境界を変数一つずつ壊す方が情報量が高い。

## v9 の原則

### 1. F-path に first refusal を与えない

F0–F7 は一つの human-written reference path のまま。

- F4 が繰り返されただけなら小さな falsification/control floor のみ維持。
- 新しい深さ、balance collapse、pre-split instability、network fission candidate が出た時だけ配分を増やす。
- F lane は深くなっても全 frontier 予算を独占できない。
- F7 が出ても biological cell division とは呼ばない。

### 2. X は「回数」より specificity を優先

優先度には、

- exact hit rate
- nearby hit rate
- contrast hit rate
- `REPEATED_SPECIFIC_CANDIDATE / VERIFYING / REPEATED_NONSPECIFIC`
- 試行数
- 最近同じ X を調べた回数

を使う。

巨大な `REPEATED_NONSPECIFIC` は背景現象として残すが、raw recurrence count だけで frontier 予算を取り続けない。

### 3. 同じ X を連続で掘り続けない

最近の frontier history を見て、直近で何度も調べた X のscoreを下げる。

これにより、条件特異性を持つ複数の X 候補が自動で交代しやすくなる。

### 4. 小予算でも knob を偏らせない

従来の one-factor spec は固定順だったため、予算が小さいと先頭の knob だけ測る危険があった。

v9 は毎 burst / pattern で開始 knob を決定論的に回転し、fresh baseline の後、異なる knob をなるべく広く触る。

結果形状、X outcome、渦、三角、分裂位置・時刻は与えない。

### 5. R0 は「足りないもの」を壊すために使う

Root lane は、

- permutation quotient 後の新しい区別がない
- robust relational closure がない
- `relation_trend` に依存していて hidden memory assumption の疑いがある

などの未解決監査に応じて重みを上げる。

operator ablation が必要でも、そのoperatorをfundamental lawとは呼ばない。

### 6. 実行できない予算を割り当てない

- F one-factor set は最大12件
- R0 ablation は active operator 数まで
- X は複数候補へ分配可能

という**実際の実行容量**をcapとして使う。

`allocated > executable` のまま研究量を水増ししない。レポートには requested / allocated / executed / unallocated / execution gap を残す。

## NØ の扱い

Strict NØ は「何も与えない」ため、seed・size・time・randomness を変えた大量試行をしてはいけない。

したがって v9 の物理 frontier budget を NØ の反復へ回さない。

NØ は毎burst一度の meta-control と決定性監査を行い、First-Given の65,535組合せは**列挙だけ**行う。65,535件の物理実験とは数えない。

## Cross-World の独立追試

通常の Cross-World comparator は seed 一つの shadow 観測なので、strict lead / overlap lead が出たり消えたりする。

v9では、**そのburstでprimary comparatorがmatchを出した時だけ**、相手world/zeroをfresh seedで少数回追試する。

- leadが0なら追加計算0。
- leadが出た時だけ標準3 fresh seeds。
- 累積CWX ledgerは更新しない。追試3回を「反復3回」と水増ししない。
- `replication_latest.json` に別shadow evidenceとして保存。
- 同じfingerprintでも identical physics / universality / common conservation law とは言わない。

## 変えないもの

このoptimizerは以下を一切変更しない。

- 物理方程式
- start purity の意味
- target encoding gate
- 第8監査
- Prefix Identity Audit
- Local Vortex Energy の geometry-first 選択
- Multi-World / Cross-World / local-energy の shadow status
- Room promotion
- official Emergence Levels
- F0–F7 の定義
- NØ の strictness

つまり、**真実の判定を変えるのではなく、次の計算をどこへ使うかだけを改善する。**

## Active Vessel について

現在openのActive Vessel測定器PRやartifactが残る枝は、最新main基準の測定器監査が終わるまでこの自動budget routerへ入れない。

古い枝の「生命らしい」信号を自動研究の成功報酬にすると、測定artifactやscaffolded setupをPure Genesisの前進と混同するためである。

## 合言葉

> **最も“成功しそう”な実験ではなく、最も“間違いが分かる”実験へ次の計算を使う。**

そして常に：

> **それは育ったのか、置いたのか？**