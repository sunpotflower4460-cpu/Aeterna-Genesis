# EVIDENCE_CONTRACT_V2.md — 証拠契約 v2（前登録・docs-only）

> **これは前登録（preregistration）です。** 本 PR（Phase A1）では **docs のみ**を追加し、schema・Room metadata・
> App・物理コード・artifact・CI・数値結果を **一切変更しません**。ここで語彙と不変条件を一意に固定し、
> 実装（機械化された semantic lint・metadata 移行）は **Phase A2 以降**の別 PR で、レビュー後に行います。
>
> 規律：`AGENTS.md` / `docs/ANTI_DRIFT.md` / `docs/PHYSICS_INTEGRITY.md` / `docs/DIMENSION_POLICY.md` /
> `docs/EMERGENCE_LEVELS.md`。本書と最新 `AGENTS.md` が衝突する場合は **`AGENTS.md` を優先**し、衝突点を報告する。

## 0. なぜ v2 が要るか（問題の一次証拠）

現行 metadata には、**別々の事実が一つのフラグに畳み込まれている**箇所がある。代表例：

- `room-g002-a` / `room-g003-a` は `official: true` かつ `status: official` だが、実体は **2D** で
  `dimension_status.full_3d: not_started`（`rooms/official/room-g00{2,3}-a/room.yaml`）。
  → 「正式（official）」という一語が **"検証済みである"** と **"3D 昇格が完了している"** を混同している。
- `physics_status.conservation: passed` は、**厳密保存**・**収支則**・**Lyapunov 単調性**・**独立推定の一致**・
  **数値残差**という**性質の異なる 5 種**を一語で表している（G001 は非保存 TDGL の自由エネルギー単調減少、
  G002 は二つの Nusselt 推定の一致、G003 は質量厳密保存＋自由エネルギー H 定理——**どれも "conservation" ではない**）。
- `emergence.reached_level` は一本の整数だが、**個体性と自発運動は独立軸**（`EMERGENCE_LEVELS.md` 冒頭）。
  能力ベクトルが一次情報で、Level はその保守的要約であるべきなのに、現状は Level が二重の真実になりうる。

v2 は、これらを**二軸＋区別された語彙**へ分解し、`official` に**機械検証可能な不変条件**を与える。
**既存の数値・folder・checksum は変えない**（移行は metadata の *言い換え* であって *再計算* ではない）。

---

## 1. 状態を二軸に分ける（§6.1）

一つの Room / candidate の状態を、**独立な二軸**で表す。

### 1.1 証拠検証軸 evidence_validation（その主張がどの次元で測定検証されたか）

| 値 | 意味 | 既存 `dimension_status` からの写像 |
|---|---|---|
| `unvalidated` | まだ測定検証がない | どの段も not_started |
| `validated_2d` | 2D で測定検証済み | `exploration_2d: passed` |
| `validated_local_3d` | 局所（薄いスラブ等）3D で検証済み | `local_3d: passed` |
| `validated_global_3d` | 大域 3D（粗〜full）で検証済み | `coarse_global_3d: passed` または `full_3d: passed` |

これは **"どこまで測ったか"** の軸。**削除・降格の概念ではない**（2D 検証は 2D 検証として恒久的に有効）。

### 1.2 昇格軸 promotion_status（研究資産としての公式度）

| 値 | 意味 | 既存 `official`/`status`/フォルダからの写像 |
|---|---|---|
| `exploration` | 探索段階（AI Lab の 2D screen 等） | `rooms/candidates/` の初期候補 |
| `candidate` | 昇格候補（測定はあるが official 条件未達） | `official: false` の候補 Room |
| `promotion_ready` | official 条件を全て満たし登録待ち | （新）full_3d passed だが未登録 |
| `official` | 正式 Room（下記不変条件を全充足） | `official: true` **かつ不変条件充足時のみ** |
| `rejected_in_3d` | 2D では有効だが 3D 昇格で棄却された | （新）3D で不安定/非再現と判明した候補 |

これは **"公式資産としてどう扱うか"** の軸。

### 1.3 official の不変条件（機械検証可能・A2 で lint 化）

```
promotion_status == official
  ⇒ genesis.dimension == 3
  ⇒ すべての official run で run.dimension == 3
  ⇒ dimension_status.full_3d == passed
  ⇒ convergence == passed
  ⇒ reproducibility == passed
  ⇒ balance_or_invariant == passed        # §3 の区別済み保存監査のいずれかが passed
  ⇒ integrity_audit == passed             # 第8監査
```

**帰結（G002/G003 の移行方針）**：現行 `official: true` の 2D Room `room-g002-a` / `room-g003-a` は、v2 の
official 不変条件を**満たさない**（full_3d が not_started）。これらは **「失敗」に落とさない**。
移行では次のように**言い換える**（A2 で metadata 化、A1 では方針のみ固定）：

- `evidence_validation: validated_2d`（2D DNS として検証済み——**価値はそのまま**）
- `promotion_status: candidate`（3D 昇格候補。official-3D バッジは外す）
- **数値結果・folder・checksum・run manifest は変更しない。** lineage/catalog は履歴を保持する。

`room-g001-a` は full-3D 実行済み（`MIGRATION.md` PR6）なので、不変条件を満たせば `official` を維持できる
（A2 で機械検証して確定。§3 の balance_or_invariant を「Lyapunov 単調性」で満たす、を明示する）。

---

## 2. Level と能力ベクトルの関係（§6.2）

### 2.1 能力ベクトルが一次情報・Level は保守的要約

- **能力ベクトル（capability vector）を現象の一次情報**とする（`emergence.json.detected` を細分化）。
- **`reached_level` は、連続した下位 gate を全て満たした範囲の保守的要約**とする。
- 能力が高次軸で true でも、**途中 gate が未通過なら reached_level を飛び越えさせない**
  （例：自発運動 true でも個体性 gate 未通過なら Level 4 を主張しない）。

### 2.2 曖昧な能力を分ける（一つの真偽に畳まない）

現行 `detected.localization`（真偽一つ）を、少なくとも次へ分ける：

| 新能力 | 意味 |
|---|---|
| `pattern_localization` | 模様・ドメインの局在（対流セル等） |
| `interface_localization` | 界面の局在（相分離の界面等） |
| `compact_individual` | 周囲と区別される compact 単一個体（存在ゲート PASS 級） |

現行 `detected.spontaneous_motion` / `circulation` を、少なくとも次へ分ける：

| 新能力 | 意味 |
|---|---|
| `material_flow` | 物質・場の流れ（移流） |
| `circulation` | 循環（∮v·dl ≠ 0・渦度） |
| `pattern_translation` | 模様全体の並進 |
| `single_individual_self_propulsion` | **単一個体の自走**（M2 の drift・重心が持続的に動く） |

これらは **`EMERGENCE_LEVELS.md` の Level 定義を変えない**。Level への**写像を細かくする**だけ
（例：`compact_individual` かつ `single_individual_self_propulsion` が揃って初めて Level 3〜4 の一部を主張）。

### 2.3 既存 Room の写像（例）

| Room | 現行 detected | v2 能力ベクトル（写像） | reached_level（保守的要約） |
|---|---|---|---|
| room-g001-a | difference, localization | `pattern_localization`（渦線）＋位相欠陥 | 2（差＋位相巻き欠陥） |
| room-g002-a | difference, localization, circulation, motion=false | `pattern_localization`＋`circulation`（定常セル）；`pattern_translation=false` | 1（差・模様。循環は測定済だが定常セルは並進せず candidate=3） |
| room-g003-a | difference, localization | `interface_localization`＋`material_flow`（場から生じた流れ） | 2（相分離＋界面局在。共分化 Level 5 は candidate） |

**注**：この表は**現データの言い換え**であり、`emergence.json` の値も checksum も A1 では変更しない。

---

## 3. balance / invariant / Lyapunov を分ける（§6.3）

現行 `physics_status.conservation` は広すぎる。次の **5 種を区別**する語彙を導入する（A2 で metadata 化）：

| 区別された種別 | 意味 | 代表 |
|---|---|---|
| `exact_invariant` | 解析的に規則から従う厳密保存量（機械精度） | G003 の質量 ∫φ；agent_reaction の N_A−N_B |
| `balance_law` | 定常での収支則（流入＝流出） | G002 の定常熱収支 |
| `lyapunov_monotonicity` | 自由エネルギー等の単調減少（散逸系） | G001 の post-quench 自由エネルギー；G003 の H 定理 |
| `independent_estimator_agreement` | 独立な二推定の一致 | G002 の二つの Nusselt（フラックス vs 散逸） |
| `numerical_residual` | 離散スキームの残差（丸め・打ち切り） | 全 Room の discrete budget residual |

**§1.3 の `balance_or_invariant` gate は、この 5 種のうち "その白に理論上正しい種" が passed であることを要求する**：

- **G001**：非保存 TDGL。**`lyapunov_monotonicity`**（自由エネルギー単調減少）で満たす。
  → 「conservation passed」ではなく「Lyapunov 監査 passed」と**正しく名付け直す**。
- **G002**：**`balance_law`（定常熱収支）＋`independent_estimator_agreement`（二 Nusselt 一致）**。
- **G003**：**`exact_invariant`（質量）＋`lyapunov_monotonicity`（自由エネルギー H 定理）**。
  coupled energy は §6.4 の通り全エネルギー budget（`C·F + KE`）で別途監査（Phase D）。

---

## 4. claim tier の改定予定（§6.4・A1 は方針固定のみ）

実装は A2 以降。A1 では**移行方針だけ**を固定する（現主張を削除・否定しない）。

- **G001**：現診断（XY plaquette winding のみ、`genesis/diagnostics/measures.py`）が支える範囲では
  **「3D 位相欠陥の lower-bound proxy」**。一般の loop topology（線接続・閉ループ数）は**未検証**。
  → 一般の「渦ループのトポロジーを証明」とは書かない（Phase B の 3D vortex instrument v2 が通るまで）。
- **G002 / G003**：**validated 2D**。official-3D を主張しない（§1.3 で candidate へ言い換え）。
- **agent_reaction**（`genesis/models/agent_reaction.py`, commit #51）：
  - `MSD ∝ t`：**established / Validation（V）**（連続極限の既知則）。
  - `N_A − N_B`：**stoichiometry から導かれる exact invariant / V**。
  - local × parallel × central-none：**実装アーキテクチャ上の成果**（物理主張でない）。
  - `at most one pair per site per step`：**微視的更新規則**として明記。
  - reaction front：**定量診断（front 位置・幅・rate profile・感度）ができるまで unverified claim**。
- **Model H（G003）**：`F` 単独の一般 H 定理表現を弱め、**`C·F + KE` の全エネルギー budget**を次の監査対象にする（Phase D）。

---

## 5. semantic lint の予定仕様（§6.5・A2 で機械化）

Phase A2 で `tools/validate_semantics.py`（schema shape とは別に cross-file *意味* を検査）として実装する。
**入力・エラー条件・warning→error 移行**を以下に前登録する。

**入力ファイル**：`rooms/**/room.yaml`・`rooms/**/genesis.yaml`・`rooms/**/emergence.json`・
`rooms/**/runs/*/manifest.json`・`experiments/*/experiment.yaml`・`app/generated/catalog.json`・`docs/TRUST_MAP.md`。

**ルール（error＝CI 失敗）**：

1. `official ⇒ full 3D passed`：`promotion_status==official`（または現行 `official:true`）なのに
   `dimension_status.full_3d != passed` は **error**。
2. **dimension consistency**：`room.genesis.dimension`・各 `run.dimension`・`render.dimension` が不一致なら error。
3. **room↔run reached-level consistency**：`room.emergence.reached_level` が run の測定 Level と矛盾したら error。
4. **capability↔Level 写像規則**：途中 gate 未通過で高 Level を主張（§2.1 違反）したら error。
5. **experiment source header ↔ `experiment.yaml`**：source role/target encoding が不一致なら
   （移行期は）**warning**、移行完了後に **error**。
6. **catalog / TRUST_MAP / experiment count consistency**：数え方（41 vs 44）が一本化されていなければ error
   （サブ実験は別軸で数える）。
7. **artifact 不改変**：metadata 移行が recorded artifact / checksum を変更していたら error。

**warning→error 移行**：ルール 5 は「source header 無し」を**最初は warning**、role 監査を 41 件全件へ拡張
（Phase A2 §7.3）した後に **error** へ格上げする。移行期間は `TRUST_MAP.md` に明記する。

**負のテスト fixture（A2 で必須）**：official=true/dimension=2；official=true/full_3d=not_started；
room≠run dimension；source role ≠ experiment.yaml role；target_encoded=true かつ primary role=E/V；
catalog count ≠ experiment count。

---

## 6. 閾値の前登録（§6.6・A1 は値を変えない）

各閾値を **由来・単位・感度・pass/fail 境界**と共に登録する**表の様式**を定義する。
**A1 では値を変更しない**（現行コードの値をそのまま転記する監査表を A2/Phase F で作る）。様式：

| threshold_id | 現在値 | 単位 | 由来（コード位置） | 感度分析 | pass/fail 境界 | tier |
|---|---|---|---|---|---|---|
| `winding_amplitude_mask` | (現値) | 振幅比 | `genesis/diagnostics/measures.py` | (要 A2) | 巻き欠陥計数の on/off | preregistered |
| `level1_amplitude_growth` | (現値) | 成長率 λ | measures.py | (要 A2) | Level 1 判定 | preregistered |
| `structure_prominence` | (現値) | S(k) ピーク比 | measures.py | (要 A2) | Level 1 判定 | preregistered |
| `g002_nu_agreement` | (現値) | 相対差 | `tools/build_room_g002.py` | (要 A2) | balance 監査 | preregistered |
| `m2_existence_residual` | 1e-2 | rel_res | `genesis/diagnostics/coupled_spectrum.py::existence_gate` | (要 Phase F) | 存在ゲート | preregistered |
| `m2_existence_area_fraction` | 0.5 | area_frac | 同上 | (要 Phase F) | 存在ゲート | preregistered |
| `goldstone_overlap` | 0.4 | overlap | coupled_spectrum.py | (要 Phase F) | Goldstone 判定 | preregistered |
| `goldstone_eigenvalue_tol` | 5e-3 | λ | coupled_spectrum.py | (要 Phase F・格子 pin で緩和検討) | Goldstone 判定 | preregistered |
| `drift_before_split_tol` | 1e-3 | λ | coupled_spectrum.py::classify | (要 Phase F) | drift 分類 | preregistered |

**preregistered（前登録）と post-hoc（結果を見て決めた）を必ず区別**して記録する（各 PR の DoD）。

---

## 7. 移行表（G001 / G002 / G003 / agent_reaction）

| 資産 | 現行 | v2 evidence_validation | v2 promotion_status | balance_or_invariant の正しい名 | claim tier 方針 |
|---|---|---|---|---|---|
| room-g001-a | official:true / full-3D | `validated_global_3d` | `official`（不変条件を A2 で機械確認） | `lyapunov_monotonicity` | 3D 位相欠陥の lower-bound proxy（一般 loop topology は未検証） |
| room-g002-a | official:true / 2D | `validated_2d` | `candidate`（official-3D バッジを外す） | `balance_law`＋`independent_estimator_agreement` | validated 2D（official-3D を主張しない） |
| room-g003-a | official:true / 2D | `validated_2d` | `candidate` | `exact_invariant`（質量）＋`lyapunov_monotonicity` | validated 2D；共分化 Level 5 は candidate |
| agent_reaction | E 的記述あり | `validated_2d`（該当実験） | n/a（Room でない） | `exact_invariant`（N_A−N_B） | MSD=t→V／N_A−N_B→derived invariant／arch 成果／front は unverified |

**A1 では上表は "方針" である。** 実際の `room.yaml` / `experiment.yaml` の値の書き換えは **A2**（negative fixture 付き）。

---

## 8. A1 の完了条件（自己チェック）

- [x] 実装前に意味論が一意に伝わる（本書 §1–§7）。
- [x] G001/G002/G003/agent_reaction の移行表がある（§2.3・§7）。
- [x] A2 の semantic lint がテスト可能な形で仕様化（§5・負の fixture 列挙）。
- [x] 数値結果・schema・metadata・CI・App に差分がない（**docs-only**）。
- [ ] `validate_schemas.py` / `audit_roles.py` / `build_catalog.py --no-write` / `pytest` が変更前と同等に通る（本 PR で確認・報告）。
- [ ] read-only の代表画像 1 枚＋独立監査ファイル（`EVIDENCE_CONTRACT_V2_AUDIT.md`）を提出。

**A1 完了後、A2 へ進まず停止し、レビューを待つ。** 研究の目的は問題を急いで消すことではなく、
**どこまで言え、どこから先はまだ言えないかを、コードと証拠が同じ言葉で語る状態にすること**。

---

## 9. 追記（外部監査対応・2026-07-16・docs-only）

H021 渦ダイポールキャンペーン（e052–e058）の外部監査2件（GPT・別Claude）を受け、A1 の語彙を3点補強する。
**本節も docs-only**——schema・CI・数値には手を触れない。

### 9.1 禁止主張リスト（"言ってはいけないこと"を明文化）

これまでの閾値表（§6）は**測る量**を定義したが、**測った量から何を主張してはいけないか**を明文化していな
かった。以下は preregistered な禁止リスト（A2 で semantic lint の negative fixture に格上げ予定）：

| 禁止する言い回し | 理由 | 正しい言い回し |
|---|---|---|
| 「σ(m=1)≈0 は自走しないことの証明」 | m=1 は並進の **Goldstone モード**（並進対称性から来る恒等的にゼロ近傍の固有値）であり、σ≈0 はこれを**検出しているだけ**。自走の有無を判定していない（M2 の核心的教訓、`docs/ANGULAR_MODES.md`） | 「調査した断面では m=1 は Goldstone として現れ、真の drift 固有値は結合固有値解析（M2）でのみ判定できる」 |
| 「渦ダイポールの並進＝単一個体の自走（L4）」 | L3（2体の並進）と L4（単一個体の自走・codimension≥2 ナイフエッジ）は別の問い（e053/AUDIT.md・WHITE_CEILINGS.md で既に区別済み。ここで明文の禁止リストに固定） | 「自己形成渦ダイポールの自発並進（L3）」、L4 は別途 `recovers_after_perturbation`・`tracked_id_lifetime`・`inside_outside_contrast` を測る |
| 既知理論の引用（点渦誘導速度・Poincaré–Hopf 等）を「創発の証明」として使う | 既知理論との**一致**は物理的妥当性の傍証にはなるが、**測定した現象が非 seeded であること自体は別に監査する必要がある**（第8監査・target_encoded） | §9.2 の4層で「一致した」と「測定した」を分離して記録する |

### 9.2 外部物理一致の4層フィールド（`known_match` の精密化・A2で実装予定）

現行 `known_match` は自由記述の一文字列。既知理論との一致が**創発成功の代用**にならないよう、将来
（A2）以下の4層に分ける前登録：

```
external_correspondence:
  theorem:        # 参照する既知理論・法則の名前（例：点渦誘導速度 v~1/(2d)）
  known_model:     # その理論が成立する既知の設定（例：2D 非圧縮超流体点渦動力学）
  measured_here:   # 本実験で実際に測った量（例：候補ペアの並進速度、比 0.74〜1.16）
  interpretation:  # 一致から言えること（傍証）と言えないこと（非 seeded の証明にはならない）を分離
```

A1 では**方針のみ固定**。既存 `known_match` フィールド・値は変更しない。

### 9.3 hole/torus/memory の段階ゲート予約（誤登録防止）

`docs/HOLES_TORUS_MEMORY.md`（存在する場合）または将来の同種ドキュメントで、"穴・トーラス・記憶" 方向の
主張を以下の段階でのみ許可する、と予約する（**まだ実装しない・まだ実験しない**——後で Hγ 相当の主張を
誤って E に登録することを防ぐための、先回りした足場）：

| 段階 | 内容 | role |
|---|---|---|
| V1 | Topological Atlas（既存の b₀/b₁/b₂/χ・genus 計測器の適用範囲を固定検証） | V |
| F1 | One-Handle Selection（1つの穴/ハンドルがどう選ばれるかの前登録・実装前） | F（prereg） |
| E候補 | Emergent Holonomy（穴/トーラスが非 seeded で自己組織化したことを、matched control 付きで測定） | E候補（未達） |

3D 渦リング（自己形成した閉ループ＝自己組織化したトーラス）は F1 の自然な入口になりうる、と記録する
（H021-3D キャンペーンの一次候補、PR-C 以降）。

### 9.4 用語ガイダンス（L3 と L4 の混同を防ぐ）

「自走」「self-propulsion」は**単一個体**（L4）に予約する。**渦ペア（2体）の並進**（L3、e052–e058）は
「自己形成渦ダイポールの自発並進」「self-formed vortex-dipole translation」と呼ぶ。既存の committed
experiment.yaml / AUDIT.md の文言は歴史的記録として変更しないが、**今後の新規実験・ドキュメント・報告**
ではこの語彙を使う。
