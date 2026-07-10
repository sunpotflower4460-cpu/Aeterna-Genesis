# e031 — 因果集合の作用はなぜスミアリングが要るか（H008 を定量化）— AUDIT

> **FRONTIER**（H005–H008 続き）。e023 が指摘した H008「実重み因果集合作用は生の Benincasa-Dowker 作用が
> ゆらぎに支配され多様体を選べない」を**定量測定**し、メソスケール**スミアリング**（Glaser-Surya）が
> ゆらぎを大きく damp する（部分的な治療）ことを示す。GREEN。ゲート名は物理量（作用の標準偏差）。
> 「因果集合作用／時空曲率」は analogy。

## 測定（`--quick`／`results/smearing.json`）
| 量 | N=200 | 400 | 800 |
|---|---|---|---|
| **生 BD 作用の std**（seed×4） | 124 | 145 | **369（N とともに増大＝ゆらぎ支配）** |
| **スミアド BD 作用の std** | 14 | 6 | **9.5** |
| damp 係数（生/スミアド, 最大 N） | | | **~39×** |

**曲率の床（正直に）**: flat vs 密度バンプ（曲率集中）のスミアド作用は **~1σ しか分離しない**（marginal）。
**きれいな曲率回復は達成できていない＝床**（深いフロンティアは開いたまま）。

GREEN gates: `raw_action_fluctuation_dominated`（生 std が N で 2× 超に増大）／
`smearing_damps_fluctuations`（生 std / スミアド std > 5）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「生はゆらぐ」「スミアが効く」を書いていない。作用の定義と sprinkle のみ |
| 2 | 忠実な物理? | **Yes** | Benincasa-Dowker 離散作用・Glaser-Surya スミアド作用は established |
| 3 | 結果は初期条件に? | **No** | sprinkle は Poisson。ゆらぎの増大・damp は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 生の std が N で増大、スミアが ~39× damp（入れていない） |
| 5 | 数で合う? | **Yes** | core.causet の BD 作用と厳密一致（鎖 S=N・反鎖 S=N、test で確認） |
| 6 | 頑健? | **Yes** | seed batch・eps を変えても obstacle+cure 成立（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 作用の std を測定。ゆらぎ/damp を書き込まない |

## claim tier
- **measured**: 生 BD 作用の std が N で増大（ゆらぎ支配）、スミアリングが std を >5×（実測 ~39×）damp。
- **interpretive**: 実重み因果集合作用は**メソスケールのスミアリングがないと使える観測量にならない**＝H008 の定量化。
- **analogy / KNOWN MATCH**: Benincasa-Dowker 作用、Glaser-Surya スミアド作用、因果集合量子重力の作用のゆらぎ問題。
- **FRONTIER**: きれいな曲率回復は未達（床）。ここで示したのは**障害の定量化＋部分的治療**。

## 床（隠さない・必須）
1. **FRONTIER**：きれいな曲率回復は accessible な N で達成できていない（曲率バンプは flat より ~1σ のみ）＝**床**。
2. 示したのは障害（生はゆらぐ）と部分治療（スミアが ~39× damp）——多様体選択の完全解ではない。
3. 「因果集合作用／時空曲率」は analogy——measured は作用の統計量のみ。

## 再現
```bash
python experiments/e031_causal_action_smearing/smearing.py --quick --no-write
pytest tests/test_e031.py
```
