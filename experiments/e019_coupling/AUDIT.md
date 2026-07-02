# e019 — 循環 × 粒子の結合（輸送＋U_c／三体フル結合）— AUDIT

> 器の循環が粒子を運び、「第三」が循環のシアに抗して**同一性（Q_H）を U_c まで保つ**（超えると
> 引き裂かれる）。Stage2 は**三体フル結合**（代謝＋自己組織した流れ＋粒子を一つのループに双方向
> 結合）＝本ミッション最重要。「粒子/同一性/ホメオスタシス」は analogy/interpretive。

## 監査ヘッダ（coupling.py / three_body.py 先頭と同一）

```
Stage1: MODULE e019_coupling (transport + U_c)
  QUESTION 規定循環は粒子を運び、第三は Q_H を U_c まで保つか。
  EMERGED (measured) centroid が U で単調移動；Q_H は U_c まで保持、超えると引き裂かれ Q_H→0・size 発散。
  CLAIM measured(centroid(U)・Q_H(U)・U_c) ; interpretive(第三がシアに抗う) ; analogy(粒子/同一性)。
  A_OR_B (A) 忠実。手入力＝ホップ粒子＋エネルギー＋流れ＋規定 roll、移動と引き裂きは創発。
Stage2: MODULE e019_coupling (three-body coupling)
  QUESTION 代謝<->流れ<->粒子の閉ループで、背反応が流れを自己制限（ホメオスタシス）し、駆動を切ると三体が止まるか。
  EMERGED (measured) 双方向は自己制限で粒子保持／一方向は過駆動で崩壊／駆動オフで流れ停止。
STATUS GREEN（輸送＋保持→引き裂きの U_c／自己制限 vs 一方向／駆動オフ停止が measured；規定 roll・振幅還元流は床）。
```

## Stage 1 — 輸送＋U_c（`coupling.py` → `results/coupling.json`）

安定化ホップ粒子を settle 後、局在 roll（x-z 面の渦）で**純移流**（移流中は緩和しない）。
成分場（3,L,L,L）の勾配は**空間3軸**で（罠回避：4D/成分軸を使わない）、centroid は勾配エネルギー密度重み。

| U | Q_H | centroid 変位 | size | 判定 |
|---|---|---|---|---|
| 0 | 1.00 | 0.00 | ~4.1 | 保持（動かない） |
| 2 | ~1.0 | 0.75 | ~4.4 | 保持・運ばれる |
| 4 | ~1.0 | 1.17 | ~4.7 | 保持・運ばれる |
| 6 | ~0.9 | 1.49 | ~5.0 | 保持 |
| 8 | ~0.6 | 1.75 | ~5.2 | （劣化） |
| 11 | ~0.05 | 2.21 | ~5.7 | **引き裂き（Q_H→0, size 発散）** |

- **循環が粒子を運ぶ**：centroid 変位が U とともに単調増（0→2.2）— measured。
- **第三が同一性を U_c まで保つ**：Q_H は U_c≈7 まで保持、超えると引き裂かれ Q_H→0・size 発散
  — measured。（罠 b 回避：成分場勾配を空間軸で、AxisError/誤重心を避ける。）

## Stage 2 — 三体フル結合（`three_body.py` → `results/three_body.json`、★本丸）

代謝 b・流れ振幅 U・実 3D ホップ粒子 n を**双方向**に結合：
`db/dt=s(1−b)−kU·U·b`（駆動が代謝供給、流れが消費）、
`dU/dt=gU·b−dampU·U−drag·P(n)`（代謝が流れを駆動・減衰・**粒子コヒーレンス P が抗力＝背反応**）、
n は振幅 U(t) の roll で移流＋安定化。

- **双方向（drag>0）**：背反応が流れを**自己制限**（U を 3.6 に抑え）粒子を保持（Q_H=0.97）＝創発的な
  負のフィードバック（ホメオスタシス）。一方向では出ない。
- **一方向（drag=0）**：背反応なし→同じ代謝が U を 8.3 まで過駆動→**粒子崩壊（Q_H=−0.36）**。
  **背反応が粒子を救う＝差が結合そのもの**（backreaction_matters=True）。
- **駆動オフ（s=0）**：b→0→U→0→流れ停止→輸送停止（三体が一蓮托生）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 局所則＋規定 roll のみ。移動/引き裂き/自己制限を書いていない |
| 2 | 忠実な物理? | **Yes** | Faddeev-Skyrme・移流・結合速度論は実在 |
| 3 | 結果は初期条件に? | **No** | settle 後に流れを掛ける。移動/崩壊は後から |
| 4 | 入れてない物が出る? | **Yes** | U_c 閾値・背反応の自己制限 |
| 5 | 数で合う? | **Yes** | centroid(U) 単調、U_c≈7、two-way vs one-way vs no-drive |
| 6 | 頑健? | **Yes** | c4・roll_R で（robustness.json） |
| 7 | コードが発見? | **Yes** | Q_H は B=curl A、U/b は ODE、自己制限は入れない |

→ measured 部分は全監査通過＝**GREEN**。「粒子/同一性/ホメオスタシス」は analogy/interpretive。

## 床（隠さない・必須）
1. **流れは規定 roll**（Stage1）／**振幅還元モデル**（Stage2、完全 Navier-Stokes でない）、roll 形は規定。
2. **U_c は crossover**（鋭い普遍閾値でない）、引き裂きは高シアで格子下スケールが立つ解像度効果。
3. 粒子は実 3D だが箱は小・固定格子。「粒子/同一性/ホメオスタシス/一蓮托生」は analogy/interpretive、生命ではない。

## 再現
```bash
python experiments/e019_coupling/coupling.py     # 輸送＋U_c
python experiments/e019_coupling/three_body.py   # 三体フル結合（★本丸）
python experiments/e019_coupling/robustness.py
pytest tests/test_e019.py
```
