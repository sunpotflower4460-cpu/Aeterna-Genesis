# AI_EXPERIMENT_POLICY.md — AI の変更可能範囲と昇格

AI（Claude / Codex）が前提条件を探索するときの明文化ルール。**AI の仕事は完成形を設計することではなく、Universe Aquarium の Recipe を考え、世界自身が何を始めるかを調べる自動実験者として働くこと。**

人間のアイディアがなくても AI は新しい Aquarium を提案・探索してよい。人間が「こんな系を見たい」と目的を出した場合は、その Intent を研究方向として尊重し、過去の Evidence / Research Memory を使って前提条件を提案してよい。

ただし最重要境界は [`docs/UNIVERSE_AQUARIUM.md`](UNIVERSE_AQUARIUM.md) に従う。

> **Intent は自由。結果は仕込まない。** planning layer は Intent を読んでよいが、physics layer は Intent 文を読んではならない。

---

## 1. 基本ルール（19）

1. すべての候補は**時刻 0 から**実行する。
2. 完成した機能を**途中追加しない**。
3. 親 Room を変更せず、必ず子 Room / 新 Run を作る。
4. 条件比較では変更点を**一つまたは少数**に限定し、何を変えたか追跡できるようにする。
5. 2D 結果を 3D 結果として扱わない。
6. 正式昇格には**本番 3D** が必要。
7. **法則変更とパラメータ変更を区別**する。
8. 保存量を壊す補正を禁止する。
9. **失敗結果も保存**する。
10. 可視化データを物理結果として使わない。
11. 物理的主張は**測定値からのみ**生成する。
12. 過去の Room・Aquarium・Recipe・結果を削除しない。
13. AI は候補を提案できるが、**物理監査を単独で通過させない**。
14. 新しい創発は、既存の意味ラベルでなく**測定量から**判定する。
15. 「生命」「脳」「身体」「宇宙」「生態系」「細胞分裂」等の強い語は、正式定義を満たさない限り測定結果の名称として断定しない。Intent 名には使ってよいが、Intent と observation を区別する。
16. **実験を提案・実行する前に `ai_lab/discoveries/research_memory.json` を確認する。** `avoid_exact_repeat=true` の問いは、`reopen_when` に書かれた実質的な新条件がない限り同じ形で繰り返さない。負の証拠を消すのではなく、**次の問いを変えるために使う。**
17. **AI は人間の指示がなくても Aquarium idea を考えてよい。** その場合も `origin=ai` として記録し、人間が後から意図・理由・現在地を読めるようにする。
18. **Goal-directed exploration を禁止しない。** 「分裂を見たい」「トーラス形成を見たい」などの目的は planning に使える。ただし solver / equation / initial state が Intent 文を読み、結果を直接作ることは禁止する。
19. **人間との連携を研究状態の一部にする。** Human Note と AI Direction Note を同じ Aquarium に紐づけ、AIが自律運転しても「何を考え、なぜ次を試すか」が戻ってきた人間に分かるようにする。

> 人向けの現在地は [`CURRENT_RESEARCH.md`](../CURRENT_RESEARCH.md)、Aquarium 一覧は `aquaria/registry.json`、人間/AI共有メモは `aquaria/notebook.json`。Research Compassの方針は [`docs/RESEARCH_COMPASS.md`](RESEARCH_COMPASS.md)。失敗詳細を人向けに軽くしても、AIの研究記憶からは消さない。

---

## 2. AI が変更してよいもの（前提条件側）

初期分布 ／ seed の有無・種類 ／ ノイズ強度 ／ ノイズの空間相関 ／ 物理定数 ／ 拡散係数 ／ 反応係数 ／ 外部流入量 ／ 外部流入分布 ／ 継続的な drive（光・熱・栄養供給に相当するもの） ／ 初期対称性 ／ 局所相互作用範囲 ／ 空間スケール ／ 時間スケール ／ 保存則を満たす局所法則候補 ／ 法則候補間の比較。

**Seeded / scaffolded / driven は価値が低いのではなく、問いが違う。** strict minimal start と混同せず、Aquarium class と start purity を明記する。

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

- 求める完成形／完成形を評価する画像類似度を物理更新則に使うこと。
- 完成した膜・器官を「自然形成の証拠」として初期配置すること。
- 中心制御装置・全体を監視する外部 oracle。
- 生死を直接決める条件分岐。
- 分裂を開始する外部命令。
- 結果を特定形状へ収束させる強制項。
- 分裂位置・分裂時刻・渦配置・電荷・トーラス位置など、見たい結果の場所や時刻を先に決めること。
- **成功判定コード・保存則の計算・監査閾値**を結果に合わせて変えること。
- 過去の結果・正式 Room・親 Room・既存の raw data。
- 物理法則の意味を変える無断補正・結果に合わせたクリッピング。

### 持続入力について

外部入力を途中から「望む結果が出るように」追加することは禁止する。一方、**Recipe として t=0 前に宣言された持続 drive** は正当な Aquarium 前提条件になり得る。

例：一定光、熱流、資源流入、外部場、周期 drive。

重要なのは「入力があるか」ではなく、**入力が結果そのものを命令しているか**。

---

## 4. 法則変更（パラメータ変更と分離）

```yaml
mutation_type:
  - initial_state_change
  - parameter_change
  - boundary_change
  - drive_change
  - law_variant   # 法則変更は別扱い
```

**法則変更を単なるパラメータ探索として扱ってはならない。** 法則変更候補は、パラメータ探索より厳しい監査を通す：物理的由来・対称性・次元整合性・保存則・熱力学整合性・既知極限・**結果を直接符号化していないこと（第8監査）**。

Goal-directed Aquarium で law variant を考えること自体は禁止しない。ただし「欲しい結果が出るから」という理由だけでは物理法則候補にならない。**結果から独立した物理的説明**を必要とする。

---

## 5. 第8監査（AI が最も陥りやすい罠）

**評価ゲート・初期条件・方程式に、結論と同型の因果を埋め込んではならない。**（詳細は `docs/PHYSICS_INTEGRITY.md` §6。）

AI が候補を提案するたびに自己点検：
1. 初期条件に、証明したい量そのものが入っていないか?
2. ゲートが結論の因果を直接 if 判定していないか?
3. ゲート閾値が対照（null/線形/ランダム）でも通らないか?
4. 「創発した」量が別の入力の代数的言い換えでないか?
5. **Intent を equation / solver が読んでいないか?**
6. Goal に近づくための変更が「前提条件の探索」ではなく「結果命令」へ変質していないか?

**必須の対照を省かない：** 「機構 X が現象 Y を起こす」なら X を切った対照で Y が消えることを並べる。多様性は有界空間＋中立対照。well-mixed vs spatial は mass-matched。

---

## 6. Aquarium / Run / Room の昇格段階

Aquarium 自体は昇格しない。Aquarium は研究系列であり、公式Levelではない。

Aquarium 内の具体的な Recipe / Run / Room が次の段階を進む。

```
IDEA → RECIPE PROPOSED → INTEGRITY CHECKED
→ 2D SCREENED → 2D REPRODUCIBLE → DIMENSION AUDIT PASSED
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

`aquaria/registry.json` と `aquaria/notebook.json` は planning layer なのでAIが提案更新してよいが、**人間メモを削除・意味変更してはならない。** supersededにする場合も履歴を残す。

---

## 8. AI 探索の基本ループ

1. **Aquarium を選ぶ、または新しい Aquarium idea を提案する。** 人間起点でもAI起点でもよい。
2. Intent を読む。Open-endedなら結果名を先に置かない。Goal-directedなら目的地を理解するが、結果をsolverへ渡さない。
3. **`research_memory.json` と Evidence Library を確認し、過去の近い問い・失敗・成立条件を探す。**
4. Recipe を提案する。何を入れるか、何を変えるか、なぜその変更を試すかを記録する。
5. Integrity check：target outcome / morphology / location / time を結果としてseedしていないことを確認する。
6. **必ず時刻 0 から新 Run として実行**する。
7. Observation を測定する。Intent 名ではなく測定量で記録する。
8. 近いRecipe・対照・親Room・過去Runと比較する。
9. Discovery または negative evidence を記録する。
10. Human Note があれば保持し、**AI Direction Note に「次に何をなぜ試すか」を残す。**
11. 同じ問いの惰性反復ではなく、条件境界・反証・独立seed・長時間化など情報量の高い次Recipeへ進む。
12. 良い候補は 2D → 局所3D → 低解像度全体3D → 本番3D と昇格する（次元監査を通す）。
13. **AI は過去の Aquarium / Recipe / Room / negative evidence を削除しない。**

---

## 9. 人間との連携契約

AI が自律的に何時間・何日探索しても、人間が戻ったときに次を短く答えられる状態を保つ。

1. どのAquariumを探索したか
2. 何を見たい系列か
3. 今回何を入れた／変えたか
4. 何が起きたか
5. 何が再現し、何が消えたか
6. 何を発見したか／まだ分からないか
7. 次に何を試そうとしているか
8. 人間のアイディアをどこへ反映したか

`ai_lab/aquarium/compass.py` はこの共有地図を作る planning-only utility。Aquarium Compass は **physics / compute allocation / scientific truth / Room promotion / official Level を変更しない。**
