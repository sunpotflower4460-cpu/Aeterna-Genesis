# e039 — 分化を「場」から（エージェントなし・French-flag モルフォゲン＋Turing）— AUDIT

```yaml
id: e039
role: E
claim_tier: measured
evidence: "モルフォゲン勾配(拡散+分解)＋一つの閾値則で 3 空間順序ドメイン(French flag)／Gierer-Meinhardt が一様+ノイズから対称性を破りパターン自己組織(活性化因子 std 0.02→1.19)"
target_encoded: false
known_match: "Wolpert French-flag 位置情報／Turing・Gierer-Meinhardt 反応拡散パターン"
open_issues: ["閾値 th1/th2 はモデル選択(床)", "「分化/同じゲノム」は場の fate の analogy"]
```

> **場化 wave2（H019 深化・e033 分業の続き）**。遺伝的に**同一の細胞**（一つの則＝同じゲノム）が空間で
> **異なる特化型**になる仕組みを、エージェントなしの純粋な場から。(1) モルフォゲン勾配＋一つの閾値則
> （Wolpert French flag）、(2) Turing（Gierer-Meinhardt）不安定性で一様+ノイズからパターン自己組織。role E。

## 入れたもの（PUT IN）
- (1) モルフォゲン M：局在源＋拡散分解 ∂M/∂t = D∇²M − kM、**全細胞に同一の閾値則** fate=f(M)。
- (2) 活性化-抑制系 ∂a/∂t = Da∇²a + a²/h − μₐa + ρ、∂h/∂t = Dh∇²h + a² − μ_h h、一様+微小ノイズから。
- 「3 順序ドメイン」「パターンが出る」は**入れていない**——測定。

## 測定（`results/differentiation.json`、full）
| 機構 | 出たもの |
|---|---|
| French flag | fate ドメイン（勾配沿い）= [23,34,63]、**空間順序 A→B→C = True**（源で type0→勾配下降で type1→type2） |
| Turing | 活性化因子 std **0.021→1.186**（一様→自己組織パターン）、高活性 fraction 0.252（自発的二型分化） |

GREEN gates: `french_flag_three_ordered_domains`（3 非空・順序）／
`turing_symmetry_breaks_from_uniform`（std 0.02→>0.5）／
`turing_two_type_differentiation`（高活性 fraction 0.1–0.5）。

**罠**: 閾値則は**全細胞同一**（一つのゲノム）。ドメインの**順序は入れていない**（単調な創発勾配から従う）。
Turing パターンは**入れていない**（一様状態から自己組織）。順序と std の**増大**でゲート。閾値値はモデル選択（床）。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「順序ドメイン」「パターン」を書いていない。場の法則と一つの閾値則のみ |
| 2 | 忠実な物理? | **Yes** | Wolpert 位置情報・Turing/Gierer-Meinhardt＝established |
| 3 | 結果は初期条件に? | **No** | 一様+ノイズ／源のみ。勾配・順序・パターンは後から |
| 4 | 入れてない物が出る? | **Yes** | 指数勾配・ドメイン順序・Turing 波長（どれも入れていない） |
| 5 | 数で合う? | **Yes** | 3 順序ドメイン・std 0.02→1.19 |
| 6 | 頑健? | **Yes** | 分解 k・seed を変えても 3 順序＋パターン（`robustness.json`） |
| 7 | コードが発見? | **Yes** | ドメイン順序・std を測定。結果を書き込まない |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 順序は単調勾配から創発、パターンは一様から自己組織。閾値のみモデル選択 |

## claim tier
- **measured**: 3 順序ドメイン、Turing std 増大、二型分化。
- **interpretive**: 位置情報と自己組織が同一細胞を分化させる。
- **analogy / KNOWN MATCH**: Wolpert French-flag／Turing・Gierer-Meinhardt。

## 床（隠さない）
1. 「分化/同じゲノム/細胞型」は場の fate の analogy。閾値 th1/th2 はモデル選択。
2. **同じ数学≠同じもの**：生物発生＝この PDE とは主張しない。同じ事実がエージェントなしの場から出る。
3. **(A) 忠実**：場の法則は手入力。

## 再現
```bash
python experiments/e039_field_differentiation/differentiation.py --quick --no-write
pytest tests/test_e039.py
```
