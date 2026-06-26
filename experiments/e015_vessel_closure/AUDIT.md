# e015 — 器の閉じ（開-閉の二重性、駆動依存）— AUDIT

> 器は**開（駆動・throughflow）かつ閉（自己維持）**の散逸構造か、駆動を切ると閉じが崩れて
> 死ぬか。Stage1：Gray-Scott 自己複製スポットで **駆動あり→自己維持・自己修復（切除→再生）・
> 増殖／駆動を切る（F→0）→溶けて死（総 v→0）**。Stage2：膜 M＋代謝 A の相互生産（最小モデル）で
> **どちらの腕を切っても死**（オートポイエーシスの両腕）。「器/閉じ/死/生命」は interpretive・analogy。

## 監査ヘッダ（vessel_closure.py 先頭と同一）

```
MODULE:   e015_vessel_closure
QUESTION: 器は開(駆動)かつ閉(自己維持)の散逸構造で、駆動を切ると閉じが崩れて死ぬか。
PUT IN:   Gray-Scott RD + 供給率 F(throughflow)。「F を切ると死」は入れない。
EMERGED:  (measured) 駆動下で自己維持・自己修復・増殖；F→0 で総 v→0(死)；生存の臨界 F。
CLAIM TIER: measured(persist/collapse, heal, drive-dependence) ; interpretive(開-閉の二重性) ; analogy(autopoiesis)。
KNOWN MATCH: Gray-Scott(Pearson); 散逸構造(Prigogine); autopoiesis(Maturana-Varela)。
STATUS:   GREEN（駆動依存＋自己修復＋両腕が measured。「器/閉じ/死/生命」は analogy）。
A_OR_B:   (A) 忠実。手入力＝Gray-Scott RD＋throughflow F；開-閉の振る舞いは創発。
```

## Stage 1 — 駆動依存（`vessel_closure.py` → `result.json`、L=96, mitosis F=0.0367 k=0.0649）

- **駆動下で自己維持・増殖**：総 v が成長（mitosis）、生存面積 ~0.21 — measured。
- **駆動を切る（F→0）→ 総 v→0（死）** — measured。閉じは throughflow が無いと維持できない。
- **自己修復**：半分切除（総 v を半減）→ 駆動下で**ほぼ完全再生**（~98%） — measured。
- **生存の臨界 F**：F スイープで生存窓 F∈[~0.03, ~0.07]、F が小さすぎ/大きすぎると死 — measured。

## Stage 2 — 両腕オートポイエーシス（`autopoiesis.py` → `autopoiesis.json`、膜 M＋代謝 A）

相互生産：`dM/dt=αA(1−M)−βM`（代謝が膜を作る）、`dA/dt=γM(1−A)S−δA`（膜＋基質が代謝を支える）。

| 操作 | M, A | 判定 |
|---|---|---|
| 健全＋駆動 | (0.80, 0.80) | **生存** |
| **膜を壊す**（γ→0） | (0.004, 0.000) | **死**（共倒れ、両腕＜0.05） |
| **代謝を止める**（α→0） | (0.000, 0.003) | **死**（共倒れ、両腕＜0.05） |

> 注：切った腕がまず崩れ、もう一方も支え/作り手を失って共倒れ（full run の終端値）。quick や cut が遅いと残存腕が ~0.08 までしか落ちない（時間不足）が、判定は「両腕とも生存閾値 0.05 未満＝死」で行う。

- **どちらの腕を切っても死**（膜を壊す→代謝が支えを失う→共倒れ／代謝を止める→膜が作り手を失う→共倒れ）— measured。
- **生存の臨界駆動 S_c**：S スイープで S<S_c（≈0.05）は死、S>S_c は生存 — measured。
- → 閉じは**両腕の相互生産ループ全体**であって、片方だけでは生きた単位にならない。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | Gray-Scott／相互生産は局所。「死ね」を書いていない |
| 2 | 忠実な物理? | **Yes** | Gray-Scott RD・相互触媒は実在の散逸系 |
| 3 | 結果は初期条件に? | **No** | 種一つ／M=A=0.5。維持・死は後から |
| 4 | 入れてない物が出る? | **Yes** | 自己維持・自己修復・F→0 で死・両腕の必要性 |
| 5 | 数で合う? | **Yes** | 総 v 成長→0、再生 ~98%、生存窓、両腕とも死、臨界 S |
| 6 | 頑健? | **Yes** | F スイープ・S スイープ・両腕で |
| 7 | コードが発見? | **Yes** | 死は駆動/腕を切ると創発、死則は書かない |

→ measured 部分は全監査通過＝**GREEN**。「器/閉じ/死/生命」は analogy。

## 床（隠さない・必須）
1. **固定格子＝空間は与えられている**。
2. **Gray-Scott は既知 RD**。「器/閉じ/死/生命」は interpretive・analogy。パターンで単一細胞ではない。
3. Stage2 は**最小の動力学モデル**（空間的な膜ではない）。「膜/代謝/生命」は analogy。
4. **生命を作ったとは言わない**。「同じ数学」≠「同じもの」。

## 再現
```bash
python experiments/e015_vessel_closure/vessel_closure.py  # 駆動依存・自己修復・臨界F
python experiments/e015_vessel_closure/autopoiesis.py     # 両腕（どちらを切っても死）
pytest tests/test_e015.py
```
