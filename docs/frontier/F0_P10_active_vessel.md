# F0 プリレジストレーション — P10「化学的に能動な器」（選択的境界 ⇄ 内部反応の維持ループ）

> **docs-only プリレジストレーション（F0）。** physics code・schema・CI・Room・実験番号は**一切変更しない**。
> 「入れるもの／出ると主張するもの／既知理論／対照／失敗条件」を実装前に反証可能な形へ凍結する。
> **F0 提示のみ・実装せず承認待ちで停止。** provisional slug: `p10_active_vessel`（未採番）。
>
> **本白は縦の創発契約（`docs/VERTICAL_EMERGENCE_CONTRACT.md`）の下流キャンペーン §5「3D Chemically
> Active Vessel」の F0 である。** P01（自走・motility）とは**別の能力**を狙う——P01 は「個体が動くか」、
> P10 は「**境界が内部反応を維持し、内部反応が境界を再生する**維持ループが、下位化学から生まれるか」。
> 縦の軸で見た標的ゲートは **I→II→III**（契約 §2）。特に **Gate III（下位実現された backreaction）**を
> Aeterna で初めて本格的に問う白——器という上位変数が内部化学という下位を変え、下位が器を保つ循環が、
> **別の外力でなく下位の局所相互作用として実現**されているかを matched control で判定する。

## 0. 中心問い
> **局所化学（複数種・化学量論・fuel/waste）と相分離から、選択的な境界が自発形成され、その境界が内部
> 反応を集中・維持し、内部反応がその境界を再生する——という維持ループが、器という上位変数を手で置かず、
> 下位の局所相互作用だけで閉じるか。** 膜を置かない・区画を置かない・内外差を置かない。

一様混合＋等方ノイズ → 相分離で液滴（器候補）→ 界面が特定化学種にだけ透過的（選択透過が界面物理から創発）
→ fuel が内部へ選択的に入り反応 → 反応生成物が界面を再生・維持 → fuel を止めると崩壊、再開で回復。
**activity を途中で on にせず、境界も透過選択性も維持ループも符号化しない。**

## 1. なぜこの白か（P01・G003 との差分と、Gate III の初挑戦）
- **G003（Model H, validated-2D candidate）**：相分離＋界面＋流れの共分化は既に role E で確立。しかし
  **単一の受動液滴**であり、化学量論・fuel/waste・選択透過・維持ループは無い（Gate I/II 止まり、Gate III 無し）。
- **P01（active droplet, F0 済）**：界面化学で液滴が**動く**（motility）。器の**維持**は問わない。
- **P10（本白）**：動きではなく**器としての自己維持**を問う。GPT 外部監査（2026-07-16）が指摘した
  「膜モデル＋代謝モデル＋複製モデルをつなぐのでなく、**同じ局所化学から内外差・境界・透過選択性・反応
  集中・エネルギー消費・成長・破損回復が同時に出る**白を探す」に対応する。
- **縦の軸での位置**：契約 §3 の橋監査で「B3（下位実現された backreaction）は一度も無い」と記録した。
  P10 はその B3 を初めて狙う——器（上位）→内部化学（下位）の下向き作用が微視物理として実現されているか。

## 2. 白（連続式・第一候補：保存化学 + Model H 相分離 + 低Re流体）
```
# 器候補：保存相場 φ（Model H, G003 再利用・no_touch）
F[phi] = ∫[ a/4 (phi^2-1)^2 + kappa/2 |grad phi|^2 ] dV ;  mu_phi = a phi(phi^2-1) - kappa lap phi
∂_t phi + u·grad phi = M_phi lap mu_phi
# 化学：fuel f, 中間体 m, waste w（化学量論 f -> m -> w、質量/元素保存を厳密に監査）
∂_t f + u·grad f = div( D_f(phi) grad f ) + J_f(x,t) - k1 R(phi) f
∂_t m + u·grad m = div( D_m(phi) grad m ) + k1 R(phi) f - k2 m
∂_t w + u·grad w = div( D_w(phi) grad w ) + k2 m - k_out w
# 流体（低Re Stokes・発散形応力・総内部力=0 を運動量収支で監査）
0 = -grad p + eta lap u + div( sigma_K[phi] ) ; div u = 0
```
- **選択透過は "置かない"**：`D_f(phi), D_m(phi), D_w(phi)` は φ の**滑らかな関数**（同一の局所法則）。
  内外で拡散係数が違うのは、φ の相分離が作った局所環境の帰結——**内外差・透過選択性を IC に置かず、
  φ から創発させる**。手で「膜の中だけ透過」と書かない（それは Gate I FAIL＝B0）。
- **維持ループの候補機構**：反応生成物 `m` が界面張力または κ を弱く変調（`gamma(m)` or `kappa(m)`）→
  界面が反応集中領域で安定化 → 反応が界面近傍に集中 → 界面が保たれる。**この結合は下位の局所項として
  書き、器という大域ラベルを参照しない。**
- **fuel 供給 `J_f`**：空間一様な流入（`thermodynamic_ledger` の `matter_in`）。器の位置を参照しない
  （器へ狙い撃ちする流入は Gate I FAIL）。
- **FFT の honesty（契約・C）**：Stokes 射影に FFT を使う版は「global spectral validator」と明記し
  「中央計算なし」とは呼ばない。将来 local stencil で独立検証（P01 と同じ規律）。

## 3. claim ladder（各段が縦の契約のどの Bridge-Level を狙うか）
| 段 | IC / 幾何 | 置くもの | 主張 | role | 標的 Bridge-Level |
|---|---|---|---|---|---|
| **V0** | 固定球界面・解析 D(phi) | 界面＋反応 | 選択透過フラックスの既知則（界面での化学種分配）を再現 | V | Gate I 検証 |
| **S1** | 球状 φ bump・f=m=w=0・u=0 | 器だけ seeded | 内外差・反応集中・維持ループが創発（器は seeded・維持は emerged） | S/E split | Gate II 候補 |
| **E2** | 一様混合 φ̄+ノイズ・化学 0・u=0 | 平均組成＋固定法則 | 器・選択境界・維持ループが同じ固定白から | E candidate | Gate II |
| **E3** | E2 ＋ fuel 停止/再開プロトコル | 同上＋`J_f` の時間プログラム | fuel 停止で崩壊・再開で回復し、**器→内部反応の下向き作用が下位局所項だけで実現**（matched control） | E candidate | **Gate III** |

## 4. 測定器の必要精密化（新規観測器・no_touch・measures.py 非改変）
- **選択透過の定量**：界面を横切る各化学種フラックス `⟨D(phi) ∂_n f⟩` を種別・内外別に測定。
  「内外で透過率が違う」を数値で（人が「膜」とラベルせず）。
- **維持ループの因果**：反応集中度（界面近傍の `k1 R(phi) f` 積分）と界面安定度（界面幅・|∇φ| の分散）の
  相互相関・時間遅れ。上位変数 U=「界面の存在/位置」を φ から**導出**（Gate I）。
- **`thermodynamic_ledger`（契約 §6）**：`energy_in/useful_work/dissipation/chemical_free_energy_change`・
  `matter_in/matter_out/waste_out/entropy_production` を毎フレーム収支。**入力を止めると崩壊/再開で回復/
  内部が入力を境界維持へ変換しているか**を測る。
- **Gate III matched control（契約 §2 III）**：`m→界面`の結合経路だけを、その**時間・空間平均値に固定**して
  「反応生成物の揺らぎを通じた界面変調」を除去し、**下位化学の周辺分布・素の反応則・拡散は不変に保つ**。
  この対照下で維持ループ（崩壊後回復）が**消え**、通常 run では**残る**ときに限り、器→内部反応の下向き
  作用が下位経由と言える。無差別に化学をスクランブルする対照は使わない（U 経由の切り分けにならない）。

## 5. 事前登録ゲート（決定的閾値・契約 §2 と整合・結果を見てから緩めない）
- **器の存在（Gate I 前提）**：連結成分=1・体積 CV<2%・非 domain-filling・界面 4–6 cell・φ から U 導出。
- **選択透過の創発（Gate I）**：内外の実効透過率比 ≥2（種別）が φ のみから生じ、IC に透過ラベル無し。
- **維持ループの有効法則（Gate II・4基準）**：契約 §2 のデフォルト閾値を継承——予測残差 `R_pred<0.10`／
  独立 seed ≥5・係数 CV<0.15／閉性残差<0.20／粗視化 ≥3 スケール（線長比 ≥4×）で関数形不変。
- **下向き実現（Gate III）**：fuel 停止で `thermodynamic_ledger` の自由エネルギー流入が断たれ器が崩壊、
  再開で回復。かつ §4 の matched control 下で回復が消える・通常 run で残る（`U` は下位を通じてのみ因果）。
- **収束/artifact 拒否**：48³→64³→96³（fixed-L）と fixed-dx 有限箱を分離・`ε/R→0` で維持ループ onset 収束。
  diffuse-interface Marangoni/透過 artifact が界面幅 ε と共移動し `ε/R→0` で消えるなら `N: interface artifact`。

## 6. 対照（同 solver・同 seed）
`k1=0`（反応なし）／`m→界面`結合 off（維持ループの下向き経路を切る＝Gate III の主対照）／`J_f=0`
（fuel なし・崩壊のみ）／`D(phi)=const`（選択透過を殺す）／advection off／固定球 analytic validator。

## 7. 成功時に言ってよい / いけない（契約 §4 禁止主張を継承）
- V0 のみ＝界面での化学種分配の既知則再現（**器を作った、とは言わない**）。
- S1＝seeded 器で選択透過・維持ループが自発（**器自体が白から生まれた、とは言わない**）。
- E2＝一様場から生じた器が固定法則のまま選択境界・維持ループを作る（**細胞・代謝・生命、とは言わない**）。
- E3（Gate III PASS）＝器→内部反応の下向き作用が下位局所項だけで実現された **downward-realized bridge**
  （**生命・自己複製・意志・目的、とは言わない**——契約 §0 の用語規律：これは「生命の器候補」方向）。
- 最強の適切表現：**3D field-generated self-maintaining chemically-selective vessel candidate（B3 候補）**。

## 8. 実施順（各段停止・契約と F0 の停止規律を継承）
**前提（prereq・Codex 監査 2026-07-16）**：本白は **3D** の器を問うため、G003（現 validated-2D candidate）の
**3D 昇格または dimension-transfer 監査**（`DIMENSION_POLICY.md`・`EVIDENCE_CONTRACT_V2` §1.3）を先に通す。
2D Model H の成功を 3D 橋の十分条件として扱わない。

F0（本書・承認待ち停止）→ [prereq: G003 3D 昇格/dimension-transfer] → F1 V0（固定球 validator＋選択透過測定）→
F2 S1（器 seeded・選択透過・維持ループの Gate II 候補）→ F3 E2（一様場・複数 seed・収束・対照）→
F4 E3（fuel 停止/再開＋Gate III matched control）。失敗も相図/ledger へ保存。

## 9. 分岐（P10 失敗時・別 ID/別 F0）
P10-B 二種保存化学のみ（流体なし・反応拡散の維持パターン）／P10-C 電荷/pH 勾配で選択透過（Donnan 様）／
外部監査提案の Embodied Adaptive（P10 の維持境界に感覚-運動ループを足す・**別白・Gate I 継承必須**）。
**同じ白へ項を足し続けて同一 ID の成功にしない。**

## 10. 一次文献（プロトセル・能動液滴・維持）
Zwicker et al. active droplets (Nat. Phys. 2017)／Weber–Zwicker–Jülicher–Lee physics of biomolecular
condensates (2018)／Michelin autophoretic reviews／Model H (Hohenberg–Halperin 1977)／
非平衡 self-organization と継続エネルギー供給（散逸構造）。実装時に各主張へ対応付けて確定引用する。

**役割**: preregistration（F0）／**実装**: none／**採番**: none／**repo 変更**: docs 1ファイル。
**次の正しい行為**: うえきさん承認 → prereq（G003 3D）確認 → F1（V0）から実装。
