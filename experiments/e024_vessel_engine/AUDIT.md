# e024 — 器のエンジン（ラチェット→モーター→器のモーター）— AUDIT

> 「生命の宿りうる器」の**心臓**を三段で作る。**回転・仕事・自己維持を直接コーディングせず**、
> 非対称ポテンシャル・三相・燃料勾配だけを入れ、整流電流・回転数・器の振幅 Ψ を測る。
> 三段とも GREEN（物理量ゲートのみ）。「生命／ATP合成酵素」は KNOWN MATCH の analogy に置き、
> **ゲート名には入れない**（「同じ数学≠同じもの」）。

## 監査ヘッダ（各 `<module>.py` 先頭と同一）
- **Stage1 `ratchet.py`**: 非対称周期ポテンシャルは対称ノイズを整流するか。
- **Stage2 `motor.py`**: 三が回転の最小か・三相ロータは回るか。
- **Stage3 `vessel_motor.py`**: 燃料勾配は三回対称ロータを回し、仕事をして器を維持するか。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 ratchet（`results/ratchet.json`）
| 量 | quick 再現 | 正典（eratchet2.py） |
|---|---|---|
| 整流 (v(+A)+v(−A))/2 @asym=1, A=4.5 | **+0.604** | +0.603 |
| A=1.5→6 の整流（単調増） | 0.019→0.961 | 0.019→0.959 |
| 対称（asym=0） | ~0（\|·\|<0.05） | ~0 |
| asym=0.1（51/49） | **+0.075** | +0.077 |

GREEN gates（物理量のみ）: `rectifies_symmetric_drive` / `rectification_grows_with_drive` / `any_asymmetry_rectifies`。
**罠**: 整流は静的傾き v(+A),v(−A) を別々に測って平均（rocking 直接積分は障壁と拮抗して弱い）。

### Stage2 motor（`results/motor.json`）
| 量 | quick 再現 | 正典（emotor.py） |
|---|---|---|
| 場のリップル N≤2 / N≥3 | 0.999 / 0.00 | 0.999 / 0.00 |
| 三相電流和 max\|Σ\| | 0.0（<1e-9） | 0.0 |
| トリプレン零相高調波 | [3,6,9] | [3,6,9] |
| ロータ回転（三相 / 単相 / 単相+ラチェット） | +9.5 / −0.11 / +9.6 rev | +19.0 / −0.06 / +19.1 rev |

GREEN gates: `three_is_min_rotation` / `three_phase_balanced` / `triplen_zero_sequence` / `rotor_self_spins`。
回転数の**絶対値は床**（T/Np 依存）。ゲートは「>5rev・\|<0.5\|」の符号／閾値（quick でも full でも成立）。

### Stage3 vessel_motor（`results/vessel_motor.json`）
| 量 | quick 再現 | 正典（evessel_motor2.py） |
|---|---|---|
| rate(Δμ=5) / rate(0) | +0.557 / 0.0 | +0.557 / 0.0 |
| 停動 load | ~3 | ~3 |
| 器 Ψ（燃料あり / 切断後） | 0.925 / 0.00 | 0.925 / 0.00 |
| 方向反転 rate(+5) / rate(−5) | +0.559 / −0.557 | +0.558 / −0.557 |

GREEN gates: `motor_turns_on_fuel` / `motor_does_work_vs_load` / `motor_sustains_vessel` /
`vessel_dies_on_fuel_cutoff` / `direction_reverses_with_fuel`。
**罠**: 産物は**平滑化した正味回転** `om_s`（0.99·om_s+0.01·mean(dφ)/dt）で駆動し `max(om_s−0.05,0)`。
`max(dφ/dt,0)` はノイズの前向き揺らぎを拾い、燃料を切っても器が死なない（＝穴あき版の失敗）。方向は燃料の符号。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 回転／仕事／死を書いていない。非対称・三相・燃料勾配のみ入力 |
| 2 | 忠実な物理? | **Yes** | 過減衰 Langevin・回転磁場・三相理論・三回対称ラチェットは実在 |
| 3 | 結果は初期条件に? | **No** | 位相はランダム初期化。整流／回転／Ψ は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 対称ノイズ→定符号電流、燃料切断→器の崩壊（入れていない） |
| 5 | 数で合う? | **Yes** | 正典値を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed／格子（Np）／dt を掃引しゲート符号は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 整流＝静的傾き平均、回転＝∫dφ、Ψ＝ODE で測定。答えを書き込まない |

→ 三段とも忠実な**measured**。GREEN。

## claim tier
- **measured**: 三段の全 GREEN ゲート（整流・回転・仕事・自己維持・死・反転）。
- **interpretive**: 「器の心臓」＝勾配→回転→仕事→自己維持。整流の非対称起源＝運動方向の源。
- **analogy / KNOWN MATCH**: ブラウン・ラチェット、三相回転磁場、ATP合成酵素。**「生命」はゲート名に入れない**。

## 床（隠さない・必須）
1. 1D／過減衰点粒子・スカラー Ψ ODE。絶対電流／回転数／Ψ 準位は (D,T,dt,asym,feed) 依存＝床。
   ゲートは符号・閾値・崩壊（頑健）を見る。
2. 「ボルトが締まる／器が生きる・死ぬ」は analogy（Ψ の準位）。**ATP合成酵素を作ったのではない**。
3. quick は T/Np を縮小（回転数は小さくなる）。**符号・閾値は不変**、正典の絶対値は full で再現。

## 再現
```bash
python experiments/e024_vessel_engine/ratchet.py --quick --no-write
python experiments/e024_vessel_engine/motor.py --quick --no-write
python experiments/e024_vessel_engine/vessel_motor.py --quick --no-write
pytest tests/test_e024.py
```
