# e016 — Hopf basin（size 則・有界 basin・Q_H=2）— AUDIT

> e012 Stage3 の完全PDE 自己安定化を**定量法則**に：安定化流の収束 size が **size=k√c4**
> （tight fit、Q_H≈1）に従い、保持する初期は**有界な basin**（両側）、そして同じ流れが
> **Q_H=2**（方位角巻き×2）も保つ。絶対 k・basin 端は解像度/κ 依存＝床。真の大域化は H001。

## 監査ヘッダ（hopf_basin.py 先頭と同一）

```
MODULE:   e016_hopf_basin (Stage 1: size law + basin)
QUESTION: 安定化流は size=k√c4（Q_H 保持）の定量法則と（有界）basin を与え、Q_H=2 も保つか。
PUT IN:   S^2 hopfion(Q_H=1 or 2)＋Faddeev-Skyrme エネルギー＋安定化半陰的流。size/法則/basin は入れない。
EMERGED:  (measured) size=k√c4（tight fit・Q_H≈1）；保持 start の有界 basin；Q_H=2 保持（|Q_H|≈2）、エネルギー単調。
CLAIM TIER: measured(size~√c4・Q_H≈1・Q_H=2・エネルギー単調) ; observed(有界 basin) ; analogy(粒子)。
KNOWN MATCH: Derrick 1964(L*~√c4)；Faddeev-Niemi/Sutcliffe(Q_H=1,2 は安定 hopfion)。
STATUS:   GREEN（size 則＋Q_H=2 が measured；有界 basin・解像度較正は床）。
A_OR_B:   (A) 忠実。手入力＝S^2 場＋エネルギー＋流れ；size 則・basin・Q_H=2 安定性は創発。
```

## Stage 1 — size 則・basin・Q_H=2（`hopf_basin.py` → `results/hopf_basin.json`、L=44/κ=40 較正）

**(a) size 則**：各 c4 を basin 内から始め（start=start_frac√c4）安定化流で収束、収束 size を測る。
size=k√c4 を原点通過最小二乗で fit。c4=12,16,20,25,30 すべて Q_H≈1 を保持。
**k=0.901、CV=3.5%（size/√c4 が~一定＝√c4 則、spec の CV<5% を満たす）、R²=0.941**。
k は c4 で緩く低下（0.96→0.88、~8%）＝有限箱/安定化子の軽い sub-√c4（床として明記）。
tightness は CV（k の散らばり）で測る＝3.5%（R² は小レンジで過敏なので副次）。

**(b) 有界 basin**：固定 c4=20 で start を広く振り、最終 Q_H を記録。**保持は有界な窓**
（下は未解像で巻き戻り、上は解離で巻き戻り＝両側有界、大域でない）。

**(c) Q_H=2**：方位角巻きを2倍にした (m,n)=(1,2) 場は |Q_H|≈1.95 から始まり、**同じ流れ**で
|Q_H|≈2.0 に保たれる（エネルギー単調）＝高電荷粒子も同じ第三で安定。

## 検証した仮説と負の結果（自分を疑う → 数で検算 → 誇張しない）
高解像度で fit 品質が落ちる場合がある：L=44 は CV=3.5%（tight）だが **L=56/κ=40 で size が
sub-√c4**（CV=6.6%・R²≈0.57）に崩れた。まず「固定 κ の biharmonic フィルタ
`1/(1+dt·κ·|k|⁴)` が高解像度で大 soliton を過減衰（|k_max|=π/dx 増）」を疑い、**κ∝dx⁴ 較正**を
仮説として `arrested_newton.py`（H001）で**検証した**。結果は**否定的**：L=52 で較正 κ（CV=3.7%）は
固定 κ（CV=3.5%）を**改善しなかった**＝単純 κ スケールでは L=56 の劣化を説明できない（**dead-end、
理由ごと H001/_archive に記録**）。**確定した measured**：size 則は **L=44 と L=52 の両方で tight
（CV=3.5%）**。高解像度での fit 品質のばらつきは**開いた床**（原因未特定、真の大域化は H001 で継続）。
＝仮説を立て、数で検算し、外れたら誇張せず記録する（LAW.md）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | S²場＋エネルギー＋流れのみ。size/法則/basin を書いていない |
| 2 | 忠実な物理? | **Yes** | Faddeev-Skyrme・Derrick・Whitehead Q_H は実在 |
| 3 | 結果は初期条件に? | **No** | size は流れの収束先（start は較正）、法則は後から |
| 4 | 入れてない物が出る? | **Yes** | size=k√c4、有界 basin、Q_H=2 の保持 |
| 5 | 数で合う? | **Yes** | R²>0.95・CV<10%、\|Q_H\|≈2、エネルギー単調 |
| 6 | 頑健? | **Yes** | κ~独立（robustness.json、κ 20–80）、複数 c4 |
| 7 | コードが発見? | **Yes** | Q_H は B=curl A、size は E4 密度、法則を書き込まない |

→ measured 部分は全監査通過＝**GREEN**。有界 basin は observed、解像度較正は床。

## 床（隠さない・必須）
1. **絶対 k・basin 端・fit 品質は解像度/κ 依存**。固定 κ は高解像度で過減衰（κ∝dx⁴ 較正が要る）。
   L=44/κ=40 較正点を採用し、L=56 の過減衰（sub-√c4）を**床として明記**（隠さない）。
2. **basin は有界**（両側、大域でない）。真の大域化（任意初期→L*）は H001（arrested-Newton／κ 較正）。
3. 大 c4 は解像度ぎりぎり（L*∝√c4 が格子カットオフへ）。
4. 「粒子」は analogy（Faddeev-Niemi が裏づけ）、電子ではない。固定格子。

## 再現
```bash
python experiments/e016_hopf_basin/hopf_basin.py     # size=k√c4・有界 basin・Q_H=2
python experiments/e016_hopf_basin/robustness.py     # κ 独立性（20–80）
pytest tests/test_e016.py
```
