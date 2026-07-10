# app/ — Observatory App（catalog 駆動の静的 PWA）

Room を眺め・比較し、**入れたもの/自然に出たもの/監査**を一画面で確認する観測アプリ。

## 唯一の表示元は `catalog.json`（HTML にデータを直書きしない）
```
experiment.yaml + rooms/official/*/ + rooms/catalog.json
        ↓  tools/build_catalog.py（Python）
app/generated/catalog.json  (+ catalog.js = window.CATALOG)
        ↓
app/index.html（catalog を読むだけ・ハードコードなし）
```

## 使い方
```bash
python tools/build_catalog.py            # app/generated/catalog.{json,js} を再生成
# app/index.html をブラウザで開く（catalog.js を <script> で読むので file:// でも動く）
```

## 画面
- **Universe Lobby**：正式 3D Room（official と明示）・AI 発見候補（**正式 Room と区別**）・Evidence Library の役割別集計。
- **Room View / Physics Integrity Panel**：入れたもの・自然に出たもの・到達 Level・保存/収束/再現/第8監査・
  格子収束表・複数 seed の checksum・**可視化対応（表示→実測物理量）**。

## 誠実さ（`docs/PHYSICS_INTEGRITY.md` §18）
- 表示要素は実測物理量に対応（存在しない流線/粒子を描かない・強調は normalized を明示）。
- **official 3D Room と 2D/AI 候補を混同しない**。2D 成功を 3D 成功として見せない。
- 役割別集計は `experiment.yaml`（機械可読な一次メタデータ）由来。強い語は使わない。
