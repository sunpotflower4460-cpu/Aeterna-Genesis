# ROOM_MODEL.md — Genesis Room とは

**Genesis Room は、一つの保存結果ではなく、一つの始原条件から毎回再生可能な、一つの宇宙の型。**

---

## 1. Evidence Module と Genesis Room の違い

**Evidence Module**（`experiments/e001–e036`）：問いを一つに絞り、その物理現象を検証する。例：「渦リングは自己伝播するか」「対流の臨界値は正しいか」「受動液滴は分裂するか」。

**Genesis Room**（`rooms/`）：一つの始原条件から、**複数段階がどこまで連続して立ち上がったか**を記録する。

- ⚠️ Genesis Room は**複数の実験コードを順番に実行するワークフローではない**。
- 一つの物理系を、**時刻 0 から中断せずに**発展させる。
- **途中で別モデルへ切り替えたら、一つの Genesis Room として認定しない。**

```
Genesis Conditions
      ↓ 同一の時間発展（中断なし・モデル切替なし）
   差 → 局在 → 運動 → さらに自然に出たもの
```

---

## 2. Genesis Conditions（始原条件）

狭義の初期値だけでなく、次をまとめて始原条件として扱う（変更項目はすべて履歴に残す）：

場の種類 ／ 初期分布 ／ 微小ゆらぎ ／ 局所物理法則 ／ 定数 ／ 保存則 ／ 散逸則 ／ 境界条件 ／ 外部エネルギー・物質流 ／ 空間次元 ／ ランダムシード。

**与えてはならない（完成形）：** 完成した身体形状・脳構造・膜の完成形・内外指定・循環器官・モーター・センサー・生存目標・分裂位置/時刻・安定形状へ引き寄せる目標関数・求める現象を直接実行する if 文。

---

## 3. パラレル宇宙（上書き禁止・分岐保存）

Room A で Level 3 まで育ったら、Room A は成功例として**そのまま保存**。その先を試すために **Room A の途中状態を改造してはならない**。代わりに Room A の始原条件を複製し、一部だけ変更した Room B を作る。

```
Root
├─ Room A
│  ├─ Room A-1
│  ├─ Room A-2
│  └─ Room A-3
├─ Room B
└─ Room C
```

- 各 Room は削除・上書きせず、別の可能性として保存。
- 新しい Room が以前より深い Level へ達しても、**以前の Room は残す**。
- これらは上位版/下位版でなく、**異なる始原条件から育ったパラレル宇宙**。

---

## 4. Room データモデル

```
rooms/official/room-g001-a/
├─ room.yaml
├─ genesis.yaml
├─ solver.yaml
├─ diagnostics.yaml
├─ emergence.json
├─ dimension-transfer.yaml
├─ lineage.yaml
├─ render.yaml
└─ runs/
   └─ seed-0001/
      ├─ manifest.json
      ├─ summary.json
      ├─ checksum.json
      └─ preview/
```

**genesis.yaml**（始原条件）:
```yaml
schema_version: 1
model: g001_3d_kz_field
dimension: 3
domain: {size: [128,128,128], spacing: 1.0, boundary: periodic}
fields: {psi: {type: complex_scalar}}
initial_state:
  type: uniform_plus_noise
  mean_amplitude: 0.0
  noise_amplitude: 0.001
  correlation_length: 2.0
protocol: {quench: {start: 0.0, duration: 20.0}}
seed: 42
```

**room.yaml**（到達状態）:
```yaml
room_id: room-g001-a
title: 3D Vortex-Line Genesis
parent_room: null
favorite: true
official: true
emergence: {reached_level: 2, candidate_level: 3}
dimension_status: {exploration_2d: passed, local_3d: passed, coarse_global_3d: passed, full_3d: passed}
physics_status: {conservation: passed, convergence: passed, reproducibility: passed, integrity_audit: passed}
```

**lineage.yaml**（系統）:
```yaml
parent: null
children: [room-g001-a1, room-g001-a2]
changes_from_parent: []
```

---

## 5. 最初の正式 Room 候補

最初から「身体」「宇宙」を狙わない。まず 0→1→2（→3）を正式 3D で再現する基準 Room を作る。**完成した渦線/roll を初期条件に置かない。**

- **G001：3D 対称性破れ・欠陥形成**（3D TDGL / 複素 Ginzburg–Landau / GPE クエンチ）。期待：Lv1 分散/構造因子増大 → Lv2 欠陥/渦線/渦ループ → Lv3 候補 欠陥の移動/再結合。
- **G002：3D 自発対流**（3D Boussinesq / 壁付き Rayleigh–Bénard）。期待：Lv1 不安定モード → Lv2 局在対流構造 → Lv3 循環/輸送。
- **G003：3D 相分離と流体の共発展**（Model H / Cahn–Hilliard–Navier–Stokes / 反応性 phase-field hydrodynamics）。**部品接続でなく、同じ自由エネルギー・化学ポテンシャル・応力・流速場から相分離/界面/流れ/変形/輸送が同時に生じる全体場**として扱う。**最初の統合候補として有望だが G001・G002 より後。**

---

## 6. 昇格段階（IDEA → OFFICIAL ROOM）

```
IDEA → 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT PASSED
→ LOCAL 3D PASSED → COARSE GLOBAL 3D PASSED → FULL 3D REPRODUCIBLE
→ PHYSICS AUDIT PASSED → TEMPLATE CANDIDATE → OFFICIAL ROOM
```

**途中段階を飛ばして正式 Room を作れない。** 詳細は `docs/DIMENSION_POLICY.md`。
