# 🧭 Research Compass（研究の羅針盤）

> 自動生成：`python tools/build_compass.py`（正本は [`research/index.json`](research/index.json)）。手で編集しない。
> 更新：2026-09-28

**北極星**：完成形を置かず、宇宙の条件（法則・始め方・環境）だけを仮説にして t=0 から回し、この前提ならどうなるかを正直に測る。法則は現実の化学・物理だけ（2026-09-28）。届かなくてよい。どこで天井かを地図にする。

## 白ごとの現在地（天井地図）

| 白 | 到達 | tier | 天井の理由 | 水槽 |
|---|---|---|---|---|
| g001 TDGL（緩和 GL クエンチ） | **L2** | measured（法則 B：近似） | 運動量/移流が無いので動けない | [`tdgl-quench-3d`](app/public/aquarium/tdgl-quench-3d/) |
| damped GPE（超流体） | **L3** | measured（法則 A：現実の物理） | 散逸で長く持たない | [`gpe-dipole-2d`](app/public/aquarium/gpe-dipole-2d/) |
| g002 Boussinesq 対流 | **L3（大域）** | measured（法則 A：現実の物理） | 大域ロールで局在しない | [`convection-2d`](app/public/aquarium/convection-2d/) |
| CGL（振動 GL） | **L2＋乱流運動** | measured（法則 B：近似） | 乱流は coherent でなく個体化しない | [`cgl-spirals`](app/public/aquarium/cgl-spirals/) |
| Swift-Hohenberg | **L4-static** | measured（法則 B：近似） | 変分なので動かない（局在の種は置いている） | [`sh-localized`](app/public/aquarium/sh-localized/) |
| Gray-Scott | **L7-partial** | measured（法則 D：結果を書いた規則） | 遺伝する内部自由度が無い | [`gray-scott-split`](app/public/aquarium/gray-scott-split/) |
| 三成分反応拡散 | **frontier** | frontier（法則 C：簡略モデル） | 閉じ込めと自走が拮抗（codimension≥2 の可能性） | [`three-component-frontier`](app/public/aquarium/three-component-frontier/) |
| g003 Model H | **L2（L5 は frontier）** | frontier（法則 A／B：現実の物理＋近似） | 共分化の測定器が未収束 | — |

- g001 TDGL（緩和 GL クエンチ）：2026-08〜09 の自動研究が約 7,000 run 回したが L2 を越えない（docs/TREASURE_AUDIT.md）

詳しくは [`docs/WHITE_CEILINGS.md`](docs/WHITE_CEILINGS.md)。

## 開いている問い（優先順）

1. **すべてが起こりうる対称な場が壊れて「差が生まれる」宇宙では、何が起きるか（中身と外の条件を水槽で並べて比べる）**（P19（計画中）・AGENTS.md「本懐はフロンティア」）
2. **「局在（個体）」と「自発運動」を一つの白で同時に得る最小の材料は何か？（三成分反応拡散は法則 C の簡略モデルで、段の証拠にはならない）**（三成分反応拡散・docs/ANGULAR_MODES.md（M2 結合固有値解））
3. **X-0a3002e1aa / X-29d79aabf4：平坦値付近で渦数を変えずに amp_std が揃う出来事は緩和か？（位置追跡と自由エネルギーで測る）**（docs/X_PATTERN_AUDIT.md）
4. **もともと内部状態を持つ白から、受け継がれる違い（遺伝）が育つか？**（docs/WHITE_CEILINGS.md「うえきの最深の問い」）

## 監査

- [docs/INVENTORY_2026-09.md](docs/INVENTORY_2026-09.md)：凍結点 faac01d。bot 停止前の棚卸し。
- [docs/TREASURE_AUDIT.md](docs/TREASURE_AUDIT.md)：候補 6,940 Room は 37 条件の TDGL の繰り返し。60/60 決定的。
- [docs/X_PATTERN_AUDIT.md](docs/X_PATTERN_AUDIT.md)：再実行 567 回中 565 回が通常のクエンチ物理。未説明 2 回。
- [docs/reports/2026-09-28-real-chemistry-audit.md](docs/reports/2026-09-28-real-chemistry-audit.md)：法則を A（現実の物理・化学）／B（近似）／C（簡略モデル）／D（結果を書いた規則）に分類。Gray–Scott 系は D。はしごは R3 → R0（R1 は一部）。

## 提案と決定（`research/`）

- 未決の提案：0 件（`/propose` で作る）
- 決定済み：0 件

## 見る・動かす

- 水槽：アプリ（`app/`）の最初の画面。テンプレート一覧は `app/public/aquarium/templates.json`。
- AI と対話で進める：`CLAUDE.md` と `/status`・`/run-white`・`/audit`・`/report`・`/propose`。
