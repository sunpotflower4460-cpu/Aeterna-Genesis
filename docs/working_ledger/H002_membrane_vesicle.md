# H002 — 膜小胞化（phase-field で境界をもつ小胞）

- **状態**: resolved (**promoted**)
- **起票者**: Claude Code / 2026-07-01
- **狙う Type**: B（床つき measured・頑健な創発観測）
- **依拠する既知事実**: e015/e018 Stage1（両腕・三腕オートポイエーシスは 0 次元動力学＝空間充填）。
  器は「開（駆動）かつ閉（自己維持）」の散逸構造（Type C）。膜は空間的境界のはずだが、
  これまで空間を持たなかった。→ phase-field なら**境界をもつ小胞**を出せるか。

## 仮説
Allen-Cahn 二重井戸＋駆動質量制御（Zwicker 系の能動ドロップレット最小版）で、
**空間充填でなく、薄い界面（膜）をもつ有界な小胞**が自発形成し、
**駆動で持続・駆動を切ると溶ける（死）**。漏れ↑→生存に必要な駆動↑（e018 Stage1 の
臨界駆動曲線の空間版）。

## 試験（方法）
`experiments/e018_membrane_vesicle/membrane_vesicle.py`。
`dphi/dt = eps^2 lap(phi) - (phi^3-phi) + mu(t)`、`mu(t)=s(target-<phi>)-leak(<phi>+1)/2`。
128²、6000 步。連結成分数（scipy.ndimage.label）・界面帯・境界接触・生存を測る。
駆動あり／s=0／(s,leak) スイープで生存閾値。

## 結果
- **駆動あり**：単一連結（n_components=1）の**有界**ドロップレット（inside_frac≈0.28、
  境界に接触しない）＋**薄い界面**（interface_band≈0.05＝膜）。空間充填でない。
- **駆動を切る（s=0）**：inside_frac→0、溶解（死）。
- **漏れ↑→駆動↑**：leak=0.0→最小生存 s=0.1、leak=0.4/0.8→0.2（生存判定=bounded_single_vesicle、閾値が漏れとともに上がる）。
- `not_scripted_check`：ドロップレット・界面・溶解はすべて場の力学から創発。形も死も入れていない。
- 床：粗視化連続 phase-field（脂質二重膜でない）。「膜/小胞/protocell/死」は analogy。固定周期格子。

## verdict
- [ ] promising → 実装 eXXX
- [ ] dead-end → _archive/
- [x] **promoted** → Type B に昇格、`claim_ledger`（e018 §）に追記。GREEN。

## H002+ 続き（e020 小胞分裂 → 負の結果, promoted）
`experiments/e020_vesicle_division/division.py`：分裂を直接コーディングせず、形（円/楕円/ダンベル/
フィラメント）＋緩めた質量制御で連結成分数を測定。
- **受動 phase-field は自発分裂しない（measured, 負）**：Allen-Cahn は合体（ダンベルのくびれが埋まる）、
  Cahn-Hilliard（保存・半陰的）はフィラメントが退縮＝全形が単一ドロップレットに緩和（全 run final=1）。
- **分裂には能動 turnover（Zwicker 能動ドロップレット）が要る**＝frontier（誘導しないので回していない）。
- `not_scripted_check`：分裂則を書かず ndimage.label で測定。誠実な負。→ claim_ledger e020 §。

## e021（小胞の中に粒子）＝別セッションへ
「小胞の中に粒子」（e016 ホップ粒子を e018 小胞に内包・共存）は、粒子の第三（c4）を小胞内でのみ
active にする空間結合が要る（∫c4(x)F² の変分勾配）。プロトタイプで機構は動くが**幾何依存が強い**
（小胞半径 > 粒子サイズが必要）＝丁寧な設定が要る 3D 実験。指示書の推奨どおり**独立セッション**で実装する。

## verdict
- [x] **promoted**（e018 小胞＋e020 分裂の負の結果、GREEN）。
- e021（小胞内粒子）は proposed（別セッション、3D・幾何依存）。

## メモ
「小胞を作った」でなく「境界をもつ有界ドロップレットが駆動下で創発・持続し、駆動を切ると
溶ける」を数で。分裂も「割れた」でなく「受動では割れない（能動が要る）」を数で。protocell を作ったとは言わない。
