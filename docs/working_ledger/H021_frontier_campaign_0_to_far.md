# H021 — 0から最も遠くに行くキャンペーン（自律・長期・append-only）

> **北極星の問い**：「一つの根源的な白（単一の局所法則・t=0 未分化 IC）から、中断なく、どこまで自然に育つか」
> （`docs/EMERGENCE_LEVELS.md` の L0→L8 ラダー）。**Level N の後に Level N+1 の機能を足さない**——より深く
> 行きたければ **始原条件を変えて Level 0 から再実行**する（同一原則をこのキャンペーン全体で厳守）。
> 本台帳は「積み上げを忘れず記録する」ための一次記録（G1〜G8 継続性ガバナンス、`docs/integration/research_continuity_audit.md`
> の是正策）。**このキャンペーンの全反復をここに追記する（削らない・上書きしない）。**

## 0. 出自
うえきさんの指示（2026-07-16）：「0から最も遠くに行くにはどうしたらいいかを自動で考え、試行し、様々に実験して、
情報収集もおこない、自由に長い時間やってよいので『0から充分に遠くに行けた』と思った場所からさらに探究を重ねて
どこまで行けるか自動で実践する。PRレビュー・マージ・次のステップへ進む判断もすべて任せる。」
→ `/loop`（自己ペース・間隔指定なし）で駆動。各反復で: 現状把握 → 次の一手を設計 → 実装＋監査 → テスト →
コミット/プッシュ → （節目で）PR作成・レビュー・マージ → 台帳追記 → 次の wakeup を予約。

## 1. 開始時点の誠実な現状（2026-07-16 時点、`docs/WHITE_CEILINGS.md` 要約）
- **単一の白が L0→L8 を通しで登った例はまだ無い。** 断片は別々の白から別々に出る:
  - L1〜L2：KZ クエンチ（e008/e010）、CGL 白（既知の対称性破れ＋巻き）。
  - L3：自己組織 Rayleigh–Bénard（e013）— ただし「渦の自然発生的な自走」という個体レベルの L3 は別問題。
  - L4：Swift–Hohenberg 局在個体（自己修復、単一 attractor）— しかし **並進 drift は m=1 Goldstone に阻まれ σ≈0**
    （M1/M2 角モードキャンペーン、`docs/ANGULAR_MODES.md`）。「単一自走個体」は **codimension≥2 のナイフエッジ**
    （単一に閉じ込め ∧ drift 閾値超 ∧ 分裂閾値の手前、を単純な少数場の白が同時に満たすのは一般に難しい）と
    正直にマップ済み。
  - L5：Model H 純粋共分化（相分離＋界面＋流れが一つの自由エネルギーから、role E）。
  - L7-partial：Gray-Scott 型分裂（遺伝は "置いた" バイスタブルタグ＝role S、真の遺伝可能な内部状態は未達）。
  - L8：最深 frontier（未証明）。
- **P07（本セッション直前の成果）**：遅い履歴場 `s` を置くと basin 記憶が出る（S1/S2, role S, robust）が、
  `s` 自体を未分化から育てても（e051）その過剰は **記憶(lag) ではなく結合再規格化**（`memory_copy_collapse`,
  role N）。「構造が育つ」≠「記憶が育つ」を分離した誠実な負の結果。
- **e002（既知理論の確認、role E/analogy）**：**置いた** ± 渦ペアは GPE 局所法則だけで並進する
  （同符号=共回転／逆符号=並進）。これは「渦動力学として並進が起きる」ことの確認であり、**「KZ クエンチが
  自然にそのような ± ペアを生成し、それが周囲の欠陥タングルの中で識別可能な並進として生き残るか」は別の、
  まだ測っていない問い**——これが本キャンペーン最初の一手（e052）の標的。

## 2. キャンペーンのやり方（プロトコル・全反復共通）
1. **育ったのか置いたのか**を毎回監査（IC に完成構造を置かない・第8監査 target_encoded）。
2. **関係したのか、同じ attractor へ崩れただけか**を matched control で判別（OFF/copy/shuffle 等、対象に応じ選ぶ）。
3. **Level N+1 の機能を追加しない** — 深く行きたい白は Level 0 から別 run（既存の run を後から改造して主張しない）。
4. 失敗も資産：honest negative（role N）・honest frontier（role F）を隠さず記録する。
5. 既存資産の重複を避ける：新しい実験を書く前に `docs/generated/evidence_index.md` と `docs/WHITE_CEILINGS.md` を確認。
6. 新規実験は `experiments/eNNN_*` + `experiment.yaml` + `AUDIT.md` + `tests/test_eNNN_*.py` + CI 行、
   継続性ガバナンス（`build_evidence_index.py --write`, `verify_result_integrity.py --update`）を都度再生成。
7. **no_touch 厳守**：`genesis/diagnostics/measures.py`・`rooms/official/**`・既存 experiments・schema・registry。
   新しい観測器は別ファイル（LT-1/2/3 と同じパターン：observers を足す、物理を足さない）。
8. 節目（1〜数実験がテスト・監査green）ごとに PR を作り、CI green を確認してからマージする（レビューはこの台帳と
   AUDIT.md が一次資料）。

## 3. 反復ログ（append-only・新しい行を下に追記）

### 反復1（2026-07-16）— e052 着手
- **状態**：`claude/emergence-frontier-campaign` ブランチで着手。
- **設計**：単一連続 t=0 run（一様+ノイズ IC・damped GPE KZ クエンチ、e010 と同じ法則・物理は再利用のみ）から
  自然発生する渦を `core.vortex.find_vortices` で毎フレーム検出し、新規観測器
  `genesis/diagnostics/level3_motion.py`（no_touch厳守・measures.py は変更しない）で frame-to-frame 追跡、
  ±符号の隣接ペアが持続的に並進するか（Level 3：`com_velocity ≠ 0 AND circulation ≠ 0`、直線性ゲート）を、
  (a) 箱全体重心ドリフト床、(b) ランダム誤対応ペアリング対照、の二つの matched control で判定。
- **次**：実装 → テスト → 監査 → コミット・プッシュ → 結果次第で台帳・WHITE_CEILINGS 更新。

### 反復1 結果（2026-07-16）— e052 完了：Level 3 frontier candidate
- **測定**：6 seed 中 **3 seed で Level 3 到達**（`level3_dipole_survives_in_budget`）。全 6 seed が Level 2
  には到達（KZ クエンチの L2 天井を再確認）。
- **物理的裏付け**：候補ペアの並進速度は点渦誘導速度 `v ~ 1/(2d)` と同じ桁・同じ 1/d 傾向（比 0.74〜1.16）
  ——level3_motion.py が本物の渦ペア力学を捉えている独立した証拠。
- **正直な限定**：jitter 床超過は約10〜12%とマージン薄く、seed 依存（3/6）。**role F（frontier candidate）
  ・confidence C** で記録——「Level 3 到達」を確定させない。e049(S1)→e050(S2) と同じ構造で、次はロバスト性
  検証（seed 数拡大・解像度・margin 感度）が必要。
- **観測器の途中バグ**：初期設計（ミスマッチペア shuffle null）は少数欠陥で自己汚染することを合成テストで
  発見・修正（母集団ジッター中央値＋解析的ランダムウォーク床の2床方式に変更）。`tests/test_level3_motion.py`
  に3シナリオ（真ダイポール／全体一様ドリフト／純ジッター）を固定。
- **育ったのか置いたのか**：渦もペアもIC に置いていない（`seeded_structure: false`）。運動は測定のみ、
  target_encoded=false。
- **成果物**：`genesis/diagnostics/level3_motion.py`（新規観測器・role V・measures.py 非touch）、
  `experiments/e052_dipole_self_propulsion/`（role F・confidence C）。
- **天井の更新**：単一連続 t=0 run の到達点は **L2（確定）〜L3（frontier candidate、seed依存）**。
  `docs/WHITE_CEILINGS.md` への正式な反映は、robustness follow-up の後（結果を見てからマップを書き換えない
  ——確定してから記録する）。
- **次の反復候補**：(a) e052 の robustness follow-up（seed拡大・解像度・margin 感度、S2 パターン）、
  (b) 別の quench 速度・法則クラスでの再現性、(c) L4（persistent individuality）方向への新しい白の探索。

### 反復2 結果（2026-07-16）— e053 完了：**天井が確定昇格（L2→L3, robust）**
- **測定**（3解像度×独立44 seed、e052 の物理・閾値を完全凍結・変更なし）：
  - L=64: 12中6 (50.0%, 95%CI [25.4%,74.6%])／L=96: 24中15 (62.5%, [42.7%,78.8%])／L=128: 8中6 (75.0%, [40.9%,92.8%])
  - **3解像度すべてで Level 3 到達、有限サイズで消えない**（むしろ僅かに増加傾向）。マージンも1.05〜1.70と
    e052反復1の際どい水準（〜1.10）より明確に健全。**判定 `robust_level3_candidate_confirmed`。**
- **role を F→E（secondary V）へ引き上げ**（e053 として新規記録。e052 自体は反復1の正直な記録として不変更・
  上書きしない——e049(S1)→e050(S2) と同じ「候補→robust」の積み上げパターン）。
- **天井の確定更新**：単一連続 t=0 run（damped GPE KZ クエンチ、e010と同一白）は **Level 3（自己形成 ±渦
  ペアの並進）に頑健に到達する（50〜75%の run、universal ではない）**。L2 は全 seed で確定。
- **【重要な整理】Level 4（単一個体の自走・codimension≥2 ナイフエッジ）とは別問題のまま**：本結果は
  「渦ペア（2体）の並進」＝Level 3。`docs/WHITE_CEILINGS.md` の「単一自走個体」議論（SH ソリトン m=1
  Goldstone 問題）は未解決のまま——混同しない、と e053/AUDIT.md に明記。
- **次の反復候補**：(a) 3D 昇格（e050 パターン）、(b) 別 τ_Q・γ での再現性、(c) **L4 方向**（単一個体自走）
  への新しい白の探索——これが北極星に対して残っている、より難しい問い。

<!-- 次の反復はここに追記 -->
