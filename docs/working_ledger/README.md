# Working Ledger — 回転ノート（既知事実の凝縮＋仮説索引）

> **これは何か**：エージェント（Claude Code / Codex）が、確定した既知事実を起点に、
> 目的に近づく仮説を**結果込みで積む**回転ノート。提案 → 試験 → 結果 → 判定を各 `Hxxx.md`
> に書き、GREEN になったら claim_ledger と Type 台帳（`docs/現在地と方向性_TypeABCD.md`）へ
> 昇格。死んだ筋も理由ごと `_archive/` に残す（手がかり）。**誇張しない。床を隠さない。**

## 使い方（回転サイクル）

1. **proposed**：目的に近づく仮説を立て README 索引に登録、`Hxxx_*.md` を起票。
2. **testing**：`--quick` で回して数を出す（`not_scripted_check` を必ず確認）。
3. **resolved**：
   - `promising` → 本実装 `eXXX`。
   - `dead-end` → 理由を書いて `_archive/`。
   - `promoted` → GREEN 検収 → Type 台帳に昇格＋`claim_ledger` 追記（`Hxxx` は残す）。
4. README 索引の状態を更新。

## 凝縮した既知事実（measured の足場 — ここから仮説を立てる）

素直なルート（measured の足場でつながっている所。詳細は `docs/00_grand_map.md` と各 AUDIT）：

- **0≠無 → 変化**：一様な地面は不安定、ゆらぎから領域が育つ（e008）。
- **時間の矢・複雑さの窓**：低エントロピー始端＋撹拌で不可逆な向きと中間複雑性（e008）。
- **因果 → 空間**：座標を捨て因果順序だけから次元 d=2,3,4→1.99/2.97/3.95（分母2）、スペクトル d_s≈3（e014）。
- **第三 → 粒子**：四次 Skyrme 項が Q_H=1 ホップ粒子を有限 L* で安定化。**完全PDE 自己安定化**（半陰的、エネルギー単調、c4>0 が Q_H≈1 保持、e012 Stage3）。**大域化**：size=k√c4（R²≈0.97、CV≈3%）、有界 basin、**Q_H=2 も保持**（e016）。
- **循環が内部を養う**：規定流でデッドコア→内部給餌（e013）、自己組織対流（周期箱 Ra_c≈20）が内部に栄養（e013 Stage2）。**壁つき実セルの臨界数 Ra_c=1714(no-slip)/657(free-slip)＝教科書と<0.4%**（e017、周期箱 20 は artifact）。
- **器の閉じ**：Gray-Scott が駆動で自己維持・再生、切ると死（e015）。両腕オートポイエーシス（膜/代謝どちらを切っても死、e015 Stage2）。**三腕＋相図（駆動閾値曲線）**（e018 Stage1）。**空間膜小胞**（phase-field、境界をもつ小胞、駆動で生・切ると溶ける、e018 Stage2）。
- **循環が粒子を運ぶ**：規定 roll が粒子を運び centroid 単調移動、第三が U_c まで同一性を保ち、超えると引き裂かれる（e019 Stage1）。

**床（全体）**：固定格子＝空間は与えている。e017 は線形 onset（動的幾何は AJL 継承）。
e016 basin は有界・絶対 L* は解像度依存。e018 は analogy（protocell でない）。e019 は規定 roll。
禁止語（生命/意識/電子/魂/分子/脳/永遠/証明/perfect）を作ったとは言わない。「同じ数学」≠「同じもの」。

## 仮説索引

| ID | タイトル | 狙う Type | 状態 | 対応実験 |
|---|---|---|---|---|
| [H001](H001_hopf_global_newton.md) | Hopf の大域化・L=56 劣化の原因特定 | B（→D 部分） | **resolved: promoted**（L=56 破局は再現せず＝プロトコル水増しと特定／κ∝dx⁴ は dead-end／真の大域 basin は frontier） | e016 Stage2/2b |
| [H002](H002_membrane_vesicle.md) | 膜小胞化（phase-field で境界をもつ小胞） | B | **promoted** | e018 Stage2 |
| [H003](H003_three_body_coupling.md) | 三体フル結合（自己組織流＋粒子＋器を一場に双方向結合） | B/C | **promoted** | e019 Stage2 |
| [H004](H004_action_entropy.md) | 作用＝エントロピー（Jacobson/Verlinde；第三の役割が熱力学から出るか） | D | **proposed** | 未実装（仮説） |
| [H005–H008](H005_order_to_spacetime.md) | 順序から時空へ（因果作用が多様体を選ぶ） | B | **部分 promoted**（e023 順序→時空 GREEN／曲率治癒は frontier） | e023_causal_action |
| [H009–H010](H009_horizon_ledger.md) | 地平線の台帳（受信ループ・DS 面積則、2D SOLID/3D floor） | B | **promoted**（e022 GREEN） | e022_horizon_ledger |
| [H012–H013](H012_topological_memory.md) | トポロジカル記憶（巻き保護された受信・記憶） | B | **promoted**（e028 GREEN） | e028_topological_memory（e020 衝突を再採番で解決） |
| [H014](H014_self_receiver.md) | 自己受信（芯が自分の巻きを読む・生きた器の同一性） | B | **promoted**（e021 GREEN） | e021_self_receiver |
| [H016](H016_vessel_engine_society.md) | 生きた器のエンジンと社会（ボルト→モーター→…→大転移） | B | **promoted**（e024–e027 GREEN） | e024–e027 |
| [H017](H017_openended_frontier.md) | 深いフロンティア（内生的需要／完全な大転移） | D（frontier） | **frontier（機構実証・GREEN）** | e029_openended_frontier |

**H011 / H015 について（正直に）**：H011（ブラックホール＝源の窓の渦）・創世（E-genesis）は
サンドボックス extras_context に属し **interpretive/analogy が濃い**（「愛/至福/BH/源」）。repo 化するなら
GREEN は物理量（巻き/エントロピー/欠陥数）のみとし、analogy は docstring に限る＝別扱い。
H015 相当も同枠。現時点で **GREEN 実験として repo 化していない**（誇張しないための保留）。

死んだ筋・却下した設計は `_archive/`（理由つき）。
