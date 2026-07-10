# e030 — 分業（凸な適応度リターンが germ-soma 分化を生むか）— AUDIT

> **FRONTIER**（H017 続き）。e029 の大転移は協力を救ったが**分業がなかった**。細胞群が生殖（germ）と
> 生存（soma）に**特化**するのはいつか。Michod/Rueffler：**リターン曲線が凸（加速的）なら特化が有利**。
> 分業則を書かず、リターン形状 a のみ設定して配分分布を測る。GREEN。ゲート名は物理量（配分分布）。
> 「germ/soma/分業/多細胞性」は analogy。

## 測定（`--quick`／`results/division_of_labor.json`）
| リターン凸性 a | specialist 率（x<0.2 or >0.8） | 両役を持つ群（純 germ かつ 純 soma） |
|---|---|---|
| 0.5（凹） | 0.255 | 0.818 |
| 1.0（線形） | 0.453 | 0.99 |
| 2.0（凸） | 0.761 | 1.00 |
| 3.0 | 0.805 | 1.00 |
| 4.0（強凸） | **0.853** | **1.00** |

> **注（第1層で訂正）**：旧表は前バージョンの run 値（0.29/0.87…）で `results/division_of_labor.json`
> と不一致だった。上表は committed JSON に一致させた。
> **注（第8監査で要対応）**：`両役 both_roles` は **線形(a=1.0)で 0.99・凹(a=0.5)でも 0.818** と高く、
> 凸性を**区別できていない**（弱いゲート）。**判別力は specialist 率**（0.255→0.853 で単調）にある。
> `germ_soma_differentiation` ゲートは §2/§4 で「凸 vs 凹の CONTRAST」へ強化する（`target_encoded` 予防）。

GREEN gates: `convex_returns_drive_specialization`（凸で specialist>0.6）／
`specialization_rises_with_convexity`（凸 > 1.5×凹・単調）／`germ_soma_differentiation`（凸で両役群>0.9）。
**測定の宝**: 群れ適応度＝mean(repro)×mean(viab)（両機能が必要）で、**リターンの凸性だけ**から
**世代群が bimodal な germ/soma に分化**する（分化を手で入れていない）。

**罠**: 群れ適応度は二機能の**積**——生殖だけ／生存だけの群は死ぬ＝両役が必要。特化は凸性のみが駆動。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「特化せよ」を書いていない。リターン形状 a と群れ適応度のみ |
| 2 | 忠実な理論? | **Yes** | Michod 適応度凸性理論・Rueffler 分業進化は established |
| 3 | 結果は初期条件に? | **No** | 全 generalist(x=0.5)近傍から出発。bimodal 分化は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 凸リターンだけから germ/soma 分化（入れていない） |
| 5 | 数で合う? | **Yes** | 理論の向き（凸→特化）と一致、単調 |
| 6 | 頑健? | **Yes** | seed・群れ幾何（G,n）を変えても凸で強い特化（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 配分分布の bimodality/両役共存を測定。分化を書き込まない |

## claim tier
- **measured**: specialist 率の凸性依存・単調、強凸での germ-soma 普遍共存。
- **interpretive**: 分業は**凸な適応度リターン**から創発＝大転移に欠けていた最後の一片（分業）。
- **analogy / KNOWN MATCH**: Michod 適応度凸性、Rueffler 分業進化、Volvox の germ-soma 分化。
- **FRONTIER**: トイモデル。実細胞・生物を分化させたのではない。

## 床（隠さない・必須）
1. **FRONTIER**：有界トイ。「germ-soma/分業/多細胞性」は analogy（配分の bimodality）。
2. 凹リターンでも drift で多少の spread が残る（純 generalist にならない）＝robust なのは**凸 vs 凹の対比**と単調上昇。
3. 実際の細胞・生物を分化させたのではない——measured は配分分布のみ。

## 再現
```bash
python experiments/e030_division_of_labor/division_of_labor.py --quick --no-write
pytest tests/test_e030.py
```
