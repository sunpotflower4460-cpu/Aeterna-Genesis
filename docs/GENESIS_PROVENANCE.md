# GENESIS_PROVENANCE — その初期条件は、どこから来たのか（ANTI_DRIFT の上流拡張）

> **これは何か**：[`ANTI_DRIFT.md`](ANTI_DRIFT.md) は「**完成形を初期条件に埋めない**」を守る。本書はその一段上流——
> **「その初期条件・その"体"自体はどこから来たのか」** を問う。ANTI_DRIFT を**否定せず精密化**する。
> 合言葉「**その部品、どこから持ってきたの?**」を、`manually_set: true/false` として**記録できる構造**にする。
> 出典：うえき × GPT レビュー。監査：Claude が 7＋8。関連：[`CAUSAL_CLOSURE.md`](CAUSAL_CLOSURE.md)・
> [`PERIODIC_TABLE.md`](PERIODIC_TABLE.md)・[`EMERGENCE_LEVELS.md`](EMERGENCE_LEVELS.md)。

## 大原則

> **創発と呼べるのは、発展から生じた Emerged State だけ。** 置いたもの・準備したもの・環境として与えたものは、
> **正直にそう記録し、創発と呼ばない。** IC は「答えを描く装置」でなく「**どう展開するかを追跡する装置**」。

これは既存の芽の延長：`genesis.schema.json` の `drive_class`（autonomous / externally_driven /
time_programmed_environment / runtime_controlled）と `emergence.json` の `natural_emergence`
（`target_shape_seeded` 等）を、**入力の由来**として体系化する。

## 1. 入力の4分類（すべての入力をどれかに置く）

| 種類 | 意味 | 例 | 創発と呼べるか |
|---|---|---|---|
| **Fundamental Relations**（基礎関係） | 法則・保存則・反応・接触力——設計者が選び、**明示**する | GL/NS/反応拡散、周期BC、重力 | — （土台であって主張対象でない） |
| **Prepared State**（準備状態） | **準備過程の結果**として生成した状態（直接設定でない） | 落ちて静止した石、一様＋ノイズ、REST(KE=0) | — （準備の由来を記録） |
| **Environmental Condition**（環境条件） | この問いでは上流を対象にしないため外部に置く | 温度差・太陽エネルギー流・重力場・壁 | ❌（`claim_excludes` を必ず付す） |
| **Emerged State**（創発状態） | 時間発展から生まれたもの | 局在・境界・回転・分裂・内部状態 | ⭕ **これだけを創発と呼ぶ** |

**速度・静止も「置く」でなく履歴から生成する**（例：石）：
- ❌ 弱い：`velocity: [0,0,0]` を理由なく直接置く。
- ⭕ 良い：**支えを外す → 力の釣り合いから静止が"結果として"生じる**（`prepare_until: net_force<1e-8, kinetic_energy<1e-10`）。
  ソルバー内部に速度変数が「直接設定される」のでなく、**準備過程から生成**される。

## 2. 記録ファイル（各 Room に追加・既存 Room は監査のみ／上書きしない）

- **`provenance.yaml`**：各 entity/state_variable が `manually_set: true/false`、`source`
  （`parent_room` / `preparation_result` / `environmental_model` / `law`）、`outcome_targeted: false`。
- **`preparation.yaml`**：準備過程（`state: supported_equilibrium`、`relax_until: {net_force<tol, kinetic_energy<tol}`、
  `event: remove_support_at: t0`）。
- **`causal-ancestry.yaml`**：**因果祖先**——ある Room の環境/状態が、別の Room の発展から生成された系譜。

スキーマ：[`schemas/provenance.schema.json`](../schemas/provenance.schema.json)・
[`preparation.schema.json`](../schemas/preparation.schema.json)・
[`causal-ancestry.schema.json`](../schemas/causal-ancestry.schema.json)。

## 3. 環境条件は正直にラベル（claim_excludes）

```yaml
temperature_gradient:
  provenance: imposed_environment
  manually_set: true
  claim_excludes: [spontaneous_temperature_gradient]   # 「対流は創発」と言えるが「温度差は創発」とは言わない
```
より深い Room は、その環境条件**自体**を生成する（例：温度差を「太陽吸収エネルギー流」から生成する C3 版）。

## 4. Room 関係の2種を混同しない

- **`variant_lineage`**（変種系譜）：Room A のパラメータを変えて Room B（diffusion 変更 → A1）。**同じ問いの別設定**。
- **`causal_ancestry`**（因果祖先）：ある Room の**環境/状態が、別 Room の発展から生成**される（環境→状態→…）。
  単に複数モデルを順番に接続するのと違う——**因果的に受け渡している**ことを記録。

## 5. AI が起動時に問う5つ（各 Room の主張に対して）

1. 結果（完成形）を script していないか?
2. 状態を直接置いたか、別の過程から生成したか?（`manually_set`）
3. その状態を、さらに上流の Room で生成できるか?
4. 環境条件に `claim_excludes` が付いているか?
5. その主張に十分な**因果的閉包**（[`CAUSAL_CLOSURE.md`](CAUSAL_CLOSURE.md)）が得られているか?

> **全てを根源まで遡れないことを理由に研究を止めない。** 各 Room の問いに応じて**因果境界を明示**すればよい。

## 6. 創発主張の標準文

> 「この Room の **X** は、記録された**物理的準備過程**（または**親 Room の発展**）**から生じた**。直接設定していない。」

## seeded vs emerged は「能力ごと」に（GPT②・ANTI_DRIFT 精密化）

一つの Room が全部 emerged とは限らない。**能力ごと**に seeded/emerged を記録する（`higher_levels` の
`seeded_localization` 等 ＝ `provenance.yaml` の state_variable 毎 `manually_set` の能力粒度版）：
- **Swift-Hohenberg の L4**：自己修復・持続・サイズ非依存は**emerged**だが、**局在は seeded**（ガウス bump を置く）。
  → `seeded_localization: true`。「0 から個体性が創発」でなく「**置いた局在 seed が自己修復する attractor に育った**」。
- **Gray-Scott の L7-partial**：分裂 event は**emerged**（未命令）だが、個体数増加は**seeded な founder 起点**。
  → `division_event_not_commanded: true` ＋ `spot_count_growth_from_seeded_founders: true`。
