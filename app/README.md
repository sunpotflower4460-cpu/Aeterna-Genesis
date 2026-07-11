# Aeterna Genesis — Observatory (React + Vite + R3F)

始原条件から育った宇宙を **3D 現象を主役に** 眺める観測アプリ（UI 刷新 Phase 1：Visual Prototype）。
刷新前の単一 HTML 版は `app/legacy.html`（参照用に保存）。

- **catalog 駆動**：UI はデータをハードコードしない。`app/public/data/`（`catalog.json` ＋ 各 Room の
  `field.json` / `render-manifest.json`）を読む。これらは Python 側が生成する一次情報のコピー。
- **本物の実測場を再生**：`field.json` は Phase 0 の記録パイプライン（`genesis/recording/`）が書き出した、
  シミュレーションが実際に計算した場の間引き・量子化スナップショット。偽の粒子は描かない。
- **表示 ↔ 物理の分離**：View スライダー（閾値/透明度/発光）は即時・物理不変。Genesis スライダーは
  「保留中の始原条件」に貯め、新しい Room として t=0 から実行する（Live Runner は Phase 3）。

## 開発

```bash
cd app
npm install                          # 依存はローカルにバンドル（CDN 不使用）
python ../tools/build_catalog.py     # app/generated/catalog.json を生成
python ../tools/collect_app_data.py  # app/public/data/ を組み立て（catalog + field.json + manifest）
npm run dev                          # 開発サーバ
npm run build                        # dist/ に自己完結の静的ビルド（オフライン成立）
npm run typecheck                    # 型チェック
```

## 画面（Phase 1）

- **Universe Lobby**：catalog の Room をカード表示（到達 Level・次元バッジ・Physics Verified）。
- **Room Workspace**：R3F ビューポート（2D は面、3D は体積の点群として実測場を色付け）／観測レンズ切替
  （実測物理量に対応）／再生・一時停止・時間移動・速度／HUD／下部コントロール／Branch Room。
- **Inspector**：View（表示・即時・物理不変）／Genesis（保留中の始原条件→新 Room 実行）／Physics（やさしい
  概要→確認項目→研究者向け数値の 3 段階）。パネルを開いても 3D を見続けられる。

Phase 別計画は `docs/MIGRATION.md`。Phase 2=記録データ統合の作り込み、Phase 3=Live Runner（非同期ジョブ）、
Phase 4=AI Discovery。
