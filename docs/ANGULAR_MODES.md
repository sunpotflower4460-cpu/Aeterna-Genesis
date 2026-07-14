# ANGULAR_MODES — Frontier Campaign M1：動くモデルを探すな、どのモードが先に不安定化するかを測れ

> **これは何か**：自走個体フロンティア（[`WHITE_CEILINGS.md`](WHITE_CEILINGS.md)・#41）の攻め方を**根本から変える**。
> 「面白い動くパターンを探す」（存在窓が極薄で運任せ）のでなく、**静止した局在構造の角モード成長率の順序を測る**。
> ＝パターン探索から、**必要条件・禁止条件・普遍性を測る研究**へ。前提：[`ANTI_DRIFT.md`](ANTI_DRIFT.md)（**物理量を先に、意味ラベルは後**）。

## 転換

```
❌ これまで: 自走する「モデルを探す」（存在窓が極薄で運任せ）
⭕ これから: 静止スポットの「角モード固有値の順序を測る」
           drift(m=1) が 分裂(m=2) より先に不安定化するか
```

## 角モード（静止局在構造の摂動）

| モード | 摂動 | 不安定化＝ |
|---|---|---|
| **m=0** breathing | 半径の膨張（`r·∇u`） | 呼吸・脈動 |
| **m=1** translation | 剛体並進（`∂u/∂x, ∂u/∂y`） | **自走（drift）** |
| **m=2** split | 四重極変形（`x u_x − y u_y`） | **分裂**（＝複製の罠・単一個体でない） |

**成長率** `σ_m = ln(|a(T)|/|a(0)|)/T`（`a(t)=⟨u(t)−u*, φ_m⟩`・`u*` は静止固定点）。σ>0 不安定・~0 marginal・<0 安定。

## 自走のシグネチャ＝drift-before-split

**自走個体候補 ＝ σ(m=1) > 0 かつ m=1 が最初に（最も）不安定**（`classify_angular_spectrum` → `self_propelled_drift`）。
逆に **σ(m=2) が先** なら `splitting`（分裂・複製の罠＝単一個体でない）。何も不安定でなければ `static`。

## 測定された no-go（変分の白は自走しない）

**厳密な勾配流（変分の白）は自走できない**——主張でなく**測定**で確認：
- **Swift-Hohenberg（#40・変分の静止局在状態）** の角モードを測ると：
  - **m=1 translation σ ≈ 0（marginal・Goldstone）** → 決して正にならない → **自走しない**。
  - m=0 breathing σ ≈ −0.30、m=2 split σ ≈ −0.21（ともに安定）。
  - → `classify_angular_spectrum` = **`static`**。**変分 SH が静止するのは探索不足でなく法則構造。**
- ＝GPT/Claude の no-go を、この repo の白で**測定で再現**（`genesis/diagnostics/angular_modes.py`・`tests/test_angular_modes.py`）。

## no-go は white-specific に

「変分の白では m=1 ≤ 0」は**この白（と調査領域）での no-go**。**「宇宙の全パラメータで不可能」とは言わない。**
自走が出るには **m=1 が m=2 より先に正**になる白（**非変分／非相反**）が要る。

## V1（測定）：非変分 SH は split-before-drift（自走しない・機構つき）

勾配構造を壊せば m=1 が正になるか? を測定（`genesis/models/nonvariational_swift_hohenberg.py`：SH ＋
**等方・parity-even・非変分**項 `a|∇u|² + c u∇²u`。方向は課さない＝もし m=1 が不安定化すれば方向は自発的破れ）。

| 非変分係数 a | σ(m=1) translation | σ(m=2) split | 分類 |
|---|---|---|---|
| 0.0（変分） | ≈ 0（marginal） | −0.216 | static |
| 0.5 | ≈ 0（**変わらない**） | **−0.028（+0.19 上昇）** | static（split 側へ） |
| ≳1.0 | — | — | 発散（blow-up） |

**測定された機構（M1 proxy）**：非変分項は **split モード（m=2）を不安定側へ動かすが、translation（m=1）は
marginal のまま**。→ この調査断面では m=2 が先。

> ⚠️ **M2 による限定・修正（GPT M2 追記 §1〜§2・正直な後退）**：M1 の m=1 測定は**単一場の並進形 ∂x u へ直接
> 摂動する短時間 proxy** だった。だが並進対称 PDE の静止解では **∂x U\* は並進対称性由来の Goldstone モードで、
> drift 分岐の前後を問わず固有値は中立（λ≈0）**。したがって **「σ(m=1)≈0」は Goldstone が中立なだけ**で、drift の
> 有無を語らない。真の drift モードは **Goldstone とは別の非 Goldstone m=1 極性モード**である。
> **正確な結論**：**調査した非変分 SH の c=0 断面・測定範囲では m=2 の増幅が先に観測され、非 Goldstone な drift 分岐は
> 未確認（否定もできていない）**。**「SH 族全体に自走なし」「SH では必ず split が先」とは（結合固有値解と (a,c)
> 2次元面の確認前には）言わない。** 変分 SH の勾配流 no-go（構造的）と、特定の非変分 SH 断面の測定結果は分ける。
> → M2 の正式判定は結合固有値解 [`coupled_spectrum.py`](../genesis/diagnostics/coupled_spectrum.py) を source of truth とする
> （`angular_modes.py` は M1 proxy として履歴保持）。

## M2：結合固有値解（source of truth）

全場を束ねた**結合ヤコビアン**を matrix-free（step-map JVP）＋ Arnoldi で解き、**Goldstone を overlap で同定・除外**し、
**非 Goldstone m=1** が m=2 より先にゼロを横切るか（drift-before-split）で判定する（`classify_drift_before_split`）。
スカラー SH で検証済み：**m=1 近傍の2モードは並進 Goldstone（λ≈0・overlap≈1・x/y 縮退）＝正しく除外**、非 Goldstone m=1
は**なし**、m=2 は安定（λ≈−0.18）＝M1 の符号順序と整合。**真の drift 判定はこの結合固有値解による**（次段 M2-B/C/D）。

## 運動を置かない（ANTI_DRIFT・条件付き非変分 OK）

非変分/非相反は**条件付き OK**：等方的・外部方向なし・初期極性なし・速度指定なし・**drift 方向が seed ごとにランダム**
（自発的対称性の破れ）なら「運動を入力した」でなく「静止状態が運動へ**不安定化できる法則の性質**」。角モード測定は
まさにこの「不安定化できるか」を σ(m=1) で測る。

## 3軸を独立に（θ 走査が死んだ教訓）

θ 単独走査はスポットを殺す（局在・drift・崩壊を同時に動かすから）。**3軸を独立に**：
**A** 局在を保つ（双安定性・pinning 幅・非線形飽和）／**B** drift を動かす（非相反性・非変分性・時間遅れ）／
**C** 分裂・乱流化を抑える（抑制場の拡散長・高次飽和・資源制約）。角モード σ_m がこの3軸を分離して読む。

## 最大の成果

> **どの白で、なぜ drift が分裂より先に起きるのか。あるいはなぜ必ず分裂が先か。** を**説明**できること。
> 届かなくてよい——**no-go を測定で示すのも立派な成果**（原則5：避けず挑む・答えは置かない）。
