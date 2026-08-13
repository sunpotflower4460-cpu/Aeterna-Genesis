# Progress Ratchet — 「同じことを繰り返さず、分からない範囲を減らす」自動研究

## 目的

Adaptive Research Yield は、追加の frontier 計算予算を「成功しそうな一本道」ではなく、反証可能で情報量の高い問いへ配る。

Progress Ratchet はその上に、もう一つの問いを置く。

> **前の burst と同じ問いを惰性で繰り返したのではなく、分からない範囲を一つでも減らしたか？**

ここでいう前進は「毎回、新しい自然現象が出る」ことではない。自然現象の出現を保証しようとすると、結果に合わせた条件選びや target encoding に近づく。

代わりに、追加計算を次のどれかへ使う。

- 未試験の start-side control を調べる
- 必要な独立 replication を明示して行う
- Root candidate の未試験 operator ablation を行う
- F-reference の成立境界を別条件で調べる
- target が飽和したら、次 burst は別 target / lane へ移る

**negative result も、事前に定義した問いを閉じたなら前進になりうる。** ただし数値計算の失敗は物理的negative evidenceにはしない。

---

## 4つの層

### 1. Research Compass — 人が最初に見るもの

`CURRENT_RESEARCH.md` と `research_compass_latest.*` は、現在の大事な発見・前進・次の問いを人向けに見やすくする。

失敗の詳細を前面に出しすぎないが、生データは削除しない。

### 2. Research Memory — 長く忘れないもの

`ai_lab/discoveries/research_memory.json`

- weakened X
- saturated background X
- Deep-Time quarantine
- integrity rules
- **Progress Ratchet が実際に評価した question key**

を保存する。

Progress Ratchet の `progress_question` entry は、短いrecent windowを越えても「この問いは既に試した」と覚えるための durable coverage である。

Research Compass は既存entryを保持してmergeするため、Ratchetのquestion memoryを後段で消さない。

### 3. Adaptive Research Yield — 次の計算をどこへ使うか

F / X / Root の各laneへ、specificity・contrast・未解決integrity・新規depthなどに基づいて bounded budget を配る。

F0–F7は one human-written reference path であり、自然の正解ルートではない。

### 4. Progress Ratchet — 前回より何が分かったか

実行後に、

- 新しいquestion cellを評価したか
- replicationだけだったか
- laneが低gainだったか
- 次burstで同じtargetから離れる必要があるか

を監査する。

---

## Question key は「実際に実行された条件」で作る

パラメータ候補は許可範囲へclipされる。

たとえば `drive_strength=5.0` が上限なら、

- `×1.30`
- `×sqrt(1.30)`
- `×1.69`

の複数候補が全部 `5.0` にclipされることがある。

この場合、それらを3つの新しい実験として数えてはいけない。

Progress Ratchet は、**factorではなくclip後の実際の値**をquestion keyに使い、同じ実行条件へ潰れる候補を1cellへdeduplicateする。

例:

```text
x|X-abc|drive_strength|5
f|white:117|quench_duration|10.24
root|RLAW-xyz|relation_trend
```

これは物理observableではない。研究計画のbookkeepingである。

---

## Coarse-to-fine

一つのknobについて、まず既存の標準controlを調べる。

1. standard-low
2. standard-high
3. refine-low / refine-high
4. stronger boundary probes

小さなbudgetでも、refinementが標準low/highより先に割り込まない。

knobの開始位置はburstごとに決定論的にrotateするが、同じknobのlow/highは対になってから次へ進む。

これにより、片側方向だけを測って「このknobに敏感」と誤読することを避ける。

---

## Novelty は短い履歴だけで判定しない

recent history は「最近このlaneを掘りすぎていないか」を見るために使う。

しかし「初めての問いか？」の判定には使わない。

noveltyは、

1. Research Memory のdurable `progress_question`
2. 互換用にfull retained frontier ledger

から判定する。

したがって13 burst前、あるいはさらに古い問いが、recent windowから落ちたという理由だけで「未試験」に戻ることはない。

---

## Route Escape は記録するだけでなく、次burstで実行する

あるburstが、

- replication only
- low gain
- frontier実験なし

で終わった場合、`next_burst_escape_required=true` と、実際に使ったtargetを `next_burst_escape_targets` に保存する。

次burstのplannerはそのflagを読み、同じtargetへ直行しない。

対象は、

- `x:<pattern_id>`
- `f:<family:trial>`
- `root:<law_id>`

で識別する。

これは永久禁止ではない。次の問い・条件・upstream evidenceが実質的に変われば再び候補になりうる。

---

## Research Memory の no-repeat と再開条件

### weakened X

`avoid_exact_repeat=true` の weakened X は、同じ問いのまま繰り返さない。

現在の自動再開条件は、upstream evidenceがそのXを `REPEATED_SPECIFIC_CANDIDATE` へ実質的に再分類した場合。

### saturated background X

巨大な反復回数だけを増やさない。

ただし、まだ未試験のstart-side intervention cellがあるなら、「新しい境界/機構の問い」として再開できる。

全cellが既知なら、recurrence-only confirmationはfrontier priorityから外す。

---

## 数値失敗は物理的negative evidenceではない

F interventionでscreenがnon-finiteになった場合、

```text
finite_screen = false
counts_as_tested_question = false
```

とする。

そのquestion keyはcoverageへ追加しない。

したがって数値安定性を直した後に、同じ物理条件を正しくretryできる。

---

## Inactive lane は「失敗したlane」ではない

そのburstでbudgetを受け取らなかったlaneには `lane_knowledge_units=0` を書かない。

zero-gain streakは、**実際に実験を行ったlaneだけ**について数える。

初めてeligibleになったlaneが、過去のinactive burstのせいで最初からcooldownされることを防ぐ。

---

## Progress status

主なstatus:

- `ADVANCED` — 新しいquestion cellまたは有効な新しい比較情報が増えた
- `ADVANCED_BY_REPLICATION_ONLY` — 独立確認は増えたが、新しい境界は閉じていない
- `LOW_GAIN` — computeは使ったが、compactな新規知識をほぼ増やしていない
- `STALL_NO_FRONTIER_EXPERIMENT_EXECUTED` — frontier実験が実行されなかった

replication-only / low-gain / stall は次burst route escapeの対象になる。

raw recurrence countだけはprogressに数えない。

---

## Integrity — 変えないもの

Progress Ratchet / Research Memory は次を変更しない。

- 物理方程式
- 初期条件の物理内容
- scientific truth gate
- start purity / Z-A / Z-B
- Prefix Identity Audit
- Local Vortex Energy の geometry-first selection
- Room promotion
- official Emergence Levels
- Cross-World / Multi-World のshadow status
- F0–F7の定義

また、

- X-pattern
- vortex pair / triangle
- split location/time
- organism / brain
- energy landscape
- target morphology

をseedしない。

Progress scoreやquestion countは**物理observableでもconfidenceでもない**。

---

## 「毎回しっかり前進」の意味

この仕組みが保証しようとするのは、

> 毎burstで新しい自然現象が現れること

ではない。

近づけるのは、

> **同じ計算予算を、未試験control・必要な独立追試・境界精密化・未試験ablation・飽和からのroute changeへ使い、分からない範囲を少しずつ減らすこと**

である。

合言葉:

> **同じ成功をもう一度見に行くより、次に何を壊せば説明が狭まるかを調べる。**
