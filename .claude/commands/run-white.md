---
description: 白（場の法則）を t=0 から回し、スクショと3点報告を作る
argument-hint: <white> [seed]
---
対象：`$ARGUMENTS`（白の名前と、任意で seed）

1. **白を特定する**：`docs/WHITE_CEILINGS.md` と `genesis/registry/models.yaml` から、対応するモデルファイル（`genesis/models/*.py`）と、関連する実験（`experiments/eNNN/`）を探す。
   既存の実験に `run.py` があれば、それを入口として優先する。
2. **始原条件を確認する**（`physics-integrity` skill）：初期条件は一様＋ノイズか、対称なものだけか。結論の形（渦・膜・スポットなど）を置いていないか。置いているものは `put_in` として明記する。
3. **t=0 から回す**：seed を固定して決定的にする。長い計算は `--quick` や小さい格子から始める。3D が本線だが、2D で回した場合は「2D＝候補、正式ではない」と書く。
4. **測る**：`genesis/diagnostics/` の既存の測定器を使う（`measures.assess_level` など）。新しい測定器を作った場合は、結論を知らないことを確認する。
5. **スクショ**：`from tools.snapshot import render_field` で、代表フレーム（初期・中間・最終）を PNG にし、スクラッチパッドに保存してうえきさんに送る。
6. **報告**：`/report` の形式に従う（やさしい説明はチャット、監査用報告は別ファイル）。

到達しなかった Level は「この白の天井」として正直に書く。足して越えようとしない（`docs/ANTI_DRIFT.md`）。
