# SOURCE_INVENTORY — 読んだ資料と、既存 P10 資産の所在（v0.1）

基準コミット：`649fd7e0de259a30048684ba98480739be1edcd9`（main）。作業ブランチ：`audit/p10-transport-free-energy-v01`（専用 worktree）。開始時の作業ツリーは clean。

## 1. 必読資料（依頼書 §2）と読んだ範囲

| # | ファイル | 読んだ範囲 | 要点 |
|---|---|---|---|
| 1 | `AGENTS.md` | 全文 | 三層構造、報告の 3 点セット（📸・😊・📄 別ファイル）、「法則は現実の化学・物理だけ」、「起きてほしい結果を言い換えた規則は置かない」 |
| 2 | `docs/ANTI_DRIFT.md` | 見出しと合言葉（全文は未読） | 答えを置くな。初期条件に結論を入れない |
| 3 | `docs/PHYSICS_INTEGRITY.md` | 全文 | 物理として主張する最低条件、禁止事項、役割（E/V/S/N/F/Q）、第8監査（target_encoded） |
| 4 | `docs/EVIDENCE_CONTRACT_V2.md` | 見出しと §9 近辺のみ | 証拠の二軸、閾値の前登録 |
| 5 | `docs/DIMENSION_POLICY.md` | 全文 | 2D 探索と 3D 正式の分担。2D 成功は候補であり正式成功ではない |
| 6 | `docs/VERTICAL_EMERGENCE_CONTRACT.md` | §2（三ゲート）、見出し | Gate I 導出／II 有効法則／III 下位実現 |
| 7 | `docs/frontier/F0_P10_active_vessel.md` | 全文 | P10 の F0（docs-only、承認待ち停止と記載）。式 F、μ_φ、輸送式 |
| 8 | `genesis/diagnostics/vessel_permeability.py` | 全文 | 既存 V0（3D 固定球）。SG 流束、`μ = RT ln c + χφ`、`J = −D(∇c + (χ/RT) c∇φ)` |
| 9 | `tests/test_vessel_permeability.py` | 全文 | 既存 V0 の 12 テスト（ベースラインで **12 passed**） |

`CLAUDE.md` は読んだ（3 点報告、3D 先行の規則、ladder の扱い）。本監査は Room でも実験でもないため、3D 先行・ladder 更新の対象外であり、その理由を INDEPENDENT_AUDIT.md に書く。

## 2. P10 関連ファイルの一覧

| 種別 | パス | 状態 |
|---|---|---|
| 設計（F0） | `docs/frontier/F0_P10_active_vessel.md` | 既存・変更禁止 |
| 既存 V0 実装 | `genesis/diagnostics/vessel_permeability.py` | 既存・読み取りのみ（コミット `bfaf9fc15`） |
| 既存 V0 テスト | `tests/test_vessel_permeability.py` | 既存・変更禁止 |
| 関連（別白の P10 名称） | `docs/reports/2026-09-26-p10-torus.md`、`tools/torus_*.py`、`tests/test_torus.py` | **番号衝突**：「P10」がトーラス白にも使われている。監査では参照しない |
| 関連（F0 の前提） | `docs/frontier/F0_P01_active_droplet.md`、`docs/WHITE_CEILINGS.md` | 参考のみ |

## 3. 基準時点のハッシュ（依頼 §1.2 の記録）

- 対象ファイルの SHA-256（先頭 16 桁は `sha256sum` の出力、全桁は `results/manifest.json`）：
  - `docs/frontier/F0_P10_active_vessel.md`：`e7050c57c2e96a47…`
  - `genesis/diagnostics/vessel_permeability.py`：`d2566177b03bd5d7…`
  - `tests/test_vessel_permeability.py`：`06fe810408d7c5f4…`
  - `AGENTS.md`：`e5b6a466aeff19cf…`
- 保護ディレクトリの git tree SHA（基準コミット時点）：`docs` `a4432723…`、`experiments` `b34e9214…`、`genesis` `68e5de7c…`、`rooms` `a7006c21…`、`ai_lab` `2e55df98…`、`research` `d50a8d9b…`、`tests` `90824a53…`、`schemas` `f9b6b054…`、`AGENTS.md` `078df436…`、`pyproject.toml` `2f1a9b40…`。

## 4. 既存資産の状態（依頼の確認事項）

- CI 設定：`.github/workflows/*.yml`（18 本）。本監査は CI を変更しない。`pyproject.toml` の `testpaths = ["tests"]` のため、`audits/` 配下のテストは既存スイートに混ざらない。
- テスト基底名（`test_variation.py` など）は既存 `tests/` に衝突がない。
- 既存 V0 の 12 テストは基準時点で全通過（`pytest tests/test_vessel_permeability.py`、55 秒）。

## 5. 文書間の不一致（記録のみ・修正しない）

- F0 は「実装: none・承認待ち停止」と書くが、V0 の実装とテストが既にある（D-7）。
- F0 §2 の輸送式は `div(D∇c)` で、本文の「選択透過は χ_i の分配から創発」を書かれた式から導けない（D-1）。
- 「P10」の番号がトーラス白（2026-09-26 報告）にも使われている（D-7）。
