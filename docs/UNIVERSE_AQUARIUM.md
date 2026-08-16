# UNIVERSE_AQUARIUM.md — 宇宙水槽という研究モデル

Aeterna-Genesis の最上位の見方を、**宇宙水槽（Universe Aquarium）**として整理する。

ここでいう水槽とは、結果を作る装置ではない。
**法則・物質・初期状態・境界・持続入力などの前提条件を与え、その世界が自分で何を始めるかを見る実験系列**である。

水槽に土・水・種・光を入れても、森の形を直接描いたことにはならない。同じように、Aeterna では「何を見たいか」という意図を持ってよいし、そのために前提条件を工夫してよい。ただし、最終形・発生位置・発生時刻・分裂命令など、**見たい結果そのものを物理へ書き込まない**。

---

## 1. 最重要の区別：Intent と Encoding

### Intent — 研究者・AIが持ってよい

例：

- 「持続する一つのまとまりが、いつか二つへ分かれる系を見たい」
- 「トーラス状の持続構造が自然に形成される条件を探したい」
- 「関係だけから距離や次元のようなものが定義できるか見たい」
- 「何が起こるか決めず、未知の反復現象を探したい」

これらは**研究の目的地・探索方向**であり、禁止しない。人間も AI も自由に提案できる。

### Outcome encoding — 創発の証拠としては混ぜてはいけない

例：

- トーラスを初期条件として置き、「トーラスが生まれた」と主張する
- 指定時刻に分裂を開始する命令を入れる
- くびれ位置や分裂位置を外部から指定する
- 完成形との画像類似度を物理更新則へ直接入れる
- 見たい構造の座標・電荷・配置を結果として先に固定する

**合言葉：意図は自由。結果は仕込まない。**

機械的な境界は次の通り。

```text
planning layer may read intent
physics layer must not read intent text
measurement layer may define what to observe
promotion/science gate may use preregistered measurements
no layer may rewrite the physics after seeing a desired outcome
```

---

## 2. Aquarium と Room の違い

- **Aquarium**：研究系列。「何を見たい／何を試したい」「どの前提条件の範囲を探索するか」を持つ。
- **Recipe**：一つの具体的な前提条件セット。法則、初期状態、境界、外部供給、パラメータ、seed など。
- **Run**：Recipe を t=0 から実際に走らせた一回の宇宙。
- **Room**：保存・再現可能な Run / 宇宙の記録。正式 Room と候補 Room を区別する。
- **Observation**：Run で測ったもの。
- **Discovery**：Recipe の差と Observation の差から得た、再試験可能な発見。
- **Direction Note**：人間または AI が書く「次に何を試すか」のメモ。科学的証拠そのものではない。

Aquarium は Room より上位にあり、**一つのAquariumから多数のRecipe・Run・Roomが分岐してよい**。

---

## 3. 水槽の種類は優劣ではなく問いの違い

### Open-ended Aquarium

何が起こるかを先に決めない。名無し反復、未知の遷移、長寿命状態などを探す。

### Goal-directed Aquarium

「分裂を見たい」「トーラス形成を見たい」など明確な研究意図を持つ。ただし intent は探索計画にのみ使い、結果を物理へ埋め込まない。

### Pure / Minimal-start Aquarium

一様に近い状態や最小ノイズから始める。純粋な genesis の問いに向く。

### Seeded / Scaffolded Aquarium

種、小さな欠陥、少数seedなどを前提条件として入れる。**価値が低いわけではない。問いが違う。**
「種を入れた世界で何が育つか」を調べる正当な水槽である。

### Driven Aquarium

日光・熱・栄養供給のような持続的入力を持つ。外部供給があること自体は target encoding ではない。
**供給が何を作るかを直接指定しないこと**が重要。

一つの Aquarium は複数の属性を同時に持ってよい（例：goal-directed + seeded + driven）。

---

## 4. 人間と AI の役割

人間と AI を上下に分けない。両方が**水槽アイディアを出す研究者**である。

### 人間ができること

- 「こんな系を見たい」「こんなことを実現したい」と提案する
- Recipe を自分で作る
- 水槽をアプリで見る
- 発見・失敗・AIの次方針を分かりやすく把握する
- AIの提案を採用・修正・保留する
- 自分のメモを残す

### AI ができること

- 人間のアイディアを Recipe に落とす
- 過去の Evidence / Research Memory から関連記録を探して助言する
- 人間が依頼した Aquarium を裏で探索する
- 人間の指示がなくても新しい Aquarium を提案・探索する
- 似た過去実験、失敗理由、条件境界を見つける
- 次に情報量が高い Recipe を提案する
- Direction Note を残す

### 連携の条件

AIが自律的に進んでも、人間が戻ったときに必ず次を答えられること。

1. 今どの Aquarium があるか
2. それぞれ何を見たい系列か
3. 何を入れたか
4. 何が起きたか
5. 何が再現し、何が壊れたか
6. AI は次に何をしようとしているか
7. 人間が今どこへ介入できるか

---

## 5. Aquarium の研究ループ

```text
Idea / Intent
  ↓
Recipe proposal
  ↓
Integrity check
  ↓
Run from t=0
  ↓
Observation
  ↓
Compare with controls / nearby recipes / history
  ↓
Discovery or negative evidence
  ↓
Human note + AI direction note
  ↓
Next recipe
```

このループは、goal-directed でも open-ended でも同じ。

重要なのは「成功したか」だけではなく、**なぜこの配合でこうなったのかを徐々に地図化すること**。

---

## 6. Recipe に入れてよいもの

例：

- field / matter の種類
- 局所法則・既知物理・監査付き law variant
- 初期分布、seed、noise、correlation
- 境界条件
- 空間・時間スケール
- 拡散、反応、結合などの係数
- 外部流入、熱、光に相当する持続 drive
- 保存則を壊さない局所相互作用
- 観測する measurement の選択

ただし、**「結果を直接実現する命令」ではなく世界の前提条件として説明できること**。

---

## 7. Goal-directed 探索の正しい使い方

「細胞分裂のようなものを見たい」という intent を例にする。

AI は次を変更してよい。

- 供給と排出の比
- 内外の輸送
- 反応速度
- 物質保存・エネルギー流
- 局所的な界面物理
- 相互作用範囲
- 初期seedの有無
- drive の強さや周期

AI は、過去の結果を見て「成長はするが崩壊するなら供給を下げる」「境界が維持できないなら排出側を変える」のように**意図へ近づく探索**をしてよい。

一方で、「中央を細くする」「時刻Tで二つに切る」のように結果と同型の因果を追加してはいけない。

**目的地を見ながら道を探すことと、目的地を最初から地面へ描くことは別。**

---

## 8. 発見の単位

Aeterna が蓄積すべき最重要情報は、画像ではなく次の対応関係。

```text
Recipe A → Observation A
Recipe B (Aから1〜少数変更) → Observation B
差分 → 仮説
独立seed / 対照 → 再試験
```

発見例：

- drive を上げると構造量は増えるが寿命が短くなる
- seed がある場合だけ境界が長寿命化する
- ある条件域では recurrent X が出るが、境界を越えると消える
- 長時間化しても状態が一段上へ進まず、同じ関係を保つ

負の結果も同じ価値で残す。

---

## 9. アプリ（Observatory）の役割

Observatory は単なる3Dビューアではなく、最終的に**人間とAIが共有する研究室**になる。

最低限、人間はアプリで次を見られるようにする。

- Aquarium 一覧
- Intent / Recipe family / status
- 実際の Run / Room の美しい field visualization
- 何を入れたか
- 何が起きたか
- 最新 Discovery
- Human Note
- AI Direction Note
- 過去の関連 Evidence
- 次に試す候補

人間が Aquarium idea を入力した場合、それはまず**planning data**として保存される。物理的な主張にはならない。

---

## 10. 科学的な安全線

- Intent は evidence ではない。
- Direction Note は evidence ではない。
- AI の operational priority は scientific truth を変えない。
- Seeded / scaffolded を strict minimal genesis と混同しない。
- Driven system を closed / autonomous と混同しない。
- Goal-directed を target-encoded と自動的に同一視しない。
- target-encoded な実験にも別の価値はあり得るが、自発形成の証拠としては分ける。
- 人間が見たい名前（division / torus / ecosystem など）と、実際に測定した量を必ず分離する。

---

## 11. Aeterna の新しい中心文

> **Aeterna-Genesis は、無数の宇宙水槽へ異なる前提条件を与え、世界自身が何を始めるかを観察し、その条件地図を人間とAIが共同で学び続ける研究環境である。**
>
> 人間もAIも「こんな世界を見たい」と意図してよい。
> ただし、結果を置くのではなく、結果が起こり得る前提を探す。
