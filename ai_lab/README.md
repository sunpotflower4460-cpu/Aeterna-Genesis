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
python ai_lab/lab.py --n 8 --no-write     # 8 候補を 2D スクリーニング（書き込まない）
python ai_lab/lab.py --n 8 --record       # 発見台帳 ai_lab/discoveries/ledger.json に追記（append-only by key・冪等）
python ai_lab/lab.py --review             # 蓄積した発見台帳を要約表示（AI/人が確認する一次記録）
python ai_lab/lab.py --n 8 --promote-best # 最良候補を local-3D スクリーニングし、非公式の候補 Room を作る
```

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
- **一度に一つの knob** を変える。**親 Room・`rooms/official/`・過去結果を上書きしない**（別候補として保存）。
- **自己昇格しない**：Lab は `2d_screened` まで。full-3D 判定・Room 登録は別段階（昇格コマンド／人）。
- **決定的**：探索値は固定グリッド（Math.random 不使用）＝再現可能。

## 昇格段階（飛ばせない・`docs/AI_EXPERIMENT_POLICY.md`）
`IDEA → 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT → LOCAL 3D → COARSE GLOBAL 3D → FULL 3D → PHYSICS AUDIT → TEMPLATE → OFFICIAL ROOM`
