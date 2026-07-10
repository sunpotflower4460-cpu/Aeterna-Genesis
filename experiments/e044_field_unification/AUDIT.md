# e044 — 協力が ONE 場に参加（局所公共財が協力者を支える）— AUDIT

```yaml
id: e044
role: E
claim_tier: measured
evidence: "同じ ONE 場の宇宙(分裂+継承+変異+選択+適応+分化)に、隣人の減衰を下げる局所公共財を足すと、clonal パッチ上で協力者が持続(協力割合~0.6)／公共財の便益をゼロにした決定的対照は協力が崩壊(~0.3)＝object tracking の clonal パッチによる同類化が公共財を成立させる"
target_encoded: false
known_match: "Hamilton/同類化(assortment)／clonal パッチ上の局所公共財(cf e037 生態的PGG)／Gray-Scott object tracking"
open_issues: ["HYBRID: 純 GS 動力学だが形質+coop は追跡 per-TISSUE ラベル／公共財の生産とコストは入力", "「協力/公共財」は coop 場の analogy／協力割合は death-rate/param 依存(床)"]
```

> **場化 wave2 capstone（統一）**。e043 に **協力**（局所公共財）を足し、clonal 同類化で協力が持続するか、
> 便益ゼロ対照が崩壊するか。role E（hybrid）。**e037 の別実装（体の上で）**。

## 測定（`results/unification.json`、full）
- **協力（公共財あり）** ~0.6 持続／**対照（便益ゼロ・同コスト）** ~0.3 崩壊（advantage>0.15）。
- **体はなお**：occupied>0.25、corr(形質,最適点)>0.6、left<right 分化。

GREEN gates: `cooperation_persists_with_public_good`（>0.5）／`control_no_benefit_collapses`（advantage>0.15）／
`body_still_adapts_and_differentiates`。

**罠（設計者は踏んだ・我々は回避）**: 参照サンドボックスは公共財強度を**掃引して最良の協力割合を報告**＝
結果に合わせたチューニング（**禁止**）。我々はパラメータを**事前固定**し、**対比**（公共財あり vs 便益ゼロ対照）で
ゲート、robustness では**各設定が対照を上回る**ことを示す（cherry-pick なし）。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「協力持続」を書いていない |
| 2 | 忠実な物理? | **Yes** | GS 場＋局所公共財拡散＝忠実 |
| 3 | 結果は初期条件に? | **No** | coop はランダム初期。持続は選択の帰結 |
| 4 | 入れてない物が出る? | **Yes** | 同類化による協力持続（対照は崩壊） |
| 5 | 数で合う? | **Yes** | 公共財~0.6 vs 対照~0.3 |
| 6 | 頑健? | **Yes** | seed を変えても公共財>対照（`robustness.json`）。絶対値は param 依存＝床 |
| 7 | コードが発見? | **Yes** | 協力割合と対比を測定 |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 対比でゲート。param は**事前固定**（掃引最良は不使用＝チューニング回避） |

## 床（隠さない）
1. **HYBRID**：純 GS 動力学だが形質+coop は追跡 per-TISSUE ラベル。公共財の生産/コストは入力。
2. 「協力/公共財」は analogy。協力割合は param/death-rate 依存（床）——robust は**公共財>便益ゼロ対照**であって
   絶対値でない。**同じ数学≠同じもの**。param は事前固定（参照の best-of 掃引＝チューニング禁止を回避）。

## 再現
```bash
python experiments/e044_field_unification/unification.py --quick --no-write
pytest tests/test_e044.py
```
