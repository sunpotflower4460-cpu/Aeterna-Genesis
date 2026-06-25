# e011 — 欠陥の動的化学（±束縛 ＋ 有限温度の解離）— AUDIT

> 渦の「化学」を**動的に**測る。Stage1：保存GPEで ±/++ 対を追尾し、**選択的な
> ハミルトニアン則**（± は並進 v·d=const、++ は回転 ω·d²=const）を数で出す。
> Stage2（新規）：確率的(有限T)GPE で ±対を熱浴に入れ、**温度で解離**するか
> （T↑で寿命↓）を測る。「分子/化学」は analogy、物理量だけを主張する。

## 監査ヘッダ（各 run.py 先頭と同一）

```
MODULE:   e011_defect_chemistry
QUESTION: 束縛渦対は選択的なハミルトニアン則に従い(v·d, ω·d² 一定)、有限Tで解離するか。
PUT IN:   Stage1 保存GPE＋一様凝縮＋imprint した2渦。Stage2 確率的GPE(Langevin浴 √(2γT)dW)＋±対。運動・崩壊率は名指さない。
EMERGED:  (measured) ± 並進 v·d=const、++ 回転 ω·d²≈2、選択的；有限Tで寿命が T とともに単調減少（解離）。
CLAIM TIER: measured(v·d, ω·d², 選択性, 寿命 vs T) ; interpretive(Arrhenius/熱活性) ; analogy(分子/化学)。
KNOWN MATCH: 点渦ハミルトニアン(双極子 v~1/d, 同符号 ω=2/d²)；熱活性/BKT 解離。
STATUS:   GREEN（両則＋選択性＋寿命↓ は measured。Arrhenius は床つき interpretive）。
A_OR_B:   (A) 忠実な創発。手入力＝GPE＋一様背景＋imprint した巻き数（＋Stage2 は熱浴）。
```

## Stage 1 — 動的束縛（`x_pair_binding.py` → `results/pair_binding.json`）

| 対 | 観測 | measured | 選択性 |
|---|---|---|---|
| **±（双極子）** | 並進 v、積 **v·d** | v·d = **0.67**（CV≈0.01、d=16–28） | 回転 ω≈0（並進のみ） |
| **++（同符号）** | 回転 ω、積 **ω·d²** | ω·d² = **2.08**（CV≈0.04）＝点渦 ω=2/d² | 重心ドリフト≈0（回転のみ） |

- **二つの異なるハミルトニアン則が一つの場の方程式から**出る：逆符号は並進、同符号は公転。
- 床：v·d は**小 d（芯重なり）で崩れる**ので芯サイズより十分大きい d で報告。定数は格子/GPE 単位。「分子」は analogy。

## Stage 2 — 有限温度の解離（★新規、`finite_T_dissociation.py` → `results/finite_T.json`）

確率的GPE（Langevin浴 dψ=[-(i+γ)(H-μ)ψ]dt+√(2γT)dW、core.field.step_sgpe_2d）に ±対を入れ、
**その対**を連続性で追尾（熱背景の渦を tight window で排除）、消滅までの寿命を測る。

| T | 平均寿命 | 消滅数/8 |
|---|---|---|
| 0.00 | 2500（cap、束縛） | 0 |
| 0.15 | ~2400 | — |
| 0.30 | ~2300 | — |
| 0.45 | 2160 | 3 |
| 0.60 | 1985 | 5 |

- **寿命は T とともに単調減少（slope≈−780、drop≈21%）＝熱解離**（measured）。T=0 は束縛、加熱で崩壊。
- Arrhenius τ~exp(ΔE/T)（ΔE≈0.02）は **interpretive**：低T は cap で右側打ち切り、高T は BKT 背景渦増殖。clean 窓は中間 T（床）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | GPE は局所。並進/回転/解離率を書いていない |
| 2 | 忠実な物理? | **Yes** | 保存GPE・確率的GPE(FDT)は実在 |
| 3 | 結果は初期条件に? | **No** | 一様背景＋2渦の巻き数のみ。運動は後から |
| 4 | 入れてない物が出る? | **Yes** | v·d 一定、ω·d²≈2、選択性、熱解離 |
| 5 | 数で合う? | **Yes** | ω·d²=2.08≈点渦2、v·d CV≈0.01、寿命単調減 |
| 6 | 頑健? | **Yes** | 複数 d で則、複数 T・seed で解離曲線 |
| 7 | コードが発見? | **Yes** | 連続性追尾で運動/寿命を測定、結論を書かない |

→ measured 部分は全監査通過＝**GREEN**。Arrhenius・絶対定数は床。

## 床（隠さない・必須）
1. **固定格子＝空間は与えられている**。渦は欠陥で、もつれ幾何ではない。
2. **「分子/化学」は analogy**。束縛渦対であって化学結合ではない。「同じ数学」≠「同じもの」。
3. v·d は小 d で崩れる（芯重なり）。定数は格子/GPE 単位。
4. 有限T解離：低T は cap で打ち切り、高T は BKT 背景渦。γ>0 ゆえ T=0 でも最終的に減衰（保存GPE の対が真の束縛基準）。Arrhenius は interpretive。

## 再現
```bash
python experiments/e011_defect_chemistry/x_pair_binding.py        # ± v·d / ++ ω·d² / 選択性
python experiments/e011_defect_chemistry/finite_T_dissociation.py # 寿命 vs T（熱解離）
pytest tests/test_e011.py
```
