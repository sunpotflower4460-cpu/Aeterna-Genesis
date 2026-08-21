# Science Bridge + Research Continuity + Safe Maintenance

Aeterna-Genesis に「外から知識を入れる」「過去を忘れない」「散らかった研究状態を安全に整理する」を追加する層。

この3つは科学的真実を決めない。strict evidence の生成規則、Room、official Level、truth gate は変更しない。

## 1. Science Bridge

Science Bridge は既存科学を **答えとして移植する場所ではない**。

論文・既知の機構から、Aeternaで壊せる問いを作る。

流れ:

1. `science_bridge_sources.json` に出典・DOI・機構・翻訳上の注意を保存。
2. Crossrefで既知DOIのmetadataを確認。
3. OpenAlexで関連研究候補を追加探索。
4. 自動実験に使うのは、人間/AI Scientistが明示的にAeterna向けへ翻訳した `experiment_templates` のみ。
5. 実験は `science_bridge_runner.py` から **Free Hypothesis Lab** へ送る。
6. 結果は `science_bridge_experiment_latest.json` / ledger に別保存。
7. strict側へ戻せるのは「抽象的な機構の問い」だけ。論文の形・完成結果をstrictのseedへコピーしない。

初期sourceには、reaction-diffusion morphogenesis、active-droplet growth/division analogy、finite-rate transition/defect formation、motility-induced phase separationを含む。

MIPSはg001にself-propulsion DOFが無いため、現在はconcept/instrument-design sourceだけで、無理に直接再現しない。

### Science Bridge の禁止事項

- 論文に書いてある = Aeternaでも確認済み、にしない。
- 類似結果 = 同じ物理、にしない。
- 文献に触発された介入runをstrict-zero evidenceにしない。
- 文献のtarget morphologyをstrict初期条件へ持ち込まない。
- citation数を真実スコアにしない。

## 2. Research Continuity

Research Memory・immutable manifest・Git historyが詳細な保存層。

`research_continuity.json` は、それを毎回すべて読み直さなくても**次のAI Scientistが絶対に見落としたくない事項**を読むためのhandoff層。

保存対象:

- condition-specific / WEAKENED X-pattern
- 三角形 vs 非三角形の反証比較
- local-energy と geometry の矛盾/時間順序
- Prefix-qualified Deep-Time と長寿命の別枝
- Free Hypothesisからstrictへ戻したい抽象的問い
- Science Bridgeの出典とliterature-inspired question
- unresolved instrument / infrastructure debt
- Cross-Worldの「同fingerprint != 同物理」という意味境界

現在のreportから消えたlessonも削除せず `currently_visible=false` にする。

つまり「今出ていない = 過去に無かった」にはしない。

`must_carry_forward` は最大40項目に圧縮し、future AI Scientistが方向転換前に必ず読めるサイズへ保つ。

## 3. Safe Research Maintenance

掃除は**科学的証拠の削除ではない**。

自動で許すもの:

- Research Continuity再生成
- derived catalog / indexの再生成
- JSON破損検出
- required research stateの欠落検出
- stable identity重複検出
- stale burst reference検出
- existing immutable hot/cold archiveのinventory

自動で許さないもの:

- negative result削除
- quarantine削除
- raw ledgerの都合の良い切り詰め
- immutable manifest削除/書換え
- Git historyの書換え
- 「古いから」という理由だけのscientific evidence削除

大きなledgerの容量問題には既存 `ledger_archive.py` のhot/cold splitを使う。古いentryはimmutable archiveへ移るだけで消えない。

## 自動配置

### Science Bridge

- 1日2回
- public scholarly APIからmetadata/候補をrefresh
- curated literature-inspired experimentをFree Labで3 fresh seeds
- evidence + literature provenance + continuityを保存

### Research Continuity

以下の成功後に自動更新:

- Genesis Dream Loop
- Free Hypothesis Lab
- Science Bridge

### Safe Maintenance

- 1日1回 03:23 JST
- non-destructive organizationのみ
- core file欠落 / parse failure / duplicate identity / stale current-burst reference はvisible failureにする
- report自体は先に保存するため、故障理由は失われない

## 研究の大きな流れ

```text
既存科学 ──> Science Bridge ──> Free Hypothesis experiment
                                  │
                                  └─> 抽象的 mechanism question
                                             │
Strict/Open-ended/3D/Deep-Time ───────────────┤
                                             v
                                  Research Continuity
                                             │
                                             v
                                      AI Scientist
                                             │
                                             v
                                     次の実験方針

        Safe Maintenance = この循環の証拠を消さずに整理・点検する
```

大事な区別は最後まで維持する。

> **外の科学は地図。Free Labは探検。Strict laneは本当にその世界自身が育てたかを確かめる場所。**
