# e060 AUDIT — 第8監査の自己点検

対象：`experiments/e060_l4_monad_frontier`（L4 Frontier — モナド白から「一つのもの」が生まれるか）
一次情報：`monad_audit.yaml`（単子性の凍結分類）・`experiment.yaml`（事前登録）・`results/phase0_calibration.json`

---

## 1. 第8監査（結論と同型の因果を埋め込んでいないか）

`docs/AI_EXPERIMENT_POLICY.md` §5 の4問に答える。

### 1-1. 初期条件に、証明したい量そのものが入っていないか？

**入っていない。これが本実験の主題である。**

証明したい量＝「単一の局在した個体」。従来の白（swift_hohenberg・mass_conserved_3d）は初期条件に
ガウシアンbumpを置いており、**証明したい局在をそのまま初期条件に入れていた**。リポジトリは
これを `localization_seeded=True` として正直に記録している（`docs/WHITE_CEILINGS.md`）。

本実験の主軸ICは `whites.uniform_plus_noise` ＝ **一様な平均値＋ゼロ平均ノイズのみ**である。
回帰テストで固定した内容（`tests/test_e060_l4_monad_frontier.py`）：

- `test_zero_mean_noise_is_exactly_zero_mean` — ノイズ平均が厳密に0（大域オフセットも置かない）
- `test_uniform_ic_places_no_localized_structure` — 中心と周辺の振幅が同等（bump構造がない）、
  最大振幅がノイズ振幅を超えない
- `test_bump_ic_is_visibly_different_from_uniform_ic` — 陽性対照との差が2桁以上
- `test_mass_conserved_uniform_ic_conserves_total_and_has_no_bump` — 総和が b0·N² と一致、
  活性化核を置いていない

### 1-2. ゲートが結論の因果を直接 if 判定していないか？

**していない。合格判定を自作していないため、構造的に不可能にしてある。**

L4の合否は既存の `genesis/diagnostics/higher_levels.assess_individuality_level` に**丸ごと委譲**する
（`l4_protocol._judge`）。本実験は独自の合格閾値を持たない。回帰テスト
`test_l4_judgment_is_delegated_to_untouched_assessor` がこの委譲を固定し、
`test_existing_l4_thresholds_are_unchanged` が判定器の閾値が動いていないことを挙動で固定する。

Phase 1 の分類器 `classify.py` が使う閾値も、既存判定器と**同一の値**を採用している
（`area_max=0.25` ＝ `localized`、`amax_floor=0.5` ＝ `contrast`、`steady_change=1e-2` ＝ `persistent`）。
`test_classifier_thresholds_match_the_existing_assessor` で固定。**独自の甘いゲートを作っていない。**

本実験が判定器に**加えた**のは緩和ではなく**追加の制約**のみ：

- G1「終盤の連結成分が1個」（`single_component`）
- 「局在が seeded でない」（`not seeded_localization`）

`pure_l4 = (reached_level == 4) and single_component and (not seeded_localization)` であり、
既存L4より**厳しい**。`test_pure_l4_requires_unseeded_localization_and_single_component` で固定。

### 1-3. ゲート閾値が対照（null/線形/ランダム）でも通らないか？

**Phase 0 で測定して確認した**（`results/phase0_calibration.json`、3 seed）。

| 対照 | 事前登録した期待 | 実測 | 結果 |
|---|---|---|---|
| A. SH + bump（陽性） | L4通過・単一・`pure_l4=False` | `reached_level=4`, `ncomp=1`, `area_fraction=0.0149`, `persistence_change≈2e-8` | **PASS** |
| B. SH bumpなし | 既定パラメータでは通過しない | `DIES`（`amax=0.0`・場が数値ゼロへ減衰） | **PASS** |
| C. TDGL（陰性） | L4の4基準を満たさない | `area_fraction≈0.998`（全域）・`persistence_change≈0.68`（未定常）・巻き欠陥 2〜8個 | **PASS** |
| D. mass_conserved | 保存が厳密 | `mass_drift = 0.0 〜 1.5e-16` | **PASS** |

Cが重要である。TDGLは**L2の巻き欠陥を実際に持つ**（2〜8個検出）が、それでもL4判定は通らない
（全域を埋め、定常でない）。すなわち**「模様や欠陥があれば通る」ゲートではない**ことが測定で示された。

前回キャンペーン `gl-haiku-1000-robustness` は `min_reached_level=1` が緩すぎて200条件すべてが
5/5通過し、条件間を弁別できなかった。その反省から本実験の通過ラベルは
`PERSISTENT_SINGLE_CANDIDATE` ただ一つに絞ってある。

### 1-4. 「創発した」量が別の入力の代数的言い換えでないか？

**言い換えではない。** 測定量（連結成分数・支持面積率・最大振幅・持続変化量・重心変位・
摂動後の再接近）はいずれも**場の時間発展の結果**から計算され、入力パラメータの代数関数ではない。
とりわけ `recovers_after_perturbation`（自己修復）は**置くことができない**量であり、
L2の凍結欠陥とL4の個体を分ける決定的判別子である（`higher_levels.py` の設計思想）。

---

## 2. モナド前提に固有の監査

`monad_audit.yaml` は白0を「これ以上分割できないもの」として扱う前提を、白の適格性判定の
運用基準に変換したもの。**Phase 0 実行前に凍結**した（`frozen_before_phase0: true`,
`frozen_at_commit: 9d5f9cf`）。

| 条件 | 監査内容 | 本実験での扱い |
|---|---|---|
| **M1 無分割** | 場は「部品」か「一つのものの様態」か | `mass_conserved`（a+b厳密保存）と `swift_hohenberg`（単一実スカラー）を monadic として主軸に。**非相反w付き `mass_conserved_nr` は composite として主軸から除外**（wは保存拘束を共有しない独立部品） |
| **M2 窓なし** | 外部oracle・実行時介入がないか | 主張の土台は無摂動control（`runtime_interventions=0`）。摂動枝は認識論的プローブとして分離記録 |
| **M3 内的原理** | 個体は切り出された部品か、全体場のモードか | **bumpを置かない**＝本実験の主軸そのもの |

`test_primary_whites_are_monadic_and_nr_is_excluded` / `test_perturbation_policy_keeps_the_monad_windowless`
で凍結値を固定している。

**この監査の帰結として、当初検討していた「動かすために非相反場を足す」路線は主軸から外した。**
何かを足した時点でM1違反であり、`docs/ANTI_DRIFT.md` の喩えで言えば木に買ってきたリンゴを
くくりつけることに当たる。主軸は**何も足さず、種（初期条件）だけを変える**。

---

## 3. 必須の対照（省いていないこと）

- **陽性対照**：SH + bump（既知のL4-static）。測定器が通すべきものを通すことの確認。
- **陰性対照**：TDGL（既知のL2天井）。測定器が落とすべきものを落とすことの確認。
- **保存則対照**：mass_conserved の質量ドリフト。保存が壊れていれば結論は無効。
- **主軸の対照**：同じ白・同じパラメータで bump の有無だけを変えた比較（A対B）。
  局在が seeded か emerged かの差だけを取り出している。

---

## 4. 現時点で主張していないこと（正直な範囲）

- **純粋Level 4の到達は主張していない。** Phase 0 で確立したのは「測定器が正しく較正されており、
  既定パラメータの近傍には純粋Level 4が存在しない」ことのみ。
- **2D限定。** `docs/AI_EXPERIMENT_POLICY.md` 基本ルール5に従い、3D結果として扱わない。
  `mass_conserved` は元来3D存在テスト用の白であり、2Dでの `FILLS_DOMAIN` は既知の次元感受性で
  あって白の否定ではない。
- **「この白ではLevel 4が出ない」とも言っていない。** パラメータ探索（Phase 1以降）は未実施であり、
  既定パラメータ1点の結果から白全体のno-goを主張するのは誤り。

---

## 5. 未解決の監査項目

`experiment.yaml: unresolved_audit` に記載。要点：

- 連結成分数は支持領域閾値 `thr=0.3` に依存する。Phase 0で凍結したが感度は未検証。
- 摂動をM2（窓なし）と両立させる切り分け（controlを主張の土台に置く）自体は解釈であり、
  `claim_tier` に `interpretive` を含めるべきかは未決。
- 純粋Level 4の到達／未到達はPhase 1以降の結果を待つ。**到達しなかった場合も、どこが天井か
  （単一化できない／持続しない／回復しない／箱依存／分裂が先）が測定として残れば成果である**
  （`docs/ANTI_DRIFT.md` 原則5：正直な未達は前進、避けることが失敗）。
