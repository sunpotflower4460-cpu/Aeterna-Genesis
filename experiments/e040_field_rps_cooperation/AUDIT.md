# e040 — 協力＝持続スパイラル波（純 PDE・C-D-L 循環優位・エージェントなし）— AUDIT

```yaml
id: e040
role: E
claim_tier: measured
evidence: "拡散ありの C-D-L 循環優位(RPS)反応拡散がスパイラル波に自己組織し三者(協力者含む)が持続(C~0.31,D~0.29,L~0.26)／well-mixed 対照はヘテロクリニックに一種へ崩壊"
target_encoded: false
known_match: "循環 Lotka-Volterra / May-Leonard／Reichenbach-Mobilia-Frey スパイラル波"
open_issues: ["C-D-L 循環構造は loner-PGG を汎用循環競争として抽象(analogy)／spiral 形成は regime 依存・確率的(少数 seed は崩壊)＝床"]
```

> **場化 wave2（e037 の別ルート）**。D>C, C>L, L>D（RPS）で、空間循環 Lotka-Volterra が**スパイラル波**に
> 自己組織し協力者が持続するか、well-mixed は崩壊するか。role E。

## 測定（`results/rps_cooperation.json`、full）
- **空間**：C=0.306, D=0.294, L=0.261（三者持続）、協力 std 0.347（スパイラル）。
- **well-mixed 対照**：一種が優占（例 D=1.0）、他は ~絶滅（ヘテロクリニック崩壊）。

GREEN gates: `cooperation_persists_as_spirals`／`spatial_spiral_pattern`（協力 std>0.03）／
`wellmixed_collapses_to_one`（優占>0.8・最小<0.05）。

**罠**: **対比**（空間共存 vs well-mixed 崩壊）でゲート＝空間が協力を維持、と主張。循環構造は入れたが
スパイラル・共存は入れていない。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「スパイラル」「協力持続」を書いていない |
| 2 | 忠実な物理? | **Yes** | 循環 Lotka-Volterra/May-Leonard＝established |
| 3 | 結果は初期条件に? | **No** | 一様+ノイズ。スパイラルは後から |
| 4 | 入れてない物が出る? | **Yes** | スパイラル波・三者共存（入れていない） |
| 5 | 数で合う? | **Yes** | 三者 0.26–0.31、well-mixed は一種優占 |
| 6 | 頑健? | **Yes（多数）** | N=200/D=0.6 で seed の多数(4/5)がスパイラル、well-mixed は常に崩壊（`robustness.json`）。少数崩壊は床 |
| 7 | コードが発見? | **Yes** | 共存・std・崩壊を測定 |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 対比でゲート。循環構造のみ入力 |

## 床（隠さない）
1. 「協力/RPS」は三密度場の analogy。C-D-L は loner-PGG の汎用循環競争抽象。
2. **spiral 形成は regime 依存・確率的**：N>~180・D<~0.8（過拡散は均質化）が要る。少数 seed は一種へ崩壊
   （有限サイズ双安定）＝床。robust は「多数がスパイラル＋well-mixed は常に崩壊」。
3. **同じ数学≠同じもの**。(A) 忠実：循環 RD 則は手入力。

## 再現
```bash
python experiments/e040_field_rps_cooperation/rps_cooperation.py --quick --no-write
pytest tests/test_e040.py
```
