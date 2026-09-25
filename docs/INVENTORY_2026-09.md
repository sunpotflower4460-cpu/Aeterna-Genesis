# INVENTORY 2026-09 — 再始動前の棚卸し（P0）

生成: `python tools/inventory.py` · 2026-09-25 · 読み取りのみ（研究データは変更しない）。

## 凍結点

- 凍結 commit: `5a6691b8dc7be1bcc9a5e1c6617493d5d0d3beec`（bot を止める直前の `main`）
- 凍結タグ: `evidence-freeze-2026-09`（この commit を指す）。ここに全バイトが残るので、
  以降の整理で作業ツリーから外すものは `git restore --source=evidence-freeze-2026-09 -- <path>` で復元できる。

## 全体

- 追跡ファイル数: **110,364**
- 追跡ファイル合計サイズ: **5.0 GB**

| 最上位 | ファイル数 | サイズ |
|---|---:|---:|
| `app/` | 14,413 | 2.2 GB |
| `rooms/` | 84,291 | 2.2 GB |
| `ai_lab/` | 10,900 | 589.2 MB |
| `experiments/` | 394 | 1.8 MB |
| `docs/` | 79 | 664.3 KB |
| `tests/` | 151 | 512.0 KB |
| `genesis/` | 61 | 380.4 KB |
| `tools/` | 15 | 179.2 KB |
| `.github/` | 14 | 66.7 KB |
| `core/` | 8 | 45.5 KB |
| `(root files)` | 8 | 36.6 KB |
| `genesis_orchestrator/` | 7 | 36.5 KB |
| `room/` | 2 | 33.8 KB |
| `schemas/` | 15 | 33.5 KB |
| `ci/` | 6 | 11.7 KB |

### 大きいサブディレクトリ（rooms / app / ai_lab）

| パス | ファイル数 | サイズ |
|---|---:|---:|
| `app/public/data/` | 14,384 | 2.2 GB |
| `rooms/candidates/` | 68,861 | 2.0 GB |
| `ai_lab/reports/` | 10,773 | 494.6 MB |
| `rooms/rejected_in_3d/` | 3,021 | 170.0 MB |
| `ai_lab/discoveries/` | 33 | 93.7 MB |
| `app/generated/` | 2 | 19.1 MB |
| `rooms/jobs/` | 12,336 | 12.4 MB |
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
| `ai_lab/reports/easy/root_latest.json` | 20.1 MB |
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
| `ai_lab/discoveries/event_ledger.json` | 1.9 MB |
| `app/public/data/dream/event-ledger.json` | 1.9 MB |
| `ai_lab/reports/nightly/2026-08-07T07-09-57Z/events.json` | 1.7 MB |
| `ai_lab/reports/gl-haiku-1000-robustness/all_trials_registry.json` | 1.5 MB |
| `ai_lab/discoveries/research_index.json` | 1.2 MB |
| `ai_lab/discoveries/emergence_graph.json` | 1.2 MB |
| `ai_lab/discoveries/view_presets.json` | 1.1 MB |

## 自動生成の候補部屋（`rooms/candidates/`）

- 部屋数: **6,888**

| genesis_model（白） | 部屋数 |
|---|---:|
| `g001_ginzburg_landau_quench` | 6,886 |
| `(no room.yaml)` | 1 |
| `g002c3_boussinesq_flux_heated` | 1 |

| reached_level | 部屋数 |
|---|---:|
| 1 | 5,323 |
| 2 | 1,564 |

| candidate_level | 部屋数 |
|---|---:|
| 2 | 5,322 |
| 3 | 1,565 |

> 読み方（測定事実のみ）：候補部屋のほぼ全てが同じ白 `g001_ginzburg_landau_quench`（TDGL）。
> この白の天井は `docs/WHITE_CEILINGS.md` で **L2**（運動量/移流が無い）と既に測定されている。
> candidate_level 3 の由来と、名無し変化 X-… の正体は P2（宝の監査）で 0 から再実行して検証する。
> ここでは価値判断をしない。

## コミットの内訳

- 期間 2026-07-27 .. 2026-09-25: 合計 **4,125** コミット、うち人間アカウント **198**（約 5%）、`aeterna-dream-bot` 単独で 1,146。
- 最後の人間コミット: 2026-09-01
- 出典: GitHub commit search (repo:sunpotflower4460-cpu/Aeterna-Genesis), 2026-09-25（ローカル clone は shallow のため git log では再計算できない）

## GitHub Actions の trigger（この棚卸し時点）

| workflow | trigger |
|---|---|
| `dream-loop-ci` | pull_request, workflow_dispatch |
| `dream-loop` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `free-hypothesis-ci` | pull_request, workflow_dispatch |
| `free-hypothesis-lab` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `numerical-portability` | workflow_dispatch, schedule, pull_request |
| `pure-genesis-ci` | pull_request, workflow_dispatch |
| `research-continuity` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `research-contracts-ci` | pull_request, workflow_dispatch |
| `research-infra-ci` | pull_request, workflow_dispatch |
| `research-maintenance` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `research-postflight` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `science-bridge` ⏸ | workflow_dispatch · run 内で main へ push する手順あり |
| `science-continuity-ci` | pull_request, workflow_dispatch |
| `swarm-profile-ci` | pull_request, workflow_dispatch |

⏸ = 2026-09 再始動のため自動 trigger を外し、手動（`workflow_dispatch`）のみにした bot。
元の trigger は凍結 commit の各 `.yml` に残っている。
