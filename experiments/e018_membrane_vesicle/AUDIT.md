# e018 — 器の膜（三腕オートポイエーシス＋相図／空間膜小胞）— AUDIT

> e015 の両腕を**三腕**（基質→代謝→膜）に拡張し、**どの腕を切っても・駆動を切っても死ぬ**を
> 相図で。さらに**空間**へ：phase-field で**境界をもつ有界小胞（膜）**が駆動で持続・切ると
> 溶ける。0次元動力学（Stage1）から空間の器（Stage2）へ。「膜/小胞/protocell」は analogy。

## 監査ヘッダ（vessel_membrane.py / membrane_vesicle.py 先頭と同一）

```
Stage1: MODULE e018_membrane_vesicle (three-arm closure + phase diagram)
  QUESTION 基質→代謝→膜の駆動ループで、各腕は必要か、相図は駆動閾値で支配されるか。
  EMERGED (measured) 無傷→共存；どの腕/駆動を切っても死；駆動閾値曲線 s_c(dA) が漏れとともに上昇。
  CLAIM measured(共存・三様の死・臨界駆動曲線) ; interpretive(駆動下閉包) ; analogy(代謝/膜/器)。
Stage2: MODULE e018_membrane_vesicle (phase-field vesicle)
  QUESTION 駆動 phase-field は境界をもつ小胞を作り、駆動で持続・切ると溶けるか。
  EMERGED (measured) 単一・有界・薄膜の小胞が駆動で持続；駆動オフ→溶解；漏れ↑→駆動↑。
  CLAIM measured(有界単一小胞・駆動持続・溶解・漏れ→駆動) ; analogy(膜/小胞/protocell)。
STATUS GREEN（三様の死＋駆動閾値曲線／有界小胞＋駆動依存が measured；膜/生命は analogy）。
```

## Stage 1 — 三腕＋相図（`vessel_membrane.py` → `results/vessel_membrane.json`）

`dS/dt = s(1−S) − k1·A·S·M`（基質を駆動供給、膜内で消費）、
`dA/dt = k1·A·S·M(1−A) − dA·A`（代謝：基質**と**膜が要る）、
`dM/dt = k2·A(1−M) − dM·M`（膜は代謝が作る）。

| 操作 | 結果(S,A,M) | 判定 |
|---|---|---|
| 無傷＋駆動 | (0.36, 0.76, 0.79) | **ALIVE** |
| 代謝を切る k1=0 | (1.0, ~0, ~0) | 死 |
| 膜を切る k2=0 | (1.0, ~0, ~0) | 死 |
| 駆動を切る s=0 | (~0, 0, ~0) | 死 |

- **三腕すべて load-bearing**：代謝・膜・駆動のどれを切っても共倒れ — measured。
- **相図は臨界駆動曲線 s_c(dA)**：漏れ dA=[0.15,0.25,0.35] に対し s_c=[0.02,0.05,0.1]＝
  **駆動閾値が漏れとともに上昇**（散逸が増えるほど必要な throughput が増える）— measured。

## Stage 2 — 空間膜小胞（`membrane_vesicle.py` → `results/membrane_vesicle.json`）

質量制御 Allen-Cahn の能動ドロップレット（Zwicker 系最小版）：
`dφ/dt = ε²∇²φ − (φ³−φ) + μ(t)`、`μ(t)=s(target−⟨φ⟩) − leak(⟨φ⟩+1)/2`。

| 状態 | inside_frac | 界面帯（膜） | 連結成分 | 判定 |
|---|---|---|---|---|
| 駆動あり | 0.28（有界） | 0.05（薄い） | 1（単一） | **小胞・生** |
| 駆動オフ s=0 | 0.00 | — | 0 | 溶解（死） |

- **境界をもつ有界な単一小胞＋薄い膜**が自発形成（空間充填でない）— measured。
- **駆動で持続・切ると溶ける（死）**、**漏れ↑→生存に必要な駆動↑**（leak 0→0.8 で min s 0.1→0.3）
  ＝ Stage1 の臨界駆動曲線の空間版 — measured。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 反応/場の局所則のみ。「死ね」「小胞を作れ」を書いていない |
| 2 | 忠実な物理? | **Yes** | 反応速度論・相分離（Allen-Cahn/能動ドロップレット）は実在 |
| 3 | 結果は初期条件に? | **No** | 一様/種から、共存・小胞・死は後から |
| 4 | 入れてない物が出る? | **Yes** | 三様の死・境界をもつ小胞・溶解 |
| 5 | 数で合う? | **Yes** | s_c(dA) 単調、inside_frac/界面帯/連結成分、漏れ→駆動 |
| 6 | 頑健? | **Yes** | (s,dA)・(s,leak) スイープで（robustness.json） |
| 7 | コードが発見? | **Yes** | 死も小胞も場から創発、形も死も入れない |

→ measured 部分は全監査通過＝**GREEN**。「代謝/膜/器/生命」は analogy・interpretive。

## 床（隠さない・必須）
1. Stage1 は**最小動力学**（空間膜でない）。Stage2 は**粗視化連続 phase-field**（脂質二重膜でない）。
2. 「代謝/膜/小胞/protocell/死」は **analogy・interpretive**。単一細胞・生命を作ったのではない。
3. 固定周期格子。小胞サイズは駆動/漏れの釣り合いで決まる。
4. 「同じ数学」≠「同じもの」。

## 再現
```bash
python experiments/e018_membrane_vesicle/vessel_membrane.py    # 三腕＋相図（駆動閾値曲線）
python experiments/e018_membrane_vesicle/membrane_vesicle.py   # 空間膜小胞（駆動で生・切ると溶ける）
pytest tests/test_e018.py
```
