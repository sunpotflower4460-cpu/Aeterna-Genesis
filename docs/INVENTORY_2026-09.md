# INVENTORY 2026-09 — 再始動前の棚卸し（P0）

生成: `python tools/inventory.py --commit faac01d7b525 --confirmed-freeze` · 2026-09-25 · 読み取りのみ。**全ての数値は下の commit オブジェクトから数えた**（作業ツリーは見ない）。

## 測定した commit と凍結点

- 測定 commit: `faac01d7b525225df414a4978fb92ce0932c5805`（tree `de52ce00f51be9954893f2ed38ed8e29d174267c`、2026-09-26T04:13:36+09:00 sunpotflower4460-cpu）
- **凍結点として確定**：bot の自動 trigger 停止と、実行中・待機中 run の排出を確認した後の `main` 先頭。
- 排出の確認: 2026-09-25 19:14 UTC に GitHub Actions API で確認。in_progress の run は 0 件。queued は 2026-09-13 から止まっている 2 件（research-postflight 34748579138、research-continuity 34748579151。どちらも 12 日間開始されていない。このセッションの権限では cancel が 403）のみ。main では easy/latest・research_health・research_continuity の burst がすべて dream-20260925-1180 で揃い、research_maintenance_entrypoint は healthy=True。停止後の最後の bot commit は d95e5b3（18:57 UTC）。
- 復元手順: `git restore --source=faac01d7b525225df414a4978fb92ce0932c5805 -- <path>`（SHA は不変。タグ作成後はタグ名でも可）
- 凍結タグ `evidence-freeze-2026-09`: origin に**未作成**（`git ls-remote` で確認）。作成されるまでは SHA を使う。

## 全体

- 追跡ファイル数: **111,172**
- 追跡ファイル合計サイズ: **5.1 GB**（git blob サイズの合計）

| 最上位 | ファイル数 | サイズ |
|---|---:|---:|
| `app/` | 14,521 | 2.2 GB |
| `rooms/` | 84,911 | 2.2 GB |
| `ai_lab/` | 10,978 | 592.6 MB |
| `experiments/` | 394 | 1.8 MB |
| `docs/` | 80 | 670.3 KB |
| `tests/` | 151 | 512.0 KB |
| `genesis/` | 61 | 380.4 KB |
| `tools/` | 16 | 191.8 KB |
| `.github/` | 14 | 66.7 KB |
| `core/` | 8 | 45.5 KB |
| `(root files)` | 8 | 36.7 KB |
| `genesis_orchestrator/` | 7 | 36.5 KB |
| `room/` | 2 | 33.8 KB |
| `schemas/` | 15 | 33.5 KB |
| `ci/` | 6 | 11.7 KB |

### 大きいサブディレクトリ（rooms / app / ai_lab）

| パス | ファイル数 | サイズ |
|---|---:|---:|
| `app/public/data/` | 14,492 | 2.2 GB |
| `rooms/candidates/` | 69,391 | 2.1 GB |
| `ai_lab/reports/` | 10,851 | 497.4 MB |
| `rooms/rejected_in_3d/` | 3,031 | 170.6 MB |
| `ai_lab/discoveries/` | 33 | 94.2 MB |
| `app/generated/` | 2 | 19.3 MB |
| `rooms/jobs/` | 12,416 | 12.5 MB |
| `ai_lab/dream/` | 78 | 886.8 KB |
| `rooms/official/` | 72 | 554.2 KB |
| `app/src/components/` | 8 | 54.7 KB |
| `ai_lab/campaigns/` | 7 | 22.4 KB |
| `app/src/lib/` | 6 | 12.9 KB |
| `app/src/` | 5 | 11.3 KB |
| `ai_lab/missions/` | 2 | 9.5 KB |
| `ai_lab/prompts/` | 3 | 2.9 KB |

### 大きいファイル上位 20

| ファイル | サイズ |
|---|---:|
| `ai_lab/discoveries/promising_leads.json` | 25.1 MB |
| `ai_lab/reports/easy/root_latest.json` | 19.5 MB |
| `app/generated/catalog.json` | 19.3 MB |
| `app/public/data/catalog.json` | 19.3 MB |
| `ai_lab/discoveries/ledger.json` | 16.9 MB |
| `ai_lab/discoveries/research_memory.json` | 13.8 MB |
| `ai_lab/discoveries/coverage_atlas.json` | 9.9 MB |
| `rooms/jobs/ledger.json` | 6.5 MB |
| `ai_lab/discoveries/hypothesis_graph.json` | 4.8 MB |
| `ai_lab/discoveries/research_continuity.json` | 4.0 MB |
| `ai_lab/discoveries/deep_time_fission.json` | 3.9 MB |
| `ai_lab/discoveries/fission_path_leads.json` | 3.0 MB |
| `ai_lab/discoveries/research_decisions.json` | 2.7 MB |
| `ai_lab/discoveries/event_ledger.json` | 2.0 MB |
| `app/public/data/dream/event-ledger.json` | 2.0 MB |
| `ai_lab/reports/nightly/2026-08-07T07-09-57Z/events.json` | 1.7 MB |
| `ai_lab/reports/gl-haiku-1000-robustness/all_trials_registry.json` | 1.5 MB |
| `ai_lab/discoveries/research_index.json` | 1.2 MB |
| `ai_lab/discoveries/emergence_graph.json` | 1.2 MB |
| `ai_lab/discoveries/view_presets.json` | 1.2 MB |

## 自動生成の候補部屋（`rooms/candidates/`）

- 部屋数（ディレクトリ数）: **6,940**

| genesis_model（白） | 部屋数 |
|---|---:|
| `g001_ginzburg_landau_quench` | 6,939 |
| `g002c3_boussinesq_flux_heated` | 1 |

| reached_level | 部屋数 |
|---|---:|
| 1 | 5,373 |
| 2 | 1,567 |

| candidate_level | 部屋数 |
|---|---:|
| 2 | 5,372 |
| 3 | 1,568 |

> 読み方（測定事実のみ）：候補部屋のほぼ全てが同じ白 `g001_ginzburg_landau_quench`（TDGL）。
> この白の天井は `docs/WHITE_CEILINGS.md` で **L2**（運動量/移流が無い）と既に測定されている。
> candidate_level 3 の由来と、名無し変化 X-… の正体は P2（宝の監査）で 0 から再実行して検証する。
> ここでは価値判断をしない。

## コミットの内訳

期間: 2026-07-27 〜 2026-09-26T04:13:36+09:00（測定 commit から到達できる履歴を `git log` で数えた）

| 作者 | コミット数 |
|---|---:|
| `aeterna-continuity-bot` | 1,760 |
| `aeterna-dream-bot` | 1,155 |
| `aeterna-research-integrity-bot` | 811 |
| `sunpotflower4460-cpu` | 199 |
| `aeterna-free-hypothesis-bot` | 133 |
| `aeterna-science-bridge-bot` | 71 |
| `aeterna-maintenance-bot` | 36 |
| `Claude` | 4 |

- 合計 **4,169**、うち `*-bot` 以外 **203**（約 5%）。最後の `*-bot` 以外のコミット: 2026-09-26T04:13:36+09:00

## GitHub Actions の trigger（測定 commit 時点）

| workflow | trigger |
|---|---|
| `dream-loop-ci` | pull_request, workflow_dispatch |
| `dream-loop` ⏸ | workflow_dispatch · run 内で main へ push |
| `free-hypothesis-ci` | pull_request, workflow_dispatch |
| `free-hypothesis-lab` ⏸ | workflow_dispatch · run 内で main へ push |
| `numerical-portability` | workflow_dispatch, schedule, pull_request |
| `pure-genesis-ci` | pull_request, workflow_dispatch |
| `research-continuity` ⏸ | workflow_dispatch · run 内で main へ push |
| `research-contracts-ci` | pull_request, workflow_dispatch |
| `research-infra-ci` | pull_request, workflow_dispatch |
| `research-maintenance` ⏸ | workflow_dispatch · run 内で main へ push |
| `research-postflight` ⏸ | workflow_dispatch · run 内で main へ push |
| `science-bridge` ⏸ | workflow_dispatch · run 内で main へ push |
| `science-continuity-ci` | pull_request, workflow_dispatch |
| `swarm-profile-ci` | pull_request, workflow_dispatch |

⏸ = P0（2026-09 再始動）で自動 trigger を外し、手動（`workflow_dispatch`）のみにする bot。
上の表は測定 commit 時点の trigger をそのまま示す。停止前の trigger は、P0 より前の commit の各 `.yml` に残っている。
