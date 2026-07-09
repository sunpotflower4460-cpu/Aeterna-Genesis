# e028 — トポロジカル記憶（穴の巻き＝受信されるビット）— AUDIT

> 受信弧の基盤。**記憶を「穴（非観測領域）を囲むループの巻き」として測る**。記憶則を書かず、
> 巻きの非局所性・保護・容量（固定小受信機が自分の dof より多くのビットを読む）を測定。
> 二段とも GREEN。**ゲート名は物理量のみ**（winding / capacity / energy / gauge）——「記憶・自己・受信」は
> analogy として docstring・本 AUDIT に置く（「同じ数学≠同じもの」）。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 memory（`results/memory.json`）— 静的（非局所・保護・容量）
| 量 | quick 再現 | 正典（ereceiver/edecisive） |
|---|---|---|
| 容量：固定 h=6 受信機（dof≈48）が回復するビット | M=4..121 **全 100%** | 全 100%（M≤121） |
| M>dof で容量が dof を超える | M≥49 で True（**121 ビット>48 dof**） | 同 |
| 保護：局所平滑ノイズ下の巻きビット | **全ノイズで 100%** | 100%（不変） |
| 対照：動的バンプビット（記憶を dof に貯める） | 高ノイズで劣化（90%） | 劣化（86–94%） |
| 非局所：穴を囲まぬループ / 全穴を囲む箱ループ | **0 / Σビット（−3=−3）** | 0 / Σビット |

GREEN gates: `nonlocal_winding` / `protected_under_local_perturbation` / `capacity_exceeds_dof` / `dynamical_baseline_erodes`。
**罠**: 巻き読みは**反時計回り**（core.holonomy）。全穴を囲むには**箱ループ**（円は角の穴を逃す）。

### Stage2 ring（`results/ring.json`）— 動的 GL リング（スペクトル ETD）
| 量 | quick 再現 | 正典（erecv_dyn2） |
|---|---|---|
| 受信巻き n＝round(Φ)（半整数で整数跳躍） | 0/0.8→1/1.6→2/2.8→3 | 同（0/0.6→1/1.8→2/2.7→3） |
| ゲージ不変 dE（単一値ゲージ） | **4e-6**（<1e-4） | 2e-6 |
| 位相スリップ障壁（**床**）：基底 E / 強制ノード E | **0.79 / 3.84** | 0.79 / 3.81 |

GREEN gates: `autonomous_quantized` / `gauge_invariant` / `phase_slip_barrier`。
**罠**: 剛拡散は**スペクトル ETD** `exp(−(k−Φ)²dt)`（陽解法は overflow→NaN）。障壁は**床**（強制ノード proxy、GREEN 閾値でない）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 非局所/保護/容量/量子化を書いていない。穴＋ビット＋リングのみ |
| 2 | 忠実な物理? | **Yes** | Aharonov-Bohm 位相・トポロジカル電荷・GL フラックス量子化は実在 |
| 3 | 結果は初期条件に? | **No** | 穴とビットは入力だが、巻きの不変性・容量・量子化は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 容量>dof、局所ノイズ不変、n=round(Φ)（入れていない） |
| 5 | 数で合う? | **Yes** | 正典を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed 掃引で巻き不変・容量・量子化は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | CCW ループ/箱ループで巻きを読み、ETD で緩和。答えを書き込まない |

→ 二段とも忠実な **measured**。GREEN。

## claim tier
- **measured**: 非局所性・保護・容量>dof・量子化・ゲージ不変（全 GREEN ゲート）。
- **interpretive**: ビットは**穴に受信**される（受信機の dof に貯まるのでない）；リングは触れない磁束を読む。
- **analogy / KNOWN MATCH**: Aharonov-Bohm、トポロジカル電荷、超伝導リングのフラックス量子化。**「記憶」はゲート名に入れない**。

## 床（隠さない・必須）
1. 静的粗視化場・固定格子（容量数は finite-size）。1D GL リングトイ。
2. **位相スリップ障壁は強制ノード proxy＝床**（正確なインスタントンでない、GREEN 閾値に入れない）。
3. 「記憶／受信／源の窓」は analogy（巻き不変量／フラックス量子化）。**記憶を作ったのではない**。

## 再現
```bash
python experiments/e028_topological_memory/memory.py --quick --no-write
python experiments/e028_topological_memory/ring.py --quick --no-write
pytest tests/test_e028.py
```
