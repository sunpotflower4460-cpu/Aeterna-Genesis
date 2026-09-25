# CLAUDE.md — Claude Code 向けの実務メモ

原則と禁止事項は **[`AGENTS.md`](AGENTS.md) が正本**（最初に読む）。ここは Claude Code が手を動かすための実務だけ。
合言葉：**「それは育ったのか、置いたのか？」**

## いまの状態（2026-09 再始動）

- 2026-07〜09 の自動研究 bot は **P0 で停止済み**。凍結点は `faac01d`（[`docs/INVENTORY_2026-09.md`](docs/INVENTORY_2026-09.md)）。
  6 本の bot workflow は `workflow_dispatch` のみ。**うえきさんの判断なしに trigger を戻さない。**
- 再始動プラン：P0 凍結 → P1 土台 → P2 研究の理解＋宝の監査 → P3 アーカイブ化 → P4 水槽ビューア → P5 整理と小さな自動化。
- 研究は **対話主導**。AI が自走して main に書き込み続ける運用には戻さない。

## セットアップ

クラウドでは `.claude/hooks/session-start.sh` が自動で `pip install -r requirements.txt` と `app/` の `npm install` を行う。
手元では次を実行する。

```bash
pip install -r requirements.txt            # numpy, scipy, PyYAML, jsonschema, pytest
export PYTHONPATH=$PWD                      # core / genesis / ai_lab をリポジトリ直下から import
(cd app && npm install && npm run typecheck)
```

## テスト

```bash
pytest -m "not slow" -q        # 速い一式（661件・約3分）
pytest tests/test_<name>.py    # 触った所だけ
pytest -q                      # 全部（732件・1コアで20分以上）
```

marker は `pyproject.toml` に定義してある。
- `slow`：実測で 5 秒を超えるもの（`tests/slow_tests.txt` に列挙し、`tests/conftest.py` が付ける）。
- `network`：外部に接続するもの。
- `archived`：凍結した旧 bot 系。

CI（`.github/workflows/*-ci.yml`）はファイルを明示して実行するので、`addopts` で marker を除外していない。

## どこに何があるか

| 場所 | 中身 |
|---|---|
| `genesis/models/` | 場の法則（白）。`make_initial` / `step` が基本形（モデルごとに差あり） |
| `genesis/diagnostics/` | 測定器（`measures.py` の `assess_level` など）。**測定器は結論を知らない** |
| `genesis/runners/runner.py` | Room の共通ランナー（現状 TDGL のみ）。`--mode 2d-screen|local-3d|…` |
| `experiments/eNNN/` | 証拠庫。削除・番号変更しない。各 `AUDIT.md` に7監査の結果 |
| `rooms/official/` | 正式 Room（g001/g002/g003）。`rooms/candidates/` は bot が生成した候補（P2 で監査予定） |
| `docs/WHITE_CEILINGS.md` | 白ごとの天井地図＝現在地の最重要文書 |
| `tools/snapshot.py` | numpy＋zlib だけで PNG を作る（`render_field(arr, path)`） |
| `tools/inventory.py` | 1 つの commit を読み取り専用で棚卸しする |
| `app/` | Observatory（React＋three.js）。データは `tools/build_catalog.py` → `tools/collect_app_data.py` で作る |
| `ai_lab/dream/` | 停止した自動研究の実装（P5 で整理予定。新しい作業の足場にしない） |

## コマンド（`.claude/commands/`）

- `/status`：いまの現在地を短く要約する。
- `/run-white <白> [seed]`：白を t=0 から回し、PNG と3点報告を作る。
- `/audit <room|X-id|experiment>`：7監査、第8監査、決定性を確認する。
- `/report`：うえきさん向けのやさしい説明と監査用報告を**別々のファイル**で出す。
- `/propose`：次の実験提案を `research/inbox/` に置く（採否は人が決める）。

「育ったのか、置いたのか」の自己点検は skill `physics-integrity` を使う。

## 報告（毎回・必須。AGENTS.md「報告フォーマット」）

1. 📸 スクリーンショット（`tools/snapshot.py`）
2. 😊 やさしい説明（チャット本文）
3. 📄 監査用報告（別ファイル。主張・測定・限界・再現手順・規律チェック）

## 作業の約束

- ブランチを切って PR にする。main への直接 push や bot 的な連投はしない。
- 研究データ（`rooms/`、`experiments/`、`ai_lab/discoveries/`）は削除しない。整理は「別の棚へ移す＋マニフェストで復元可能」にする（P3）。
- `rooms/candidates/` と `ai_lab/discoveries/` の数値を見出しにするときは、P2 の監査結果（`audit/`）を通してからにする。
