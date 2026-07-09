# e025 — 生きた器（三器官・二つの死 → オートポイエーシス閉環）— AUDIT

> e024 の心臓（モーター）を核に、一つの 2D CGL 場に**同一性（+1 芯）・代謝（三回対称モーター）・
> 境界（駆動散逸液滴）**を共存させる。**死・自己維持を直接コーディングせず**、介入（燃料切断／塊切除／
> 反渦注入）に対する **bulk|ψ|² と巻き**を測る。Stage2 で芯が自分の巻きを読み gain を gate（閉環）。
> 二段とも GREEN。**ゲート名は物理量のみ**（bulk / winding）——「自己・生・死・同一性」は analogy として
> docstring・本 AUDIT に置く（「同じ数学≠同じもの」）。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 complete（`results/complete.json`）— 三器官・二つの崩壊モード
| シナリオ | bulk / winding（quick） | 正典（evessel_complete.py） |
|---|---|---|
| 燃料あり（living） | **1.96 / +1.00** | 1.96 / +1.00 |
| 燃料切断（代謝的崩壊） | **0.01 / +1.00**（巻きは崩壊まで保持） | 0.01 / +1.00 |
| 塊切除（body excise） | **1.96 / +1.00**（再生） | 1.96 / +1.00 |
| 反渦注入（巻き→0） | **1.98 / +0.00**（bulk 高いまま） | 1.97 / −0.00 |

GREEN gates（物理量のみ）: `bulk_and_winding_sustained` / `bulk_collapses_on_fuel_cut` /
`winding_survives_body_excision` / `winding_lost_while_bulk_high`。
**測定の宝**: 二つの崩壊は**独立**——燃料切断は bulk を落とす（巻きは最後まで保持）、
反渦は巻きを 0 にするが bulk は高いまま。**代謝 ≠ 同一性**（interpretive）。

### Stage2 autopoietic（`results/autopoietic.json`）— 閉じた輪
| 量 | quick 再現 | 正典（evessel_auto.py） |
|---|---|---|
| **決定的対比** 反渦後 open / closed の bulk | **1.97 / 0.04** | 1.97 / 0.03 |
| closed living（bulk/巻き/gate） | 1.93 / +1.00 / 0.98 | 1.93 / +1.00 / 0.98 |
| closed 燃料切断 bulk | 0.01 | 0.01 |
| closed 塊切除（芯無傷） | 1.93 / +1.00 | 1.93 / +1.00 |

GREEN gates: `bulk_and_winding_sustained_closed` / `bulk_collapses_on_fuel_cut` /
`winding_survives_excision_closed` / **`winding_loss_collapses_bulk_iff_closed`**（核）。
**罠**: gate は場の**自分の巻きの平滑化読み**（gate←0.92·gate+0.08·σ(8(|w|−0.5)))；巻きは CCW 環（core.holonomy）。
gate するのは物理的 **gain**（"life" という変数を作らない）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 死／自己維持／閉環の因果を書いていない。場＋モーター＋gate のみ |
| 2 | 忠実な物理? | **Yes** | CGL 駆動液滴・三回対称ラチェット・トポロジカル電荷は実在 |
| 3 | 結果は初期条件に? | **No** | +1 芯を置くのみ。崩壊モード・閉環の結合は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 二つの独立崩壊、閉環下でのみ巻き喪失→bulk 崩壊（入れていない） |
| 5 | 数で合う? | **Yes** | 正典値を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed／格子（Nr）掃引でゲートの符号／対比は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 巻きは CCW 環で読み、bulk は領域平均で測定。因果を書き込まない |

→ 二段とも忠実な **measured**。GREEN。

## claim tier
- **measured**: bulk|ψ|² と巻きの準位・対比（全 GREEN ゲート）。
- **interpretive**: 二つの死は別物（代謝≠同一性）；操作的閉包＝自己と自己維持が不可分（Maturana-Varela）。
- **analogy / KNOWN MATCH**: 「生きた器・二つの死・真の自己・オートポイエーシス」。**ゲート名に入れない**。

## 床（隠さない・必須）
1. 2D 粗視化 CGL トイ・固定周期格子。絶対 bulk（~1.9）・崩壊閾値は (gain,dissip,dt,Rdrop) 依存＝床。
   ゲートは準位対比（>0.5 vs <0.2、|w|~1 vs ~0）を見る。
2. gate の形・閾値はモデル選択。ゲートされる事実は**閉環の対比**（閉＝巻き喪失で bulk 崩壊／開＝生存）であって絶対値でない。
3. 「自己／生／死／代謝／同一性」は analogy。**細胞・代謝・死・自己を作ったのではない**。quick は T/Nr 縮小、符号・対比は不変。

## 再現
```bash
python experiments/e025_vessel_life/complete.py --quick --no-write
python experiments/e025_vessel_life/autopoietic.py --quick --no-write
pytest tests/test_e025.py
```
