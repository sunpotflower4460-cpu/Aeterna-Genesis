# e027 — 進化と大転移（ダーウィン的ループ・複雑性の上昇・協力の高次個体）— AUDIT

> 器の弧の最後。**エージェントモデル（場でない＝床）**で、継承＋突然変異＋選択が
> **適応・多様化・追跡（Stage1）／複雑性の上昇（Stage2）／協力＝高次個体（Stage3）**を出すかを測る。
> 三段とも GREEN。ゲート名は**測定量**（平均形質・std・ゲノム長・協力率・assortment）——
> 「進化・複雑性・協力・大転移」は analogy として docstring・本 AUDIT に置く。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 evolution（`results/evolution.json`）— ダーウィン的ループ
| 量 | quick 再現 | 正典（eevolution.py） |
|---|---|---|
| 適応：突然変異 ON / OFF の平均形質 | **1.51 / 0.00** | 1.51 / 0.00 |
| 多様化：負の頻度依存の std | **>0.5**（quick 4.9） | 7.69 |
| レッドクイーン：移動最適の追跡遅れ | **0.07** | 0.07 |

GREEN gates: `mutation_enables_adaptation` / `negative_freq_dependence_maintains_diversity` / `moving_optimum_tracked`。

### Stage2 openended（`results/openended.json`）— 複雑性の上昇
| 環境 | 平均ゲノム長（quick） | 正典（eopenended.py） |
|---|---|---|
| 単純（2 課題） | **1.4** | 1.4 |
| 豊か（8 課題） | **5.8** | 6.0 |
| 需要増（2→10） | **6.1** | 6.5 |

GREEN gates: `simple_env_plateaus` / `demand_raises_complexity` / `rising_demand_keeps_rising`。
**材料＝拡張可能ゲノム（遺伝子重複）＋需要**。

### Stage3 transition（`results/transition.json`）— 協力＝高次個体
| 量 | quick 再現 | 正典（emajor.py, b=1.4） |
|---|---|---|
| よく混ぜた協力率 | **0.00** | 0.00 |
| 空間協力率 | **0.77** | 0.73 |
| assortment | **+0.11** | +0.13 |
| b 掃引（空間） | b≥1.7 で崩壊 | b≥1.7 で崩壊 |

GREEN gates: `well_mixed_cooperation_collapses` / `spatial_cooperation_survives` / `cooperators_cluster`。
**罠**: 誘惑 b は**生存域**（b≈1.4 で生存、b≥1.7 で崩壊）。域外の b は転移を偽装/隠蔽する。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 適応/多様化/複雑性上昇/協力生存を書いていない。適応度・課題・利得則のみ |
| 2 | 忠実な物理? | **Yes** | Wright-Fisher・頻度依存・遺伝子重複・Nowak-May 空間ゲームは実在（established） |
| 3 | 結果は初期条件に? | **No** | 単一形質/単一ゲノム/半々から出発。統計は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 多様化（1→20帯）、複雑性上昇、空間協力の生存（入れていない） |
| 5 | 数で合う? | **Yes** | 正典値を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed 掃引でゲート符号は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 平均形質/std/ゲノム長/協力率/assortment を測定。結果を書き込まない |

→ 三段とも忠実な **measured（＋established の統合）**。GREEN。

## claim tier
- **measured**: 全 GREEN ゲート（適応・多様化・追跡・複雑性上昇・協力生存・クラスタ）。
- **interpretive**: ダーウィン的ループが閉じる；複雑性の材料＝拡張ゲノム＋需要；高次個体＝空間 assortment で束ねた協力。
- **analogy / KNOWN MATCH**: Wright-Fisher/頻度依存/遺伝子重複/Nowak-May/多層選択/Hamilton 則。

## 床（隠さない・必須）
1. **エージェントモデル（場でない）**。固定 1D 形質空間（Stage1）は適応・多様化するが**新しい構造次元は出ない**。
2. Stage2 の需要は**外部設定**（上昇は課された需要に「合わせる」）。**真のオープンエンド性＝需要が内生的に上がり続ける
   （共進化/ニッチ構築）は frontier**。ゲノム長は複雑性の代理。
3. Stage3 は協力の**安定化（必要条件）**であって完全な大転移でない。**群れの再生産・分業・対立抑制（ボトルネック/警察）は frontier**。
4. 「進化・複雑性・協力・大転移・高次個体」は analogy。**生物・社会を作ったのではない**。

## 再現
```bash
python experiments/e027_evolution_transition/evolution.py --quick --no-write
python experiments/e027_evolution_transition/openended.py --quick --no-write
python experiments/e027_evolution_transition/transition.py --quick --no-write
pytest tests/test_e027.py
```
