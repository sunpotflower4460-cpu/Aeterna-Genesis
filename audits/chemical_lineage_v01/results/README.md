# results

- 本実行（事前登録の値）は、`run_audit.py --out results/formal_v01` で**新しく作る**。既存の空でないディレクトリには書かない。
- 出力：`series_level.csv`（系列ごと）、`generation_summary.csv`（世代ごとの平均と CI）、`summary.json`（判定と不変量）、`manifest.json`（コードとプレレジの SHA-256、コミット）、図（PNG）。
- 結果は AUDIT.md に記載する。図は結果の表示であり、計算の入力ではない。
