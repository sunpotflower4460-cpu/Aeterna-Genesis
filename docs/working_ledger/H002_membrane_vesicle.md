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

## メモ
「小胞を作った」でなく「境界をもつ有界ドロップレットが駆動下で創発・持続し、駆動を切ると
溶ける」を数で。protocell を作ったとは言わない。次：小胞の分裂（体積制御を緩める）、
三体結合（H003）で小胞の中に粒子（e019）。
