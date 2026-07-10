# e043 — ONE 反応拡散場に多数の生命過程が同時共起（分化した体が自己組織）— AUDIT

```yaml
id: e043
role: E
claim_tier: measured
evidence: "一様な低形質シートから、自己複製 GS スポットが分裂して場を満たし(occupied~0.4)、成長端で per-tissue 形質を継承+変異し、空間変化するモルフォゲン最適点へ選択され、順序ある空間形質ドメインに自己組織(corr~0.8、left~0.2→right~0.8)＝分裂+継承+変異+選択+適応+分化が ONE 場で同時"
target_encoded: false
known_match: "Gray-Scott 自己複製／Wolpert 位置情報／e038(object tracking)+e039(morphogen) の統合"
open_issues: ["HYBRID: 動力学は純 GS 場だが形質は追跡 per-TISSUE ラベル／モルフォゲン最適点 tau*(x) は入力(環境)、分化した体は創発", "「体/発生/進化」は形質場の analogy"]
```

> **場化 wave2 capstone（統合）**。e038（連続形質進化）と e039（分化）を **ONE 場** に統合。一様シートから
> 分化した局所適応の体が自己組織するか。role E（hybrid）。

## 測定（`results/universe.json`、full）
- **分裂**：occupied ~0.4（自己複製スポットが場を満たす）。
- **適応**：corr(形質, 局所最適点) ~0.8（一様 τ=0.5 から）。
- **分化**：body left ~0.2 → mid ~0.5 → right ~0.8（順序ドメイン、contrast ~0.47）。

GREEN gates: `division_fills_field`（occupied>0.25）／`cells_adapt_to_local_optimum`（corr>0.6）／
`ordered_spatial_trait_domains`（left<mid<right・contrast>0.3）。

**罠**: モルフォゲン最適点は入れた**環境**。測定した非自明は、de novo 変異+局所選択が一様シートを実際に
そこへ**駆動**し（corr>0.6）順序ドメインに割れること（選択は失敗しうる）。e038 の moving-optimum lag と同型。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「空間ドメイン」「最適点一致」を書いていない |
| 2 | 忠実な物理? | **Yes** | Gray-Scott 自己複製＝established |
| 3 | 結果は初期条件に? | **No** | 一様 τ=0.5 から。ドメインは後から創発 |
| 4 | 入れてない物が出る? | **Yes** | 適応した分化ボディ（入れていない） |
| 5 | 数で合う? | **Yes** | corr~0.8、contrast~0.47 |
| 6 | 頑健? | **Yes** | seed を変えても分化ボディ成立（`robustness.json`） |
| 7 | コードが発見? | **Yes** | occupied・corr・ドメインを測定 |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 最適点は環境。適応・分化は創発。e038/e039 と同じ扱い |

## 床（隠さない）
1. **HYBRID**：純 GS 動力学だが形質は追跡 per-TISSUE ラベル。モルフォゲン最適点は入力（環境）、分化ボディは創発。
2. 「体/発生/進化」は analogy。**同じ数学≠同じもの**。e038（object tracking）+e039（morphogen）の**統合**であり
   新機構の追加ではない——それらが ONE 場で同時共起することを示す。

## 再現
```bash
python experiments/e043_field_universe/universe.py --quick --no-write
pytest tests/test_e043.py
```
