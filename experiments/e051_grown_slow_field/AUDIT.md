# e051 育つ遅い場は記憶か — E候補ブリッジ（P07、結果は role N）

北極星「育ったのか置いたのか」を **記憶場そのもの**へ当てた実験。e049(S1)/e050(S2) は遅い場 `s` を**置いて**、
matched `g=0` OFF を超える hysteresis 過剰を測り `slow_field_basin_memory_candidate`（role S）とした。本実験は
`s(t=0)=0`（未分化）から `s` を**育て**、その過剰が **遅い場の「記憶(lag)」なのか、ただの結合効果なのか**を、
prereg §6 の `memory_copy_collapse` null（瞬時コピー対照）で正面から検定する。

## 測った 4 系（格子・seed・掃引 schedule・dt・step 数を完全一致）
| 系 | g | s | 役割 |
|---|---|---|---|
| OFF | 0 | 受動 | hysteresis 基準（掃引率・臨界緩和 confound） |
| **grown** | 0.6 | **s(t0)=0**、`|psi|^2` から育つ、遅い（τ=10） | **E候補**：置かない記憶場 |
| placed | 0.6 | 構造テンプレ（秩序 well へ偏り） | 「置いた」参照・上限 |
| **copy** | 0.6 | **s=`|psi|^2` 瞬時（τ→0, lag なし）** | 結合はあるが**記憶なし**の対照 |

`excess(系) = area(系) − area(OFF)`。**`history_gain = excess(grown) − excess(copy)`** が lag（記憶）の寄与。

## 測定結果（full）
- excess: **grown 0.332**、placed 0.368、copy **0.320**、OFF 0（定義）。
- **history_gain = grown − copy = 0.012 ≦ margin 0.06** → **copy-collapse**。
- 育ち計量 struct(s): grown は t0 で **厳密に 0** → settle で 0.047（**s の空間構造は確かに育った**）。
- 履歴 hold（参考）: 崩壊端で grown の s は field が 0 に落ちても一部保持するが、その lag は hysteresis 面積に**足していない**。
- seed 0.318±0.013、2D→3D でも excess は残る（0.257）が、**いずれも copy でも出る**＝記憶の証拠にならない。
- **判定 `memory_copy_collapse`（E候補 不支持）。** 実行は valid（エネルギー有界・確定判定）＝ STATUS GREEN、科学的結論は下記。

## 何が分かったか（正直な科学）
- **過剰は遅い場の「記憶(lag)」ではなく結合の再規格化。** 瞬時コピー `s=|psi|^2` は有効方程式を
  `∂_tψ = a·ψ − (1−g)|ψ|²ψ + ∇²ψ` に変える＝**有効飽和を弱める**だけで、同じだけ hysteresis を広げる。
  遅い `s` の lag はその上に**測れるほどの記憶を足さない**（history_gain≈0）。
- **育ったのか置いたのか（第一監査）**：`s` の空間構造は 0→0.047 と**育った**。しかしその育った構造は
  **記憶を担っていない**（copy でも同じ過剰）。「構造が育つ」と「記憶が育つ」は別物、を分離できた。
- **関係したのか同じ attractor へ崩れただけか（第二監査）**：OFF 差はある（excess>0）が、その差は copy と共通＝
  遅い場**固有の**関係ではない。真の「記憶」主張には **matched instantaneous-copy 対照が必須**。

## e049/e050 への含意（限定・no_touch は維持）
本結果は e049(S1)/e050(S2) の **数値・artifact を一切変更しない**（no_touch）。ただし解釈を限定する：
両者の「basin memory」hysteresis 過剰は **結合再規格化を含む**。遅い場の lag に固有の記憶を主張するには、
本実験が追加した **瞬時コピー対照**（τ→0）を通す必要がある。S1/S2 は「置いた遅い場＋結合で履歴依存の
hysteresis が出る（role S）」としては有効。「記憶」という語は本対照を通すまで保留が正しい。

## Discipline
- **role N**（negative_constraint）：E候補は不支持。honest negative＝資産。失敗も台帳へ（本 AUDIT＋result JSON）。
- **target_encoded=false**：s に目標/template を置かない（grown 系は t0 で厳密 0）。8th 監査 OK（primary∉{E,V}）。
- **no_touch**：measures.py・rooms/official・既存 experiments・schema・registry・app 不変。新規実験のみ。

## Reproduce
```
python experiments/e051_grown_slow_field/grown_slow_field.py            # full
python experiments/e051_grown_slow_field/grown_slow_field.py --quick    # smoke
pytest tests/test_e051_grown_slow_field.py -q
```
