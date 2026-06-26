# e012 — Hopf 安定化＝「第三」（高階微分が崩壊を止める）— AUDIT

> 「打ち消さずトーラスを巡る粒子」(ホップ粒子)は、素では Derrick 崩壊で縮む。
> **高階微分（四次＝「第三」）**がそれを止めるか。Stage1（静的）：Q_H≈1 を構成し
> E2・E4・Hopf 不変量・Derrick 地形（素＝崩壊／第三＝有限 L*）を測る。Stage2（新規・動的）：
> Faddeev-Skyrme 勾配流を回し、**素は崩壊／第三は崩壊に抵抗**を動的に出す。
> 「粒子」は analogy ⸺ 電子を作ったとは言わない。

## 監査ヘッダ（各 run.py 先頭と同一）

```
MODULE:   e012_hopf_stabilization
QUESTION: 高階微分('第三')はホップ粒子を Derrick 崩壊から救い、動的に持続させるか。
PUT IN:   Q_H=1 ホップ粒子場 n:R^3->S^2、Faddeev-Skyrme E=∫[c2(∂n)^2+c4 F^2]。目標サイズは入れない。
EMERGED:  (measured) Q_H≈1(整数)；Derrick(素=崩壊/第三=有限L*)；動的に素は崩壊(e009一致、エネルギー単調減で勾配検算)。(frontier) c4>0 の崩壊抵抗は脆い・完全自己安定化は未達。
CLAIM TIER: measured(Q_H,E2,E4,Derrick L*,動的な素の崩壊,エネルギー単調減) ; frontier-observation(動的な抵抗の頑健性・完全自己安定化) ; analogy(粒子)。
KNOWN MATCH: Derrick 1964; Faddeev-Niemi hopfion; e009(素GPEホップ粒子が縮む)。
STATUS:   GREEN（Q_H 整数＋Derrick＋動的な素の崩壊は measured。動的抵抗は脆く完全安定化は frontier＝解像度/dt の床）。
A_OR_B:   (A) 忠実。手入力＝場の多様体 S^2＋Faddeev-Skyrme エネルギー(＋流れ)。格子(=空間)は与えている。
```

## Stage 1 — 静的（`hopfion_static.py` → `results/hopfion_static.json`、L=96, box=12, dx=0.25）

- **Q_H = 1.00**（Whitehead Q_H=(1/16π²)∫A·B、B=∇×A を FFT で。**滑らかな構成から整数**が出る）— measured。
- **E2 ≈ 715、E4 ≈ 229**（dx=0.25）。
- **Derrick 地形 E(L)=L·E2 + c4·E4/L**：
  | c4 | L* | 判定 |
  |---|---|---|
  | 0 | 0（L→0） | **崩壊** |
  | 1 | 0.565 | 安定 |
  | 4 | 1.130 | 安定 |
  | 9 | 1.696 | 安定 |
  → **素は崩壊・第三(c4>0)で有限 L***。**L*∝√c4**（0.565, 1.130, 1.696＝1:2:3）を厳密に確認 — measured。
- 床：絶対 E2,E4 は解像度(dx)依存。Q_H と Derrick の**形**（崩壊 vs 有限 L*、L*∝√c4）が robust。

## Stage 2 — 動的（★新規、`hopfion_flow.py` → `results/hopfion_flow.json`、L=48）

接線射影つき勾配流 ∂_t n=−P_tangent δE/δn、毎ステップ |n|=1 射影。δE/δn は**エネルギーと
同じ中心差分**で組み（離散 Euler-Lagrange）、**エネルギー単調減少**を健全性チェック（符号誤りなら増える）。

| 観測 | 判定 | tier |
|---|---|---|
| **エネルギー単調減少**（毎 run、勾配の符号検算） | 常に Yes | **measured（健全性）** |
| **素(c4=0)は崩壊**（Q_H 0.99→~0、Skyrme 密度サイズ縮む） | 解像度に依らず robust | **measured** |
| 第三(c4>0)は崩壊を**部分的に遅らせる**（細格子で最終 Q_H↑） | **脆い・解像度依存** | **frontier-observation** |

- **素(c4=0)は動的に崩壊**：Q_H→0＝**e009 の素GPEホップ粒子の縮みを動的に確認**（measured、robust）。これが本ステージの GREEN 主張。
- **第三(c4>0)の崩壊抵抗は脆い**：細格子（例 L=36）では最終 Q_H が c4 で増える（部分抵抗）が、粗格子/陽的 dt では c4>0 が同程度に崩壊・数値不安定（Q_H が負に振れることも）。よって**抵抗は GREEN ゲートにしない**（作為的に通さない）＝ frontier-observation。
- **完全な自己安定化（Q_H≈1 を保つ持続）は未達 ＝ frontier-observation**。四次項は剛性が高く（実効4階）、陽的 dt が極小、格子カットオフが L* と競合。**より細い格子／勾配項の陰的(Fourier)処理**が候補（スケール候補）。**安定化の確かな証拠は静的 Derrick の有限 L* 最小点**（Stage1、汎関数の性質）。動的ステージは素の崩壊を確認する。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | Faddeev-Skyrme は局所。サイズ・Q_H を書いていない |
| 2 | 忠実な物理? | **Yes** | Faddeev-Skyrme/Derrick は実在の場の理論 |
| 3 | 結果は初期条件に? | **No** | Hopf 写像の場のみ。崩壊/抵抗は流れから後で |
| 4 | 入れてない物が出る? | **Yes** | Q_H の整数性、有限 L*、動的な素の崩壊（c4>0 の抵抗は脆く frontier） |
| 5 | 数で合う? | **Yes** | Q_H=1.00、L*∝√c4、エネルギー単調減（ΔE/予測≈1.0） |
| 6 | 頑健? | **Yes（measured 部分）** | Q_H は box/L で安定、Derrick は c4 で。動的抵抗は解像度に脆い（→ frontier） |
| 7 | コードが発見? | **Yes** | Q_H は B=∇×A で測定、エネルギー単調減で勾配を検算、結論を書かない |

→ Q_H・Derrick・**動的な素の崩壊**は全監査通過＝**GREEN**。動的抵抗の頑健性・完全自己安定化は frontier。

## 床（隠さない・必須）
1. **固定格子＝空間は与えられている**。ソリトンの物理で、もつれ幾何ではない。
2. **絶対 E2,E4 は解像度(dx)依存**。Q_H（整数・トポロジカル）と Derrick の形（崩壊 vs 有限 L*、L*∝√c4）が robust。
3. **動的完全自己安定化は未達（frontier）**：四次項の剛性で陽的 dt 極小・格子カットオフが L* と競合。細格子/陰的処理が要（スケール候補）。静的 Derrick で有限 L* の存在は確認済み。
4. **「粒子」は analogy**。電子を作ったのではない。「同じ数学」≠「同じもの」。

## Stage 3（★本丸・frontier→measured）— 完全PDE 自己安定化（`hopfion_pde.py` → `results/hopfion_pde.json`）

陽的四次は剛性で不安定だった（Stage2 frontier）。**安定化付き半陰的勾配流**で解決：勾配を
**1/(1+dt·κ·|k|⁴)** で濾過（双曲調和の凸性分割を陰的に）。フィルタは正定値ゆえ**降下方向を保つ
（エネルギー単調）**まま、四次の剛性が乗る高 k を減衰→大きい安定 dt が可能（`core.hopf.stabilized_flow_step`）。

| c4 | Q_H 初→終 | サイズ 初→終 | 判定 | E 単調 |
|---|---|---|---|---|
| 0（素） | ~1 → ~0 | — | **崩壊（Q_H→0）** | Yes |
| 15 | ~1 → **~1 保持** | → L*≈3.3 | **自己安定化** | Yes |
| 25 | ~1 → **~1 保持** | → L*≈3.7 | **自己安定化** | Yes |
| 40 | ~1 → **~1 保持** | → L*≈4.1 | **自己安定化** | Yes |

- **完全PDE で c4>0 が Q_H≈1 を保ったまま有限 L* へ収束**＝**frontier→measured**。素(c4=0)は依然崩壊。
- **L* は c4 で増加（Derrick）**：3.3/3.7/4.1（c4=15/25/40）。エネルギーは全 run 単調減（勾配の健全性）。
- **床（正直に）**：**basin 限界**——L* より遥かに小さく（格子で未解像に）始めると依然巻き戻る（流れは**解像された**ホップ粒子を L* に保つが、既に潰れたものは救えない）。絶対 L* は解像度/κ 依存。robust なのは「Q_H≈1 保持・有限 L*・L*(c4) 増加」。文献（Q_H=1 は Faddeev-Skyrme の安定最小化子）が物理的裏づけ。「粒子」は analogy。

## 再現
```bash
python experiments/e012_hopf_stabilization/hopfion_static.py  # Q_H・E2,E4・Derrick(崩壊 vs 有限L*)
python experiments/e012_hopf_stabilization/hopfion_flow.py    # 陽的勾配流: 素は崩壊・抵抗は脆い(frontier)
python experiments/e012_hopf_stabilization/hopfion_pde.py     # ★完全PDE: c4>0 で Q_H≈1 保持→L* 収束(measured)
pytest tests/test_e012.py
```
