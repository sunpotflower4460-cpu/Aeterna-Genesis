# AI_EXPERIMENT_POLICY.md — AI の変更可能範囲と昇格

AI（Claude / Codex）が始原条件を探索するときの明文化ルール。**AI の仕事は完成形を設計することではなく、より深い創発まで自然に発展する始原条件を探す自動実験者として働くこと。**

---

## 1. 基本ルール（15）

1. すべての候補は**時刻 0 から**実行する。
2. 完成した機能を**途中追加しない**。
3. 親 Room を変更せず、必ず子 Room を作る。
4. 変更点は**一つまたは少数**に限定する。
5. 2D 結果を 3D 結果として扱わない。
6. 正式昇格には**本番 3D** が必要。
7. **法則変更とパラメータ変更を区別**する。
8. 保存量を壊す補正を禁止する。
9. **失敗結果も保存**する。
10. 可視化データを物理結果として使わない。
11. 物理的主張は**測定値からのみ**生成する。
12. 過去の Room・テンプレート・結果を削除しない。
13. AI は候補を提案できるが、**物理監査を単独で通過させない**。
14. 新しい創発は、既存の意味ラベルでなく**測定量から**判定する。
15. 「生命」「脳」「身体」「宇宙」等の強い語は、正式定義を満たさない限り使わない。

---

## 2. AI が変更してよいもの（始原側のみ）

初期分布 ／ ノイズ強度 ／ ノイズの空間相関 ／ 物理定数 ／ 拡散係数 ／ 反応係数 ／ 外部流入量 ／ 外部流入分布 ／ 初期対称性 ／ 局所相互作用範囲 ／ 空間スケール ／ 時間スケール ／ 保存則を満たす局所法則候補 ／ 法則候補間の比較。

`search_space.yaml` で許可された範囲だけを変更する：
```yaml
search_space:
  initial_state:
    noise_amplitude: {min: 1.0e-5, max: 1.0e-2, scale: log}
    correlation_length: {min: 1.0, max: 12.0}
  physical_parameters:
    diffusion_ratio: {min: 0.1, max: 10.0}
    drive_strength: {min: 0.0, max: 5.0}
  boundary_conditions:
    allowed: [periodic, no_flux, physical_wall]
```

---

## 3. AI が直接変更してはいけないもの

- 求める完成形／完成形を評価する画像類似度。
- 完成した膜・器官。
- 中心制御装置・全体を監視する外部 oracle。
- 生死を直接決める条件分岐。
- 分裂を開始する外部命令。
- 結果を特定形状へ収束させる強制項。
- **成功判定コード・保存則の計算・監査閾値**（結果に合わせて変えない）。
- 過去の結果・正式 Room・親 Room・既存の raw data。
- 物理法則の意味を変える無断補正・結果に合わせたクリッピング・途中からの外部介入。

---

## 4. 法則変更（パラメータ変更と分離）

```yaml
mutation_type:
  - initial_state_change
  - parameter_change
  - boundary_change
  - law_variant   # 法則変更は別扱い
```

**法則変更を単なるパラメータ探索として扱ってはならない。** 法則変更候補は、パラメータ探索より厳しい監査を通す：物理的由来・対称性・次元整合性・保存則・熱力学整合性・既知極限・**結果を直接符号化していないこと（第8監査）**。

---

## 5. 第8監査（AI が最も陥りやすい罠）

**評価ゲート・初期条件・方程式に、結論と同型の因果を埋め込んではならない。**（詳細は `docs/PHYSICS_INTEGRITY.md` §6。）

AI が候補を提案するたびに自己点検：
1. 初期条件に、証明したい量そのものが入っていないか?
2. ゲートが結論の因果を直接 if 判定していないか?
3. ゲート閾値が対照（null/線形/ランダム）でも通らないか?
4. 「創発した」量が別の入力の代数的言い換えでないか?

**必須の対照を省かない：** 「機構 X が現象 Y を起こす」なら X を切った対照で Y が消えることを並べる。多様性は有界空間＋中立対照。well-mixed vs spatial は mass-matched。

---

## 6. 昇格段階（飛ばせない）

```
IDEA → 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT PASSED
→ LOCAL 3D PASSED → COARSE GLOBAL 3D PASSED → FULL 3D REPRODUCIBLE
→ PHYSICS AUDIT PASSED → TEMPLATE CANDIDATE → OFFICIAL ROOM
```

昇格ルール例：
```yaml
promotion:
  from: exploration_2d
  to: local_3d
  requires: [reproducible_across_seeds, no_conservation_violation, dimension_transfer_risk_not_critical]
```

**候補の状態：** 2D 候補 ／ 局所 3D 候補 ／ 低解像度全体 3D 候補 ／ 本番 3D 検証待ち ／ 本番 3D 検証済み ／ 物理監査待ち ／ 正式テンプレート。

---

## 7. AI の no-touch 領域

```
rooms/official/
results/official/
validation/baselines/
docs/history/
```

AI は通常これらを直接編集しない。**昇格コマンドを通じてのみ**追加する（`aeterna promote --room ...`）。

---

## 8. AI 探索の基本ループ

1. 親 Room を選ぶ。
2. 始原条件の一部を変更する（一つ/少数）。
3. **必ず時刻 0 から再実行**する。
4. 自然創発の到達 Level を測定する（`docs/EMERGENCE_LEVELS.md`）。
5. 親 Room と結果を比較する。
6. 新規性・再現性・物理的妥当性を評価する。
7. 良い候補を再試験する。
8. 2D 候補 → 局所 3D → 低解像度全体 3D → 本番 3D と昇格（次元監査を通す）。
9. **AI は過去の Room を削除しない。**
