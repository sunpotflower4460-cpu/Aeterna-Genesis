# archive/ — 作業ツリーから外した生成データの目録

P3（2026-09 再始動）で、bot が大量に生成したデータを**作業ツリーから外した**（git の履歴には全部残っている）。
何を外すかは P2 の監査（[`docs/TREASURE_AUDIT.md`](../docs/TREASURE_AUDIT.md)）で決めた。

`MANIFEST.jsonl.gz` の構成：
- 1 行目：`source_commit`（外す直前の commit）、ファイル数、合計バイト数
- 2 行目以降：外した**全ファイル**の `{path, blob, size, reason}`（`blob` は source_commit 時点の git blob id）

| reason | 中身 |
|---|---|
| index-only room | L1 の seed 違いの重複 Room（丸ごと）。1 行の要約は `audit/candidates.jsonl` |
| distill room display frames | L2 の重複 Room の表示用フレーム。キーフレームは `audit/candidates_keyframes.npz` |
| generated app data | `app/public/data`、`app/generated`（`tools/build_catalog.py` と `tools/collect_app_data.py` で再生成できる） |
| timestamped bot report | `ai_lab/reports/{nightly,easy}/20*/`（参照されている 2 つは残した） |

```bash
python tools/archive.py verify --sample 20     # 記録した blob が source_commit で解決できるか
python tools/archive.py restore rooms/candidates/room-auto-dream-20260807-0001-native-window-v000-2dscreen-s87702
python tools/archive.py restore rooms/candidates   # 全 Room を戻す（約 2 GB）
```

Observatory のデータは、deploy の前に生成する。

```bash
python tools/build_catalog.py && python tools/collect_app_data.py
```
