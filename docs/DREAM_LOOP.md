# Aeterna Dream Loop v1

Dream Loop は、Aeterna-Genesis が人間の操作がない時間にも **有限予算の研究 burst** を続けるための層。
既存の `ai_lab` / `genesis_orchestrator` / Observatory を置き換えず、その上で

> 探索 → 再現 → 2D→3D移行 → 出来事化 → 説明 → 観察

をつなぐ。

## 絶対境界

Dream Loop は研究の説明・順番・観察を自動化するが、次を変更しない。

- `measures.assess_level` 等の成功判定
- 保存則・監査閾値
- `rooms/official/`
- coarse-global-3D / full-3D の人間承認ゲート
- novelty を成功条件として使うこと

View Preset は **表示だけ**を変更する。物理・計算結果・科学的 status は変えない。

## 二本の探索レーン

### 1. Expanded 2D lane

既存 `ai_lab.lab.search` を利用する。

- random / grid / evolutionary
- IC family
- noise amplitude
- correlation length
- diffusion ratio
- drive strength
- quench duration

上位候補だけを別 seed で再実行する。3 seed 中 2 seed 以上で元の到達 Level を再現すると
`REPRODUCED` event を作る。ただしこれは **2D reproducible** であり 3D の主張ではない。

### 2. Runner-native recorded lane

Observatory で実際に再生できる候補を作るため、common Runner が現在本当に適用する

- `noise_amplitude`
- `quench_duration`

だけを小さく探索する。既存 `genesis_orchestrator` を通し、

`2d-screen → local-3d → [HUMAN GATE] coarse-global-3d → [HUMAN GATE] full-3d`

と進む。2D / local-3D の各 run は既存 recorder が field を保存するため、Dream Report の
**見る**ボタンから Observatory へ接続できる。

## Event Ledger

`ai_lab/discoveries/event_ledger.json`

主な event:

| kind | 意味 |
|---|---|
| `NEW_BEHAVIOR` | 過去の探索から離れた測定パターン |
| `NEW_REGION` | Autopilot の 2D gate を通過 |
| `REPRODUCED` | 別 seed でも同じ到達 Level を再現 |
| `PROMOTION_READY` | local-3D を通過し coarse 3D の確認価値が高い |
| `STAGE_PROMOTED` | 承認済みの後段を実測で通過 |
| `DIMENSION_FAILURE` | 2D候補が3Dで崩れた |
| `NEGATIVE_RESULT` | 親より浅い領域を確認 |
| `RARE_EVENT` | 最初の挙動が追加 seed では再現しにくい |
| `NUMERICAL_WARNING` | 数値不安定。物理的失敗と混ぜない |

説明文は v1 では **ルールベース**。LLM は不要。

## Night Report

各 burst は以下を生成する。

```text
ai_lab/reports/nightly/<timestamp>/
├── summary.json
├── events.json
└── report.md

ai_lab/reports/nightly/latest.json
```

Observatory の Discovery Inbox は `latest.json` を読み、

- 実験数
- 新規候補
- 再現成功
- 昇格候補
- 3Dで崩れた候補
- Most Interesting

を人間語で表示する。

## Observation Preset

`ai_lab/discoveries/view_presets.json`

測定値から `phase` / `density` lens、表示 threshold、opacity、glow、再生速度、親との比較を選ぶ。
Night Report の **見る** を押すと、該当 Preset を実際に Observatory state へ適用してから Room を開く。

Preset の `honesty` は常に

```json
{
  "changes_physics": false,
  "changes_success_gate": false,
  "scientific_promotion": false
}
```

である。

## 手動実行

軽い確認:

```bash
python -m ai_lab.dream \
  --quick --mode random --trials 12 \
  --repro-top 2 --repro-seeds 3 \
  --native-variants 2 --max-jobs 8
```

広い2D探索だけ:

```bash
python -m ai_lab.dream --quick --trials 100 --no-native
```

## 自動実行

`.github/workflows/dream-loop.yml`

デフォルトは毎日 **03:17 JST** に bounded burst を一回実行する。

GitHub Actions 上では状態を cache に保存し、Night Report / candidate evidence を artifact として30日保存する。
デフォルトでは bot が main を勝手に更新しない。

継続結果をrepository自体にも保存したい場合だけ、GitHub repository variable:

```text
PERSIST_DREAM_RESULTS=true
```

を設定する。この場合も自動commit対象は generated evidence / reports / candidate Rooms のみで、
`rooms/official/` は含まれない。

## v1 の意図

Dream Loop の目的は「AIに結論を考えさせ続ける」ことではない。

- 数値計算は既存の物理コード
- 探索はアルゴリズム
- 再現は seed replay
- 3D移行は既存 gate
- 説明は測定値から機械生成
- 人間は重要候補を見て、後段昇格を決める

という分離を守る。

LLM Scientist は将来、**次にどの対照実験を試す価値があるかを提案する任意層**として追加できるが、
Dream Loop 本体は AI API が一切なくても研究を継続できる。
