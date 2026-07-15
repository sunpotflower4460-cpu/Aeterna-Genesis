# F0 プリレジストレーション — P06「球面相当の液滴が自分でトーラスへ穴を開けるか」

> **これは docs-only のプリレジストレーション（F0）です。** physics code・schema・CI・Room・既存結果・experiment
> 番号は**一切変更しません**。この F0 は「入れるもの／出ると主張するもの／既知理論／対照／失敗条件」を**実装前に
> 反証可能な形へ凍結**するためのものです。**F0 提示後は実装せず、うえきさんの承認を待って停止します。**
>
> provisional slug: `p06_sphere_to_torus`（実験番号は未採番）。規律：`AGENTS.md` / `ANTI_DRIFT` / `EVIDENCE_CONTRACT_V2`。

## 0. 中心問い
> **穴のない一つの3D液滴が、トポロジーを列挙されず、局所場の散逸だけで中心を穿ち、持続する solid torus
> （体積 b₁: 0→1）へ動的に変わるか。**

トーラスを**答えとして置かない**。球・トーラス・多重ハンドル・分裂・崩壊の**すべてを同じ条件で許し**、
どれが結果として残るかを Topology Instrument v1（b₀/b₁/b₂/χ/genus・マージ済み）で測る。

## 1. なぜ今 / e046 との関係
- e046（role V）は「**置いた**トポロジーが何本の保護巻きチャネル（b₁）を許すか」を検証した。
- 図6のサンドボックスは「固定した球面/トーラス候補への**粗いエネルギー交差**」（toy model・非動的、conflict
  register C07）。J* の不一致（0.67 vs 0.5）も未解決 → **repo に未登録**。
- P06 は「**穴が実際に開くか（E）**」を、置かず・育てて・測る。**e046 の V を E へ引き上げる自然な次段**であり、
  王冠 P12（穴×巻きの共創発）の**唯一の前提**。

## 2. 白（推奨：流体なし・変分 gradient flow を第一候補）
穴の生成を**自由エネルギー降下として監査**できるよう、最初は流体を入れず mass-conserving phase field + Q-tensor
gradient flow にする（ネマティック弾性異方性が穴形成の駆動）。

```
F[phi,Q] = F_interface[phi] + ∫ h(phi) f_LdG(Q) dV + F_elastic[Q; L_splay, L_bend] + F_anchoring[phi,Q]
∂_t phi = M ∇²(δF/δphi)                 (保存・Cahn–Hilliard 型)
∂_t Q   = -Γ P_ST(δF/δQ)                (P_ST = symmetric-traceless 射影)
```
- `phi`：液滴の相場（内 +1／外 −1）。`Q_ij`：3D ネマティック秩序テンソル。
- **diffuse interface** により、明示的な mesh surgery なしで pinch・hole creation を許す。
- 駆動：splay/bend 弾性異方性・界面張力・anchoring の競合（Koizumi et al. 2023 / Lin–Wang の機構）。
- 局所・等方・achiral に固定。穴・ハンドル・巻き・優先軸・genus 依存項は**置かない**。IC は対称 bump＋微小ノイズ。

（無次元化・係数・格子・dt は F0 承認後の実装段で凍結し、値を見てから動かさない。）

## 3. claim ladder（V0/S1/E2/R3 を分離）
| 段 | 幾何 / IC | 置くもの | 許される主張 | role |
|---|---|---|---|---|
| **V0** | 人工 ball / torus / double-torus | 形そのもの | Topology Instrument の b₀/b₁/b₂/genus 検証（**済：本測定器は合成対照 GREEN**） | V |
| **V1** | 固定形状上で full free energy | 形＋秩序 | sphere–torus 自由エネルギー交差を固定形状で再現 | V |
| **S1** | 穴のない単一液滴を置く・Q は対称+ノイズ | 身体（液滴）だけ | 置いた液滴が**穴を置かれずに** genus 転移した | S（body seeded / handle emergent） |
| **E2** | 一様 isotropic mixture + ノイズ | 平均組成と固定法則のみ | 相分離→単一液滴→handle 形成が**同じ固定白**から | E candidate |
| **R3** | E2 が seed/解像度/箱/dt/solver を越える | — | robust measured candidate | R |

**V0 を E と呼ばない。S1 を「0 から」と呼ばない。E2 の一例を robust と呼ばない。**

## 4. 測るもの（体積 b₁ と表面 genus を混同しない）
材料体積 Ω={φ>φc} について：solid ball (b₀,b₁,b₂)=(1,0,0)／solid torus (1,1,0)。**境界面の genus=1・表面 b₁=2 と、
体積 b₁=1 を区別**（conflict register C03）。Topology Instrument v1 で時系列追跡。

## 5. 事前登録ゲート
**存在＋転移**
- `b₀=1` を保ったまま `b₁: 0→1`（分裂 b₀≥2 や周期箱 wrap を torus と**誤認しない**）。
- hole radius が interface width より十分大きく、tail で**持続**。
- **total mass 保存**・**free energy 単調非増加**・topology event 時に数値発散なし。

**機構の因果**
- defect/elastic energy の低下が、増えた surface/bending cost を上回る時系列。
- **anisotropy/anchoring を切ると ball へ戻る**（機構が弾性異方性由来である対照）。

**相図（成功例だけを選ばない）**
- parameter sweep で ball / torus / split / multi-handle を**同じ判定器で分類**。torus だけを狙う探索にしない。
- 死ぬ・埋まる・分裂・崩壊・発散の領域も相図へ残す。

**収束**
- fixed-L resolution 収束・fixed-dx 有限箱監査を分離・threshold φc 感度・cubical χ と surface Euler の二重測定。

## 6. 最重要の反証（どれかなら P06 は不支持）
- 穴が **1–2 cell** だけ → 数値 pinch。
- 中心が **mass loss** で抜けた → 非保存 artifact。
- **periodic boundary を貫通した cylinder** → solid torus ではない。
- **torus IC しか安定しない** → V であって動的 handle genesis ではない。
- diffuse-interface 幅に onset が支配され、`ε/R→0` で消える → interface artifact（N）。

## 7. 探索と検証を分ける
Discovery で見つけた seed/閾値/パラメータを、そのまま確認証拠に使わない。窓を見つけたら判定規則を凍結し、
**未使用 seed と独立解像度**で Verification。

## 8. 成功時に言ってよい / いけない
- **S1**：「置かれた単一液滴が、穴を置かれずに genus 転移した」。
- **E2**：「液滴形成と handle 形成が同じ固定白から生じた」。
- measured は Betti・genus・energy・defect。「差が記憶を欲した」等は interpretive。**生命・意識・宇宙とは言わない。**

## 9. 実施順（各段で停止・報告）
- **F0**（本書・docs のみ）→ 承認待ちで停止。
- **F1**：V0/V1（測定器＋固定形状の自由エネルギー交差）→ テスト・小 artifact →停止レビュー。
- **F2**：S1（穴なし液滴が genus 転移）→ 存在＋転移ゲート・相図 →停止レビュー。
- **F3**：E2（一様場から）→ 複数 seed・収束・対照 →成否どちらも ledger 保存。

## 10. 一次文献
- Koizumi et al., Topological transformations of a nematic drop, arXiv:2307.00632
- Lin & Wang, Isotropic–Nematic Phase Transition and Liquid Crystal Droplets, arXiv:2009.11487

**文書の役割**: preregistration（F0）／**実装状態**: none／**採番**: none／**repo 変更**: docs 1 ファイルのみ。
**次の正しい行為**: うえきさん承認 → F1（V0/V1）から実装。
