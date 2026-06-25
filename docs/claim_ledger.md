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
| 4 | z 順序 b(z=1) > b(z=2)＝KZ b=(D−d)ν/(1+νz) と同じ向き（小 z→大 b） | **measured(順序)/interpretive(KZ)** | 整合プロトコルで NLKG(z=1) b≈0.5 > GPE(z=2) b≈0.24（`robustness.json`） |
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
| 3 | 動的：素(c4=0)はホップ粒子が崩壊（Q_H→0、e009 の縮みの動的確認） | **measured** | `results/hopfion_flow.json`：Q_H 0.99→~0、エネルギー単調減 |
| 4 | 動的：第三(c4>0)は崩壊に抵抗（最終 Q_H・整定エネルギーが c4 で単調増） | **measured** | 最終 Q_H が c4 とともに増加（単調） |
| 5 | 完全な自己安定化（Q_H≈1 を保つ持続）は本解像度で未達 | **frontier-observation** | 四次項の剛性で陽的 dt 極小・格子カットオフが L* と競合（細格子/陰的処理が要） |
| 6 | 絶対 E2,E4 は解像度(dx)依存／「粒子」は analogy（床） | **（床の明示）** | AUDIT.md 床1–4 |
