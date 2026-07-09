# H017 — 深いフロンティア（内生的需要／完全な大転移）への挑戦

- **状態**: **frontier（機構を実証・GREEN、`experiments/e029_openended_frontier/`）**
- **起票者**: Claude Code / 2026-07-09
- **狙う Type**: D（深い未踏の仮説）——ただし measured は物理量のみ、床は隠さない。
- **依拠する既知事実**: H016（器の弧）の e027 が名指した二つの**深いフロンティア**：
  (1) 真のオープンエンド性＝複雑性が**内生的に**上がり続ける（e027 は外部需要に「合わせる」上昇のみ）。
  (2) 完全な大転移＝**群れが再生産する高次個体**（e027 は協力の空間安定化＝必要条件のみ）。

## 仮説
1. **内生的需要**：宿主寄生者の**敵対的共進化**を**非有界形質**上で回すと、需要（寄生者の広がり）が
   外部ノブなしに内側から上がり、宿主の複雑性の頭打ちが外れる。
2. **完全な大転移**：選択の単位を群れに移す（群れが平均適応度で再生産＋創設者ボトルネック）と、
   個体選択が崩す協力が安定な高次個体になる。ボトルネックが群内の対立を抑える。

## 結果（`experiments/e029_openended_frontier/`、GREEN・物理量ゲートのみ）
**Stage1 coevolution**（内生的需要）：STATIC は複雑性頭打ち（中央値 ~12、平坦）／COEVOLVE は需要が
内生的に上昇（寄生者広がり 0.5→~2.4）し複雑性が**まだ上昇中**（中央値 ~26・最大 ~31・スロープ +0.028）。
full で 4/6 が escalate、残りは collapse（軍拡競争の変動＝正直な床、**ensemble 中央値でゲート**）。
ゲート：`static_env_plateaus` / `demand_rises_endogenously` / `coevolution_removes_plateau`。

**Stage2 major_transition**（完全な大転移）：個体選択は協力崩壊（0.05–0.06）／群れ再生産＋ボトルネック k=1 は
協力を救済（0.92–0.96）／狭いボトルネックほど協力↑（k=1: 0.92 > k=20: 0.81）。
ゲート：`individual_selection_collapses` / `group_reproduction_rescues_cooperation` / `bottleneck_tightens_cooperation`。

ゲート名は物理量（genome length / parasite spread / cooperator fraction）。「生命/心/社会/多細胞性/
オープンエンド性」は analogy（docstring/AUDIT）。robustness は seed batch・格子を変えても ensemble ゲート成立。

## verdict
- [x] **frontier（機構を実証）**：欠けていた材料——**内生的に上がる需要**（軍拡競争）と**群れ再生産＋ボトルネック**
  ——を GREEN で示した。`claim_ledger` e029 §。
- **未解決（正直に）**：真の無限オープンエンド性、分業・生殖体細胞分化を含む完全な大転移は依然フロンティア。
  ここで示したのは**機構**であって解ではない。

## メモ
「オープンエンド進化を解いた／社会を作った」でなく「内生的需要が複雑性の頭打ちを外す・群れ再生産が協力を
高次個体にする」を数で。確認でなく発見を、誇張なく、床つきで。軍拡競争の崩壊も正直に報告（ensemble 中央値）。
