# TRUST_MAP — 実験の信頼地図（E / V / S / N / F / Q）

> **これは何か**：全実験を LAW.md §6 の役割で色分けした一枚地図。GPT 監査統合（第8監査）後の状態。
> **GREEN と呼べるのは E か V だけ**（7＋8 監査全通過）。S=設計回路、N=負の結果、F=frontier、Q=隔離（GREEN 剥奪）。
> 「同じ数学≠同じもの」。禁止語（生命/意識/魂/perfect/proved 等）を「作った」とは言わない——すべて analogy。
> 各実験の YAML ヘッダ（`role/claim_tier/target_encoded/…`）が一次情報。本表はその集約。

## 役割の定義（要約）
| 役割 | 意味 |
|---|---|
| **E** Emergence | 忠実な法則＋最小条件から現象が勝手に出た（7＋8監査全通過） |
| **V** Validation | 教科書・解析結果と数で一致（E に劣らない硬い検証） |
| **S** Synthesis | 設計回路・oracle を含む（創発と呼ばない・必ず明示） |
| **N** Negative | 負の結果（正直な失敗＝資産） |
| **F** Frontier | 未解決・機構実証のみ・障害の定量化 |
| **Q** Quarantine | GREEN 剥奪（主張とコード不一致 or target_encoded） |

## 集計（44 実験・複数役割の実験は主役割で計上）
- **E（創発）: 20** — e001, e002, e003, e008, e010, e011, e012, e014, e021, e023, e028, e033, e034, e036, e037, e038, e039, e040, e043, e044
- **V（検証）: 2** — e017（Ra_c=1714/657 教科書<0.4%）, e022（DS→π²/6, 2D）
- **S（設計回路）: 5** — e004, e013, e019, e025(autopoietic), e041(bottleneck 幾何)
- **N（負の結果）: 2** — e020（受動 phase-field は分裂しない）, e045（内生ニッチ構築は中立を超えない）
- **F（frontier）: 11** — e016, e024, e026, e027(evolution/openended/transition), e029, e030, e031, e032, e035
- **Q（隔離）: 0**

> **CI 第8監査ガード**：`tools/audit_roles.py` が全実験の YAML ヘッダを走査し、
> **target_encoded=true の実験が E/V（GREEN）を名乗っていないか**を機械チェック（CI で強制）。

> ※ e033/e034/e035/e036 は**創発かつ教科書一致**（E＋V グレード検証）。主役割は E とし V 級一致を注記。
> ※ e035 は Hopf 点が解析 Jacobian と一致（V 級）だが「頭打ち→内生振動」の創発が主眼＝E。

## 全実験（役割・理由・target_encoded）

| 実験 | 役割 | claim_tier | target_encoded | 一言 |
|---|---|---|---|---|
| e001 GPE 渦歳差 | **E** | measured | false | 点渦スケール則が場から出る |
| e002 GPE 二渦 | **E** | measured | false | 同符号共回転／逆符号並進 |
| e003 GPE 渦リング | **E** | measured | false | リングが自己伝播（トーラス） |
| e004 オクターブ/ホログラフィー | **S** | analogy | — | MERA/AdS の**設計構造**（忠実創発でない・自己申告 analogy） |
| e008 同時共創発 | **E** | measured/interpretive | false | 白＋GPE で物質/時間/空間が同時 |
| e010 KZ コヒーレンス長 | **E** | measured | **false（第8監査 CLEARED）** | spacing/ξ は独立 N・ξ の比較＝本物 |
| e011 欠陥の化学 | **E** | measured | false | v·d, ω·d² 選択則・有限T解離 |
| e012 Hopf 安定化（第三） | **E/V** | measured | false | 完全PDE 自己安定化・Derrick L*∝√c4（静的最小化＝V級） |
| e013 器＋中身 | **S/E** | measured | false | 規定流は設計(S)／自己組織 RB は創発(E) |
| e014 因果→次元 | **E** | measured | false | 順序のみから d=2,3,4→1.99/2.97/3.95 |
| e015 器の閉じ | **E** | measured | false | 駆動で自己維持・切ると死（M∧A 連言） |
| e016 Hopf basin | **F** | observed | **true（√c4 撤回）** | √c4 size 則は初期条件埋込＝撤回。Q_H=2 安定性は observed |
| e017 壁つき RB | **V** | established | false | Ra_c=1714/657＝教科書<0.4% |
| e018 膜小胞 | **E** | measured | false | phase-field 小胞・三腕死（連言） |
| e019 結合 | **S** | measured | false | 規定 roll は設計／U_c crossover |
| e020 小胞分裂 | **N** | measured(negative) | false | 受動 phase-field は**分裂しない**（負の結果） |
| e021 自己受信 | **E** | measured | false | 外場ゼロでリングが芯巻きを読む |
| e022 地平線台帳 | **V** | measured | false | DS 分子→π²/6（2D SOLID・3D は F） |
| e023 順序→時空 | **E** | measured | false | 因果順序から時間・有限次元・向き |
| e024 器のエンジン | **F** | measured | false | ラチェット整流は忠実だが「器モーター」は設計＝frontier |
| e025 complete（三器官） | measured | measured | false | 三器官の対比（faithful CGL） |
| e025 autopoietic | **S** | measured | **true** | winding→gain は**手配線の閉ループ回路**（oracle 明示） |
| e026 分裂会計 | **F** | measured | false | 巻き算術は測定／**分裂は静的会計・動的 pinch は frontier** |
| e027 evolution | **F** | measured | false | **エージェント模型**（場でない・床）／場版は e036 |
| e027 openended | **F** | measured | false | エージェント＋外部需要（前1/3 vs 後1/3 で判定） |
| e027 transition | **F** | measured | false | Nowak-May エージェント／場版は e034 |
| e028 トポロジカル記憶 | **E** | measured | false | 巻き保護受信・capacity>dof（read-miss を honest 化） |
| e029 coevolution | **F** | frontier | false | 内生需要で growth 到達可（二峰性は床・reachability ゲート） |
| e029 major_transition | **F** | frontier | false | 群再生産＋ボトルネックで協力救済（機構実証） |
| e030 分業 | **F** | frontier | false | エージェント群選択（凸性→分業）／場版は e033・判別ゲート化 |
| e031 因果作用の平滑化 | **F** | frontier | false | BD 揺らぎを定量化（治療でなく障害） |
| e032 3D DS 病理 | **F** | frontier | false | 面積則成立・係数ドリフト＝d>2 病理 |
| e033 分業＝場（CH） | **E** | measured | false | Cahn-Hilliard スピノーダル（χc=2・binodal＝V級） |
| e034 空間協力＝場（Nagumo） | **E** | measured | false | 双安定 RD フロント（Maxwell 点・Nagumo 速度＝V級） |
| e035 Red Queen＝場（Hopf） | **E** | measured | false | 捕食者被食者 Hopf（発生点＝解析 Hopf＝V級） |
| e036 適応＝場（RM） | **E** | measured | false | replicator-mutator（σ²=√(2D/k)・lag load＝V級） |
| e037 生態的 PGG（協力＝場） | **E** | measured | false | 生態的 payoff で協力が純 PDE で持続・古典は崩壊・機構は feedback（空間でない） |
| e038 連続形質進化（object tracking） | **E** | measured | false | GS 場＋tissue 形質で de novo 上昇（0.2→0.9、standing variation なし）・連続・追跡（**hybrid 床**） |
| e039 分化（morphogen＋Turing） | **E** | measured | false | French-flag で 3 順序ドメイン・Turing が一様から自己組織（std 0.02→1.19） |
| e040 協力＝RPS スパイラル | **E** | measured | false | C-D-L 循環 RD がスパイラル波で三者共存・well-mixed は崩壊（spiral は regime 依存・確率的 床） |
| e041 ボトルネック（幾何） | **S** | measured | false | ネック幅→創設者数→relatedness（狭→clonal・広→mixed）。**幾何サンプリング模型（連続場でない）** |
| e043 場の宇宙（統合） | **E** | measured | false | ONE GS 場で分裂+継承+変異+選択+適応+分化が同時＝一様シートから分化した適応ボディ（corr~0.8・**hybrid**） |
| e044 場の統一（協力） | **E** | measured | false | 協力が同じ場に参加：局所公共財が clonal 同類化で協力を持続（~0.6）・便益ゼロ対照は崩壊。**param 事前固定（掃引最良は不使用）** |
| e045 内生ニッチ（負） | **N** | measured(negative) | false | 内生的頻度依存は中立を超えず（excess≤0）・強罰は場を絶滅＝**忠実な負の結果**（open-endedness は frontier のまま） |

## 依存（food chain — 何の上に何が乗るか）
- **物理基盤（E/V）**: e001–e003（渦）・e008/e010/e011（KZ/欠陥）・e014/e023（因果→時空）・e017（RB）
  → この上にだけ重い結論を積む。
- **第三＝粒子（E/V／一部 F）**: e012（完全PDE・Derrick）→ e016（Q_H=2 は observed・**√c4 は F**）。
- **器の弧（E/S／一部 F）**: e013/e015/e018（器の閉じ）→ e019（結合）→ e024（エンジン, F）→ e025（complete／autopoietic=**S**）→ e026（分裂, **F**）。
- **進化（F）→ 場化（E）**: e027/e029/e030（エージェント=**F**）を e033/e034/e035/e036（**場=E**）が置換
  （H019：同じ事実を規則でなく場から。「同じ数学≠同じもの」）。
- **場化 wave2（H020）**: e037（生態的 PGG）・e038（連続形質進化）・e039（分化）・e040（RPS 協力）・e041（幾何ボトルネック）
  → capstone **e043**（ONE 場に 6 過程統合＝分化ボディ, E）・**e044**（協力が同じ場に参加＝局所公共財, E）。
  **e045**（内生ニッチ構築）は忠実に試して**負の結果 N**（中立を超えない・強罰は絶滅）＝open-endedness は frontier。
- **受信の弧（E/V）**: e021（自己受信）・e022（地平線, V/2D）・e028（記憶）。
- **frontier（F）**: e029–e032（オープンエンド/BD/3D DS）・e024・e026・e027・e016。

## 保留（正直に）
- **e004**（MERA/AdS）・**e027 openended の無限オープンエンド性**・**e016 の真の大域 L***・
  **e023 曲率治癒**・**e031/e032 の cure**は忠実な達成が **frontier**。「作った/解いた」と偽らない。
- YAML ヘッダは第8監査で再分類した実験（e010/e016/e025/e026/e027）に導入済み。残りは順次付与（本表が集約の一次地図）。
