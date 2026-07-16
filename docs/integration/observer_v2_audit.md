# Observer v2 監査ノート（外部レビュー対応・docs-only 説明）

外部監査2件（GPT・別Claude、2026-07-16 受領）を受け、H021 渦ダイポールキャンペーン（e052〜e057）の
測定基盤に3つの具体的な弱点があると指摘された。**物理結果・既存 artifact は一切変更せず**（no_touch
厳守）、新しい独立した観測器（Observer v2）として3ファイルを追加し、これらの弱点に対応する。

## 指摘された3つの弱点と対応

### 1. トラッカーが greedy（順序依存の ID 交換リスク）
`genesis/diagnostics/level3_motion.py::link_frames`（v1）は、アクティブなトラックを固定順で処理し、
一つずつ最近傍の同符号コアを取る greedy 方式。密な欠陥場では、処理順によって2つのトラックの ID が
入れ替わりうる。

**対応**：`genesis/diagnostics/vortex_tracking_v2.py::link_frames_v2` — 符号別に、全アクティブトラックと
全候補コアを**同時に**最小コスト（周期距離の二乗和）でグローバル割当（`scipy.optimize.linear_sum_assignment`、
Hungarian 法）。速度予測（前ステップの速度で外挿した予測位置とのコストを最小化）も選択可能。
per-step confidence を記録し、消滅イベントを対消滅／合体候補／未分類／観測窓終了に best-effort で分類。

### 2. ペア判定がトラック全体の平均（パートナー交換を検出できない）
v1 の `mutual_neighbor_durations` は、重複期間**全体の平均**分離距離・直進性でペアを判定する。相手が
途中で入れ替わっても、片方が別の対となおも「相互最近傍」であり続ければ一つの長いペアとして数えうる。
また物理的シグネチャ（COM 速度が分離ベクトルとほぼ直交＝並進、径方向接近ではない）を一度も検査していない。

**対応**：`genesis/diagnostics/dipole_episodes.py::detect_episodes` — **フレームごと**に相互最近傍判定・
分離距離の急変チェック・COM 速度と分離ベクトルの直交性チェックを行う。同じ (正, 負) トラック対が連続する
限り一つの episode、パートナー交換や条件不成立で即座に episode を終了する（黙って延長しない）。
ペア COM 軌道は周期境界をまたいで時間方向に unwrap してから直進性を計算する（v1 はフレーム内の中点は
周期対応していたが、軌道全体の unwrap はしていなかった——箱端を横切ると見かけ上の大跳躍になりうる）。

### 3. e056 の「飽和」判定が独立 seed 集合の最大値比較（打ち切りを死亡として扱っていない）
e056 は3・6・9倍の異なる観測窓で、**異なる独立 seed 集合**の最長持続時間を比較し、窓の拡大に対する
伸びの鈍化を「飽和」の根拠とした。しかし（a）独立集合の最大値比較は標本サイズ・偶然に強く左右される、
（b）観測窓終了時点でまだ結合していたペアは**右側打ち切り（right-censored）**であり「死亡」ではない
——これを死亡として扱うと持続時間統計が過小評価され、見かけ上の飽和を作り得る。

**対応**：`genesis/diagnostics/survival_analysis.py` — 打ち切りに対応した Kaplan-Meier 生存曲線・
制限付き平均生存時間（RMST、中央値が届かなくても常に定義できる）・打ち切り割合を明示的に報告する
標準的な統計手法を実装。`summarize()` は打ち切り割合を必ず一緒に返し、隠さない。

## 位置づけ（no_touch・追加のみ）
- `genesis/diagnostics/level3_motion.py` は**不変**。e052〜e057 の committed 結果・experiment.yaml・
  AUDIT.md も**不変**——これらは反復1〜6の正直な記録として歴史に残す。
- Observer v2 は v1 を**検証するための独立した道具**であり、v1 を黙って置き換えるものではない
  （LT-1/2/3 が measures.py に対して取ったのと同じパターン）。
- 次のPRで、Observer v2 を使って e053（多解像度実験、実際は τ_Q/hold/post_track_steps も同時に変えて
  いたため「resolution robustness」という呼称は精密でない）と e056（飽和主張）を再監査し、呼称・role を
  必要に応じて正直に補正する。

## テスト
`tests/test_vortex_tracking_v2.py`・`tests/test_dipole_episodes.py`・`tests/test_survival_analysis.py`
（合成データによる既知シナリオ検証：ID交換回避・パートナー交換分割・周期unwrap・打ち切り対応KM）。
