# AGENTS.md — Aeterna-Genesis で働く AI への共通規則

このリポジトリで作業する AI（Claude Code / Codex / その他）が**最初に読む**ファイル。詳細は `docs/` の各文書へ。

> 🌌 **まず [`docs/UNIVERSE_AQUARIUM.md`](docs/UNIVERSE_AQUARIUM.md) を読む。**
> Aeterna の本質は「宇宙水槽」。人間もAIも「こんな系を見たい」と Intent を持ってよいし、人間の指示がなくてもAIが新しい水槽を考えてよい。
> **Intent は自由。結果は仕込まない。** planning は Intent を読めるが、physics solver は Intent 文を読まない。
>
> ⚠️ **Level を扱う前に必ず [`docs/ANTI_DRIFT.md`](docs/ANTI_DRIFT.md) を読む**（創発 vs 入れ込み）。
> 結論（完成形）を初期条件に入れると target_encoded＝drift。合言葉：**「それは育ったのか、置いたのか？」**
> 白ごとにどこまで登りどこで天井になるかは [`docs/WHITE_CEILINGS.md`](docs/WHITE_CEILINGS.md)（白の天井地図）。
> IC の由来（その部品どこから来たの?）は [`docs/GENESIS_PROVENANCE.md`](docs/GENESIS_PROVENANCE.md)＋
> [`docs/CAUSAL_CLOSURE.md`](docs/CAUSAL_CLOSURE.md)（C0〜C4）、能力の多軸記述は [`docs/PERIODIC_TABLE.md`](docs/PERIODIC_TABLE.md)。
> 自走個体は「探す」でなく角モード固有値の順序を「測る」＝ [`docs/ANGULAR_MODES.md`](docs/ANGULAR_MODES.md)（M1）。

---

## このプロジェクトは何か

**無数の宇宙水槽へ、法則・物質・初期状態・seed・境界・持続入力などの前提条件を与え、その世界が自分で何を始めるかを見る研究環境。**

完成した生命・身体・脳・宇宙を人間やAIが直接組み立てるのではない。ただし、**「分裂を見たい」「トーラス形成を見たい」「何が起こるか決めずに探したい」などの研究 Intent は持ってよい。** その Intent を見据えて Recipe を探索することと、結果そのものを equation / initial condition / command に埋め込むことを混同しない。

**進歩の定義：** 見たい形を作ることではない。**どの前提条件で何が起こり、何を変えると残り／消えるかを発見し、再現可能な条件地図を広げたこと**を進歩とする。

---

## Aquarium + 三層構造

0. **Universe Aquaria**（`aquaria/`）：人間・AI共有の研究系列。Intent、Recipe Space、Human Note、AI Direction Noteを持つ。**planning dataであり科学的成功状態ではない。**
1. **Evidence Library**（`experiments/e001–e036`）：現象・法則・測定器・成立条件・負の結果を蓄積した証拠庫。**削除・番号変更しない。** 生命の部品表ではなく、物理辞書。
2. **Genesis Rooms**（`rooms/`）：一つのRecipeから **t=0 から中断なく**発展させ、何が起きたかを記録した再現可能な宇宙。パラレル宇宙として分岐保存。
3. **AI Genesis Lab**（`ai_lab/`）：Aquarium、Evidence、Research Memoryを読み、**前提条件を探索**する自動実験者。候補を 2D→局所3D→全体3D と昇格。

Aquarium → Recipe → Run → Observation → Discovery → Next Recipe の履歴を、人間が後から追えること。

---

## 最重要規律（4つ）

1. **毎回 0 から始める。** 全ての run は時刻 0 から。持続driveがある場合もt=0前にRecipeとして宣言する。
2. **先へ進むために途中へ完成機能を追加しない。** より深くしたいなら、Aquariumの前提条件を変えて新Runをt=0から試す。
3. **Goal-directed exploration を禁止しない。** Intent は次Recipeを考えるために使える。しかし Intent 文・完成形・結果位置・結果時刻を physics layer が読むことは禁止する。
4. **「これは物理だ」と言える誠実さを、成果数・見栄えより優先する。** 詳細は `docs/PHYSICS_INTEGRITY.md`。

---

## 役割分担（計算環境）

| 場所 | 役割 | 担当 |
|---|---|---|
| **サンドボックス（2D＋α）** | Recipe の 2D 探索、測定器開発、粗いパラメータ地図、薄い/局所 3D の事前計算、明確な失敗の除外 | Claude（設計）|
| **リポジトリ（正式 3D）** | 正式 3D Room の計算・昇格・登録。AI 用計算場所を含む | Codex / Claude Code |

**2D 成功は候補発見であって正式成功ではない。正式 Room は t=0 から終了まで 3D。** 2D→3D は自動外挿せず、次元移行監査（`docs/DIMENSION_POLICY.md`）を通す。

---

## AI が絶対にやってはいけないこと（要約）

- 求める完成形（身体・膜・器官・脳・トーラス等）を直接与え、それを自発形成の証拠として扱う。
- 中心制御装置・全体を監視する外部 oracle・生死を決める条件分岐・分裂の外部命令。
- 結果を特定形状へ収束させる強制項、完成形との画像類似度をphysics objectiveにする。
- 分裂位置/時刻、渦位置/電荷、target morphologyなど、結果そのものを事前に固定する。
- **評価ゲート・初期条件・方程式に、結論と同型の因果を埋め込む（第8監査。`docs/PHYSICS_INTEGRITY.md` §「第8監査」）。**
- 保存量を壊す補正、結果を見た後の成功条件変更、成功 run だけ残す、可視化データを物理結果として使う。
- 過去の Aquarium・Room・Recipe・結果・失敗・人間メモを削除する。
- 「生命」「脳」「身体」「宇宙」「生態系」「細胞分裂」等の強い語を、Intent名と測定結果を混同して使う（測定量から判定。限定名称「◯◯候補」を使う）。

## AI が変更してよいもの（前提条件側）

初期分布・seed class・ノイズ強度/相関・物理定数・拡散/反応係数・外部流入量/分布・t=0前に宣言された持続drive・初期対称性・局所相互作用範囲・空間/時間スケール・保存則を満たす局所法則候補。**法則変更はパラメータ変更と明確に区別**（`mutation_type: law_variant`、より厳しい監査）。詳細は `docs/AI_EXPERIMENT_POLICY.md`。

**Seeded / scaffolded / driven は「低価値」ではない。strict minimal startとは問いが違うので、種類とstart purityを正確に記録する。**

---

## 読む順

1. `AGENTS.md`（これ）
2. `docs/UNIVERSE_AQUARIUM.md` — Aquarium / Intent / Recipe / Human×AI連携
3. `docs/PHYSICS_INTEGRITY.md` — 誠実さの規律、E/V/S/N/F/Q、claim tier、**第8監査**
4. `docs/EMERGENCE_LEVELS.md` — Level 0–8 と**測定指標**
5. `docs/ROOM_MODEL.md` — Genesis Room とは、schema
6. `docs/DIMENSION_POLICY.md` — 2D 探索 / 3D 正式 / 次元移行監査
7. `docs/AI_EXPERIMENT_POLICY.md` — AI の変更可能範囲・Aquarium探索・昇格段階
8. `docs/GENESIS_MAP.md` — 現在地
9. `aquaria/registry.json` + `aquaria/notebook.json` — 現在の水槽列と人間/AI共有メモ

Claude 固有の手順が要る場合のみ `CLAUDE.md`。原則は本ファイルへ集約。

---

## うえきさんへの報告フォーマット（毎回・必須）

実験・調査をして人へ返すときは、**毎回この3点を必ずセットで**出す（うえきさんの恒久ルール・2026-07）：

1. **📸 スクリーンショット** — その回の実験の様子を画像で（0 から回した場のカラーヒートマップ等）。
   環境に matplotlib/Pillow が無くても、**numpy+zlib だけの依存フリー PNG レンダラ**で必ず出せる
   （記録済み lens `field.json` からでも、その場計算からでも）。可視化は物理を汚さない（`render.yaml` の
   `separated_from_physics_data`／honesty ブロックに準拠）。
2. **😊 うえきさんへのやさしい説明**（チャット本文・専門語を避ける）：
   - **どのAquariumで何を見ようとしていたか**、今回Recipeで何を入れた／変えたか、
   - **今回 0 からどこまで進んだか**、**順番に何が起きて・いま何をしているか**、
   - **何を発見したか／まだ分からないか**、**AIは次に何をやりたいか**。
3. **📄 別 Claude へ渡す監査用報告書**（**チャット説明とは別ファイル**・ダウンロード可能・技術的）：
   主張／Recipe／測定／限界・弱点／再現手順／規律チェック（no_touch・tier・第8監査・決定性）を含める。
   （2 は人向けにやさしく、3 は監査向けに厳密に——**必ず別々に**出す。）

合言葉は変わらない：**「それは育ったのか、置いたのか？」** 報告も同じで、**測ったことだけを、限界つきで**伝える。

---

## 現実に忠実な「起き方」で計算する（うえきさんの指針・2026-07・恒久）

うえきさんとの対話で固まった、**白の作り方・進め方の根本視点**。Universe Aquariumでは「白だけが正しい」のではなく、Minimal / Seeded / Drivenを問い別に区別したうえで、毎回これに沿う。

1. **中央計算者はいない（局所×並列×中央なし）。** 現実は「A と B がただ在って、局所でぶつかって反応し、
   *起きたもの* が結果になる」。誰も「各々こう振る舞え」と中央で 1 個 1 個計算していない。→ **計算の構造を
   〈局所（近傍のみ）× 並列（同時）× 中央ソルバ/oracle なし〉に寄せる**。FFT・大域陰解法は *近道*（答えは
   正しいが「現実の起き方」ではない）——使ってよいが **忠実さは下** と正直にタグ。参照実装
   `genesis/models/agent_reaction.py`（局所ホップ＋局所反応で拡散則・保存則が創発）。
2. **誠実な物理の流れ（作為も既知の檻も避ける）。** Goal-directed Aquariumでは研究Intentがあってよいが、**結果の具体形は世界に任せる。**
   機構は「現実でも同じことが起こると思える」こと。現実で起きない流れがここで起きたら *作為的* の疑い。
   ただし「起きると分かっていることしかやらない」は別物（＝「既知から出られない」に堕ちる）。
   **自由なIntent × 未知の結果 × 現実的な機構**を目指す。
3. **のっぺりでなくてよい（3D 以上・トポロジカル）。** 構造なしにするのは strict minimal-start Aquarium の**初期条件**。
   Seeded Aquariumではseedを入れてよいが、それを自然発生と混同しない。場と法則は
   3D・カイラル・トポロジカル（渦・トーラス・hopfion・立体らせん）で良い。**トーラスを *置く* は形成証拠ではなく、
   *育てる* は形成探索**。平面より 3D 以上を重視。**新規の創発探索は 3D を本線**とし、3D 主張は必ず
   「本物の 3D か」を監査する（[`docs/3D_NATIVE_POLICY.md`](docs/3D_NATIVE_POLICY.md)・
   `genesis/diagnostics/topology3d.py::three_d_authenticity`＋3D 固有量）。局所本線×独立検証器で裏付ける
   （[`tools/corroborate.py`](tools/corroborate.py)：局所 vs スペクトル、Genesis-Room 3D／0-looper 2D 並列）。
   **2 層の裏付け**：① 局所 vs スペクトル（同一 repo・2D＆3D・ネット不要）は **CI/テストで毎回**自動。
   ② 外部 repo（Genesis-Room 3D＋0-looper 2D）並行は **opt-in**——ランナーに `--corroborate` を付けると run 直後に
   同じ問いを両 repo へ並行送信し `corroboration.json` を保存（ネット依存・offline は `backed=None` のソフト失敗、
   偽の pass を作らない・checksum は不変）。CI は①のみ（外部 clone はヘッドレスで不安定なため）。
4. **全体・カタチ・関係／コピーでなく唯一。** 個体だけでなく **全体（関係グラフ）** を測る。**複製（コピー）と
   個体化（内側から違う唯一）を測度で分ける**。内部の唯一性は *置かず育てる* ＝ frontier。
5. **スピリチュアル/精神の記述は科学と地続き。** 実在はひとつ。**tier は「真偽の壁」でなく「知り方」の地図**
   （measured / experiential / interpretive / analogy）。着想源として一級に扱い、主張は測定で立てる。
   **同じ絵 ≠ 同じもの**（絵がトーラスでも「生命/意識」とは言わない）。
6. **北極星。** 人間もAIも「こんな宇宙を見たい」という目的地を持ってよい。ただし **目的地を結果として埋め込まず、
   そこへ至り得る前提条件を探す。** Open-ended Aquariumでは目的地を決めずに未知を拾う。
   届かなくてよい。**どのRecipeでどこまで行き、どこで天井になり、その天井はなぜかを正直に測って地図化する**のが誠実な成果（`docs/WHITE_CEILINGS.md`）。
