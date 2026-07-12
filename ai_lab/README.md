# ai_lab/ — AI Genesis Lab（始原条件の自動探索者）

**AI の仕事は完成形を設計することではなく、より深い創発まで自然に発展する始原条件を探すこと**
（`AGENTS.md` / `docs/AI_EXPERIMENT_POLICY.md`）。この最小版 Lab は親 Room の始原条件を**許可された範囲だけ**
変えて t=0 から回し、到達 Level を測り、候補を**非破壊**に保存する。

```
ai_lab/
├─ lab.py          自動実験者（propose → 2D screen → 測定 → 候補保存）
├─ policies/       探索方針（許可 knob・昇格段階）
├─ proposals/      2D スクリーニング済み候補（実行時生成・gitignore）
└─ discoveries/    要約（実行時生成・gitignore）
```

## 使い方
```bash
# legacy（最小・2 knob グリッド）
python ai_lab/lab.py --n 8 --no-write     # 8 候補を 2D スクリーニング（書き込まない）
python ai_lab/lab.py --n 8 --record       # 発見台帳 ai_lab/discoveries/ledger.json に追記（append-only by key・冪等）
python ai_lab/lab.py --review             # 蓄積した発見台帳を要約表示（legacy＋拡張 search をランキング表示）
python ai_lab/lab.py --n 8 --promote-best # 最良候補を local-3D スクリーニングし、非公式の候補 Room を作る

# 拡張エンジン（指示書①・大量自動探索）
python -m ai_lab.lab --mode random --n 200 --parent g001 --seed 1 --quick --record
python -m ai_lab.lab --mode grid   --n 60  --quick        # 決定的：family × 単一 knob グリッド
python -m ai_lab.lab --mode evolutionary --n 40 --seed 1  # 上位 IC を世代で変異

# 法則クラスで Level を登る（深い Level は別の法則が要る・0 から）
python -m ai_lab.lab --mode lawscan --seed 0 --quick --record   # GL L2 < flow L3 < self-replication L7
```

### 法則クラスの登坂（`--mode lawscan`）
GL は 2D で **L2** が上限。深い Level は**法則クラスを変えて 0 から**登る（`genesis/models/` ＋
追加測度 `genesis/diagnostics/higher_levels.py`。成功判定 `measures.assess_level` は不変＝no_touch）：
- **g001 GL**：一様＋ノイズ → 位相巻き渦 **L2**。
- **g002 Boussinesq/RB**：REST＋ノイズ → 自発循環ロールが飽和 **coherent L3**（turbulent≠coherent を flag）。
- **gray_scott 反応拡散**：ノイズ種 → スポット自己複製/分裂 **L7 signature**（spots≠life）。
- **g003 Model H**：co-differentiation **L5** は frontier（測度 WIP）。

### 拡張エンジン（大量自動探索）
- **KNOBS を許可空間全域に**：`noise_amplitude / correlation_length / diffusion_ratio / drive_strength /
  quench_duration`（範囲は `param_ranges.yaml` が強制、超えたら reject）。`correlation_length` は
  低k フィルタ＝空間相関ノイズとして**実際に効く**形で実装。`diffusion_ratio`→Du は explicit stepper を
  CFL sub-step で安定化（`docs/traps_museum.md` T-euler）。数値破綻は `unstable` として正直にフラグ（偽の L0 にしない）。
- **IC family**（第8監査：種・ノイズ・対称・ランダム位相のみ・target 非埋込）：
  振幅系 `white / white_lowk / white_highk / single_seed / sparse_seeds / ring / gradient`、
  位相系 `seeds_phase`（バンプ×一定ランダム位相・巻きなし）/ `spectral_powerlaw` / `bandpass`、
  対照 `real_seed`（純実数）。**`vortex_charges`（巻きを種に置く）は target_encoded なので除外**。
  発見：位相が効く（位相なし real_seed は登らない）。ただし GL は実数場を実数のまま保つので real_seed に
  真の渦は無く、`winding_defect_count` が実数場のドメイン壁を誤検出する（**T-realwinding**）→ Lab の
  物理妥当性ガードが実数場に L2 を与えない（生 level と理由は記録）。→ `docs/PIECES.md` H1b。
- **score**（RANKING のみ・成功ゲートでない）：`Level（支配）＋ 中間複雑性の窓 ＋ 測定信号`。
  複雑さは**非飽和**な log 参加率（entropy が 1.0 に飽和する罠を回避＝`T-entropy-sat`）。
  **Level は `measures.assess_level`（imported）が真**、score は同 Level 内の並べ替えだけ。
- **modes**：`grid`（決定的）/ `random`（seed 決定的サンプル）/ `evolutionary`（elite＋変異の世代）。
- **多親**：`--parent g001`（GL）のみ screen 可。他 law は独自 screen が要る**別（frontier）段階**。

## 蓄積と確認（AI が読み返せる記録）
- **`ai_lab/discoveries/ledger.json`**（commit 対象・**append-only by mutation key**・決定的）＝ AI 自動探索の**永続台帳**。
  `--review` で AI/人が過去の探索（各変異の 2D Level・親との差・3D risk・昇格段階）を確認できる。
- **`rooms/candidates/`**（`--promote-best` が作成）＝ 2D→**local-3D** まで通した**非公式**候補 Room（`official:false`・
  `full_3d:not_started`）。親 `rooms/official/room-g001-a` は**変更せず**別 Room として保存（パラレル宇宙）。
- **`rooms/rejected_in_3d/`** ＝ 3D で崩れた候補（削除せず保存）。
- `ai_lab/proposals/`・`_demo_out/` は実行時の詳細（ephemeral・gitignore）。台帳と候補 Room だけが永続。

正式化（`rooms/official/`）は昇格段階（coarse-global-3D → full-3D → 物理監査）を経て**別段階**で行う。AI は自己昇格しない。

## 不変条件（AI がやってはいけないこと）
- **成功判定コード・保存則・監査閾値を変えない**：Lab は Runner/diagnostics を**import**（再定義しない）。
- **始原側のみ変更**：`genesis/registry/param_ranges.yaml` の search_space で許可された範囲だけ（超えたら reject）。
- **親 Room・`rooms/official/`・過去結果を上書きしない**（別候補として保存）。legacy は 1 knob/提案、
  拡張 search は複数 knob＋IC family を同時に振る（探索を広げるため。ただし各値は許可空間内であることを検証）。
- **自己昇格しない**：Lab は `2d_screened` まで。full-3D 判定・Room 登録は別段階（昇格コマンド／人）。
- **決定的**：legacy は固定グリッド、拡張 search は `--seed` で seed 固定サンプル＝同じ seed で同じ結果（テスト有）。
- **score は成功ゲートでない**：Level（measured）が真、score は同 Level 内のランキングのみ。

## 昇格段階（飛ばせない・`docs/AI_EXPERIMENT_POLICY.md`）
`IDEA → 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT → LOCAL 3D → COARSE GLOBAL 3D → FULL 3D → PHYSICS AUDIT → TEMPLATE → OFFICIAL ROOM`
