# F0 プリレジストレーション — P07「遅い履歴場は速い場の帰還 basin を変えるか」

> **docs-only プリレジストレーション（F0）。** physics code・schema・CI・Room・実験番号は**一切変更しない**。
> 「入れるもの／出ると主張するもの／既知理論／対照／失敗条件」を実装前に反証可能な形へ凍結する。
> **F0 提示のみ・実装せず承認待ちで停止。** provisional slug: `p07_field_slow_field_basin`（未採番）。
> 出自：Loop-Trinity 統合 LT-7（`docs/integration/loop_trinity_current_state_audit.md`）。判定は統合観測器
> LT-1（`gauge_aligned_distance`）・LT-2（`winding_reliability`）・LT-3（`plaquette_ledger`）で行う。

## 0. 中心問い（測定可能な一文）
> **同一の「損傷した」速い複素場に対し、物理的な遅い履歴場の初期状態・時間尺度・結合強度を変えると、
> 速い場が最終的に落ちる basin（トポロジカル状態）が変わるか。そしてそれは "関係した" のか、
> 対照でも同じ attractor へ落ちるだけなのか。**

「記憶が良い状態を回復させる」を成功条件にしない。測るのは **basin 選択が遅い場のパラメータで変わるか（両方向・
対照差つき）** であり、特定の「良い」状態への回帰ではない。生命・意識・記憶・関係の語を直接の成功条件にしない。

## 1. なぜこの白か（Loop の発見を Genesis の局所物理へ翻訳）
Loop-trinity は外付け EWMA バッファで「記憶が最終状態の basin を傾ける」候補を観測したが、それは *置いた記憶装置*
であり創発ではない（`99` 背景資料）。Genesis での正しい問いは **「場自身の遅い自由度／保存的な局所量が、速い場の
損傷後の帰還 basin を変えるか」**。EWMA を名称ごと移植せず、**hysteresis を持つ材料場**へ物理化する。
既存資産との接続：e028（穴を囲む巻きの保持・読み出し・保護＝*記憶そのものは作っていない*）の自然な次段、
e019（双方向 backreaction の自己制限）の機構分類、G001（未分化クエンチから 3D 渦線が育つ正式 Room）。

## 2. 白（fast/slow の方程式・局所・双方向）
**速い場** `ψ`（複素・秩序変数、巻き欠陥を持てる）。固定の局所法則（緩和型 complex Ginzburg–Landau、G001 系）:

```
∂_t ψ = [α0 + g·(s − s0)]·ψ − β·|ψ|²·ψ + (1 + i c)·∇²ψ + η(x,t)
```

**遅い場** `s`（実スカラー・材料剛性／局所 well 深さ。EWMA バッファではない）:

```
∂_t s = (1/τ_s)·[ h(|ψ|²) − s ] + D_s·∇²s        （τ_s ≫ 速い時間尺度、D_s 小、h は単調な局所関数）
```

- **双方向・局所結合**：`s` は局所 `|ψ|²` の履歴を緩やかに追跡し（過去が現在を作る）、`s` は `ψ` の局所 well 深さ
  `g·(s−s0)` を変える（現在が過去に導かれる）。中央 solver・oracle・生死分岐・目標項は無い。
- **結合強度 `g`** が主制御。`g=0` は **matched OFF 対照**（`s` は受動、basin は速い場のノイズが決める）。
- basin は「速い場が損傷後に落ちるトポロジカル状態」。最小 2 basin：巻き `W=1`（渦あり）vs `W=0`（渦なし）、
  3D では渦線が周期方向を貫く vs 貫かない。

（無次元化・係数・格子・dt・τ_s・D_s・g 範囲は **F1 校正段で凍結**し、値を見てから動かさない。Loop の GAMMA・
MEMORY_WEIGHT・0.05/0.35 等の数値は**輸入しない**。各モデルで無次元化して校正する。）

## 3. claim ladder（V/S/E を分離）
| 段 | 何を置くか | 許される主張 | role |
|---|---|---|---|
| **F1-V** | 既知 basin 状態（W0/W1/W2）＋観測器校正（LT-1/2/3 の合成対照は済） | basin を距離・巻き信頼度・plaquette で**曖昧さなく判別できる** | V |
| **S1** | 損傷 ψ を**置く**＋`s` の初期/τ_s/g を振る（`s` に目標巻きは置かない） | 遅い場のパラメータで basin 選択が変わり、**matched g=0 と有意に差**が出る | **S**（body/slow placed） |
| **S2** | S1 が seed/解像度/箱/dt を越え、2D→局所3D→全3D で残る | robust な slow-field basin-selection 候補 | S（robust） |
| **E候補** | `s` 自体が未分化クエンチから**自然発生**した場合に同じ効果 | 履歴場すら創発した basin 共選択 | E 候補（後段・本書では扱わない） |

**S1 を「記憶が回復させた」と呼ばない。matched control 差のある basin 選択の依存性のみを主張する。**

## 4. PUT IN / NOT PUT IN
**PUT IN（置く・明示）**：fast/slow の 2 場と上記局所法則、境界条件（周期）、損傷 ψ の作り方（basin 間で曖昧な
初期化）、`s0`（**滑らかな振幅バイアスのみ**）、環境としての `g`・`τ_s`・`D_s`、数値法、seed。
**NOT PUT IN（置かない）**：目標巻き・目標欠陥配置を `s` に置く／「回復コマンド」／runtime 介入／全体 oracle／
結果依存の停止／速度・向き／完成 basin との画像類似度目標。

## 5. 反証可能な予測
- **P1（両方向・対照差）**：中間 `g` で、`s0` を basin A 寄りにすると `P(final=A) > P(A | g=0)` が前登録マージンを
  超え、B 寄りでは対称に B。→ 遅い場が basin を**傾ける**。片方向の「良い状態への回帰」では**ない**。
- **P2（閾値帯）**：`g` に相図がある：低 `g`＝field-dominated（`s` 受動）、高 `g`＝slow-field-dominated（`s` が
  basin を固定）、中間に遷移帯。
- **P3（hysteresis）**：`g`（または `s0` バイアス）を上げ下げすると basin 選択曲線が異なる＝**履歴依存**（瞬時コピー
  では出ない）。

## 6. Null・代替説明（これらなら不支持）
- **common_attractor_relaxation**：`g=0` と `g>0` が `s0` に依らず同じ basin に落ちる → basin 選択なし（null）。
  matched OFF 対照が唯一の判別器（第2の監査文「関係したのか、同じ attractor へ崩れただけか」）。
- **memory_copy_collapse**：`s` が現在の `|ψ|²` にほぼ一致（LT-1 field↔slow aligned 距離が前登録床未満）
  → 過去でなく現在のコピー → 記憶ではない（第3の監査文「履歴を保持したのか、現在をコピーしただけか」）。
- **memory_detachment**：`s` が切断（距離が天井超）→ 影響なし。
- **energy_instability**：feedback がエネルギーを注入（Loop で観測）→ 総自由エネルギー監視、非有界なら失敗。
- 低振幅巻き曖昧（LT-2 で無効化）・初期化 seam・中央 slice のみ・2D 限定・有限サイズ・数値拡散・直接 target 符号化。

## 7. matched controls（必須）
| ID | 機構 | 初期 basin/損傷 | seed | 格子 | horizon | 目的 |
|---|---|---|---|---|---|---|
| ON | `g>0` | 同一 | 同一 | 同一 | 同一 | basin 選択の測定 |
| OFF | `g=0` | 同一 | 同一 | 同一 | 同一 | 「関係」か「同じ attractor」かの判別 |
| s0-A / s0-B | `g>0`, `s0` を A/B 寄り | 同一 | 同一 | 同一 | 同一 | 両方向バイアスの対称性 |
`mutual_*`・`restores_*`・`causes_*`・`memory_*rewrite*` は matched control（同一 layout/seed/horizon/dt/res）
の ON/OFF 差なしに使わない。

## 8. 測るもの（測定量・解釈でない）
- **basin 判定**：LT-1 aligned/invariant 距離で参照 basin 状態への近さ、LT-2 で巻きの**信頼度**（有効ライン上の
  dominant winding＋dominant_fraction、無効率）、LT-3 で orientation 別 plaquette 台帳。曖昧帯はフラグ。
- **選択依存**：`P(basin | s0, τ_s, g)` と **ON−OFF 差**、相図、hysteresis ループ。
- **記憶の質**：field↔slow の LT-1 距離（copy/detachment 帯・前登録）。
- **収支**：総自由エネルギー・`∫|ψ|²`・`∫s` のドリフト（energy/mass accounting）。
- **信頼度**：LT-2 無効ライン・LT-3 near-π・非有限・収束。

## 9. 前登録閾値（F1 で校正・Loop 値を輸入しない）
各閾値に：値/式・校正元・無次元正規化・感度解析・heuristic か否かを記す。
- basin 割当：aligned 距離が近い方へ割当、`|d_A − d_B|` が前登録マージン未満は「曖昧」。
- 選択有意：`P(A|s0=A) − P(A|OFF)` の下限（seed 数と二項誤差から前登録）。
- copy/detachment：field↔slow 距離帯（**F1 の既知状態で無次元化して校正**、Loop の 0.05/0.35 は使わない）。
- energy ドリフト上限（guardrail）。**すべて結果を見る前に固定。**

## 10. 分類行列（成功/失敗の一枚）
support（basin 選択が実在・対照分離・非コピー・両方向）／partial／null（common_attractor）／negative／
reliability_limited／numerical_failure／memory_copy_collapse／memory_detachment／energy_instability／
no_separation_from_control。

## 11. 次元ラダー（2D→3D）
2D screen（渦あり/なし）→ local 3D → coarse global 3D → full 3D（渦線が貫く/貫かない）。
**昇格条件**：各段で matched control 差を保って basin 選択が残る。**却下条件**：2D のみ／中央 slice のみ／
identity collapse／energy 非有界／対照と分離しない／強い seed 依存で解釈可能な帯がない。
（「3D で存在したのか、低次元の影を 3D と呼んだだけか」＝ `topology3d.three_d_authenticity` で監査。）

## 12. 7+8 監査（target encoding）
1. `s` に目標巻き/欠陥を**置かない**（`s0` は滑らかな振幅バイアスのみ）。
2. 成功ゲートは **差分**（`s0` を A/B に振ると basin が両方向へ動く AND OFF と差）で、「良い basin への回帰」ではない。
3. runtime 介入・結果依存の停止なし。
4. `g=0` OFF 対照で効果が消えること（第8監査：機構を切れば現象が消える）。
5. 因果閉包（§13）で `s` を prepared/environmental と明記し `claim_excludes` を付す。
6. 保存量を壊す補正を入れない（energy/mass 監視）。
7. 可視化は物理と分離（render honesty）。
8. 決定的（seed 固定）・成功 run だけ残さない・失敗も台帳へ。

## 13. 因果閉包クラス
`s`（遅い場）とその結合法則は **prepared_state / environmental_condition＝置いたもの → role S**。
`claim_excludes`：「遅い場の存在と結合は置いた。測るのは basin 選択の依存性のみ」。`s` 自体が未分化から自然発生
した場合にのみ後段で E 候補（本書では扱わない）。（`schemas/provenance.schema.json` に準拠。）

## 14. 停止規則（結果を見る前に固定）
seed 集合・horizon・`g`/`τ_s`/`s0` の掃引格子・basin 判定規則を実装前に凍結。結果依存で変えない。
**探索で見つけた窓は、未使用 seed と独立解像度で検証**（探索と検証を分ける）。

## 15. no-touch
`genesis/diagnostics/measures.py`・`rooms/official/**`・既存 `experiments/**`・`schemas/**`・`genesis/registry/**`・
`docs/TRUST_MAP.md`・`docs/WHITE_CEILINGS.md`・CI・app。本書は docs 1ファイルの追加のみ。

## 16. 実施順（各段で停止・報告）
- **F0**（本書・docs のみ）→ 承認待ちで停止。
- **F1（V）**：観測器校正（LT-1/2/3 は済）＋既知 basin W0/W1/W2 fixture で basin 判定器と copy/detachment 帯を校正。
- **S1（S・2D）**：損傷 ψ ＋ `s0`/τ_s/g 掃引＋matched OFF。P1–P3 と分類行列。
- **S2**：次元ラダーと robustness（複数 seed・解像度・全3D）。
- **E候補（後段）**：`s` を未分化から自然発生させて同効果が出るか。**本書では実装しない。**

## 17. 一次文献 / 接続
Kibble–Zurek（クエンチ欠陥）、Ginzburg–Landau 緩和動力学、hysteretic order parameters / slow variables、
BKT unbinding（e011）、e028（非局所巻き）、e019（双方向 backreaction）、G001（3D 渦線 Room）。Loop-trinity
の memory-biased basin selection・field↔memory 相互書換え候補（未検証・数値は輸入せず）。

**役割**: preregistration（F0）／**実装**: none／**採番**: none（frontier slug P07）／**repo 変更**: docs 1ファイル。
**次の正しい行為**: うえきさん承認 → F1（V：basin 判定器と copy/detachment 帯の校正）から実装。
