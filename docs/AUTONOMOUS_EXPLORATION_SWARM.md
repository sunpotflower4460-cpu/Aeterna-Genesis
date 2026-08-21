# Autonomous Exploration Swarm

Aeterna-Genesis の production Dream Loop に、既存の毎時 broad exploration を壊さず、**別の問いを持つ追加探索を日々差し込む**ための compute-allocation layer。

これは physics layer ではない。スケジュールや profile 名は simulator の状態変数・初期条件・方程式へ入らず、既存 runner の探索予算だけを変更する。

## 原則

- **答えを置かない。** target morphology / vortex / location / event time / desired outcome は seed しない。
- **通常の毎時探索を残す。** baseline の longitudinal evidence を維持する。
- **追加計算は別の問いへ使う。** 成熟した成功例の単純反復だけに計算を集中させない。
- **Discovery と falsification を並走させる。** 未知を増やすだけでなく、近傍条件・対照・3D・長時間・breaker で壊す。
- **F-path は一つの参照経路にすぎない。** specialist profile は F-depth 最大化を目的にしない。
- **Room / official Level / truth gate は変更しない。** profile は計算配分のみ。

## 日次配置

Production は従来通り毎時 `:17` に baseline burst を持つ。これに加えて、同じ `genesis-dream-loop` concurrency group で直列化された specialist burst を **1日6回**置く。

| JST | Profile | 主な問い |
|---|---|---|
| 01:07 / 13:07 | `native3d` | 2D候補は本物の3Dでも残るか、幾何・3D follow-up・deep-timeで壊れるか |
| 05:07 / 17:07 | `mechanism` | recurrent X / frontier lead / root law に対する intervention・breaker・競合理解 |
| 09:07 / 21:07 | `novelty` | 人間がまだ名前を付けていない遷移を広く拾い、fresh seedで追試できる問いへ変える |

`:47` の watchdog は従来通り recent completed report が無い時だけ baseline burst を補完する。通常は研究回数に数えない。

## Profile budgets

### baseline

従来 production budget を維持する。

- broad 2D: 2048
- native 3D: 100
- open-ended probes: 24
- unknown follow-up patterns: 2
- frontier experiments: 24
- emergent-field trials: 12
- root-law trials: 24
- deep-time max leads: 1

### novelty

未知の変化を増やすだけでなく、反復可能な問いへ変えることを優先する。

- broad 2D: 1024
- native 3D: 80
- open-ended probes: 72
- unknown follow-up patterns: 6
- synthesized hypotheses: 6
- frontier experiments: 56
- emergent-field trials: 18

### native3d

2Dの見栄えより3D authenticity・geometry・long-time persistenceを優先する。

- broad 2D: 768
- native 3D: 200
- compare-native3d-top: 24
- geometry top/broad: 28 / 56
- 3D follow-up trials: 64
- native variants: 2
- deep-time max leads: 2
- frontier experiments: 40

### mechanism

「出た」を数え続けず、「なぜ出る / 何を変えると消える」を優先する。

- broad 2D: 1024
- native 3D: 80
- 2D follow-up trials: 448
- fission-reference intervention trials: 48
- unknown follow-up patterns: 6
- synthesized hypotheses: 8
- root-law trials: 64 (`8,12,16,24` regulators)
- emergent-field trials: 36
- frontier experiments: 80
- deep-time max leads: 2

## Nominal daily exploration budget

スケジュールが全て完走した場合の**予定上限**であり、完走や科学的成功を意味しない。

| Lane | 従来24 baseline/day | Swarm導入後 | 増加 |
|---|---:|---:|---:|
| broad 2D trials | 49,152 | 54,784 | +11.5% |
| native 3D trials | 2,400 | 3,120 | +30.0% |
| open-ended probes | 576 | 848 | +47.2% |
| unknown-X follow-up slots | 48 | 78 | +62.5% |
| frontier mechanism/breaker experiments | 576 | 928 | +61.1% |
| emergent-field trials | 288 | 420 | +45.8% |
| root-law trials | 576 | 800 | +38.9% |
| deep-time max-lead opportunities | 24 | 34 | +41.7% |

予定された primary/specialist research opportunities は **30/day**。watchdog check 24/day はこの数に含めない。

## 何を「前進」と数えるか

追加 compute の目的は trial count の最大化ではない。以下を優先する。

1. 新しい観測可能な遷移・関係・長寿命状態を増やす。
2. recurrent pattern を fresh seed / near / control で壊し、成立条件を狭める。
3. 2D lead を native 3D で独立に失敗させる機会を増やす。
4. 短時間の候補を同じ t=0 history の deep-time で追い、Prefix Identity を守る。
5. 成熟した問いを exact-repeat せず、Research Memory / Progress Ratchet に従い新しい falsifiable question へ移る。
6. 負の結果・天井・不一致を成功例と同じように保存する。

## 実装

- profile selection: `ai_lab/dream/swarm_profile.py`
- production schedule: `.github/workflows/dream-loop.yml`
- tests: `tests/test_swarm_profile.py`

Manual `workflow_dispatch` では `auto / baseline / novelty / native3d / mechanism` を選べる。`auto` は通常 schedule policy に従う。

合言葉は変わらない。

> **それは育ったのか、置いたのか？**
