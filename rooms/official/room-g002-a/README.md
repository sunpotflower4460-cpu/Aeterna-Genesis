# room-g002-a — 2D Spontaneous Convection Genesis (walled Rayleigh-Bénard)

**二番目の正式 Genesis Room（自発対流・2D）。** 静止した流体＋微小ノイズを、**上下の壁**と
**固定した温度差**（環境）だけの下で **t=0 から途中介入なし**に時間発展させる。対流セルも
その波長も入れていない。臨界 Rayleigh 数 Ra_c = 27π⁴/4 ≈ 657.5 を境に、下では熱伝導のまま
（Nu≈1）、上では**自発的に**並進対称性が破れて対流が立ち上がる（Nu>1）。順時間の分岐であって、
置いた模様ではない。

## 測定（2D, 48×48, seeds [0, 1, 2], Ra*=1000）
- seed 0: Nu_flux=1.7543, Nu_diss=1.6907, KE=2.475e+01, convecting=True, checksum=3da5aa8eafd2
- seed 1: Nu_flux=1.7543, Nu_diss=1.6907, KE=2.475e+01, convecting=True, checksum=6b8068b2720e
- seed 2: Nu_flux=1.7543, Nu_diss=1.6907, KE=2.475e+01, convecting=True, checksum=75b4c490cfa7

## 物理監査（測定・主張でない）
- integrity_audit（onset control）: 亜臨界 Ra=300 → Nu=1.0000（伝導）／超臨界 Ra=1000 → Nu=1.7543（対流）
  ＝ 創発は始原条件に入れていない（seeded でない）ことの証拠。
- conservation: 独立な二つの Nu 推定（対流フラックス vs 熱散逸）が定常で一致 = passed
- convergence: 定常 Nu が格子解像度に依らない = passed
- reproducibility: 同 seed → 同一 field checksum = passed

## 床（正直に）
- role E（純粋創発・ラベル/外的最適なし）。外部**駆動**（熱）は環境条件として許容、外部**目標**は無い。
- reached_level=1（差・模様：静止から対流パターンへの対称性破れ、Ra_c で判定）。
- 循環（Level 3 の物理）は測定済みだが、定常セルはパターンとして並進しないため Level 3 gate は
  主張しない＝candidate=3（frontier）。強い語は使わない。
- **次元**：これは**検証済み 2D** Room。3D 昇格は別段階の監査（DIMENSION_POLICY）＝2D 成功を
  自動外挿しない。3D ソルバ（`genesis/models/boussinesq_rb_3d.py`, **experimental**）は 3/2 ゼロ詰め
  de-aliasing を実装済み・変換は厳密（roundtrip ~1e-14）・**亜臨界は Nu→1 で有界**と検証済み。ただし
  **超臨界**対流は入手可能な解像度（N≤24）で飽和近傍に崩れる＝aliasing でも dt でもなく**解像度不足**
  （同一物理時刻で崩れ・dt 非依存）。有界・格子収束の 3D DNS には N≳32 とより頑健な時間積分が要る
  ＝計算資源の段階。frontier として再現可能に保存（正式 Room には未接続）。
- 剛体壁（no-slip）・高 Ra の時間依存対流も別 Room（始原条件を変えて再実行）。
