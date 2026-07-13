# PREPARATION_PROTOCOLS — 状態は「置く」でなく「準備過程から生成する」

> **これは何か**：C2（Process-prepared・[`CAUSAL_CLOSURE.md`](CAUSAL_CLOSURE.md)）に必要な**準備過程**の書き方。
> 速度・静止・配置を**直接置かず**、物理過程の**結果として**生成する。[`GENESIS_PROVENANCE.md`](GENESIS_PROVENANCE.md) の実務版。

## 原則

> **「石が静止している」を `velocity=[0,0,0]` と置くのは C1。支えを外し、力の釣り合いから静止が生じるのが C2。**

準備過程は「答えを置く」ではない——**釣り合い・緩和・落下**のような**汎用の物理過程**で、
目標状態を**名指しせず**に状態を落ち着かせる（第8監査 clean）。

## `preparation.yaml`（例）

```yaml
# 静止状態を「置く」でなく緩和で生成
rest_state:
  state: supported_equilibrium         # 支えありの平衡から始める
  relax_until:                         # 汎用の停止条件（目標形状を名指さない）
    net_force: "<1e-8"
    kinetic_energy: "<1e-10"
  event:
    remove_support_at: t0              # t=0 で支えを外す → 以降は自由発展
  provenance: preparation_result       # manually_set: false（GENESIS_PROVENANCE.md）
```

## 認められる準備過程（汎用・目標非埋込）

- **緩和/減衰**：`relax_until` で釣り合いへ（速度・静止の生成）。
- **落下/解放**：支え・拘束を外す（`remove_support_at`）。
- **一様＋ノイズからの熟成**：未分化状態を短時間ならす（模様は生成せず、床のみ整える）。
- **クエンチ**：制御パラメータを汎用に変える（ただし**時間プログラム＝環境条件**として `claim_excludes` を付す）。

## 禁止（＝答えを置く・C0/C1 のまま）

- 目標の速度場・回転方向・配置・巻き数・分裂後の2個を**直接設定**する。
- `relax_until` の条件に**目標形状**を名指しで入れる（例：`until: two_spots_formed`）。

> 停止条件・準備過程が結論を先取りしていないか——[`ANTI_DRIFT.md`](ANTI_DRIFT.md) のチェックリストを必ず通す。
