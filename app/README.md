# Aeterna Genesis — Observatory (React + Vite + R3F)

始原条件から育った宇宙を **3D 現象を主役に** 眺める観測アプリ。
現在は、Roomを見るだけでなく、**Universe Aquarium（研究系列）・人間メモ・AI方向書を同じ研究室で共有する collaboration layer** も持つ。
刷新前の単一 HTML 版は `app/legacy.html`（参照用に保存）。

- **catalog 駆動**：UI は Room データをハードコードしない。`app/public/data/`（`catalog.json` ＋ 各 Room の
  `field.json` / `render-manifest.json`）を読む。これらは Python 側が生成する一次情報のコピー。
- **本物の実測場を再生**：`field.json` は記録パイプライン（`genesis/recording/`）が書き出した、
  シミュレーションが実際に計算した場の間引き・量子化スナップショット。偽の粒子は描かない。
- **表示 ↔ 物理の分離**：View スライダー（閾値/透明度/発光）は即時・物理不変。Genesis スライダーは
  「保留中の始原条件」に貯め、新しい Room として t=0 から実行する。
- **Aquarium ↔ Evidence の分離**：`aquaria/registry.json` と `aquaria/notebook.json` は研究意図・人間/AIメモを
  表示する planning data。**科学的証拠や公式Levelを変更しない。** Intent は planning が読んでよいが、solver は読まない。

## 開発

```bash
cd app
npm install
python ../tools/build_catalog.py
python ../tools/collect_app_data.py  # Room + Dream + Aquarium collaboration data
npm run dev
npm run build
npm run typecheck
```

## 主な画面

- **Universe Lobby**：catalog の Room をカード表示。Universe Aquarium Lab への入口も持つ。
- **Universe Aquarium Lab**：
  - Aquarium 一覧（human / AI / joint、goal-directed / open-ended）
  - Intent と変更可能な Recipe Space
  - 観測したい量
  - Human Note と AI Direction Note
  - 人間の新しい Aquarium idea のローカル下書き
  - `planning ≠ evidence` / `intent hidden from solver` を常時表示
- **Room Workspace**：R3F ビューポート（2D は面、3D は体積の点群として実測場を色付け）／観測レンズ切替
  ／再生・一時停止・時間移動・速度／HUD／下部コントロール／Branch Room。
- **Inspector**：View（表示・即時・物理不変）／Genesis（保留中の始原条件→新 Room 実行）／Physics（やさしい
  概要→確認項目→研究者向け数値の 3 段階）。
- **AI Discovery Inbox**：候補Room・ジョブ・昇格パイプラインを確認。

## Aquarium idea の実行について

現在の Aquarium idea composer は**ローカル下書きのみ**。動いたふりをしない。
次段階では Live Runner / AI Genesis Lab へ Recipe proposal として渡し、integrity check 後に必ず t=0 から新しい Run を作る。

Universe Aquarium の原則は `docs/UNIVERSE_AQUARIUM.md`。
