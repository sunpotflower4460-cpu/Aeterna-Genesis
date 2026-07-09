# e023 — 因果作用（順序から時空へ：時間・空間・向き）— AUDIT

> 受信弧（H005–H008）。**純粋な因果順序だけから時間・空間が読めるか**、そして**向き（orientation）が
> 時空を作る**（有向＝有限次元＋時間／無向＝スモールワールド mush）を測る。e014（因果次元）に隣接。
> 二段とも GREEN。**ゲート名は物理量/組合せ量のみ**（Spearman / dimension / reach / triangles）——
> 「時間・時空」は analogy（docstring/AUDIT）。**曲率治癒（H007）と経路積分（H008）は frontier（本モジュールでは
> GREEN にしない）**——サンドボックス参照が本セッションで未検証のため、SOLID のみ昇格。

## 測定（`--quick` 再現値 ／ core/causet 検証）

### Stage1 order_time（`results/order_time.json`）— 順序から時間
| 量 | quick 再現 |
|---|---|
| rank が隠れ時刻を回復（Spearman） | **0.989** |
| 中間 rank の反鎖（空間スライス）の空間広がり | **0.957**（空間を充填） |
| interval 次元（順序のみ、diamond 2D） | **2.03**（有限、≈d） |

GREEN gates: `rank_recovers_hidden_time` / `spatial_slice_fills_space` / `interval_dimension_finite`。
**罠**: 全測定は関係行列のみ（座標は順序を生成する足場、破棄）。rank を隠れ時計に照合。

### Stage2 directed_vs_undirected（`results/directed_vs_undirected.json`）— 向きが時空を作る
| 量 | quick 再現 |
|---|---|
| 有向 Myrheim-Meyer 次元 | **2.03**（有限） |
| 無向（同じ対を対称化）ball 成長 N(r) | **[1, 316, 700]**（~全 N に 2 hop で到達＝スモールワールド） |
| 無向の三角形数（サイクル＝時間なし） | **7.7M**（非巡回順序が壊れる） |

GREEN gates: `directed_dimension_finite` / `undirected_collapses_smallworld` / `undirected_has_cycles`。
**罠**: 両読みは**同じ因果対**。向きだけ異なる。スモールワールド崩壊・サイクルは測定。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「rank=時間」「無向=スモールワールド」を書いていない。sprinkle と順序のみ |
| 2 | 忠実な物理? | **Yes** | 因果集合理論（BLMS）・Myrheim-Meyer 次元は実在 |
| 3 | 結果は初期条件に? | **No** | 座標は順序を生成する足場（破棄）。時間/次元/向き対比は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | rank↔隠れ時刻、有限次元、向きで時空 vs mush（入れていない） |
| 5 | 数で合う? | **Yes** | core/causet（e014 で検証済み）で再現 |
| 6 | 頑健? | **Yes** | seed 掃引で Spearman・次元・スモールワールドは不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | rank/反鎖/interval 次元/ball 成長を関係行列から測定。答えを書き込まない |

→ 二段とも忠実な **measured**。GREEN。

## claim tier
- **measured**: rank↔時間、空間スライス、有限次元、有向 vs 無向（スモールワールド・サイクル）。
- **interpretive**: 時間と有限次元空間は順序だけから読める；**向き（因果の矢）が時空を作る**。
- **analogy / KNOWN MATCH**: 因果集合理論、Myrheim-Meyer 次元、無向ランダムグラフのスモールワールド崩壊。
- **frontier（本モジュールで GREEN にしない）**: **曲率治癒＝BD 作用降下（H007）／実重み経路積分は多様体を選べない（H008）**
  ——サンドボックス参照が本セッションで未検証のため、検証済み数値がなく**昇格しない**（正直な保留）。

## 床（隠さない・必須）
1. 固定次元 Minkowski sprinkling（多様体を入れて順序を生成）。主張は時間/次元が順序から**回復**される、であって
   多様体を無から導いたのではない。
2. **曲率治癒（BD 作用）と経路積分（多様体選択）は frontier**（未検証・未実装＝正直に保留、`docs/working_ledger/H005_*`）。
3. 「時間/時空/因果の矢」は analogy。**時空を作ったのではない**。

## 再現
```bash
python experiments/e023_causal_action/order_time.py --quick --no-write
python experiments/e023_causal_action/directed_vs_undirected.py --quick --no-write
pytest tests/test_e023.py
```
