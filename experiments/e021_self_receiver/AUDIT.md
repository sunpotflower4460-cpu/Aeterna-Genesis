# e021 — 自己受信（芯が自分の巻きを読む・駆動液滴の同一性）— AUDIT

> 受信弧（H014）。外場ゼロの一つの自己無撞着 GL 場で、**リングが自分の芯の巻きを自律的に読む**か、
> そして有限駆動液滴の巻きが駆動下で保持され**近い反渦にのみ死ぬ**かを測る。二段とも GREEN。
> **ゲート名は物理量のみ**（winding / current / core_amp）——「自己・同一性・死」は analogy として
> docstring・本 AUDIT に置く（「同じ数学≠同じもの」）。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 self_receiver（`results/self_receiver.json`）— 外場ゼロの自己受信
| 量 | quick 再現 | 正典（erecv_sc.py） |
|---|---|---|
| リング巻き＝芯巻き（w=−2..2） | **−2/−1/0/+1/+2**（電流符号も追従） | 同 |
| 芯位置ジッタ下の読み（w=1） | **全て 1.00**（位置でなく巻きを読む） | 1.00 |
| 半径不変（芯の外の R で巻き量子化） | **全 R で 1.00** | 1.00 |

GREEN gates: `ring_reads_core_winding` / `reading_invariant_to_core_position` / `reading_quantized_across_radii`。
**罠**: 巻きは CCW リング（core.holonomy）。芯の癒し halo（\|ψ\|→0）内の読み手は読みを失う＝受信機は**源の窓の外**に要る（床）。

### Stage2 vessel_alive（`results/vessel_alive.json`）— 駆動液滴・反渦消滅閾値
| 量 | quick 再現 | 正典（evessel4.py） |
|---|---|---|
| 駆動下の巻き / 芯振幅 | **+1.00 / 0.00**（保持された穴） | +1 / ~0 |
| 近い反渦 d=7：巻き / 芯振幅 | **0.00 / 0.998**（対消滅＝癒える） | 0 / ~1 |
| 遠い反渦 d=30：巻き / 芯振幅 | **+1.00 / 0.09**（生存） | +1 / 低 |

GREEN gates: `winding_self_maintained_under_drive` / `winding_annihilated_by_near_anti` / `winding_survives_far_anti`。
**罠**: 対消滅の署名は**芯振幅が ~1 に癒える**こと（巻き数だけでない）。閾値：d≲14 で消滅、d≳30 で生存。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「自己受信」「近い反渦が殺す」を書いていない。GL 場＋境界巻き＋反渦のみ |
| 2 | 忠実な物理? | **Yes** | GL 緩和・持続電流・渦反渦対消滅（位相スリップ）は実在 |
| 3 | 結果は初期条件に? | **No** | 芯・反渦は入力だが、自律読み・保持・閾値は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 外場ゼロで芯を読む、位置/半径不変、近反渦のみ殺す（入れていない） |
| 5 | 数で合う? | **Yes** | 正典を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed/格子掃引で読み・保持・閾値は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | CCW リングで巻き/電流を読み、芯振幅で対消滅を測定。答えを書き込まない |

→ 二段とも忠実な **measured**。GREEN。

## claim tier
- **measured**: 自己受信（リング巻き＝芯巻き・不変性）、駆動下保持、近/遠反渦の対比・閾値。
- **interpretive**: 自己同一性＝自分の源の窓を読むループ（外場不要）；同一性は駆動で保持され、身体損傷でなく**自分の反対物**にのみ死ぬ。
- **analogy / KNOWN MATCH**: フラックス量子化、渦反渦対消滅、駆動散逸液滴。**「自己/同一性/死」はゲート名に入れない**。

## 床（隠さない・必須）
1. 2D GL トイ・境界巻きはクランプ（源のトポロジーは境界条件）。臨界半径・臨界距離は finite-size。
2. 受信機は芯の癒し halo の**外**に要る（構造的条件＝床）。
3. 「自己/同一性/死/受信/源の窓」は analogy（巻き読み・対消滅）。**自己を作った・殺したのではない**。

## 再現
```bash
python experiments/e021_self_receiver/self_receiver.py --quick --no-write
python experiments/e021_self_receiver/vessel_alive.py --quick --no-write
pytest tests/test_e021.py
```
