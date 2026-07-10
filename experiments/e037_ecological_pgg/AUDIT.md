# e037 — 生態的 PGG：純 PDE で持続する協力（エージェントなし）— AUDIT

```yaml
id: e037
role: E
claim_tier: measured
evidence: "密度依存(生態的)payoff で協力が純 PDE で持続(frac~0.46)／古典 定コスト は崩壊(~0.00)／質量整合 well-mixed も持続=機構は生態的フィードバック(空間の離散性でない)"
target_encoded: false
known_match: "Hauert-Holmes-Doebeli / Wakano-Nowak-Hauert 生態的公共財ゲーム"
open_issues: ["「協力/公共財」は共存する密度場の analogy", "古典(固定人口)PGG は依然 離散性/network reciprocity が要る", "(A) 忠実：個体群 PDE は手入力"]
```

> **§7（Claude 参照サンドボックス `eco_pgg_pde.py`/`eco_rps.py`）**。e027/e034 は協力をエージェント格子／
> 双安定フロントで扱った。ここでは**生態的公共財ゲーム**（密度依存 payoff）から、エージェントも空間の離散性も
> なしで**純連続 PDE で協力が持続**するか、そして**機構が生態的フィードバックか（空間でなく）**を測る。role E。

## 入れたもの（PUT IN）
- 二つの個体群密度場 u（協力者）・v（裏切り者）、周期格子。空きへの誕生 × 生態的 payoff：
  **P_C − P_D = c(r·A(ρ) − 1)**、A(ρ)=(1−(1−ρ)^N)/(Nρ)＝**低密度で協力者有利**。拡散＋共通死亡率。
- **古典 定コスト**（P_C−P_D=−c、常に裏切り有利）を対照に。well-mixed＝同じ反応の∇²除去版。
- 「協力が持続する」は**入れていない**——測定。

## 測定（`results/ecological_pgg.json`、quick）
| 条件 | 協力率 | 判定 |
|---|---|---|
| 生態的（空間 PDE） | **0.465**（密度 0.136） | 持続 |
| 古典 定コスト（空間 PDE） | **0.000** | 崩壊 |
| 生態的（**質量整合 well-mixed**、∇²なし） | **0.465** | 持続＝**機構は生態的フィードバック（空間でない）** |

GREEN gates: `ecological_cooperation_persists_in_pure_PDE`（frac>0.3・密度>0.05）／
`classical_constant_cost_collapses`（frac<0.1）／
`mechanism_is_feedback_not_space`（質量整合 well-mixed も frac>0.3）。

**罠**: 以前の失敗は**誤った定コスト payoff**（P_C−P_D=−c、裏切り常勝）で「純 PDE 協力は不可能」と結論した。
正しい生態的 payoff（Hauert-Holmes-Doebeli）を入れ、持続を測定。**対比（生態 vs 古典）＋質量整合 well-mixed の
持続**でゲート＝主張は**機構**であってチューニング数値でない。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | payoff 形（生態/古典）と個体群則のみ。「持続」を書いていない |
| 2 | 忠実な物理? | **Yes** | Hauert-Holmes-Doebeli 生態的公共財＝established |
| 3 | 結果は初期条件に? | **No** | 一様＋ノイズ。持続/崩壊は後から |
| 4 | 入れてない物が出る? | **Yes** | 生態的持続・古典崩壊・well-mixed 持続（どれも入れていない） |
| 5 | 数で合う? | **Yes** | 生態 0.46 持続 vs 古典 0.00 崩壊、well-mixed 0.46 |
| 6 | 頑健? | **Yes** | r・死亡率を変えても生態持続/古典崩壊（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 協力率を測定。結果を書き込まない |
| **8** | ゲート/初期条件が結論を符号化? | **No（target_encoded=false）** | payoff は既知式、持続は測定。対比＋well-mixed で機構を分離 |

## claim tier
- **measured**: 生態持続 vs 古典崩壊、質量整合 well-mixed 持続。
- **interpretive**: 生態的フィードバック（低密度で協力者有利）が**連続体で協力を持続**させる＝(A) 境界の精緻化
  （古典 PGG は離散性が要る、生態的 PGG は要らない）。
- **analogy / KNOWN MATCH**: Hauert-Holmes-Doebeli / Wakano-Nowak-Hauert 生態的公共財。

## 床（隠さない）
1. 「協力/公共財」は共存する密度場の analogy。**同じ数学≠同じもの**——社会的協力＝この PDE とは主張しない。
2. 古典（固定人口）公共財は依然 離散性/network reciprocity が要る。連続体で持続するのは**生態的**版のみ。
3. **(A) 忠実**：個体群 PDE は手入力（根から導いていない）。
4. **協力率は死亡率に依存**（床）：低い死亡率→高密度→A(ρ) 小→協力者優位が縮小→協力率低下
   （death=1.0 で 0.276、1.2 で 0.465）。**十分低い死亡率では崩壊境界へ**。robustness は persist（>0.2、
   古典の 0.0 崩壊より明確に上）でゲート＝死亡率域をチェリーピックしない（第8監査）。持続は定性的に頑健。

## 再現
```bash
python experiments/e037_ecological_pgg/ecological_pgg.py --quick --no-write
pytest tests/test_e037.py
```
