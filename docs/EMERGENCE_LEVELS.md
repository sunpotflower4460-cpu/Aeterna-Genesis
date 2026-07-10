# EMERGENCE_LEVELS.md — 創発の深さと測定指標

**Level は優劣ではなく、一つの run が時刻 0 からどこまで中断なく自然に育ったかの到達深度。** 画像の印象で決めない——**測定量**で判定する。各 Level は「入れてはいけないもの（seeded 禁止）」と「測る量」を持つ。

**大原則：** ある Level を主張するには、その構造が**始原条件に入っておらず**（第8監査）、**時間発展の結果として現れた**ことを測定で示す。**Level N の後に Level N+1 の機能を追加してはならない**——より深くしたいなら始原条件を変えて Level 0 から再実行。

---

## Level 0：未分化な始原状態

個体・境界・器官・役割がまだ存在しない。一様または対称な場＋微小ゆらぎ。

- **入れてよい**：場の種類、局所法則、保存則、散逸則、初期分布、微小ノイズ、境界条件、外部流入、次元、定数、seed。
- **測る**：空間分散 ≈ ノイズ床、構造因子 S(k) が平坦、局在構造なし。

---

## Level 1：差・不安定性・模様

一様/未分化から、差・相分離・模様・ドメインが自然に現れる。

- **seeded 禁止**：完成した模様・ドメイン配置・特定波長の初期パターン。
- **測る（測定量）**：
  - 空間分散がノイズ床を超えて**増大**（成長率 λ）。
  - 構造因子 S(k) に**ピーク**（特徴波長 k*）が立つ。
  - 相関長 ξ が有限/成長。
  - 対称性破れの秩序変数が非ゼロ。
- **判定**：`var_growth > 0 AND S(k)_peak_emerges AND xi_finite`。一様解からの距離が増える。

---

## Level 2：局在構造・欠陥・渦

差が局在し、欠陥・渦・結び目・塊・殻になる。

- **seeded 禁止**：完成した渦線/欠陥/殻を初期条件に置く。
- **測る**：
  - 局在構造の数（閾値超の連結成分数）。
  - 欠陥数（**巻き数**・位相特異点。単なる低密度でなく位相巻きで検出）。
  - トポロジカル量、局在度（participation ratio）、構造寿命。
- **判定**：`localized_components > 0 AND winding_defects_detected AND persistence > τ_min`。密度欠損**と**位相巻きの同時検出（片方だけは弱い）。

---

## Level 3：自発運動・相互作用・循環

構造が動き、相互作用し、回転・輸送・循環を示す。

- **seeded 禁止**：初期速度場・回転方向・循環を直接与える（外部流入の勾配は環境条件として可、ただし明示）。
- **測る**：
  - 構造の重心運動（速度）、速度相関。
  - **循環積分** ∮v·dl、渦度、物質フラックス。
  - 相互作用則（距離依存の速度/角速度）、持続時間。
- **判定**：`com_velocity ≠ 0 AND circulation ≠ 0 AND flux > 0`（自発運動が入力でなく創発）。

---

## Level 4：持続する全体性・個体性候補

周囲と区別できるまとまりが、変形しながらも一定時間持続する。

- **seeded 禁止**：完成した境界・膜・内外指定を置く。
- **測る**：
  - 周囲から区別される領域（内外差、境界）。
  - **形が変わっても継続する追跡 ID**（変形を通じた同一性）。
  - 境界寿命、摂動後の回復、物質/エネルギー収支。
  - **系サイズに依存しない持続性**（有限サイズ効果でないこと）。
- **判定**：`tracked_id_lifetime > τ AND inside_outside_contrast > θ AND recovers_after_perturbation`。
- ⚠️ **ここで止めて、Level 5 の機能を追加してはならない。** より深くしたいなら始原条件を変えて再実行。

---

## Level 5：機能の共分化

境界・流れ・変換・輸送などが**別部品としてではなく、同じ全体場の異なる働きとして同時に**現れる。

- **seeded 禁止**：各機能を別モジュールとして置く／組織ごとのラベルや外的最適で機能を割り当てる。
- **測る**：
  - **複数の物理過程の同時発生**（境界＋流れ＋輸送＋変換が一つの場から）。
  - それらの**相互依存**（一つの働きが他を可能にする）。
- **純粋 vs 足場付き（重要な区別）**：
  - **純粋な Level 5（E）**：一つの連続場から、**ラベルも外的最適もなしに**共分化（例：Model H で相分離＋界面＋流れ＋変形が同じ自由エネルギー/化学ポテンシャル/応力から）。
  - **足場付き（S＝合成）**：組織ごとのラベル・外的モルフォゲン・手配線の結合で機能を割り当てたもの。**探索/合成として価値はあるが、純粋 Level 5 とは呼ばない**。役割 S で記録。
- **判定**：`co_occurring_processes ≥ 2 AND mutual_dependence AND no_per_object_labels AND no_external_optimum`（純粋の場合）。

---

## Level 6：自己維持閉環

創発した関係同士が互いを成立させ、全体が全体を維持する。

- **seeded 禁止**：中心制御装置・外部 oracle・巻き→gain のような手配線スイッチ。
- **測る**：
  - 創発した関係を同定し、**相互依存**を示す（一つを壊すと全体が崩れる＝load-bearing 閉環）。
  - **外部 oracle でないこと**（場自身の局所法則で閉じている）。
- **判定**：`emergent_relations_identified AND breaking_one_collapses_whole AND no_external_oracle`。
- **注意**：既存の e025 型（外部で巻きを測り gain へ掛ける）は role=S。純粋 Level 6 は場自身の局所 flux/化学種/gauge が自然に代謝へ影響する形。

---

## Level 7：成長・分裂・継承

全体が成長し、自発的に分かれ、内部状態を次へ渡す。

- **seeded 禁止**：分裂位置・分裂時刻・分裂を開始する外部命令。
- **測る**：
  - **入力していない分裂イベント**（位置も時刻も与えていない）。
  - 状態の継承（次の個体が前の内部状態を持つ）。
  - トポロジカル/保存則会計（複製 ≠ 単純コピー）。
- **判定**：`division_not_seeded AND state_inherited AND accounting_consistent`。

---

## Level 8：選択・開かれた発展

複数の系統が生まれ、環境との関係によって差が継続的に発展する。

- **seeded 禁止**：適応度目標・生存目標・特定形状への収束項。
- **測る**：
  - 系統分岐、選択（環境との関係で差が広がる）。
  - **開かれた新規性**（複雑性が上がり続ける／新しい形質次元が生まれる＝最深 frontier）。
- **判定**：`lineage_divergence AND selection_from_environment AND (open_ended_novelty ← frontier)`。
- **注意**：無界拡散を「多様性」と誤判定しない——**有界空間＋中立対照**で選択維持を担保（`docs/PHYSICS_INTEGRITY.md` 第8監査）。

---

## Room への記録

各 Room は到達 Level とその根拠（測定量）を保存：
```yaml
emergence:
  reached_level: 3
  candidate_level: 4          # 次を狙える兆候
  uninterrupted_from_zero: true
  detected:
    difference: true          # Level 1
    localization: true        # Level 2
    spontaneous_motion: true  # Level 3
    circulation: true
    persistent_individuality: false  # Level 4 未達
  measured_by:                # 画像でなく測定量
    variance_growth: 0.42
    structure_factor_peak_k: 0.31
    defect_count: 7
    circulation_integral: 1.8
  purity:                     # 純粋創発か足場付きか
    per_object_labels: false
    external_optimum: false
    role: E                   # E=純粋創発 / S=足場付き合成
```

**Level 番号は到達深度であり優劣ではない。** 既知理論の忠実な再現（V）や誠実な負の結果（N）は、Level と別軸で高く評価される（`docs/PHYSICS_INTEGRITY.md`）。
