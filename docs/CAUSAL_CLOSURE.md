# CAUSAL_CLOSURE — 因果的閉包 Level（C0〜C4）：主張の因果をどこまで遡って生成したか

> **これは何か**：各 Room に**因果的閉包 Level**を付す。「この Room は、自分の主張の**因果的生成**を
> **どこまで遡って**いるか」を測る。[`GENESIS_PROVENANCE.md`](GENESIS_PROVENANCE.md) の入力4分類と対。
> ANTI_DRIFT を否定せず**上流拡張**。C4 = うえきの北極星（frontier）。

## Level 定義

| Level | 名前 | 意味 | 判定 |
|---|---|---|---|
| **C0** | Outcome-scripted | 結果（完成形）を直接 script | ❌ **却下**（第8監査違反） |
| **C1** | State-specified | 初期位置/速度/形/環境を t=0 で直接指定 | 検証には可、ただし t=0 固定 |
| **C2** | Process-prepared | 状態を**準備過程から生成**（直接置かない） | ★ **official Room 最低目標** |
| **C3** | Environment-generated | 環境・流入**も**親 Room／発展から生成 | 深い |
| **C4** | Relational Genesis | 空間・次元・星**も**関係から生まれる | **最深 frontier＝北極星** |

**速度=0 を置く**＝C0/C1。**支えを外して力の釣り合いから静止が生じる**＝C2。（[`PREPARATION_PROTOCOLS.md`](PREPARATION_PROTOCOLS.md)）

## 既存 official Room の監査（現状・上書きせず記述のみ）

| Room | Fundamental Relations | Prepared State | Environmental Condition（claim_excludes） | Emerged State | 現 CC Level |
|---|---|---|---|---|---|
| **room-g001-a** TDGL | 緩和GL・複素場・周期BC | 一様＋ノイズ(mean0) | **クエンチ時間プログラム**（`spontaneous_quench`） | 位相巻き渦 L2 | **C1** |
| **room-g002-a** Boussinesq | Boussinesq/NS・壁・重力(浮力) | 静止＋ノイズ(KE=0) | **固定温度差 Ra=1000**（`spontaneous_temperature_gradient`） | 循環ロール L3候補 | **C1** |
| **room-g003-a** Model H | CH/NS/ModelH・周期BC | 一様＋ノイズ(mean0) | **なし（autonomous）** | 相分離＋流れ L2(L5候補) | **C1（C2 に最も近い）** |

- 3 Room とも現状 **C1**。既存の `drive_class`・`natural_emergence`（`target_shape_seeded: false` 等）は C1 の証跡。
- **g002 が C2/C3 昇格の筆頭**：ΔT は今 `imposed_environment`。温度差**自体**を「吸収エネルギー流」から
  生成する **C3 版子 Room** を（既存を上書きせず）新規に作れば、「温度差も創発」に一歩近づく。
- **g003 は autonomous**（環境 impose なし）＝ IC を準備過程から生成すれば **C2** に最も昇格しやすい。

> **昇格は別段階**（人が確認）。この表は**監査**であって、既存 Room の物理は変えない（no_touch）。

## 使い方

1. 新 Room を作るとき、`provenance.yaml` を書き、この表に CC Level を付す。
2. C1 なら「何を直接置いたか」を明示（検証用途として正直）。**C1 を C2 と偽らない。**
3. C2+ を主張するなら `preparation.yaml`／`causal-ancestry.yaml` で生成過程を示す。
4. 届かないなら **frontier** と正直にラベル（研究は止めない・因果境界を明示）。
