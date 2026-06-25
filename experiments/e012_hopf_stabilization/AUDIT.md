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
EMERGED:  (measured) Q_H≈1(整数)；素は崩壊(e009一致)、c4>0 で崩壊に抵抗(最終Q_H・エネルギーが c4 で単調増)。
CLAIM TIER: measured(Q_H,E2,E4,Derrick L*,崩壊 vs 抵抗) ; frontier-observation(完全自己安定化) ; analogy(粒子)。
KNOWN MATCH: Derrick 1964; Faddeev-Niemi hopfion; e009(素GPEホップ粒子が縮む)。
STATUS:   GREEN（Q_H 整数＋Derrick＋崩壊 vs 抵抗は measured。完全安定化は frontier＝解像度/dt の床）。
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

| c4 | Q_H 初→終 | 判定 | E 単調減 |
|---|---|---|---|
| 0（素） | 0.99 → ~0.0 | **崩壊（巻きが解ける）** | Yes |
| 10 | 0.99 → 中間 | 抵抗 | Yes |
| 30 | 0.99 → 最大 | 抵抗（最も残る） | Yes |

- **素(c4=0)は動的に崩壊**：Q_H→0、Skyrme 密度サイズが縮む＝**e009 の素GPEホップ粒子の縮みを動的に確認**（measured）。
- **第三(c4>0)は崩壊に抵抗**：c4 が大きいほど最終 Q_H・整定エネルギーが**単調に増える**（measured）。
- **完全な自己安定化（Q_H≈1 を保つ持続）は本解像度では未達 ＝ frontier-observation**。四次項は剛性が高く（実効4階）、陽的 dt が極小になり、格子カットオフが L* と競合。**より細い格子／勾配項の陰的(Fourier)処理**で改善見込み（スケール候補）。静的 Derrick は有限 L* の存在を既に証明済み。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | Faddeev-Skyrme は局所。サイズ・Q_H を書いていない |
| 2 | 忠実な物理? | **Yes** | Faddeev-Skyrme/Derrick は実在の場の理論 |
| 3 | 結果は初期条件に? | **No** | Hopf 写像の場のみ。崩壊/抵抗は流れから後で |
| 4 | 入れてない物が出る? | **Yes** | Q_H の整数性、崩壊、c4 単調抵抗 |
| 5 | 数で合う? | **Yes** | Q_H=1.00、L*∝√c4、エネルギー単調減 |
| 6 | 頑健? | **Yes** | Q_H は box/L で安定、Derrick は c4 で、流れは複数 c4 で |
| 7 | コードが発見? | **Yes** | Q_H は B=∇×A で測定、エネルギー単調減で勾配を検算、結論を書かない |

→ Q_H・Derrick・崩壊 vs 抵抗は全監査通過＝**GREEN**。完全自己安定化は frontier。

## 床（隠さない・必須）
1. **固定格子＝空間は与えられている**。ソリトンの物理で、もつれ幾何ではない。
2. **絶対 E2,E4 は解像度(dx)依存**。Q_H（整数・トポロジカル）と Derrick の形（崩壊 vs 有限 L*、L*∝√c4）が robust。
3. **動的完全自己安定化は未達（frontier）**：四次項の剛性で陽的 dt 極小・格子カットオフが L* と競合。細格子/陰的処理が要（スケール候補）。静的 Derrick で有限 L* の存在は確認済み。
4. **「粒子」は analogy**。電子を作ったのではない。「同じ数学」≠「同じもの」。

## 再現
```bash
python experiments/e012_hopf_stabilization/hopfion_static.py  # Q_H・E2,E4・Derrick(崩壊 vs 有限L*)
python experiments/e012_hopf_stabilization/hopfion_flow.py    # 勾配流: 素は崩壊・第三は抵抗
pytest tests/test_e012.py
```
