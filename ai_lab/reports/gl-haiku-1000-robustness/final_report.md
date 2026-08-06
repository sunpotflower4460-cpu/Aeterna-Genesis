# Aeterna Genesis 1000試行キャンペーン 最終報告

- campaign_id: `gl-haiku-1000-robustness`
- 実行方式: `genesis_orchestrator`（専用DB `runtime/gl-haiku-1000.sqlite3`）+ worker 4並列
- 開始コミット: `8223b2633f7240f0901211e620f1695bdaf7d8f0`（作業ツリーclean、`test_genesis_orchestrator.py` / `test_haiku_1000_campaign.py` 全pass後に開始）
- 実行日: 2026-08-06

## 1. 完全性判定

`tools/autopilot_campaign_report.py report --require-complete` を実行し、**終了コード 0（成功）** を確認した。

| integrity check | 結果 |
|---|---|
| 初期2Dジョブが正確に1000件 | ✅ true |
| job IDがすべて一意 | ✅ true |
| 200条件が一致 | ✅ true |
| 各条件が5 seedを保有 | ✅ true |
| official配下への出力パスが0件 | ✅ true |
| official treeが不変 | ✅ true (baseline/現在ともに file_count=72, tree_sha256=`9cecff9df638dd9e8cb57e36e8bfa1d7ec997ce05de40d04902b0738aef88604`) |
| **campaign_complete** | ✅ true |

キャンペーンは完全性を保って完了した。

## 2. 件数集計

- 初期2Dジョブ: **1000件**（期待通り）
- 総ジョブ数: **2000件**（2D 1000 + local-3D 1000）
- stage別件数: `2d-screen` 1000 / `local-3d` 1000
- status別件数: `done` 2000（`queued` / `running` / `failed` / `rejected` / `waiting_approval` はいずれも0）
- 2D通過数: **1000 / 1000**
- local-3D作成件数: 1000（2D通過ジョブ1件につきlocal-3Dが正確に1件、超過・不足なし）
- local-3D完了数: 1000 / local-3D通過数: **1000 / 1000**
- 5 seed中5/5でlocal-3Dを通過した条件数: **200 / 200条件**

## 3. インフラ障害・再試行・worker再起動

- `failures.json`: **0件**（インフラ障害の記録なし）
- worker再起動: **なし**（4 workerは起動後、queuedが尽きるまで動作し、途中でstale runningになることも、PIDが落ちることもなく正常終了した）
- 科学的失敗の削除・自動再試行: **実施していない**（該当する失敗自体が発生しなかった）
- SQLite行の直接編集: **実施していない**

## 4. 変更していないことの確認

- `rooms/official/` への書き込み: **0件**（`no_official_output_paths: true`）。tree SHA-256はbaseline取得時と実行後で完全一致。
- `coarse-global-3d`: **0件**
- `full-3d`: **0件**
- 物理モデル・runner・diagnostics・成功判定閾値・campaign YAML・parameter registryは本キャンペーン中に一切編集していない。

## 5. 上位10条件（機械的ランキング）

ランキング基準（`ai_lab/campaigns/gl-haiku-1000.yaml` と集計ツールが機械的に適用したもの、優先順）:
1. 5 seed中のlocal-3D通過数（降順）
2. local-3Dの最小到達Level（降順）
3. local-3Dの平均到達Level（降順）
4. 5 seed中の2D通過数（降順）
5. local-3Dの平均欠陥数（降順、同点処理）
6. quench_duration（短い方、同点処理）
7. noise_amplitude（低い方、最終同点処理）

| 順位 | noise_amplitude | quench_duration | 2D通過数 | local-3D作成数 | local-3D通過数 | local-3D最小Level | local-3D平均Level | local-3D平均欠陥数 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.0033598183 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 3.4 |
| 2 | 0.0069519280 | 2.75 | 5/5 | 5 | 5/5 | 1 | 1.2 | 3.0 |
| 3 | 0.0002636651 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 4 | 0.0003792690 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 5 | 0.0005455595 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 6 | 0.0011288379 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 7 | 0.0016237767 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 8 | 0.0023357215 | 2.00 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 9 | 0.0005455595 | 2.75 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |
| 10 | 0.0007847600 | 2.75 | 5/5 | 5 | 5/5 | 1 | 1.2 | 2.8 |

全件は `ai_lab/reports/gl-haiku-1000-robustness/ranked_conditions.csv`（200条件、比較可能形式）を参照。

### 5.1 この上位10条件が「測定的に優れた10条件」ではないことの確認

上表を「明確に優れた10条件」と読むことは誤りである。基準1〜4（通過数・到達Level）は200条件全てで完全同点のため、順位は基準5（local-3Dの平均欠陥数）以降で決まる。200条件のlocal-3D平均欠陥数の分布を確認したところ：

- 平均欠陥数 3.4（rank 1, v160）: 該当1条件のみ — 200条件中で唯一の値
- 平均欠陥数 3.0（rank 2, v181）: 該当1条件のみ — 200条件中で唯一の値
- 平均欠陥数 2.8（rank 3〜10はここに属する）: **該当51条件**（200条件中）

つまり、真に他と異なる測定値によって区別できるのは **rank 1とrank 2の2条件のみ**である。rank 3〜10は「平均欠陥数2.8」という51条件が共有する同点集団のうちの8条件にすぎず、その中での並び順（quench_duration昇順→noise_amplitude昇順）は測定値ではなく機械的なタイブレークのみで決まっている。したがって、**この機械的ランキングの上位10条件は、ランキング規則で定義された順位ではあるが、大部分（8/10）は測定的に他の条件から明確に区別されていない**、という判定を明記する。

## 6. 観測された傾向

**重要な留保**: 今回の閾値（`min_reached_level: 1`）では、**200条件すべてが5 seed中5/5で2D・local-3Dの両方を通過した**。つまり基準1〜4（通過数・到達Level）では全条件が完全同点になり、上位表の順位は主に基準5以降の同点処理（local-3Dの平均欠陥数→quench_duration→noise_amplitude）で決まっている。この閾値設定では200条件・1000試行の範囲内で有意な合否の差は観測されなかった。

その上で、同点処理に使われた「local-3Dの平均欠陥数」を条件横断で見ると、quench_durationとの間に単調な関連が観測された（5 seed平均、量子化はquench_durationの10段階ごと）。

| quench_duration | 平均欠陥数（20条件平均） |
|---|---|
| 2.00 | 2.48 |
| 2.75 | 2.48 |
| 3.25 | 2.33 |
| 3.75 | 2.13 |
| 4.00 | 2.01 |
| 4.25 | 1.93 |
| 4.75 | 1.72 |
| 5.50 | 1.42 |
| 7.50 | 0.69 |
| 12.00 | 0.00 |

今回のquick-grid、5 seedの範囲では、quench_durationが長いほどlocal-3Dの平均欠陥数が単調に少ない、という関連が観測された。これは前回の小規模試験（seed 0、4.0付近が相対的に良好）とは異なる方向の関連であり、両者は同一の指標を比較したものではない点に注意が必要である。また、通過判定そのもの（reached_level >= 1）は本キャンペーンの範囲では条件間で差がつかなかったため、「欠陥数が少ない = 成功しやすい」と直接結び付けることはできない。

noise_amplitude（1e-5〜1e-2、対数20段階）については、上位10条件の値が特定の狭い範囲に集中する明確な傾向は確認できなかった。低・中・高noiseの各帯で同じquench_duration依存の単調減少傾向が再現するかを次節で確認する。

## 7. 限界

- 本キャンペーンはquick-grid・5 seed・2変数（noise_amplitude, quench_duration）のみの2D→local-3Dスクリーニングであり、coarse-global-3d・full-3dの重い3D確認は実施していない。
- `min_reached_level: 1` という緩い閾値の下では200条件全てが通過したため、今回のランキングは「通過するかどうか」ではなく同点処理項目（主に平均欠陥数と機械的なタイブレーク順）で決まっている。上記5.1節で確認した通り、機械的ランキングの上位10件のうち測定値で真に区別できるのはrank 1・2の2条件のみであり、rank 3〜10は51条件が共有する同点集団からの機械的な抜粋にすぎない。この値やこの条件が普遍的な最適値であるとは断定できない。この条件が原因で必ず成功するとも言えない。
- 5 seedは偶然による成功を除外する目的には有用だが、本キャンペーンでは全条件が5/5で通過したため、seed間のロバスト性の「差」を弁別する材料にはならなかった。
- 上位ランキングは公式のスコアではなく、次段階（重いlocal/coarse/full-3D確認）に進める候補の優先順位付けに過ぎない。

## 8. 全生データの保持方針と代表条件の選定

### 8.1 保持方針（人間承認済み）

2000ジョブ全件について、生の3D場データ（field.json等）を含む完全なRoomデータを残すと約1.4GB（うち非公式Room `rooms/candidates/` 単体で724MB、Observatory用ミラー `app/public/data/` が650MB）に達し、リポジトリ肥大化が大きく後戻りしにくいコストを伴う。人間の承認の下、以下の方針を採用した。

1. **全2000ジョブの完全な履歴**は `ai_lab/reports/gl-haiku-1000-robustness/all_trials_registry.json` に残す。campaign ID・trial ID・job ID・stage・パラメータ・seed・status・reached_level・測定診断値・checksum・エラー理由・開始コミットSHA（`8223b2633f7240f0901211e620f1695bdaf7d8f0`）・出力先を含み、同一条件の意図しない再試行を防げる粒度を持つ。全2000件・パラメータ欠落0件・done件のchecksum/測定値欠落0件を確認済み。
2. **成功・不採用にかかわらず生の場データ・完全なRoomデータは、後述の代表条件セット以外は削除**した（`rooms/jobs/*.json` によるコンパクトなステータス記録とディスカバリー台帳は保持）。
3. **完全な生データを保持する条件**は、5.1節の分析結果（測定的に明確な差はrank 1・2の2条件のみで、それ以外は51条件タイの機械的抜粋）を踏まえ、「上位10件をそのまま保持」ではなく、以下の代表性を優先した層別セットに置き換えた。

### 8.2 代表条件セット（全生データ保持・10条件）

- 測定的に真に区別される最強条件（5.1節）: rank 1（v160）, rank 2（v181）
- noise_amplitude 低・中・高 × quench_duration 速・中・遅 の3×3層別格子（v160はこの格子の「高noise×速quench」枠と一致するため重複なし）

| trial_id | noise帯 | quench帯 | noise_amplitude | quench_duration | rank | 2D通過 | local-3D通過 | 平均Level | 平均欠陥数 |
|---|---|---|---|---|---|---|---|---|---|
| h001-v030 | 低 | 速 | 0.0000297635 | 2.00 | 83 | 5/5 | 5/5 | 1.0 | 2.2 |
| h001-v034 | 低 | 中 | 0.0000297635 | 4.00 | 142 | 5/5 | 5/5 | 1.0 | 1.2 |
| h001-v039 | 低 | 遅 | 0.0000297635 | 12.00 | 184 | 5/5 | 5/5 | 1.0 | 0.0 |
| h001-v100 | 中 | 速 | 0.0003792690 | 2.00 | 4 | 5/5 | 5/5 | 1.2 | 2.8 |
| h001-v104 | 中 | 中 | 0.0003792690 | 4.00 | 77 | 5/5 | 5/5 | 1.0 | 2.4 |
| h001-v109 | 中 | 遅 | 0.0003792690 | 12.00 | 191 | 5/5 | 5/5 | 1.0 | 0.0 |
| h001-v160 | 高 | 速 | 0.0033598183 | 2.00 | **1** | 5/5 | 5/5 | 1.2 | **3.4**（200条件中唯一の最大値） |
| h001-v164 | 高 | 中 | 0.0033598183 | 4.00 | 26 | 5/5 | 5/5 | 1.2 | 2.8 |
| h001-v169 | 高 | 遅 | 0.0033598183 | 12.00 | 197 | 5/5 | 5/5 | 1.0 | 0.0 |
| h001-v181 | 高 | 速+ | 0.0069519280 | 2.75 | **2** | 5/5 | 5/5 | 1.2 | **3.0**（200条件中唯一の2位値） |

この層別サンプルは合計31.6MB（100 Room: 10条件×5 seed×2 stage）で、機械的タイブレークに依存せず「quench_durationが長いほど平均欠陥数が単調に減る」という第6節の傾向がnoise帯を問わず再現することを直接示している（各noise帯で 速>中>遅 の順に欠陥数が単調減少）。

### 8.3 次の確認候補（最大10条件）

上記代表条件セットを、人間承認の下で重い3D確認（coarse-global-3d / full-3d）を検討する次段階の候補として提示する。5.1節の通り、これは「測定的に優れた10条件」ではなく「観測範囲を代表する10条件＋唯一測定的に区別できた2条件」である。

1. h001-v160: noise_amplitude=0.0033598183, quench_duration=2.00（200条件中で平均欠陥数が唯一最大）
2. h001-v181: noise_amplitude=0.0069519280, quench_duration=2.75（200条件中で平均欠陥数が唯一2位）
3. h001-v030: noise_amplitude=0.0000297635, quench_duration=2.00（低noise・速quench代表）
4. h001-v034: noise_amplitude=0.0000297635, quench_duration=4.00（低noise・中quench代表）
5. h001-v039: noise_amplitude=0.0000297635, quench_duration=12.00（低noise・遅quench代表）
6. h001-v100: noise_amplitude=0.0003792690, quench_duration=2.00（中noise・速quench代表）
7. h001-v104: noise_amplitude=0.0003792690, quench_duration=4.00（中noise・中quench代表）
8. h001-v109: noise_amplitude=0.0003792690, quench_duration=12.00（中noise・遅quench代表）
9. h001-v164: noise_amplitude=0.0033598183, quench_duration=4.00（高noise・中quench代表）
10. h001-v169: noise_amplitude=0.0033598183, quench_duration=12.00（高noise・遅quench代表）

これらの重い3D確認（coarse-global-3d / full-3d）実施の可否、および公式Roomへの昇格判断は人間が行う。残る190条件（950生ジョブ）の生データは削除済みだが、`all_trials_registry.json` に全パラメータ・測定値・checksumが残っているため、必要であれば同一seed・同一条件で再現実行できる。

## 最終判定

```
READY_FOR_FINAL
```

- 実行成果物: `ai_lab/reports/gl-haiku-1000-robustness/{summary.json,ranked_conditions.csv,failures.json,haiku_context.json,all_trials_registry.json,final_report.md}`
- 完全な生データを保持した非公式Room: `rooms/candidates/room-auto-gl-haiku-1000-robustness-{h001-v030,v034,v039,v100,v104,v109,v160,v164,v169,v181}-*`（100件、31.6MB）
- 上記以外の1900件の生Roomデータは人間承認の下で削除し、コンパクトな `all_trials_registry.json` と `rooms/jobs/*.json` のみ保持
- ディスカバリー台帳: `ai_lab/discoveries/autopilot_ledger.json`
- `app/generated/` と `app/public/data/` はrefresh-appによる一時的な変更を破棄し、実行前のHEAD状態に復元済み（再生成可能なミラーのため今回はコミットしない）
