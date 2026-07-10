# room/ — 可視化プロトタイプ（legacy）

## `中心実験室.html` は **簡易 JavaScript デモ**であり、本番の Python 実験ではない

`中心実験室.html` は Aeterna-Genesis の**最初の可視化プロトタイプ**である。ブラウザ内で動く
**独立した簡易 JavaScript シミュレーション**であり、`experiments/e001–e045` の実際の物理計算
（Python / NumPy / SciPy、`results/*.json` に保存された測定値）とは**別物**である。

- ここに表示される動きは、**実測物理量の可視化ではなく**、デモ用の軽量スケッチである。
- 物理的主張・到達 Level・監査結果の一次情報は、各実験の `results/*.json`・`docs/TRUST_MAP.md`・
  `docs/claim_ledger.md` にある。
- `docs/PHYSICS_INTEGRITY.md` の原則に従い、**軽量デモを本番シミュレーションとして見せない**。

## 今後（`docs/GENESIS_MAP.md` / `docs/MIGRATION.md`）

将来 `room/legacy/中心実験室_v1.html` として保存し、新しい Observatory App（catalog 駆動・
`app/generated/catalog.json` を唯一の表示元とする）への入口を設ける。本移行の第一段階では
**削除・移動せず**、本 README で legacy デモである旨を明示するに留める。
