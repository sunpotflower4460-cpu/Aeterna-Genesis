# room-g002-c3-flux — Flux-heated convection（温度勾配を「置く」でなく「生成する」・因果的閉包 C3 方向）

**候補 Room（official:false）。親 `room-g002-a` は上書きしない（no_touch）。** 昇格は別段階（人が確認）。

## 何が親（g002）と違うか

- **親 g002（C1）**：壁に**固定温度差 ΔT** を課す（基準プロファイル `T_base = 1 - z`）。**温度勾配は t=0 で置いた環境条件**。
- **この Room（C3 方向）**：**温度勾配を置かない**。温度を**一様＋ノイズ**（`quiescent_plus_noise`）から始め、
  **吸収エネルギー流 S(z)**（両壁は冷たく保持）を課す。温度勾配は**流束 vs 伝導の釣り合いから自己生成**し、
  発達したプロファイルが超臨界になると対流が創発する。

## 測定（`genesis/models/boussinesq_flux_heated.py`・`emergence.json`）

| 量 | t=0 | 定常 | 意味 |
|---|---|---|---|
| 垂直勾配 RMS | 0.087（ノイズ） | **5.03** | **勾配が流束から生成**（置いていない） |
| 運動エネルギー | 0.0 | **29.4** | 対流が**静止から創発** |
| Nusselt | — | **2.10** | 対流輸送（>1） |

`gradient_generated=True`・`convection_from_rest=True`（決定的）。

## 正直な因果境界（`causal-ancestry.yaml`）

- **温度勾配＝Emerged State**（生成された）。**吸収エネルギー流＝imposed environment**（まだ置いている・
  `claim_excludes: [spontaneous_energy_flux]`）。
- ＝勾配は C1（imposed）→ C3（generated）へ一段。**流束自体を上流 Room から生成**するのは **frontier**（true C3/C4）。
- 「対流は創発」と言えるが「エネルギー流は創発」とは言わない。**同じ数学 ≠ 同じもの**：生成された対流であって生命ではない。
