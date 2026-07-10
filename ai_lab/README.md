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
python ai_lab/lab.py --n 6 --quick --no-write   # 6 候補を 2D スクリーニング（書き込まない）
python ai_lab/lab.py --n 6 --quick              # ai_lab/proposals/ に保存
```

## 不変条件（AI がやってはいけないこと）
- **成功判定コード・保存則・監査閾値を変えない**：Lab は Runner/diagnostics を**import**（再定義しない）。
- **始原側のみ変更**：`genesis/registry/param_ranges.yaml` の search_space で許可された範囲だけ（超えたら reject）。
- **一度に一つの knob** を変える。**親 Room・`rooms/official/`・過去結果を上書きしない**（別候補として保存）。
- **自己昇格しない**：Lab は `2d_screened` まで。full-3D 判定・Room 登録は別段階（昇格コマンド／人）。
- **決定的**：探索値は固定グリッド（Math.random 不使用）＝再現可能。

## 昇格段階（飛ばせない・`docs/AI_EXPERIMENT_POLICY.md`）
`IDEA → 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT → LOCAL 3D → COARSE GLOBAL 3D → FULL 3D → PHYSICS AUDIT → TEMPLATE → OFFICIAL ROOM`
