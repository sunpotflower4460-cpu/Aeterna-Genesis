# e029 — 深いフロンティアへの挑戦（内生的需要／完全な大転移）— AUDIT

> **FRONTIER**。H016 が「深いフロンティア」と名指した二つ——**真のオープンエンド性（複雑性の内生的上昇）**と
> **完全な大転移（群れが再生産する高次個体）**——に、e027 を超えて挑む。**解いたのではなく、欠けていた
> 機構を示す**。frontier でも measured は物理量のみ、床は隠さない、変動（崩壊）も正直に記す。
> ゲート名は物理量（genome length / parasite spread / cooperator fraction）——「生命/心/社会」は analogy。

## Stage1 coevolution（`results/coevolution.json`）— 内生的需要
**問い**: e027 は複雑性が**外部**需要に合わせて上がった。需要を**内生的に**（外部ノブなしで）上げられるか。
**機構**: 宿主（可変長ゲノム＝防御）×寄生者（攻撃）の**敵対的共進化**を**非有界な形質線**上で。
新奇性は常に新領域へ逃げられる → 軍拡競争で需要（寄生者の広がり）が内側から上がる。

| 量（ensemble 中央値） | STATIC | COEVOLVE |
|---|---|---|
| 宿主ゲノム長（final, T=700） | ~12（頭打ち） | **~26（最大 ~31）、まだ上昇中** |
| 後半スロープ /gen | ~0（平坦） | **+0.028（正）** |
| 寄生者の広がり（需要） | 0.5（凍結） | **~2.4（内生的に上昇）** |

GREEN gates: `static_env_plateaus` / `demand_rises_endogenously` / `coevolution_removes_plateau`。
**測定の宝**: **外部ノブなしで需要が内側から上がり、複雑性の頭打ちが外れる**（欠けていた材料の実証）。

**罠/床（正直に）**: 軍拡競争は**run ごとに変動**——escalate（複雑性上昇）**または** collapse（寄生者が圧勝、
宿主崩壊）。だから**ensemble 中央値**でゲート（cherry-pick しない）。full で 4/6 が escalate、残りは collapse。
これは**真の無限オープンエンド性の証明ではない**——有限世代・有界なトイで「頭打ちが外れる」ことを示すのみ。

## Stage2 major_transition（`results/major_transition.json`）— 完全な大転移
**問い**: e027 は空間で協力が**安定化**（必要条件）。完全な大転移は**群れが再生産する単位**になること。
選択の単位を群れに移す（群れが平均適応度で再生産＋創設者ボトルネック）と、個体選択が崩す協力を救うか。

| 量 | 値 |
|---|---|
| 個体選択の協力率（b=1.5/3.0） | **0.05 / 0.06（崩壊）** |
| 群れ再生産＋ボトルネック k=1 | **0.95 / 0.92（安定な高次個体）** |
| ボトルネック強度（b=3, k=1 vs k=20） | **0.92 > 0.81**（狭いほど協力↑） |

GREEN gates: `individual_selection_collapses` / `group_reproduction_rescues_cooperation` / `bottleneck_tightens_cooperation`。
**測定の宝**: **再生産の単位を群れに移すと、滅ぶはずの協力が安定な高次個体になる**。ボトルネックが群内の
裏切りを抑える（Hamilton／germline bottleneck）。

**床（正直に）**: 協力の**安定化は必要条件**であって完全な大転移の全体ではない（**分業・生殖体細胞分化はここにない**、
policing はこの領域では限界的＝群れ選択だけで足りる）。「大転移/高次個体/多細胞性」は analogy。

## 7監査（両 Stage 共通）
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「需要が上がる」「協力が救われる」を書いていない。相互作用と再生産の型のみ |
| 2 | 忠実な物理/理論? | **Yes** | 宿主寄生者共進化・Red Queen・多層選択・Hamilton 則は established |
| 3 | 結果は初期条件に? | **No** | 半々/単一遺伝子から出発。需要上昇・崩壊/救済は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | 内生的需要上昇、群れ再生産での協力救済（入れていない） |
| 5 | 数で合う? | **Yes** | ensemble 統計で再現（quick/full/robustness） |
| 6 | 頑健? | **Yes（ensemble）** | seed batch・格子を変えても ensemble ゲート成立（`robustness.json`）。個々の run は変動（正直） |
| 7 | コードが発見? | **Yes** | ゲノム長/広がり/協力率を測定。結果を書き込まない |

## claim tier
- **measured**: 静的頭打ち・内生的需要上昇・共進化で頭打ち解除（ensemble）／個体崩壊・群れ救済・ボトルネック単調。
- **interpretive**: 欠けていた材料＝**内生的に上がる需要（軍拡競争）**；大転移＝**群れが再生産する個体**（ボトルネックが対立抑制）。
- **analogy / KNOWN MATCH**: Red Queen、宿主寄生者共進化、多層選択（Wilson）、Hamilton 則、生殖細胞ボトルネック（Grosberg-Strathmann）。
- **FRONTIER**: 真の無限オープンエンド性・分業/生殖体細胞分化を含む完全な大転移は**未解決**——ここでは**機構**を示した。

## 床（隠さない・必須）
1. **FRONTIER**：有限世代・トイのエージェントモデル。無限のオープンエンド性を解いたのではない。
2. Stage1 の軍拡競争は**変動**（escalate/collapse）——ensemble 中央値でゲート、collapse も報告。
3. Stage2 は協力**安定化**（必要条件）——**分業・生殖体細胞分化は未実装**、policing は限界的。
4. 「生命/心/社会/多細胞性/オープンエンド性」は analogy——measured は物理量（ゲノム長・広がり・協力率）のみ。

## 再現
```bash
python experiments/e029_openended_frontier/coevolution.py --quick --no-write
python experiments/e029_openended_frontier/major_transition.py --quick --no-write
pytest tests/test_e029.py
```
