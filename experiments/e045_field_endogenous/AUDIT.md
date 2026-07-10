# e045 — 負の結果：内生的ニッチ構築は場で多様性を自己生成しない — AUDIT

```yaml
id: e045
role: N
claim_tier: measured
evidence: "内生的ニッチ構築(外部最適点なし・自分の隣人への負の頻度依存だけで適応度)を GS object-tracking 場で忠実に試すと参照の主張を反証：スポット生存窓の内では罰が空間同類化を上回れず、局所形質多様性は中立ドリフト対照を上回らない(むしろ僅かに下・excess~-0.001)／罰を効かせる強さ(comp=6)にすると場は絶滅(occupied→0)。自己生成の open-ended 多様性はここでは創発しない"
target_encoded: false
known_match: "負の頻度依存選択/ニッチ構築(期待された正)／中立ドリフト帰無モデル／Gray-Scott スポット生存窓"
open_issues: ["NEGATIVE: この忠実な場での naive ルートを反証するが、内生 open-endedness が不可能とは示さない(別の場/結合なら成功しうる＝open)", "HYBRID: per-tissue 形質／頻度依存は入力／「ニッチ/open-endedness」は analogy"]
```

> **場化 wave2 capstone（内生・frontier 挑戦の正直な帰結）**。e043/e044 は外部最適点（モルフォゲン）を使った。
> 多様性を**内生**に——景観を**自己生成**——できるか。参照サンドボックスは「中立を超える多様性維持」を主張。
> 忠実な場では? → **反証**。role **N**（正直な失敗＝資産、cf e020）。

## 測定（`results/endogenous.json`、full）
- **生存窓の内（endogenous）**：局所形質分散 ~0.0017 vs 中立 ~0.0017（excess ~ **-0.001** ≦ 0＝多様性増なし）。両方 alive。
- **強い罰（参照設定 comp=6）**：occupied **→ 0**（場が絶滅）。
- 生存窓内では罰が弱すぎ空間同類化を破れず、効かせると致死＝**中立を超える生存領域なし**。

GREEN（＝負の結果を主張するゲート）: `both_baselines_alive`／`NEGATIVE_no_local_diversity_gain`（excess≤0.001）／
`NEGATIVE_strong_penalty_kills_field`（強罰で occupied<0.02）。

**罠（隠さず報告）**: 参照は内生多様性>中立を主張。GREEN が出るまでチューニング（**禁止**）せず、生存窓を掃引して
**どの領域も中立を超えない**・参照自身の強罰は**致死**を確認。**負の結果**を role N で公表。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 結果を書いていない。頻度依存だけ入力 |
| 2 | 忠実な物理? | **Yes** | GS 場＋負の頻度依存＝忠実 |
| 3 | 結果は初期条件に? | **No** | ランダム初期。負の結論は測定 |
| 4 | 入れてない物が出る? | **—（負）** | 期待された多様性が**出ない**＝反証 |
| 5 | 数で合う? | **Yes** | excess≤0・強罰で絶滅（頑健） |
| 6 | 頑健? | **Yes** | 格子/step/seed を変えても中立を超えない（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 中立比・絶滅を測定（チューニングで正を捏造せず） |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 中立帰無との比較で判定 |

## 床（隠さない）
1. **NEGATIVE**：この忠実な場の naive ルートを反証する。内生 open-endedness が**不可能**とは示さない
   （別の場/結合なら成功しうる＝open/frontier）。
2. **HYBRID**：per-tissue 形質。頻度依存は入力。「ニッチ/open-endedness」は analogy。
3. **同じ数学≠同じもの**。正直な負（cf e020 受動 phase-field は分裂しない）——隠す/チューニングで消す失敗ではない。

## 再現
```bash
python experiments/e045_field_endogenous/endogenous.py --quick --no-write
pytest tests/test_e045.py
```
