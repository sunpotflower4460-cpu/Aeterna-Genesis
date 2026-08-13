# Research Compass — 発見を見やすくし、失敗は忘れず軽く見せる

## 目的

Aeterna は hourly research によって大量の JSON・追試・負の結果・quarantine を蓄積する。
それらは科学的には必要だが、全部を同じ強さで人へ見せると、**本当に重要な前進が埋もれる**。

Research Compass は、元の証拠を削除せずに表示を二層へ分ける。

1. **人向けフロント** — 大事な発見・今回の前進・次に価値の高い問いを先に表示
2. **機械向け研究記憶** — 弱まった候補、quarantine、再発防止ルールを短く保持

元の `ai_lab/reports/**` と `ai_lab/discoveries/**` が権威であり、Compass は view/index である。

## 出力

- `CURRENT_RESEARCH.md` — GitHubを開いてすぐ読める現在地
- `ai_lab/reports/easy/research_compass_latest.md`
- `ai_lab/reports/easy/research_compass_latest.json`
- `ai_lab/discoveries/research_memory.json`

## 人向けに上へ出すもの

優先するのは、単なる回数ではなく **次の問いを狭める証拠**。

- exact / nearby では残り contrast では消える X-pattern
- strict start purityを区別したCross-World lead
- geometry-firstで選んだ後のLocal Vortex Energy測定
- Prefix Identity監査を通ったDeep-Time
- 長寿命状態など「先へ進まないこと自体」が新しい分岐になる証拠

巨大な反復Xも残すが、nonspecificなら「背景現象」としてspecific候補より下へ置く。

## 失敗の扱い

失敗を消さない。人向けでは詳細を小さくし、機械向けには次を残す。

- `WEAKENED` X: 同一条件の惰性反復を避ける
- saturated background X: 回数だけ増やさず、境界・contrast・機構介入の時だけ再開
- Deep-Time quarantine: raw F-depth低下を物理的退化として再利用しない
- numerical non-finite: 物理的negative evidenceとして閉じず、数値問題を直せるならretry可能

`avoid_exact_repeat=true` は「永久に禁止」ではない。`reopen_when` が満たされた場合は新しい問いとして再開できる。

## 重要なintegrity

Compassは以下を変更しない。

- physics / equations / initial conditions
- scientific gates / claim tier
- Room promotion / official Emergence Levels
- X-pattern status
- Cross-World status / universality判定
- Prefix Identity Audit
- Local Vortex Energyのgeometry-first selection
- F0–F7の定義

また、表示順位はscientific confidenceではない。

## 絶対に短縮しない注意

人向けに失敗詳細を軽くしても、次は常に明記する。

- recurrence ≠ physical law
- scaffolded/correlated start ≠ strict nothing
- Cross-World match ≠ universality / identical physics
- local GL energy contrast ≠ binding energy / force / cause
- F0–F7 = one human-written reference path, not official Emergence Levels
- relation-network separation ≠ biological cell division
- Q-tensor = nematic order, not spacetime/gravity

## 自動更新

Dream LoopのMulti-World/Cross-World evidence生成後に `python -m ai_lab.dream.research_compass` を実行する。

そのburstで完成した証拠を読み、Compassとmemoryだけを更新する。Compass自身は新しい物理実験を行わない。
