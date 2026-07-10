# claim_ledger — 全主張の claim tier 台帳

すべての主張に tier を付ける（LAW.md §3）。**誇張も卑下も禁止。**
tier を上げるときは新しい測定で裏づける。

tier: `measured | observed | interpretive | analogy | frontier`

---

## e001 — GPE 渦の歳差運動  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | トラップ中の渦は GPE だけから歳差する（半径ほぼ一定の円運動） | **measured** | `result.json`：累積回転 462.5°、半径 mean 10.58（min 10.01/max 11.35） |
| 2 | 累積回転は単調に増え、8000步で 360° を超える | **measured** | `result.json`：462.5°、rotation_monotonic=True（参照 ≈466°） |
| 3 | 循環は量子化（渦の巻き数＝整数 +1） | **measured** | `core/vortex.py` 巻き数、`result.json`：charge=1, circulation_quantized=True |
| 4 | +1 渦は反時計回りに歳差（循環と同符号） | **measured** | 累積回転が正、`result.json` |
| 5 | エネルギー・ノルムが保存（保存系の split-step） | **measured** | energy_drift 4.1e-8, norm_drift 1.1e-12 |
| 6 | 歳差は R0・Ω を変えても持続（頑健） | **measured** | `robustness.json`：9/9 ケース PASS |
| 7 | この歳差は BEC 実験の渦ダイナミクスと一致する | **analogy** | 既知の BEC/GPE 結果との構造的一致（Anderson et al. 等） |
| 8 | GPE は平均場の有効理論であり最終法則ではない（(B) は未着手） | **interpretive** | 入力＝場の方程式そのもの（AUDIT.md `A_OR_B`） |

---

## e002 — GPE 二渦の相互作用  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 同符号の二渦は GPE だけから互いの周りを回り合う（共回転、間隔ほぼ一定） | **measured** | `result.json`：累積回転 322.9°（単調増加）、間隔 mean 14.89（13.77–17.02、±20%以内）、中心移動 0.00 |
| 2 | 逆符号の二渦は対になって並進する（渦双極子、回転≈0） | **measured** | `result.json`：回転 0.0°、中心移動 21.16（単調増加）、間隔 mean 31.55 |
| 3 | 循環は量子化（各芯の巻き数＝±1） | **measured** | `core/vortex.py`、`result.json`：同符号 charges=[+1]、逆符号 charges=[−1,+1] |
| 4 | エネルギー・ノルムが保存（一様背景・周期境界の保存系） | **measured** | 同符号 E/N drift 2.0e-5/1.6e-12、逆符号 2.4e-5/3.4e-13（e001 より大きい理由は AUDIT §5.2） |
| 5 | 挙動の質（同符号=共回転／逆符号=並進）は間隔 d を変えても保たれ、速さの d 依存も物理どおり | **measured** | `robustness.json`：6/6 PASS。同符号は近いほど速く回り（596>323>100°）、双極子は近いほど速く進む（35>29>25） |
| 6 | 点渦理論には Biot-Savart を入れていない——相互作用は場から出た | **measured** | PUT IN は GPE＋2渦の初期条件のみ（AUDIT.md `PUT IN`） |
| 7 | この二渦ダイナミクスは点渦理論／超流体実験と構造的に一致する | **analogy** | 同符号=共回転・逆符号=並進という定性的一致（定量照合で measured に上げ得る） |
| 8 | 同符号対は静止解でないため音波が蓄積。クリーン窓を間隔で自己検出し劣化前で打ち切る | **interpretive** | AUDIT.md §5.1–5.2（窓の外の発散も隠さず明記） |
| 9 | 同符号対は周期トーラス上で正味循環 +2（鏡像で補償、L≫間隔で副次的） | **interpretive** | AUDIT.md §5.3（理想二体極限には開放/壁境界が必要） |

---

## e003 — GPE 3D 渦リング（トーラス）の伝播  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 渦リングは 3D GPE だけから軸方向に伝播する（静止して置いたリングが動く＝煙の輪） | **measured** | `result.json`：伝播距離 14.0 cells（単調、向き −z） |
| 2 | その伝播は自己誘導（鏡像/境界シート駆動でない） | **measured** | 箱サイズ収束 v(L=64)=v(L=80)=0.0133（`robustness.json` box_convergence）。シート誘導流はリング位置で指数減衰 |
| 3 | 伝播中もリング半径はほぼ一定 | **measured** | 半径 mean 10.43（10.0–11.0、spread 1.0） |
| 4 | 循環は量子化（断面の渦芯＝±1、巻き数は整数） | **measured** | `core/vortex.py` 断面追尾＋is_circulation_quantized、`result.json` |
| 5 | エネルギー・ノルムが保存（一様背景・周期境界の保存系） | **measured** | E/N drift 1.4e-5 / 6.9e-14 |
| 6 | 小さいリングほど速い（v~1/R の傾向） | **measured** | `robustness.json`：速度 0.0156>0.0133>0.0110（R=8,10,12）、3/3 PASS |
| 7 | 速度は渦リング速度公式 v∝(1/2R)ln(8R/ξ) と一致 | **analogy** | 絶対値は一定係数〜0.63（芯 ξ≈1cell が粗い）。R 3点では正確な関数形は確定不可 → analogy。AUDIT §監査5 |
| 8 | 閉じた渦線＝トーラスが伝播する | **observed/interpretive** | リング芯は閉ループ（位相的にトーラス） |
| 9 | imprint 非周期由来の静的境界シートは人工物（バルク/クリーン窓で測定し除外、駆動でないことを箱収束で確認） | **（床の明示）** | AUDIT.md 床1・監査6補足 |
| 10 | 二リングの絡み（リンク）は未実施 | **frontier** | AUDIT.md 床4（次段） |

---

## e004 — オクターブ階層 / 折り畳み / ホログラフィー  (STATUS: YELLOW)

> 数値は measured だが、双曲幾何は手作り階層に内在し ε も手入れ。MERA/AdS の
> 構造再現（analogy）であり忠実な創発ではない。**GREEN ではない＝「示唆」止まり。**

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 測定法は幾何を**判別する**：同じ法で階層=双曲・平坦2D格子=平坦と分類 | **measured** | 次元スロープ 1/d_eff 階層0.171 vs 平坦0.503、ボール成長 階層=指数勝ち/平坦=べき勝ち |
| 2 | 純粋な粗視化結線だけで双曲（log直径）が出る——手で曲率は入れていない | **measured-structural** | R² 指数0.9825>べき0.9616（差は小）。ただし直径∝log(N) R²=1.0 は2分木の準トートロジー（証拠でなく構成の帰結） |
| 3 | 折り畳み方向＝動径方向（同じ位置・違うオクターブは動径方向に離れる、夢3） | **measured（トートロジー）** | 動径距離 (0,0)→(層l,0)=l。木構造の帰結で構成の確認 |
| 4 | 螺旋：対称(ε=0)は円で閉じ、非対称(ε>0)は log半径が線形に進む | **measured** | 閉合変位 3.1e-15／slope=log(1+ε) 厳密一致 |
| 5 | (1+ε)^N=2 のとき螺旋の一周＝一オクターブ（log₂半径が毎周 +1） | **construction-identity（measured でない）** | ε を選んでそうなる恒等式。BFS/数値で「構成を検証」したもので発見ではない |
| 6 | 全帯は一つの連結幾何に束なる | **measured** | 連結 1023/1023 |
| 7 | 境界間距離 ≈ 2·log₂(分離)（木の経路のトートロジー）。RT と同じ形 | **measured（トートロジー）/ analogy** | R²(log)=0.9972 vs 線形0.6986。RT 的は **analogy** であって AdS/CFT の検証ではない |
| 8 | これは MERA/AdS-CFT/繰り込み/Ryu-Takayanagi の構造再現 | **analogy** | 既知の双曲バルク・RT 的境界距離との構造一致 |
| 9 | 折り畳み層＝繰り込み一段＝動径シェル（RG×ホログラフィーの構造対応） | **interpretive** | Part D（定量証明でなく構造対応） |
| 10 | 仮説：螺旋の段・オクターブ・周波数帯・折り畳み層・繰り込みスケール・動径次元は同一構造か | **interpretive→speculative** | Part A〜C で構造整合を測定。宇宙論的意味づけは speculative。「同一」は **提案** であって証明ではない |
| 11 | 双曲幾何は手作り2分階層に内在／εは手入れ／R²比較は非形式的／平坦実空間は2-cellが要る（床） | **（床の明示）** | AUDIT.md 床1–7。監査2・3が clean に通らず YELLOW の主因 |

---

## 今後（e003+）

各モジュールを GREEN にした時点で、その主張と tier をここに追記する。
空欄を埋めるたびに、白から構造が立ち上がる順番（docs/00_grand_map.md）を一段進める。

---

## e008 — 同時共創発（白 → 物質・時間・空間）  (STATUS: GREEN, 統合は interpretive)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 白(一様+ノイズ)＋GPEだけから KZ 渦が自発核生成、N∝τ_Q^{−b}（遅クエンチ域 b≈0.46, R²=0.92） | **measured** | `result.json` matter_kz、`robustness.json`（L・γで b=0.23–0.46, 全 PASS） |
| 2 | 正味巻き数 ≈ 0（±対で生成＝陰陽の保存対）、循環量子化 | **measured** | net_winding≈6/192²、quantized=True |
| 3 | 速クエンチで欠陥密度が飽和（KZ の膝）＝狙っていない KZ 特徴 | **measured** | fast_quench_saturates=True、full-range b=0.31 |
| 4 | 粗大化の矢：クエンチ後 N が減りスペーシング L/√N が伸びる | **measured** | spacing 8.2→28.0 単調増 |
| 5 | 可逆 echo：保存GPE(γ=0)で戻り忠実度 1.0000 → 矢は法則に無い | **measured(忠実度)/interpretive(教訓)** | echo_fidelity=1.0000。矢は散逸+低S始端から |
| 6 | 3Dで量子化渦線が白から創発し、線数は τ_Q で減少（3D KZ）。線の大半は**トーラスを巻く**（収縮可能率 ≈0.30、残りも周期境界で閉じる渦線） | **measured** | `result3d.json`（周期 union-find。**訂正**：旧「閉率0.94」は非周期ラベリングのアーティファクト＝Codex P2、収縮可能率0.30に修正） |
| 7 | 物質・時間・空間の「同時共創発」 | **interpretive** | measured は各創発と KZ 数。統合は読み |
| 8 | 固定格子＝空間は与えられている／「幾何」は相関・折りたたみでRT幾何でない／b は protocol 依存（床） | **（床の明示）** | AUDIT.md 床1–6 |

## e009 — 探索的創発（持続電流・植物・未知）

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| X1-A | 3-トーラス上の量子化循環は持続し、ノイズでも位相すべりせず保護される（打ち消さない循環） | **measured / analogy(電子的)** | `results/x1.json`：winding n=1,2,3 持続、noise でも n=2 維持、Edrift~1e-13 |
| X1-C | リンクした渦輪(Hopf的)は素のGPEで形成後に縮む（安定化項なし） | **measured(サイズ)/frontier-observation** | core_volume 2368→931。素のGPEに安定化なし＝縮むのは正直な結果（**訂正**：縮小判定の baseline を一様初期密度=0 から形成後の芯体積に修正し shrinks=True に＝Codex P2） |
| open-1 | 相対論的複素スカラー(非GPE)の白からも KZ 渦が出る＝共創発は基板非依存 | **measured / interpretive(普遍)** | `results/open_menu.json`：N∝τ_Q^{−0.50}、ρ_med≈1.0 |
| open-2 | クエンチ後 ±渦は逆符号が同符号より近い（対形成）。符号入替え帰無に対し有意 | **measured / frontier-observation** | 最近接 同13.5 vs 逆8.6（**最小像距離**）、置換検定 p<0.003 |

## e010 — Kibble-Zurek をコヒーレンス長で固める  (STATUS: GREEN, 絶対指数は protocol 依存)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | KZ 欠陥間隔は凍結コヒーレンス長 ξ の**一定倍**（間隔∝ξ＝KZ 機構） | **measured** | `result.json`：間隔/ξ=2.75、CV=0.041（16倍の τ_Q 範囲で一定） |
| 2 | ξ∝τ_Q^σ かつ N∝τ_Q^{−2σ}（**内部整合 b=2σ**） | **measured** | σ=0.282、b=0.570、2σ=0.564（相対差 1%） |
| 3 | 数えた芯は実在の凝縮体中の渦（γ未凝縮の罠を回避） | **measured** | ρ_median 0.94–0.99（全凝縮で締める） |
| 4 | z 順序 b(z=1) > b(z=2)＝KZ b=(D−d)ν/(1+νz) と同じ向き（小 z→大 b） | **measured(順序)/interpretive(KZ)** | 軽い減衰の自然 z プロトコル（γ/η は別演算子＝「整合」でない）で NLKG(z=1) b≈0.5 > GPE(z=2) b≈0.24（`robustness.json`） |
| 5 | 絶対 b は protocol 依存／間隔/ξ 値は ξ 定義依存／z 対比は減衰に敏感（床） | **（床の明示）** | AUDIT.md 床1–4 |

## e011 — 欠陥の動的化学（±束縛 ＋ 有限温度の解離）  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | ±双極子は束縛して並進、v·d=一定（ハミルトニアン双極子則 v~1/d） | **measured** | `results/pair_binding.json`：v·d=0.67、CV≈0.01（d=16–28） |
| 2 | ++同符号は束縛して公転、ω·d²≈2（点渦 ω=2/d²） | **measured** | ω·d²=2.08、CV≈0.04 |
| 3 | 選択的：逆符号は並進・同符号は公転（一つの場の方程式から2則） | **measured** | ±回転≈0、++重心ドリフト≈0 |
| 4 | 有限温度で ±対は解離、寿命は T とともに単調減少（熱活性） | **measured(寿命↓)/interpretive(Arrhenius)** | `results/finite_T.json`：寿命 2500→1985(T 0→0.6)、drop 21%、slope≈−780 |
| 5 | 「分子/化学」は analogy／v·d は小 d で崩れる／Arrhenius は cap・BKT の床 | **（床の明示）** | AUDIT.md 床1–4 |

## e012 — Hopf 安定化＝「第三」（高階微分が崩壊を止める）  (STATUS: GREEN, 完全自己安定化は frontier)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | Q_H=1 ホップ粒子の Hopf 不変量は整数（滑らかな構成から ≈1） | **measured** | `results/hopfion_static.json`：Q_H=1.00（Whitehead (1/16π²)∫A·B、box/L で安定） |
| 2 | Derrick 地形：素(c4=0)は崩壊、第三(c4>0)で有限 L*＝√(c4·E4/E2)、L*∝√c4 | **measured** | L*=0.565/1.130/1.696（c4=1/4/9＝1:2:3） |
| 3 | 動的：素(c4=0)はホップ粒子が崩壊（Q_H→0、e009 の縮みの動的確認）。エネルギー単調減で勾配検算 | **measured** | `results/hopfion_flow.json`：Q_H 0.99→~0、ΔE/予測≈1.0 |
| 4 | 動的(陽的勾配流)：第三(c4>0)の崩壊抵抗は脆い（細格子で抵抗、粗格子/陽的 dt で崩壊・数値不安定） | **frontier-observation** | `hopfion_flow.py`：陽的四次は剛性で不安定（Stage3 で解決） |
| 5 | **完全PDE 自己安定化（★本丸、frontier→measured）**：安定化半陰的流で c4>0 が Q_H≈1 を保ったまま有限 L* へ収束、L* は c4 で増加（Derrick）、エネルギー単調 | **measured** | `hopfion_pde.py`/`results/hopfion_pde.json`：Q_H≈1 保持、L*≈3.3/3.7/4.1(c4=15/25/40)、勾配を 1/(1+dt·κ·\|k\|⁴) で濾過 |
| 6 | L* 周りの**有界 basin（両側、大域的でない）**：遥かに小さくも大きくも始めると巻き戻る／大 c4 は解像度ぎりぎり(L*∝√c4 が格子カットオフへ)／絶対 L* は解像度/κ 依存／「粒子」は analogy（床） | **（床の明示）** | `hopfion_pde.py` 床。Q_H≈1 保持・有限 L*・L*(c4) 増加(κ~80×非依存)が robust |

## e013 — 器＋中身（循環は内部に load-bearing）  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 循環なし→内部デッドコア（b≈0）、循環あり→内部 b が Pe で単調増 | **measured** | `result.json`：内部 b 0→0.029（U=0→8）、2×2 対流セル |
| 2 | 総 b 差は小（外殻は拡散で生存）＝load-bearing は内部に対して | **measured** | 総 b スプレッド 7% |
| 3 | 自己組織した対流（Ra>Ra_c）が内部を養う（規定流 analogy を一段 measured へ） | **measured** | `rayleigh_benard.json`：KE 0→10（Ra_c≈20）、内部 b 0.015→0.42 |
| 4 | 内部比のゼロ割り→値で報告／境界の指数発散→ロジスティック収容力（床/罠回避） | **（規律）** | a·b·c·(1−b) で [0,1] |
| 5 | 規定流は analogy／周期箱の最小 Boussinesq／load-bearing は内部に（床） | **（床の明示）** | AUDIT.md 床1–4 |

## e014 — 3D 因果 → 次元（運動学）  (STATUS: GREEN, 動的幾何は AJL 継承)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 座標を捨て因果順序だけから次元を復元（Myrheim-Meyer、d=2,3,4） | **measured** | `result.json`：d_MM=1.99/2.97/3.95 |
| 2 | 関係対割合の正しい式は分母2（r(2)=0.5）。理論側の係数誤りを捕獲＝両方を疑う | **measured/規律** | r(d)=Γ(d+1)Γ(d/2)/(2Γ(3d/2))、r(2)=0.5 ガード |
| 3 | スペクトル次元：3D 幾何 d_s≈3、2D≈2 | **measured** | `spectral.json`：3.04 / 2.03 |
| 4 | 因果集合 Hasse のスペクトル次元は異常になり得る（合わせ込まない） | **observed** | d_s=3.13（既知の微妙量） |
| 5 | 運動学的（与因果順序→次元）。動的幾何の自己組織化は AJL 継承（床） | **（床の明示）** | AJL 1305.4702, 1110.6875 |

## e015 — 器の閉じ（開-閉の二重性、駆動依存）  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 駆動下で自己維持・増殖、半分切除→ほぼ完全再生（~98%） | **measured** | `result.json`：総 v 成長、再生 ~98% |
| 2 | 駆動を切る（F→0）→総 v→0（死）。生存の臨界 F 窓 | **measured** | 死=True、生存窓 F∈[~0.03,~0.07] |
| 3 | 両腕オートポイエーシス：膜を壊す/代謝を止める、どちらを切っても死 | **measured** | `autopoiesis.json`：γ→0 死・α→0 死、臨界 S_c≈0.05 |
| 4 | 開-閉の二重性は interpretive、autopoiesis/膜/代謝/生命は analogy（床） | **（床の明示）** | AUDIT.md 床1–4 |

## e016 — Hopf basin（Q_H 安定性は observed／**√c4 size 則は撤回**）  (STATUS: F, role F, 第8監査で GREEN 剥奪)

> **第8監査（撤回）**：`size=k√c4` は **target_encoded**（start∝√c4 を初期条件に埋込・流れ未収束）。
> decoupling テスト（start を √c4 から切り離す）で size/√c4 が drift 26%＝√c4 則は初期条件由来で崩れる。
> Derrick の L*~√c4 は既知理論だが本モジュールは清潔に測定していない。**行1・5 を撤回**。
> 残るのは Q_H≈1／Q_H=2 のトポロジカル安定性・エネルギー単調（observed）。真の start 非依存 L* は frontier/H001。

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | ~~size=k√c4 に従う~~ **撤回（target_encoded）**：start∝√c4 を初期条件に埋込・流れ未収束。decoupling で size/√c4 が drift 26%＝創発でない | ~~measured~~ → **retracted** | `hopf_basin.json`：`size_law_target_encoded=True`, `decoupling_drift` |
| 2 | **Q_H=2**（方位角巻き×2）も同じ流れで保持（|Q_H|≈2）、エネルギー単調＝トポロジカル安定性（size 非依存） | **observed** | qh2_held=True、\|Q_H\| ~1.95→~2.0 |
| 3 | 保持する start は**有界な窓**（両側）＝ basin は有界（大域でない） | **observed** | basin_window_mult（下は未解像、上は解離） |
| 4 | 絶対 k・basin 端は解像度/κ 依存／大 c4 は解像度ぎりぎり／「粒子」は analogy（床） | **（床の明示）** | robustness.json（κ~独立）、marginal_c4 |
| 5 | ~~size 則は L=44/52/56/64 で CV<5%~~ **撤回**：この CV も同じ √c4-seeding 由来で創発の証拠でない。有効なのは**負の結果**（arrested-Newton は basin を広げない） | ~~measured~~ → **retracted（負の結果は有効）** | `arrested_newton_v2.json`（L-series の CV は seeding 由来） |
| 6 | CV は L で単調上昇・arrested-Newton は basin を広げない(有界は固定格子で本質)＝**負の結果は残る** | **observed/床** | `arrested_newton_v2.json`（basin plain=accel=[0.7,1.5]） |

## e017 — 壁つき Rayleigh-Bénard（教科書 Ra_c）  (STATUS: GREEN, Type A)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 壁つき線形安定性で臨界 Rayleigh 数を教科書と<0.4%で復元：no-slip 1713.9@a_c3.12、free-slip 657.3@2.22 | **measured** | `results/rb_linear_stability.json`（教科書 1707.76/657.5、Type A） |
| 2 | no-slip > free-slip（剛体壁の方が対流が立ちにくい） | **measured** | Ra_c 順序（Type A） |
| 3 | 周期箱の Ra_c≈20（e013）は箱固有値＝artifact | **interpretive** | 壁つきが物理値 |
| 4 | 壁つき DNS：Ra>Ra_c で Nu>1（対流輸送）、内部 delivery が Ra で増 | **measured** | `rb_dns.py`（Nu(Ra)、c_interior） |
| 5 | 線形 onset のみ・固定 1D 格子・接線 BC は one-sided 必須（床/罠回避） | **（床の明示）** | AUDIT.md 床1–4 |

## e018 — 器の膜（三腕＋相図／空間膜小胞）  (STATUS: GREEN, Type B)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 三腕（基質→代謝→膜）：どの腕を切っても・駆動を切っても死 | **measured** | `results/vessel_membrane.json`（四様の死） |
| 2 | 相図は臨界駆動曲線 s_c(dA)＝漏れとともに上昇（駆動閾値が支配、下限が bracket された行のみ） | **measured** | bracketed (dA,s_c)=[(0.25,0.05),(0.35,0.1)]、strictly rises（dA=0.15 は最小駆動でも生＝閾値が走査域外→報告のみ） |
| 3 | phase-field で境界をもつ有界単一小胞（薄い膜）が駆動で持続・切ると溶ける | **measured** | `results/membrane_vesicle.json`：inside_frac≈0.28、界面帯≈0.05、連結1 |
| 4 | 漏れ↑→生存に必要な駆動↑（空間版の臨界駆動曲線、生存判定は bounded_single_vesicle） | **measured** | leak 0→0.4→0.8 で min s 0.1→0.2→0.2 |
| 5 | 最小動力学/連続 phase-field（脂質膜でない）、膜/小胞/protocell/生命は analogy（床） | **（床の明示）** | AUDIT.md 床1–4 |

## e020 — 小胞の分裂は場の力学から出るか（H002+, 負の結果）  (STATUS: GREEN=誠実な負, Type B)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 受動 phase-field（Allen-Cahn 質量制御・Cahn-Hilliard 保存）は**自発分裂しない**：軌道全体で **max_components=1**（過渡的分裂もなし）、全形が単一連結領域に緩和 | **measured（負）** | `results/division.json`：max_components_ever=1（密サンプリング）、分裂則を書いていない |
| 2 | AC は合体（ダンベルのくびれが埋まる）、CH は退縮して compact droplet＝分裂の逆。末端は正直に：多くは compact droplet、箱を跨ぐ AC フィラメントのみ単一の伸びた塊（それでも分裂せず） | **measured/interpretive** | 曲率流/表面張力、`final_single_compact_droplet` |
| 3 | 分裂には能動 turnover（Zwicker 能動ドロップレット）が要る＝frontier（誘導しない・回していない） | **interpretive/frontier** | 床 |
| 4 | 2D 連続・受動モデルのみ・「小胞/分裂」は analogy・分裂する細胞を作っていない（床） | **（床の明示）** | AUDIT.md 床1–3 |

## e019 — 循環×粒子の結合（輸送・U_c・三体）  (STATUS: GREEN, Type B/C)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 規定 roll が粒子を運び centroid が U とともに単調移動（輸送） | **measured** | `results/coupling.json`：centroid_disp 単調増 |
| 2 | 第三が同一性（Q_H）を U_c まで保持、超えると引き裂かれ Q_H→0・size 発散 | **measured** | held→torn crossover U_c≈7（U=6 保持/U=11 崩壊） |
| 3 | 重心は成分場の**空間**軸で（4D 軸を使わない）＝罠回避 | **measured/規律** | `_centroid` 空間軸のみ、test で確認 |
| 4 | 三体結合：背反応が流れを自己制限し粒子保持（U=3.35,Q_H=0.97）／背反応なし=一方向は過駆動で破壊（U=9.56,Q_H=−0.21）／駆動オフで b→0.005・流れ停止＝背反応が粒子を救う負のフィードバック | **measured** | `results/three_body.json`（two-way vs one-way vs no-drive、backreaction_saves_particle=True） |
| 5 | 規定 roll・振幅還元流（完全 NS でない）・U_c は crossover・「粒子/同一性/ホメオスタシス」は analogy/interpretive（床） | **（床の明示）** | AUDIT.md 床 |

## e024 — 器のエンジン（ラチェット→モーター→器のモーター）  (STATUS: GREEN, Type B, H016)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **非対称周期ポテンシャルは対称ノイズを整流**：整流 (v(+A)+v(−A))/2 が asym=1,A=4.5 で **+0.60**（対称 asym=0 は ~0）、A 1.5→6 で **0.02→0.96**（単調増）、asym=0.1（51/49）でも **+0.08**（閾値なし） | **measured** | `results/ratchet.json`（サンドボックス eratchet2.py と一致）；罠＝静的傾き別測平均 |
| 2 | **回転の最小は三**：等間隔 N 位相の場は N≥3 で回転（ripple<0.05）・N≤2 は脈動；三相電流和 max\|Σ\|=0；トリプレン零相＝[3,6,9]；三相ロータ自己回転 **+19rev**（単相はぐらつき、単相+ラチェットで回る） | **measured** | `results/motor.json`（emotor.py と一致） |
| 3 | **器の心臓**：燃料勾配 Δμ が三回対称ロータを回し（閾値→上昇）、負荷に停動（load≈3）、器 **Ψ=0.93** 維持、燃料切断で **Ψ→0**（死）、方向は燃料の符号で反転（±0.56）＝5ゲート GREEN | **measured** | `results/vessel_motor.json`（evessel_motor2.py と一致）；罠＝平滑化正味回転 `max(om_s−0.05,0)` |
| 4 | **interpretive**：器の心臓＝勾配→回転→仕事→自己維持。整流の非対称起源＝運動方向の源。KNOWN MATCH＝ブラウン・ラチェット/三相回転磁場/ATP合成酵素 | **interpretive/analogy** | AUDIT §claim tier；**「生命」はゲート名に入れない** |
| 5 | 1D 過減衰・スカラー Ψ ODE・絶対電流/回転数/Ψ 準位は (D,T,dt,asym,feed) 依存＝床。ゲートは符号・閾値・崩壊（頑健、`robustness.json` で seed/Np/dt 掃引）。「ボルト/生/死」は analogy——ATP合成酵素を作っていない | **（床の明示）** | AUDIT.md 床1–3 |

## e025 — 生きた器（三器官・二つの死 → オートポイエーシス閉環）  (STATUS: GREEN, Type B, H016)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 一つの 2D CGL 場に**三器官が共存**：燃料下で bulk\|ψ\|²≈1.96・巻き +1（同一性芯＋代謝モーター＋境界液滴が維持） | **measured** | `results/complete.json`：`bulk_and_winding_sustained`。ゲート名は物理量のみ |
| 2 | **二つの崩壊は独立**：燃料切断→bulk→0.01（巻きは崩壊まで保持）；反渦注入→巻き→0 だが bulk≈1.98（高いまま）＝**代謝 ≠ 同一性** | **measured/interpretive** | `bulk_collapses_on_fuel_cut` ／ `winding_lost_while_bulk_high`（サンドボックス evessel_complete.py と一致） |
| 3 | 塊切除（芯無傷）→巻き +1 保持・bulk 再生（`winding_survives_body_excision`） | **measured** | `results/complete.json` |
| 4 | **閉環（芯が自分の巻きを読み gain を gate）が二つの死を結ぶ**：反渦後、閉環なし bulk≈1.97（身体は生存）／閉環あり bulk→0.04（巻き喪失が bulk 崩壊を引く）＝**決定的対比** | **measured** | `results/autopoietic.json`：`winding_loss_collapses_bulk_iff_closed`（evessel_auto.py と一致） |
| 5 | **interpretive**：操作的閉包＝自己と自己維持が不可分（Maturana-Varela）。KNOWN MATCH＝CGL 駆動液滴/トポロジカル電荷/オートポイエーシス。「自己/生/死/同一性」は analogy——**ゲート名に入れない**、細胞・死・自己を作っていない（床） | **interpretive/analogy/床** | AUDIT §claim tier・床1–3 |

## e026 — トポロジカル分裂会計（巻きはコピーできない、創るしかない）  (STATUS: GREEN, Type B, H016)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 一つの +1 を分けると娘は **(+1, 0)**：一つは巻いた娘、もう一つは空（内側全体は +1）。**+1 を (+1,+1)=+2 にできない** | **measured** | `results/division.json`：`split_gives_one_wound_one_empty`。CCW ループで巻きを読む |
| 2 | 二つの巻いた娘には**新しい +1/−1 対の核生成＋−1 排出**が要る：娘 (+1,+1)、両娘ループ +2、全体（−1 込み）ループ +1＝**保存** | **measured** | `two_wound_daughters_need_shed_anti`（サンドボックス evessel_div2.py と一致） |
| 3 | **interpretive**：再生産＝**創る≠コピー**；電荷保存ゆえ新しい巻きは必ず反対物を伴い捨てる；子の同一性はその子自身。KNOWN MATCH＝トポロジカル電荷保存/ノークローニング/対核生成 | **interpretive/analogy** | AUDIT §claim tier；「同一性/自己/再生産」は**ゲート名に入れない** |
| 4 | 純**静的トポロジー会計**（時間発展なし・代謝コスト未払い）＝床。**動的くびれ（渦を娘へ運ぶ）は frontier**。会計は娘半径/分離/囲みループ半径に不変（`robustness.json`）。生物を再生産していない | **（床の明示）** | AUDIT 床1–3 |

## e027 — 進化と大転移（ダーウィン的ループ・複雑性の上昇・協力の高次個体）  (STATUS: GREEN, Type B, H016)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **ダーウィン的ループが突然変異で閉じる**：適応（変異 ON→平均形質 1.51／OFF→0.00）、負の頻度依存で多様化（std→7.7、~20帯）、移動最適をレッドクイーン追跡（遅れ 0.07） | **measured** | `results/evolution.json`（eevolution.py と一致）。ゲート＝測定統計量 |
| 2 | **複雑性は拡張ゲノム＋需要で上昇**：単純環境 頭打ち（ゲノム長 1.4）、豊か 6.0、需要増 6.5（解ける課題 0.9→9.4）＝材料＝遺伝子重複＋需要 | **measured** | `results/openended.json`（eopenended.py と一致） |
| 3 | **協力＝高次個体は空間構造で生存**：よく混ぜると崩壊（協力率 0.00）、空間で生存（0.73）、assortment +0.13；誘惑 b は生存域（b≥1.7 で崩壊） | **measured** | `results/transition.json`（emajor.py と一致）。**罠**：b は生存域 |
| 4 | **interpretive**：ダーウィン的ループ閉／複雑性の材料＝拡張ゲノム＋需要／高次個体＝空間 assortment で束ねた協力。KNOWN MATCH＝Wright-Fisher/頻度依存/遺伝子重複/Nowak-May/多層選択/Hamilton 則 | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **エージェントモデル（場でない）・固定 1D 形質（Stage1）・外部需要（Stage2）・協力安定化のみ（Stage3）＝床**。真のオープンエンド性（内生需要）と完全な大転移（群れ再生産・分業・対立抑制）は frontier。seed 掃引で頑健。生物・社会を作っていない | **（床の明示）** | AUDIT 床1–4・`robustness.json` |

## e028 — トポロジカル記憶（穴の巻き＝受信されるビット）  (STATUS: GREEN, Type B, H012+H013)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **記憶は穴（非観測領域）を囲むループの巻き＝非局所**：穴を囲まぬループ=0、全穴を囲む箱ループ=Σビット。局所パッチに宿らない | **measured** | `results/memory.json`：`nonlocal_winding`。CCW/箱ループで読む |
| 2 | **局所擾乱で消えない（保護）**：巻きビットは全ノイズ準位で 100%、対照の動的バンプは劣化（90%） | **measured** | `protected_under_local_perturbation` ／ `dynamical_baseline_erodes`（ereceiver/edecisive と一致） |
| 3 | **容量 > 受信機の dof**：固定 h=6 受信機（境界 dof≈48）が **M=121 保護ビットを 100% 回復**＝storage-in-loop（MC≤N）反証＝ビットは受信機でなく穴に受信される | **measured** | `capacity_exceeds_dof`（M>dof、edecisive と一致） |
| 4 | **動的 GL リング（スペクトル ETD）**：受信巻き n＝round(Φ)（\|n−Φ\|≤0.5）、ゲージ不変（dE≈2e-6＝囲む磁束のみ読む）、位相スリップ障壁で保持 | **measured** | `results/ring.json`：`autonomous_quantized`/`gauge_invariant`（erecv_dyn2 と一致）。**罠**：スペクトル ETD |
| 5 | **interpretive**：ビットは非観測の穴に**受信**される（貯蔵でない）。KNOWN MATCH＝Aharonov-Bohm/フラックス量子化/トポロジカル電荷。**床**：位相スリップ障壁は強制ノード proxy＝floor（GREEN 閾値でない）。1D/固定格子・容量は finite-size。「記憶/受信」は analogy——記憶を作っていない | **interpretive/analogy/床** | AUDIT §claim tier・床1–3 |

## e021 — 自己受信（芯が自分の巻きを読む・駆動液滴の同一性）  (STATUS: GREEN, Type B, H014)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **外場ゼロでリングが自分の芯の巻きを読む**：リング巻き＝芯巻き（w=−2..+2）、持続電流の符号も追従＝自律的自己受信 | **measured** | `results/self_receiver.json`：`ring_reads_core_winding`（erecv_sc.py と一致） |
| 2 | **読みは芯位置・受信半径に不変**：芯ジッタで巻き 1.00 不変、芯の外の全 R で巻き量子化＝位置でなく巻きを読む | **measured** | `reading_invariant_to_core_position` / `reading_quantized_across_radii` |
| 3 | **駆動液滴の巻きは駆動下で保持**（+1、芯＝穴）、**近い反渦 d=7 で対消滅**（巻き→0・芯が ~1 に癒える）、**遠い反渦 d=30 は生存**（+1）＝臨界距離 | **measured** | `results/vessel_alive.json`：3ゲート（evessel4.py と一致）。署名＝芯振幅が癒える |
| 4 | **interpretive**：自己同一性＝自分の源の窓を読むループ（外場不要）；同一性は駆動で保持され身体損傷でなく自分の反対物にのみ死ぬ。KNOWN MATCH＝フラックス量子化/渦反渦対消滅/駆動散逸液滴 | **interpretive/analogy** | AUDIT §claim tier；「自己/同一性/死」は**ゲート名に入れない** |
| 5 | 2D GL トイ・境界巻きクランプ・臨界半径/距離は finite-size・受信機は芯の癒し halo の外に要る（床）。seed 掃引で頑健。自己を作った・殺したのではない | **（床の明示）** | AUDIT 床1–3・`robustness.json` |

## e022 — 地平線の台帳（受信としてのループ・DS 分子）  (STATUS: GREEN, Type B, H009+H010)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **ギャップ（非観測領域）は観測側に一つの量子化数のみ渡す**（Aharonov-Bohm リング）：同一 loop-sum の局所位相はスペクトル不変（dE≈9e-16）、Φ は mod 1 量子で周期、局所密度は平坦 | **measured** | `results/ab_gap.json`：3ゲート（egap0.py と一致、機械精度） |
| 2 | **地平線の台帳＝Dou-Sorkin 分子はパラメータフリーな数**：⟨n⟩ が β とともに π²/6（=1.645）プラトーへ近づき導出 T(β) を追従／β=1 で密度不変（spread<0.15、1200 seed） | **measured** | `results/ledger.json`：`ds_rises_to_pi2_plateau`/`ds_density_independent`（egap3a2.py と一致） |
| 3 | **台帳は地平線ライン上のプロファイル w(u,0) のみ読む**：地平線上スポットと v 非依存リッジ（同じ w(u,0)）が同一台帳（spot==ridge）、flat と異なる | **measured** | `ledger_reads_horizon_profile`（elink_bump.py と一致） |
| 4 | **interpretive**：ギャップ/地平線は一つの受信数を渡す；地平線のエントロピー台帳は地平線プロファイルのみ読む。KNOWN MATCH＝Aharonov-Bohm/Byers-Yang/DS エントロピー分子/π²/6 係数/面積則 | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **3D（2+1）DS 係数は DS d>2 IR 病理で FLOOR（box 依存・GREEN に入れない、Barton 系が cured 版＝frontier）**。DS 数は Monte-Carlo で高分散（多 seed で収束）。2D のみ SOLID。「エントロピー/受信/地平線/BH」は analogy——BH を作っていない | **frontier/床** | AUDIT 床1–3・`robustness.json` |

## e023 — 因果作用（順序から時空へ：時間・空間・向き）  (STATUS: GREEN, Type B, H005–H008；曲率治癒は frontier)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **純粋な因果順序から時間が創発**：rank（最長鎖）が隠れ時刻を回復（Spearman 0.99）、中間 rank の反鎖（空間スライス）が空間を充填 | **measured** | `results/order_time.json`：`rank_recovers_hidden_time` / `spatial_slice_fills_space` |
| 2 | **順序だけから有限次元**：interval 次元（Myrheim-Meyer、diamond 2D）≈2＝有限。座標を捨て順序のみで測定 | **measured** | `interval_dimension_finite`（core/causet、e014 隣接） |
| 3 | **向き（orientation）が時空を作る**：有向は有限次元＋時間、同じ因果対を対称化するとスモールワールド mush（~全 N に 2 hop 到達＝次元発散）＋サイクル（非巡回順序が壊れ時間なし） | **measured** | `results/directed_vs_undirected.json`：3ゲート（ball 成長 [1,316,700]、三角形 7.7M） |
| 4 | **interpretive**：時間と有限次元空間は順序だけから読める；因果の矢が時空を作る。KNOWN MATCH＝因果集合理論(BLMS)/Myrheim-Meyer/無向ランダムグラフのスモールワールド崩壊 | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **frontier（GREEN にしない・正直に保留）**：曲率治癒＝BD 作用降下(H007)／実重み経路積分は多様体を選べない(H008)——サンドボックス参照が本セッションで未検証、検証済み数値なしのため昇格しない。**床**：固定次元 sprinkling（多様体を入れて順序を生成）＝時間/次元を回復、無から多様体を導いたのでない。「時間/時空/因果の矢」は analogy | **frontier/床** | AUDIT 床1–3・`docs/working_ledger/H005_*` |

## e029 — 深いフロンティア（内生的需要／完全な大転移）  (STATUS: GREEN=機構実証, Type D/frontier, H017)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **内生的需要で複雑性の頭打ちが外れる**：宿主寄生者の敵対的共進化（非有界形質）で、需要（寄生者の広がり）が外部ノブなしに内側から上昇（0.5→~2.4）し、宿主複雑性が STATIC の頭打ち（中央値 ~12・平坦）を超えて上昇し続ける（中央値 ~26・最大 ~31・スロープ +0.028） | **measured（frontier, ensemble）** | `results/coevolution.json`：3ゲート。full で 4/6 escalate（残り collapse＝正直な床） |
| 2 | **完全な大転移＝群れが再生産する高次個体**：個体選択は協力崩壊（0.05–0.06）、群れ再生産＋創設者ボトルネック k=1 は協力を救済（0.92–0.96）、狭いボトルネックほど協力↑（k=1: 0.92 > k=20: 0.81） | **measured（frontier）** | `results/major_transition.json`：3ゲート（Wilson 多層選択/Hamilton 則/生殖ボトルネック） |
| 3 | **interpretive**：欠けていた材料＝**内生的に上がる需要**（軍拡競争）＋**群れ再生産（ボトルネックが対立抑制）**。KNOWN MATCH＝Red Queen/宿主寄生者共進化/多層選択/Hamilton 則/Grosberg-Strathmann | **interpretive/analogy** | AUDIT §claim tier |
| 4 | **FRONTIER（未解決・正直に）**：真の無限オープンエンド性と、分業・生殖体細胞分化を含む完全な大転移は未解決——ここで示したのは**機構**であって解でない。軍拡競争は run ごとに escalate/collapse で変動（ensemble 中央値でゲート・cherry-pick しない）。協力の安定化は必要条件のみ。「生命/心/社会/多細胞性/オープンエンド性」は analogy——measured は物理量（ゲノム長・広がり・協力率）のみ | **frontier/床** | AUDIT 床1–4・`robustness.json`（seed batch/格子で頑健） |

## e030 — 分業の創発（凸リターンが生殖体細胞分化を駆動）  (STATUS: GREEN, Type D/frontier, H018)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **凸リターンが専門化を駆動**：細胞が投資 x∈[0,1] を割り当て、群れ適応度＝⟨x^a⟩·⟨(1-x)^a⟩。凸（a>1）で専門家割合が上昇（a=0.5: 0.26 → a=4: 0.85）＝Michod の適応度凸性理論 | **measured（frontier）** | `results/division_of_labor.json`：`convex_returns_drive_specialization`（凸で spec>0.6） |
| 2 | **専門化は凸性とともに単調上昇**：a=0.5/1/2/3/4 で 0.26/0.45/0.76/0.81/0.85（単調）、凹（a=0.5）の 3.3 倍以上 | **measured（frontier）** | `specialization_rises_with_convexity`（凸>1.5×凹・単調） |
| 3 | **生殖体細胞分化＝役割の共存**：凸群れは x>0.8（生殖系列 proxy）と x<0.2（体細胞 proxy）を同一群れ内に共存（both_roles=1.0） | **measured（frontier）** | `germ_soma_differentiation`（both_roles_convex>0.9） |
| 4 | **interpretive**：分業（生殖体細胞分化）は凸な適応度リターンから創発する——設計されず、投資配分の進化から。KNOWN MATCH＝Michod 適応度凸性/Volvox 生殖体細胞分化/群選択 | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **FRONTIER（床）**：これは分業の**機構**（凸性→専門化）であって完全な多細胞個体でない。x は抽象的投資、適応度は toy。「生殖/体細胞/分業/多細胞性」は analogy——measured は投資配分と専門家割合のみ。seed batch・格子(G/n)で頑健 | **frontier/床** | AUDIT 床1–3・`robustness.json` |

## e031 — 因果作用の平滑化（生 BD は揺らぎ支配・平滑化が抑える）  (STATUS: GREEN, Type D/frontier, H018)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **生 BD 作用は揺らぎ支配**：Benincasa-Dowker 生作用の std が N とともに増大（81→228→285）＝H008 の揺らぎ問題を定量化 | **measured（frontier）** | `results/smearing.json`：`raw_action_fluctuation_dominated`（生 std >3× 平滑 std を全 N で） |
| 2 | **Glaser-Surya 平滑化が揺らぎを抑える**：平滑作用の std が生の 1/7〜1/40（最大 N で damp factor 6.98、大 N で >5）＝メソスケール smearing が揺らぎを damp | **measured（frontier）** | `smearing_damps_fluctuations`（最大 N で生/平滑 std >5） |
| 3 | **曲率バンプは床**：平滑作用は曲率バンプ（mean 9.96→26.49）を拾うが揺らぎ（std 40.88）に対し ~1σ＝GREEN 閾値でなく床 | **（床の明示）** | `curvature_bump_*` vs `curvature_flat_std`（分離は ~1σ） |
| 4 | **interpretive**：離散因果作用の H008 障害（生作用の揺らぎ）は平滑化で抑えられるが、曲率信号は有限 N では揺らぎに埋もれる。KNOWN MATCH＝Benincasa-Dowker 作用/Glaser-Surya 平滑化/n0-n1-n2 分子 | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **FRONTIER（床）**：**障害を定量化**したが**治療していない**——曲率抽出は ~1σ で床。`_bd_raw` は core.causet.bd_action_2d と一致（chain/antichain=N を検証）。「エントロピー/作用」は物理量。seed batch・eps で頑健 | **frontier/床** | AUDIT 床1–3・`robustness.json`・test で core 一致 |

## e032 — 3D Dou-Sorkin の病理（2+1 面積則は成立・係数は普遍性を失う）  (STATUS: GREEN, Type D/frontier, H018)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **2+1 面積則は成立**：分子数が切り口幅 w に線形（R²>0.85、full で 0.98–0.99）＝2D（e022）の面積則が 3D へ延長 | **measured（frontier）** | `results/horizon_3d.json`：`area_law_holds_2plus1`（全密度で R²>0.85） |
| 2 | **係数は密度依存でドリフト**：係数（数/w）が密度とともに増大（99→200→400、比 4.02×／密度比 9.0）＝2D の純数（~1 で不変）と違い普遍性を失う＝d>2 IR 病理 | **measured（frontier）** | `coefficient_density_dependent`（係数比>1.3） |
| 3 | **interpretive**：DS エントロピー数は 3D でも面積スケーリングを保つが係数の普遍性を失う（d>2 IR 病理）＝2D（e022）が SOLID・3D が床、の理由を定量化。KNOWN MATCH＝Dou-Sorkin 分子/面積則/d>2 病理 | **interpretive/analogy** | AUDIT §claim tier |
| 4 | **FRONTIER（床）**：d>2 病理を**定量化**したが**治療していない**——Barton 系 cured 分子は未再現。3D 係数は普遍数でない、3D は床・2D は SOLID。「エントロピー/地平線/BH」は analogy——measured は分子数の統計量のみ。seed batch・box 高さで頑健 | **frontier/床** | AUDIT 床1–3・`robustness.json` |

## e033 — 分業を「場」から（エージェントなし・Cahn-Hilliard スピノーダル分解）  (STATUS: GREEN, Type A/faithful, H019)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **臨界点 χ_c=2 が創発**：Flory-Huggins 相互作用 χ を上げると秩序変数（場の std）が χ_c=2 で跳ぶ＝対称混合の Flory-Huggins 臨界値と一致（入れていない）。χ<2 は一様（generalist）、χ>2 は二相 | **measured** | `results/field_division.json`：`homogeneous_below_critical`（χ=1.5 で秩序変数<0.05） |
| 2 | **二相の共存＝場ネイティブな分業**：χ>2 でスピノーダル分解、φ_low（体細胞 proxy）と φ_high（生殖系列 proxy）が共存（both_phases=1.0、専門家率 0.75–0.89） | **measured** | `phase_separation_above_critical`（χ=3.0 で両相共存＆専門家率>0.6） |
| 3 | **共存組成が理論 binodal と定量一致**：χ=2.5 で 0.150/0.850（理論 0.145/0.855）、χ=3.0 で 0.070/0.930（理論 0.071/0.929）＝Flory-Huggins binodal とほぼ完全一致 | **measured** | `coexistence_matches_binodal`（相組成が binodal と 0.05 以内） |
| 4 | **入れていない随伴現象**：ドメイン波長（長さスケールを入れていない）が出る＝スピノーダル分解の特徴 | **measured** | `domain_wavelength`（χ>2 で ~11–18 grid） |
| 5 | **interpretive**：分業（専門化＋役割共存）は**場ネイティブな実現**＝スピノーダル分解を持つ。e030 のエージェントは一つの基層、場はもう一つ。KNOWN MATCH＝Cahn-Hilliard(1958)/Flory-Huggins(1942) 臨界点・binodal・粗大化 | **interpretive/analogy** | AUDIT §claim tier |
| 6 | **床**：「生殖体細胞/分業/多細胞性」は analogy。**同じ数学≠同じもの**——進化＝相分離とは主張せず、同じ定性事実がエージェントなしの場から出る、に限定。大 χ の near-pure binodal は grid/clip 分解能の床。(A) 忠実＝CH 法則は手入力。seed batch・κ で頑健 | **（床の明示）** | AUDIT 床1–4・`robustness.json`（κ=0.5/1/2 で binodal_err≤0.025） |

## e034 — 空間協力を「場」から（エージェントなし・双安定反応拡散フロント）  (STATUS: GREEN, Type A/faithful, H019)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **平均場（混合）は協力崩壊**：∇²を除いた双安定反応の ODE で、閾値下シード（u₀=0.2<a=0.40）が u→0（裏切り）に崩壊 | **measured** | `results/cooperation_front.json`：`wellmixed_seed_decays_below_threshold` |
| 2 | **空間フロントが侵入し、閾値で反転**：協力ドメインが a<1/2 でフロント侵入（c>0＝クラスタで生存）、a>1/2 で裏切りが侵入（c<0）＝誘惑が閾値超で構造でも失敗 | **measured** | `spatial_front_invades_below_maxwell_reverses_above` |
| 3 | **創発閾値 a_c=1/2（Maxwell 点）＋ Nagumo 速度一致**：フロント速度が a=0.5 で符号反転（入れていない）、速度が √(D/2)(1−2a) と定量一致（誤差<0.01） | **measured** | `front_speed_matches_nagumo_and_maxwell_at_half` |
| 4 | **interpretive**：空間構造が「有利な状態」の侵入を許し、生存は誘惑に依存（速度の符号反転）。e027 のエージェント三事実（混合崩壊/空間生存/条件閾値）が場から出る。KNOWN MATCH＝Nagumo/Schlögl 双安定フロント/Maxwell 点 a=1/2/速度 √(D/2)(1−2a) | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **床**：「協力/裏切り/大転移」は analogy。**同じ数学≠同じもの**——協力の進化＝双安定フロントとは主張せず、同じ三事実がエージェントなしの場から出る、に限定。協力の**安定性**であって完全な大転移でない。(A) 忠実＝RD 法則は手入力。D=0.5/1/2 で頑健（Maxwell 点 0.5 不変） | **（床の明示）** | AUDIT 床1–4・`robustness.json` |

## e035 — Red Queen を「場」から（エージェントなし・捕食者被食者 Hopf 分岐）  (STATUS: GREEN, Type A/faithful, H019)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **臨界富栄養化 K_c 未満で頭打ち**：Rosenzweig-MacArthur 場で K<K_c なら共存固定点が安定＝摂動が減衰し静的に頭打ち（e029 の静的寄生者プラトーの類似） | **measured** | `results/red_queen.json`：`enrichment_below_hopf_plateaus`（振幅<0.05） |
| 2 | **K_c 超で内生持続振動**：K>K_c で安定リミットサイクルが誕生（Hopf 分岐）＝外部強制なしの内生持続振動（場の Red Queen、振幅 0.14→0.76） | **measured** | `enrichment_above_hopf_sustains_oscillation`（振幅>0.3） |
| 3 | **発生点＝解析 Hopf 点**：測定発生点 K_c=0.706 が Jacobian trace=0 の解析 Hopf 点 K_c=0.7 と一致（誤差 0.006）。宿主・寄生者は位相ずれ振動（追いかけっこ） | **measured** | `oscillation_onset_matches_analytic_hopf`（誤差<0.1） |
| 4 | **interpretive**：内生的持続変化＝Hopf 分岐で生まれるリミットサイクル；静的系は頭打ちに緩和。KNOWN MATCH＝Rosenzweig-MacArthur/富栄養化のパラドクス（Hopf 不安定化）/捕食者被食者リミットサイクル | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **床**：「Red Queen/共進化/軍拡競争」は analogy。**同じ数学≠同じもの**——共進化＝Hopf とは主張せず、同じ事実がエージェントなしの場から出る、に限定。場が与えるのは内生**振動**で、文字通りの無限複雑性上昇ではない（frontier）。(A) 忠実＝個体群則は手入力。m・H0 で Hopf 点が動いても発生点が追従（0.7→0.62→0.82） | **（床の明示）** | AUDIT 床1–4・`robustness.json` |

## e036 — 適応を「場」から（エージェントなし・レプリケーター突然変異方程式）  (STATUS: GREEN, Type A/faithful, H019)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | **突然変異選択平衡＝閉形式**：replicator-mutator（Crow-Kimura）場で平衡分散が σ²=√(2D/k) と一致（D=0.05/0.1/0.2 で誤差<0.001） | **measured** | `results/adaptation.json`：`mutation_selection_balance_matches_theory` |
| 2 | **適応**：ピーク外初期分布（平均 3.0）が適応度ピーク（平均 0）へ登る＝場の適応（選択＝勾配上への移流） | **measured** | `population_climbs_to_fitness_peak` |
| 3 | **移動最適点の lag load**：共動座標系で追跡遅れ L=v/(kσ²)、速度に線形（lag/v 一定=2.236、誤差<0.003）＝e027 の追跡ラグを閉形式で | **measured** | `moving_optimum_lag_linear_and_matches_load` |
| 4 | **interpretive**：選択＝適応度勾配上への移流、突然変異＝拡散；適応・突然変異選択平衡・lag load は場の現象。KNOWN MATCH＝replicator-mutator/Crow-Kimura/平衡分散 √(2D/k)/lag load v/(kσ²) | **interpretive/analogy** | AUDIT §claim tier |
| 5 | **床**：「進化/適応/ニッチ」は analogy。**同じ数学≠同じもの**——進化＝RM 方程式とは主張せず、同じ事実がエージェントなしの場から出る、に限定。主張は小速度の線形 lag 領域のみ（臨界速度超で発散＝個体群喪失）。(A) 忠実＝場の法則は手入力。k・D で分散・遅れが理論曲線上（頑健） | **（床の明示）** | AUDIT 床1–4・`robustness.json` |
