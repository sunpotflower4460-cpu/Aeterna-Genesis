# INVENTORY 2026-09 — 再始動前の棚卸し（P0）

生成: `python tools/inventory.py --commit 97dd6fd4417d` · 2026-09-25 · 読み取りのみ。**全ての数値は下の commit オブジェクトから数えた**（作業ツリーは見ない）。

## 測定した commit と凍結点

- 測定 commit: `97dd6fd4417d404f14d5ce946fc6da0c33c088b9`（tree `452099c88492bd2c182994553cc578c00094bfcc`、2026-09-25T11:54:51+00:00 aeterna-continuity-bot）
- ⚠ **凍結点は未確定（スナップショット）**：この時点では bot がまだ動きうるため、この commit の後にも
  証拠が追加されうる。bot 停止と run の排出を確認してから `--confirmed-freeze` で再生成し、凍結点を確定する。
- 凍結タグ `evidence-freeze-2026-09`: origin に**未作成**（`git ls-remote` で確認）。作成されるまでは SHA を使う。

## 全体

- 追跡ファイル数: **110,455**
- 追跡ファイル合計サイズ: **5.0 GB**（git blob サイズの合計）

| 最上位 | ファイル数 | サイズ |
|---|---:|---:|
| `app/` | 14,425 | 2.2 GB |
| `rooms/` | 84,360 | 2.2 GB |
| `ai_lab/` | 10,910 | 590.0 MB |
| `experiments/` | 394 | 1.8 MB |
| `docs/` | 79 | 664.3 KB |
| `tests/` | 151 | 512.0 KB |
| `genesis/` | 61 | 380.4 KB |
| `tools/` | 15 | 179.2 KB |
| `.github/` | 14 | 66.5 KB |
| `core/` | 8 | 45.5 KB |
| `(root files)` | 8 | 36.6 KB |
| `genesis_orchestrator/` | 7 | 36.5 KB |
| `room/` | 2 | 33.8 KB |
| `schemas/` | 15 | 33.5 KB |
| `ci/` | 6 | 11.7 KB |

### 大きいサブディレクトリ（rooms / app / ai_lab）

| パス | ファイル数 | サイズ |
|---|---:|---:|
| `app/public/data/` | 14,396 | 2.2 GB |
| `rooms/candidates/` | 68,921 | 2.1 GB |
| `ai_lab/reports/` | 10,783 | 495.3 MB |
| `rooms/rejected_in_3d/` | 3,021 | 170.0 MB |
| `ai_lab/discoveries/` | 33 | 93.7 MB |
| `app/generated/` | 2 | 19.2 MB |
| `rooms/jobs/` | 12,345 | 12.5 MB |
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
| `ai_lab/discoveries/promising_leads.json` | 25.0 MB |
| `ai_lab/reports/easy/root_latest.json` | 20.3 MB |
| `app/generated/catalog.json` | 19.1 MB |
| `app/public/data/catalog.json` | 19.1 MB |
| `ai_lab/discoveries/ledger.json` | 16.8 MB |
| `ai_lab/discoveries/research_memory.json` | 13.7 MB |
| `ai_lab/discoveries/coverage_atlas.json` | 9.9 MB |
| `rooms/jobs/ledger.json` | 6.4 MB |
| `ai_lab/discoveries/hypothesis_graph.json` | 4.7 MB |
| `ai_lab/discoveries/research_continuity.json` | 3.9 MB |
| `ai_lab/discoveries/deep_time_fission.json` | 3.9 MB |
| `ai_lab/discoveries/fission_path_leads.json` | 3.0 MB |
| `ai_lab/discoveries/research_decisions.json` | 2.7 MB |
| `ai_lab/discoveries/event_ledger.json` | 2.0 MB |
| `app/public/data/dream/event-ledger.json` | 2.0 MB |
| `ai_lab/reports/nightly/2026-08-07T07-09-57Z/events.json` | 1.7 MB |
| `ai_lab/reports/gl-haiku-1000-robustness/all_trials_registry.json` | 1.5 MB |
| `ai_lab/discoveries/research_index.json` | 1.2 MB |
| `ai_lab/discoveries/emergence_graph.json` | 1.2 MB |
| `ai_lab/discoveries/view_presets.json` | 1.1 MB |

## 自動生成の候補部屋（`rooms/candidates/`）

- 部屋数（ディレクトリ数）: **6,893**

| genesis_model（白） | 部屋数 |
|---|---:|
| `g001_ginzburg_landau_quench` | 6,892 |
| `g002c3_boussinesq_flux_heated` | 1 |

| reached_level | 部屋数 |
|---|---:|
| 1 | 5,329 |
| 2 | 1,564 |

| candidate_level | 部屋数 |
|---|---:|
| 2 | 5,328 |
| 3 | 1,565 |

> 読み方（測定事実のみ）：候補部屋のほぼ全てが同じ白 `g001_ginzburg_landau_quench`（TDGL）。
> この白の天井は `docs/WHITE_CEILINGS.md` で **L2**（運動量/移流が無い）と既に測定されている。
> candidate_level 3 の由来と、名無し変化 X-… の正体は P2（宝の監査）で 0 から再実行して検証する。
> ここでは価値判断をしない。

## コミットの内訳

期間: 2026-07-27 〜 2026-09-25T11:54:51+00:00（測定 commit から到達できる履歴を `git log` で数えた）

| 作者 | コミット数 |
|---|---:|
| `aeterna-continuity-bot` | 1,744 |
| `aeterna-dream-bot` | 1,148 |
| `aeterna-research-integrity-bot` | 806 |
| `sunpotflower4460-cpu` | 198 |
| `aeterna-free-hypothesis-bot` | 132 |
| `aeterna-science-bridge-bot` | 70 |
| `aeterna-maintenance-bot` | 35 |
| `Claude` | 1 |

- 合計 **4,134**、うち `*-bot` 以外 **199**（約 5%）。最後の `*-bot` 以外のコミット: 2026-09-01T15:45:21+09:00

## GitHub Actions の trigger（測定 commit 時点）

| workflow | trigger |
|---|---|
| `dream-loop-ci` | pull_request, workflow_dispatch |
| `dream-loop` ⏸ | push, schedule, workflow_dispatch · run 内で main へ push |
| `free-hypothesis-ci` | pull_request, workflow_dispatch |
| `free-hypothesis-lab` ⏸ | schedule, push, workflow_dispatch · run 内で main へ push |
| `numerical-portability` | workflow_dispatch, schedule, pull_request |
| `pure-genesis-ci` | pull_request, workflow_dispatch |
| `research-continuity` ⏸ | workflow_run, workflow_dispatch · run 内で main へ push |
| `research-contracts-ci` | pull_request, workflow_dispatch |
| `research-infra-ci` | pull_request, workflow_dispatch |
| `research-maintenance` ⏸ | schedule, workflow_dispatch · run 内で main へ push |
| `research-postflight` ⏸ | workflow_run, workflow_dispatch · run 内で main へ push |
| `science-bridge` ⏸ | schedule, push, workflow_dispatch · run 内で main へ push |
| `science-continuity-ci` | pull_request, workflow_dispatch |
| `swarm-profile-ci` | pull_request, workflow_dispatch |

⏸ = P0（2026-09 再始動）で自動 trigger を外し、手動（`workflow_dispatch`）のみにする bot。
上の表は測定 commit 時点の元の trigger を示す（停止後の状態は各 `.yml` 先頭の注記を参照）。
