# e041 — 「一から始まる」＝幾何（物理的ネックが創設者数を決める）— AUDIT

```yaml
id: e041
role: S
claim_tier: measured
evidence: "狭いピンチネックは ~1 創設者を通し娘は clonal(Simpson relatedness→1)／広いネックは多数を通し娘は mixed(→0.001)＝単一細胞ボトルネックはネック幅から創発"
target_encoded: false
known_match: "生殖系列/単一細胞ボトルネック(Grosberg-Strathmann)／Simpson 多様度"
open_issues: ["S: 幾何サンプリング模型(タグ付き体上のネック帯)であり連続場でない＝ピンチを抽象／founder→clonal 再成長は課した／「clonal/relatedness/個体」は analogy"]
```

> **場化 wave2**。大転移（協力・分業）は「一から始まる」＝単一細胞ボトルネックが要る。それは抽象規則か、
> それとも**分裂の幾何**（ピンチネックの**幅**）から創発するか。role **S**（幾何サンプリング模型）。

## 測定（`results/bottleneck.json`、full）
| ネック幅 w | 通過創設者 | relatedness(Simpson) |
|---|---|---|
| 0.0003（狭） | ~1–2 | ~0.8（clonal） |
| … | … | 単調減少 |
| 1.0（広） | 3000 | 0.001（mixed） |

GREEN gates: `narrow_neck_single_founder`（狭で<3）／`narrow_neck_clonal_daughter`（relatedness>0.5）／
`wide_neck_mixed_daughter`（relatedness<0.1・創設者>100）。

**罠**: founder→clonal 再成長は課した。**測定した非自明**は幅→relatedness の**関係**（狭→1、広→0）。
その関係でゲート。role S：幾何/統計の抽象であり忠実な場 PDE でない、と正直に。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「狭→clonal」を書いていない。幅→サンプリングのみ |
| 2 | 忠実な物理? | **一部（幾何）** | ピンチ幾何の抽象。連続場でない＝S |
| 3 | 結果は初期条件に? | **No** | ランダム位置。関係は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 幅→relatedness 曲線・単調性 |
| 5 | 数で合う? | **Yes** | 狭 relatedness~0.8、広 0.001 |
| 6 | 頑健? | **Yes** | 体サイズ・seed を変えても成立（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 幅→relatedness を測定 |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 関係は幾何+統計の帰結で測定。ただし模型は設計＝S |

## 床（隠さない）
1. **S**：幾何サンプリング模型（ネック帯）であり連続場でない。ピンチを抽象、founder→clonal は課した。
2. 「clonal/relatedness/個体」は analogy。**同じ数学≠同じもの**。e026 の巻きピンチと大転移のボトルネックを繋ぐが、
   幾何であって忠実な場でない。

## 再現
```bash
python experiments/e041_field_bottleneck/bottleneck.py --quick --no-write
pytest tests/test_e041.py
