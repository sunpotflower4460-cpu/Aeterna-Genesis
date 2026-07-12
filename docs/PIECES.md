# PIECES.md — 全ピース知識ベース（tier 付き索引）

> **これは何か**：AeternaGenesis の方法論——**0 から・始原条件だけを大量に試し、失敗と仮説を積み重ねて、
> 自然に形をなす初期条件を発見・更新する**——のための、**AI が探索するときに参照する仮説の材料**。
> これまでの全ピース（テーマ A〜S）を **tier 付き**で一覧にし、各ピースを実際のコード（`experiments/`,
> `docs/working_ledger/`, `genesis/`）へアンカーする。**既知に折りたたむための地図ではない**——既知は
> 「次にどの始原条件を振るか」を決める材料であり、やることは発見の積み重ね。
>
> **併読**：失敗は [`traps_museum.md`](traps_museum.md)（堂々巡り防止）、床は
> [`honest_floors.md`](honest_floors.md)（誇張を止める）、確定主張の裏づけは
> [`claim_ledger.md`](claim_ledger.md)、回転ノートは [`working_ledger/`](working_ledger/)。

## tier の凡例（誇張も卑下も禁止・LAW.md §3）

| tier | 意味 |
|---|---|
| **measured** | このリポジトリで実際に測った数がある（`result.json` 等で再現可能） |
| **observed** | 測ったが N が小さい/条件限定（measured の一歩手前） |
| **established** | 教科書・既知の確立事実（自分で測って一致を確認したものを含む） |
| **interpretive** | 測定の解釈・言い換え（測定そのものではない） |
| **analogy** | 構造的な類似（「同じ数学」であって「同じもの」ではない） |
| **frontier** | 未収束・未検証・原理的限界あり（正直に frontier と呼ぶ） |
| **retracted/trap** | かつて主張したが監査で撤回した（→ `traps_museum.md`） |

**規律**：measured を interpretive/analogy/frontier と混同しない。曖昧なら **frontier か失敗記録**へ落とす。
完成形（三角形・液滴・分裂後の 2 つ・双曲の木・√c4 埋込）を始原条件に置かない（**第8監査**）。
「**同じ数学 ≠ 同じもの**」（Higgs の数学＝メキシカンハット、渦線≒宇宙ひも、もつれ→重力＝線形化 Einstein＝analogy）。

---

## A. 秩序の発生（0 ≠ 一様）

始原の「無ではなく一様＋微小ゆらぎ」から、差・模様・時間の矢が自然に立つか。

- **A0 枠組み（T1–T5 / D1–D3）** `interpretive` — 5 テーマ軸と 3 次元軸の framework（本 index の骨格）。
- **A1 0 ≠ 一様の throughline** `measured` — 一様な地面は不安定、ゆらぎから領域が育つ（`experiments/e008_coemergence`）。
- **A2 Kibble–Zurek 共発生** `measured` — クエンチで秩序変数と欠陥が同時に立つ。ξ ∝ τ_Q^0.314（≈1/3）、欠陥数 ∝ τ_Q^−b（b≈0.50–0.62）、クエンチ 100× で ±5%、φ=0 起点（`e008`, `e010`）。**KZ 指数は analogy でなく自分で測った measured**。
- **A3 1D スペクトル次元** `measured` — 因果グラフ 1D で d_s≈1.94（+1 ずれ）。CTC は 1 本（`e004`, `e014`）。
- **A4 Kac リング（時間の矢）** `measured` — 決定論・可逆なのに粗視化で単調 ΔS、再帰は t=2N、f0≈0.51、51/49 の非対称。Boltzmann H の教科書対応（`e023` 近傍の砂場ピース）。
- **A5 cat map / 複雑さの窓** `measured` — gzip 複雑度が始端低→中間高→終端低（Aaronson コーヒー）。**中間複雑性の窓**は ai_lab スコアの動機（→ H1）。
- **A6 t=0 起点の測定規律** `measured` — すべて t=0 から・完成形を入れない（第8監査の運用）。

---

## B. 次元（次元は測る量・2-cell 問題）

座標を捨て、関係だけから次元が出るか。「2 に張り付く」罠に注意。

- **B1 グラフ次元 ~log N** `measured` — ランダム/近傍グラフの実効次元スケーリング。
- **B2 Myrheim–Meyer 次元** `measured` — 因果集合の順序分率 r から d：r≈0.50→2D, 0.22→3D, 0.10→4D。sprinkle 数 ~N^(1/d)、d=3 で 2.93（`e014`）。
- **B3 スペクトル次元（+1 ずれ）** `measured` — 拡散の戻り確率から d_s：1D→1.94、2D→2.86（`e014`）。
- **B4 2D CDT** `measured` — 因果動的三角形分割 d≈2.07/2.12/2.11（3 手法）。
- **B5 3D CDT（2+1）** `measured→inherit` — ergodic move set＋Regge＋Metropolis、diameter_dim 3.06–3.08（arXiv:1305.4702 と一致）。**因果性は imposed**（床）。
- **B6 次元遷移** `measured` — 制御パラメータで実効次元 8.2→14.0、4→6。
- **B7 crumple / 2-cell** `measured-negative → interpretive` — crumple した膜は MD 5.3→8.6 で d≠2。「2-cell が 2D に張り付く」のは幾何ではなく **2-cell 構成の副作用**（→ traps）。
- **B8 SOC（BTW 砂山）** `measured` — 2D 自己組織臨界、雪崩サイズ scale-free、τ≈1.36。scale-free ≠ 次元、gap 注意。
- **B9 α スケーリング → d≈1/(1−β)** `measured/interpretive` — 成長則 ~N^β から実効次元、2D で ~√N。d=1 → scale-free（SOC 由来）。
- **B-floor** `frontier` — 固定格子 BD の次元推定は smeared BD が要る（生の BD は揺らぐ → traps）。

---

## C. 内と外（境界・自他）

境界がひとりでに立つか。「dim=2 に張り付く」「N=3 で自発回転」等。

- **C1 境界の自発形成** `measured` — 2D/3D で界面が立つ、始原に境界を入れない。
- **C2 3D 自発回転（Opus 検証）** `measured` — E-drift 1e-5、E−4.4%、N=2,3,4 → 位相差 150°/204°/240°。**回転方向は入れていない（NOT seeded）**（`e024` 近傍）。
- **C3 2-cell「dim=2」** `measured（floor 明記）` — dipole gas 18 で corr_dim 1.545（1D）/1.042/2.99。**q1_target_in_IC=true ＝完成形を種に入れている**ので「dim=2」は幾何主張にできない（→ traps / 第8監査）。
- **C4 三位一体（EWMA=Mori–Zwanzig=Barontini）** `measured/established` — 記憶カーネルの三つの見方が一致。topological frustration（G8）。
- **C-floor** `frontier` — 内外は場の分離であり「膜」という語は analogy。

---

## D. 器と代謝（vessel）

駆動で自己維持する「器」が立つか。切ると死ぬか。

- **D1 CGL 散逸構造** `measured` — 複素 Ginzburg–Landau ~500k step で散逸パターン維持（Prigogine class）。
- **D2 Gray–Scott（種→パターン）** `measured` — λ 領域でスポット/ストライプ、psi6 秩序。種は点・ノイズのみ。
- **D3 4 腕 vessel** `measured` — 膜/代謝いずれの腕を切っても両方死ぬ（閉じ）。"tension" は EWMA で測る（`e015`, `e018`, `e025`）。
- **D4 LLPS（相分離液滴）** `measured / frontier` — Allen–Cahn/Cahn–Hilliard は robust。**Zwicker active droplet の自発分裂は uniform 供給だと knife-edge**（→ frontier, traps）。
- **D5 throughflow の再枠組み** `measured` — φ 場の流入駆動で内部が生きる（reframe）。
- **D6 自己組織対流（Rayleigh–Bénard）** `measured/textbook` — 壁つき実セル Ra_c≈658(free-slip)/1708(no-slip)＝教科書と<0.4%、Nu(Ra)>1、内部給餌 ~12× Pe（`e017`, 正式 **G002**）。周期箱 Ra_c≈20 は artifact（→ traps）。
- **D7 Lv4–6 反応拡散 vessel** `measured` — R=kρ∇χ、clean 窓 u_far≈0.025 ≪ spinodal 0.21、AND ゲート（flow ∧ 代謝）。
- **D8 furrow（Lv7 分裂の入口）** `measured（floor 明記）` — 1→2 の furrow、clean で furrow OFF→passive。**furrow は材料を削る近似 2.5–6.7%、noisy**（→ traps / floor）。
- **D9 Model H（相分離×流体の共発展）** `measured / frontier` — 質量機械精度保存・自由エネルギー Lyapunov（2D 正式 **G003**）。integrity「流下で大きさ一定」は frontier。
- **D-floor** `frontier / analogy` — autopoiesis/chemoton は class analogy。A→M, M→confine の閉包は frontier。

---

## E. 進化と選択

複製・遺伝・変異・選択・適応が場から出るか。開放的進化は frontier。

- **E1 Gray–Scott 自己複製スポット** `measured` — スポットが分裂して増える。
- **E2 GS 世代** `measured` — ~27× 増殖、τ=1 正規化。
- **E3 turnover（赤の女王）** `measured / frontier` — A/B 交代 1.2→2.2。**適応度地形が imposed** なら frontier（→ floor）。
- **E4 場化（agents→fields）** `measured` — E-FIELD-DARWIN 連続形質 0.50→0.89、/EVOLUTION(K)、/COOPERATION(network-reciprocity)、/DIFFERENTIATION(morphogen+Turing)、/OBJTRACK、/BOTTLENECK 0.2→0.90。エージェント無しの純 PDE（`e033`–`e045`）。
- **E5 分裂＋遺伝＋選択＋適応** `measured` — 空間協力 0.76 vs well-mixed 0.40、b=1。**開放的進化（複雑さの天井を外す）は frontier**（`e043`–`e045`, `e029`）。
- **E-floor** `frontier / analogy` — 「生命」語は使わない。GS/場の進化は analogy＋measured の混合、開放性は frontier。

---

## F. 現実化（actualization / muddy）

「差が立つ」と「現実化する」は別。ここは interpretive/muddy と正直に置く。

- **F1 0≠一様 を actualize する engine** `interpretive` — 「差」から「現実化」への飛躍は測定でなく解釈（→ honest floors）。
- **F2 現実化の言い換え** `interpretive` — 用語の整理であり新しい測定ではない。
- **F3 現実化の反例テスト** `measured-negative` — 3 run で m 0.3→0.95 に clip すると 0.85–1.0 に張り付く＝**clip が結果を作る**（→ traps）。

---

## G. 全体 ↔ 部分（interpretive / analogy）

- **G1 全体論の類似** `analogy` — 部分和 ≠ 全体は構造的類似。
- **G2 n ↔ (n−1) セル** `interpretive/analogy` — /1D /2D /3D の 2-cell 対応。幾何主張にはしない。
- **G3 Rovelli 的関係主義** `interpretive` — 関係が実体に先立つ、という解釈。

---

## H. ツール（探索エンジン）

- **H1 始原探索スコア（非飽和・中間複雑性窓）** `measured tool` — `ai_lab/lab.py` に **score = Level(支配)
  ＋ 中間複雑性の窓 ＋ 測定信号**を実装。複雑さは**非飽和**な log 参加率（entropy が 1.0 に飽和する罠
  `T-entropy-sat` を回避）。IC family（white/lowk/highk/single_seed/sparse_seeds/ring/gradient・第8監査 OK）
  ＋ 許可空間全域 knob ＋ grid/random/evolutionary。**300 trial の実探索**（`ledger.json`）で
  L0 / L1 / L2 に分布、上位は **seeds_phase/white_highk ＋ 低 diffusion_ratio(0.1–0.4) ＋ 高 drive ＋ 短 quench** に
  高欠陥・中間複雑性が集中。**score は成功ゲートでない**（Level が真）。
- **H1b 位相制御 ＝ 登坂の鍵、ただし巻き測度は実数場を過大カウント** `measured` — サンドボックスの大量探索
  （350 IC・`seeds`(位相なし) 0% / 位相を持つ family ~10%）を repo で**機構ごと**再現・**深掘り**：
  random-phase 系（seeds_phase＝バンプ×一定ランダム位相・巻きなし／spectral_powerlaw／bandpass）と、
  対照 **real_seed（純実数）**を追加。**GL は実数場を実数のまま保つ**（`max|imag|=0` 実測）ので real_seed に
  真の渦は無い。だが `winding_defect_count` は実数場の**ドメイン壁**を巻きと**誤検出**し、素の測定では
  real_seed が L2 に 33% 「到達」して見えた（**T-realwinding**）。→ Lab に**物理妥当性ガード**を入れ実数場に
  L2 を与えない（生 level と理由は記録）。**`vortex_charges`（巻きを種に置く）は target_encoded で除外**。
  結論：位相が効くのは本物、だが「実数場＝渦なし」＆「離散巻き測度は実数場を過大カウント」の二重の床。

---

- **H2 法則クラスで Level を登る（深い Level は別の法則が要る）** `measured` — 「同じスコアを上げる」のでなく
  **法則クラスを変える**と 0 から届く Level が変わる（`ai_lab/lab.py --mode lawscan`、`genesis/models/`＋
  `genesis/diagnostics/higher_levels.py`）。すべて t=0・IC は種/ノイズのみ（第8監査）・Level は measured：
  - **g001 GL/TDGL**：一様＋ノイズ → 位相巻き渦 **L2**（2D の上限）。
  - **g002 Boussinesq/RB**：**REST＋ノイズ** → 自発的な循環ロールが育って**飽和**（**coherent L3**）。
    実測 KE 0→112・circulation 50.9・late_fluct=0（＝乱流 churn でなく coherent。**turbulent ≠ coherent** を flag）。
  - **gray_scott（反応拡散）**：**ノイズ種 8 個** → スポットが**自己複製・分裂**して増える（**L7 signature**、
    実測 8→20〜39・2.5–4.9×）。**同じ数学 ≠ 同じもの**：反応拡散スポットであって生命ではない（floor）。
  - **g003 Model H**：相分離×流体の共発展（**L5**）は screenable 登録だが co-differentiation 測度は **frontier**（WIP）。
  規律：no_touch（`measures.assess_level` の L1/L2 成功判定は不変・追加測度は新モジュール）・self_promotion なし・決定的。

## O. 方法論・framework（→ honest_floors）

- **O1 既知モデルは沢山ある** `frontier/floor` — Turing/Lenia/Vicsek/CGL。「作れる」ことと「本物」は別（sim の underdetermination）。
- **O2 監査の作法** `established` — 第8監査（完成形を入れない）＋文献対応（Phys. Rev. E / PRX Life / Artificial Life / Chaos）。
- **O3 対照の作法** `established` — seed を振った matched control と null を必ず持つ。

---

## P. サンドボックス／リポジトリ外（H005–H015, e021）

> **P-note**：P 群の多くは別チャットのサンドボックス測定で、**このリポジトリには未収録**（AB リング等）。
> tier は付けるが、repo アンカーが無いものは **frontier 扱い**（再現をこのリポジトリで取るのが次の仕事）。

- **P1 因果集合の Ricci / 熱力学** `measured（sandbox）` — |mean Ricci| 0.06 ≪ 0.95 ≪ 4.19、exp(−βS) 分配、bilayer −29 / chain +1、diamond+unordered で r*(2D)=1/2（H005–H008）。
- **P2 E-gap（AB リング）** `measured/interpretive（sandbox）` — 位相 mod 1、Dou–Sorkin T(β)=Li₂(1)−Li₂(1/(1+β))→π²/6、2+1、DS d>2、BD 3.5σ（H009–H010）。
- **P3 位相メモリ** `measured/interpretive（sandbox）` — 巻き数 ≈48、M=121、GL ~3.03、|ψ|=0 の芯（H012–H014, `experiments/e028`）。
- **P4 e021 VESSEL-ALIVE** `measured` — self_maintains 0.99、death_on_undrive 0.99→0.02、identity_survives_body_damage(+1)、identity_dies_to_its_anti(−1)、寿命 ~15（`experiments/e021`）。**GREEN/SOLID**。
- **P5 H015 E-GENESIS** `measured（sandbox）` — ψ=0 の source-window から Kibble–Zurek で秩序が湧く。

---

## Q. E-シリーズの器・機関（H016–H017）

- **Q1 E-BLACKHOLE** `measured/analogy` — source-window 面積則 ∝ area^0.89（ホライズン analogy）。
- **Q2 E-RATCHET** `measured` — 非対称ポテンシャルが対称ノイズを整流、rectification 0.02→0.96。
- **Q3 E-MOTOR（N≥3）** `measured/analogy` — 3 相が最小回転（Tesla polyphase 3-6-9 triplen / ATP synthase 3-fold）、Δμ→回転、Ψ=0.93。
- **Q4 E-VESSEL（COMPLETE/AUTOPOIETIC/DIVISION）** `measured` — 三器官＋閉包、**reproduction = CREATE not copy**（`e025`, `e026`）。
- **Q5 E-TWO-SELVES（cross-feeding）** `measured` — 二者が「異なるまま関係して "we" になる」（C4 Trinity, G8, C2）。
- **Q6 E-MAJOR-TRANSITION / DIVISION-OF-LABOR / ONE-FOUNDER** `measured` — Nowak–May 0.73、分業 s*=0.33、創始者 b=1 で relatedness 1.00→0.43（`e027`, `e029`, `e030`）。

> **Q-note**：E5（分裂+遺伝）は measured だが、Q6 の「大遷移」は class の analogy を含む。開放性は frontier。

---

## R. 位相と保存（トポロジカル不変量）

- **R1 因果次元の再掲** `measured` — d=2,3,4 → 1.99/2.97/3.95、d_s≈3（B2/B4 と整合、`e014`）。
- **R2 ホップ安定化と Q_H** `measured / retracted 混在` —
  - `measured`：四次項でホップ粒子が有限 L* に自己安定、**完全 PDE 自己安定化**（半陰的・エネルギー単調・c4>0 が Q_H≈1 保持）、**Q_H=2 も保持**（1.94→2.00、observed）、κ∝dx⁴（`e012`, `e016`, working_ledger/H001）。
  - **`retracted`：~~size = k√c4~~ の size 則は第8監査で撤回**（start に √c4 を埋込＝target_encoded・流れ未収束、decoupling で √c4 消滅）。真の start 非依存 L* は **frontier**（→ traps, honest_floors, H001）。

---

## S. カオス・同期（tier 慎重に）

- **S1 KAM / Arnold tongue** `interpretive` — 結合振動子で ω_B/ω_A=φ の同期、KAM トーラス。2 振動子は KAM の解釈。
- **S2 渦の位相構造** `frontier/interpretive` — z に沿う位相 φ=atan2+2πm z/N、m=1:m=2、Moffatt（2D/3D で m の意味が変わる）。
- **S3 ゲージ不変な重なり** `measured` — gaugeOverlap=|⟨A,B⟩|/(|A||B|) を測る（規約非依存）。
- **S-note** `frontier` — 同期は measured だが「意味」は付けない。

---

## この index の使い方（AI 探索とのつながり）

1. **仮説の材料**：ある Level に登った measured ピース（例 A2 KZ、D6 対流、E5 分裂）を見て、
   「近い始原条件族（IC family）＋許可ノブ」を ai_lab に振らせる。
2. **堂々巡り防止**：[`traps_museum.md`](traps_museum.md) にある失敗（√c4 埋込・clip が結果を作る・
   furrow の材料削り・dim=2 の種埋込 等）を先に読み、同じ罠を踏まない。
3. **床を守る**：[`honest_floors.md`](honest_floors.md) の「差 ≠ 現実化」「同じ数学 ≠ 同じもの」
   「imposed ≠ emergent」「CDT の因果性は imposed」を、tier を上げる前に必ず確認。
4. **昇格は別段階**：ai_lab は 2D screen まで（self_promotion 禁止）。measured→frontier の混同があれば
   Claude（サンドボックス）の監査で差し戻す。
