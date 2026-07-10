# room-g001-a — 3D Vortex-Line Genesis (TDGL quench)

**最初の正式 3D Genesis Room。** 一様に近い無秩序＋微小ノイズを **t=0 から途中介入なし**で
クエンチし、対称性破れ（Level 1）と位相巻き**渦線/渦ループ**（Level 2）が **入れずに**創発する
（Kibble-Zurek）。完成した渦線を初期条件に置いていない。

## 測定（full-3D, 64^3, 700 steps, seeds [0, 1, 2]）
- seed 0: reached_level=2, mean_amp_growth=200.5, defects=241, checksum=0f176ab4913b
- seed 1: reached_level=2, mean_amp_growth=202.4, defects=173, checksum=5145b3314af7
- seed 2: reached_level=2, mean_amp_growth=203.2, defects=117, checksum=c7445715fed2

## 物理監査（測定・主張でない）
- conservation: post-quench 自由エネルギー単調減少 = passed
- convergence: 到達 Level が 48/64/80^3 で一致 = passed
- reproducibility: 同 seed → 同一 field checksum = passed
- integrity_audit: t=0 から・目標構造 seeded なし・runtime 介入 0 = passed

## 床（正直に）
- role E（純粋創発・ラベル/外的最適なし）。2D は探索、本 Room は full-3D。
- 「渦線 Genesis」は測定量（巻き欠陥・秩序変数）で判定した名。強い語は使わない。
- Level 3+（渦線の運動・再結合の循環）は candidate＝frontier。
