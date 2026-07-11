# rooms/jobs/ — Live Runner ジョブ台帳（非公式・実計算の記録）

Observatory の Genesis タブが出す**ジョブ要求**を、Python worker（`tools/run_job.py`）が受けて
**g001 参照モデル（複素 TDGL）を t=0 から実計算**した記録。**ブラウザは物理を計算しない。**

- `<job_id>.json`：1 ジョブの状態（`schemas/job.schema.json`）。`status` は
  `queued` / `running` / `done` / `rejected`。`done` は `result_room`（`rooms/candidates/<id>/`）を持つ。
- `ledger.json`：全ジョブの一覧（追記のみ）。

## 掟（誠実さ）

- 変えられるのは**許容探索空間内の始原ノブ 1 つだけ**（`noise_amplitude` / `quench_duration`。
  `genesis/registry/param_ranges.yaml` の範囲を超えられない）。実際に計算へ効くノブだけを公開する。
- 親 Room が g001 でなければ**拒否**（他モデルを g001 で回すと物理をラベル詐称するため）。
- 生成物は**非公式**（`official:false` / `full_3d:not_started`）。**ジョブは official Room を作れない**。
  full-3D 昇格・格子収束・複数 seed・物理監査は別の gated 段階（AI_EXPERIMENT_POLICY / DIMENSION_POLICY）。
- 候補 Room は記録済みの場つきで**再生可能**。`tools/collect_app_data.py` が catalog とともに App へ渡す。

## 再現

```
python tools/run_job.py --request '{"job_id":"job-0001","parent_room":"room-g001-a",
                                    "override":{"param":"noise_amplitude","to":0.005},"seed":0}'
python tools/run_job.py --smoke   # CI 用の小さな end-to-end（コミット木を汚さない）
```
