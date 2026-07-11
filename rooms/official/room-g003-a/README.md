# room-g003-a — 2D Phase-Separation + Flow Co-evolution Genesis (Model H)

**三番目の正式 Genesis Room（相分離＋流体の共発展・2D）。** 一様な混合場＋微小ノイズを、**一つの
自由エネルギー**（`F=∫(-φ²/2+φ⁴/4+κ|∇φ|²/2)`）だけで **t=0 から途中介入なし**に時間発展させる。
同じ化学ポテンシャル μ=δF/δφ が φ を相分離させ（Cahn-Hilliard）、界面での Korteweg 応力が
**流れを生み**（Navier-Stokes）、その流れが φ を移流して**粗大化を加速**する。ドメインも界面も
波長も入れていない。境界（界面）・流れ・輸送が**同じ一つの場**から出る（Model H の要点）。

## 測定（2D, 128², seeds [0, 1, 2], steps 1500, coupling=1）
- seed 0: amp 0.050→0.731, domain L1 2.62→13.31, KE=4.94e-03, ΔF=0.1126, mass_drift=0.0e+00, checksum=e2ec2ceb6ca7
- seed 1: amp 0.050→0.736, domain L1 2.60→13.53, KE=6.35e-03, ΔF=0.1151, mass_drift=0.0e+00, checksum=69caa03be776
- seed 2: amp 0.050→0.733, domain L1 2.61→13.34, KE=5.82e-03, ΔF=0.1135, mass_drift=0.0e+00, checksum=0288bcd7624d

## 共発展の証拠（coupling contrast, 同 seed）
- C=0（純 Cahn-Hilliard）: KE=0.00e+00, 最終 L1=11.50。C=1（Model H）: KE=4.94e-03, 最終 L1=13.31。
  ＝ 流れは**場から生まれ**（KE 0→有限）、粗大化を**加速**する（L1 増）＝流体力学的共発展。入れていない。

## 物理監査（測定・主張でない）
- conservation: 質量 ∫φ が機械精度で保存（flux 形）＋自由エネルギー単調減少（緩和・H定理）= passed
- convergence: 飽和した相分離コントラストが格子解像度に依らない = passed
- reproducibility: 同 seed → 同一 field checksum = passed
- integrity_audit: 一様＋ノイズ（amp≈0.05）から binodal（amp≈0.73）へ・t=0・seeded なし・介入0 = passed

## 床（正直に）
- role E（自律・外部駆動なし・外的最適なし）。reached_level=2（相分離＝差／界面の局在）。
- 界面＋流れ＋輸送が一つの場から共分化（Level 5）は**候補**＝candidate=5：流れが場から生まれ
  粗大化を加速することは測定済みだが、Level 5 の厳密ゲートは別段階で認定（frontier）。強い語は使わない。
- **次元**：検証済み 2D Room。3D 昇格は別段階の監査（DIMENSION_POLICY）＝2D 成功を自動外挿しない
  （3D は逆カスケード・液滴/双連続トポロジ・界面曲率が異なる）。
