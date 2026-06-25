# e009 — 探索的創発 — AUDIT ＋ 驚きログ

> 確認でなく**発見**。Tier A（既知=基準線）／Tier B（妥当だが未検証）／
> Tier C（真に未知）。狙った物しか出ないなら台本を疑い、狙っていない物が出たら
> tier をつけて誠実に記録する。崩壊・縮小・閉じないも貴重なデータ。

## X1 — 打ち消さずトーラスを巡る循環（`x1_toroidal_current.py`）

| 項目 | tier | 測定 |
|---|---|---|
| Tier A 持続電流：3-トーラス上の量子化循環が持続、ノイズでも位相すべりせず保護 | **measured / analogy(電子的)** | winding n=1,2,3 が持続、noise 0.2 でも n=2 維持、E drift~1e-13。**GREEN** |
| Tier C Hopf的リンク渦輪：形成後に縮む | **measured(サイズ)/frontier-observation** | core_volume 2368→931（素のGPEに安定化項なし→縮む＝正直な結果） |

「打ち消さない循環」＝保存されたトポロジカル電荷が巡り続ける。これは electron-**like**（analogy）。**「電子を作った」とは言わない。**

## X2 — 種から育つ（形態形成、`x2_seed_growth.py`）

| 項目 | tier | 測定 |
|---|---|---|
| Tier A 自己複製（Gray-Scott mitosis）：1種→16成分 | **measured** | components=16、面積 64→437 増加 |
| Tier A 枝分かれ（coral）：フラクタル枝 | **measured** | fractal_dim=1.55、面積 64→3190 増加 |
| Tier B 勾配→方向性成長 | **measured** | 重心が勾配方向へ −8.6 セル ドリフト（directional=True） |

局所規則は「枝分かれしろ」と書いていない。形は測定で出た。「植物的」は analogy／観測事実の記述で、**生命ではない**。

## open menu（`open_menu.py`）— Tier C 本番

### open-1 普遍性（基板非依存）★驚き
| 項目 | tier | 測定 |
|---|---|---|
| 相対論的複素スカラー（非線形Klein-Gordon、**非GPE**）の白からも KZ 渦が出る | **measured / interpretive(普遍性)** | N∝τ_Q^{−0.504}、ρ_med≈1.0、正味巻き~0 |

→ **共創発は基板に依らない**（GPE と相対論的スカラーの両方で同じ KZ 渦）。指数は z（GPE z=2 / 相対論 z=1）で変わるが、**負べき＋渦創発という質は普遍**。うえきの「共通なら硬い」を一歩。

### open-2 欠陥の"化学"（±渦の対形成）★驚き
| 項目 | tier | 測定 |
|---|---|---|
| クエンチ後、±渦は逆符号の方が近くにいる（対形成＝"分子") | **measured / frontier-observation** | 最近接 同符号 14.3 vs 逆符号 **8.9**（逆符号が近い＝引力で対を作る） |

→ 「±渦が束縛した"分子/原子"を作るか?」に **yes（逆符号が有意に近い）**。束縛状態の証明ではなくスナップショット統計（床）。

## 7監査（探索編の扱い）
1 規則が結果を名指す? No（GS/GPE/NLKG は局所、複製・対形成・普遍性を書いていない）。
2 忠実な物理? Yes（GPE・反応拡散・相対論的スカラーは実在の局所法則）。
3 結果は初期条件に? No（種一つ／白／巻き数だけ）。
4 入れてない物が出る? **Yes（最重要）**：自己複製、フラクタル枝、方向性、基板普遍性、±対形成。
5 数で合う? Tier A は数で（持続・複製数・フラクタル次元・KZべき）。Tier C は観測値を記録。
6 頑健? X1 は n とノイズで、X2 は regime で、普遍性は別基板で確認。
7 コードが発見? Yes（巻き数・成分・距離・次元で測定、結論を書き込まない）。

→ **Tier A は GREEN**（明確に not-scripted＆数で合う）。**Tier C は frontier-observation**（観測されたが未解明：Hopf安定性・±分子の束縛・普遍指数）。

## 床（全体）
- 固定格子（背景＝空間は与えられている）。「幾何」は相関/折りたたみで、もつれ(RT)幾何でない。
- 「電子的」「植物的」は **analogy／観測事実の記述**。電子・生命を作ったのではない（禁止語）。
- Tier C は未知。Hopf が縮む・±分子がスナップショット統計・普遍指数が z 依存、は失敗でなく情報。
- 真の同時共創発（背景なし・もつれ幾何・器の閉じ）は最前線（未達）。

## 再現
```bash
python experiments/e009_exploratory/x1_toroidal_current.py   # 持続電流＋Hopf
python experiments/e009_exploratory/x2_seed_growth.py        # 複製・枝分かれ・方向性
python experiments/e009_exploratory/open_menu.py             # 普遍性・欠陥化学
pytest tests/test_e009.py
```
