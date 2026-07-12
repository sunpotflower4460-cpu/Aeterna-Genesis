# ANTI_DRIFT — 創発 (emergence) vs 入れ込み (putting-in)

> **これは何か**：このプロジェクトで働く AI（Claude / Claude Code / Codex / Sonnet / GPT / その他）が
> Level を扱うとき、**結論（完成形）を初期条件に入れてしまう “drift”** を防ぐためのガード。
> 両リポジトリ（本 repo ＋ サンドボックス）共通で最初に読む。詳細は
> [`EMERGENCE_LEVELS.md`](EMERGENCE_LEVELS.md) / [`honest_floors.md`](honest_floors.md) /
> [`traps_museum.md`](traps_museum.md) / [`PIECES.md`](PIECES.md)。

## 一行原則

> **発現（emergence）＝ t=0 の始原条件から自然に育ったもの。**
> **入れ込み（putting-in）＝ 主張したい完成形を初期条件に埋めたもの＝ drift。**
> Level N を主張してよいのは、その構造が **IC に入っておらず、時間発展の測定で現れた**ときだけ（第8監査）。

drift は静かに起きる。「もう一段深い Level を出したい」→ つい target を IC に足す → measured に見えるが
target_encoded。**気づかないと堂々巡り**になる。だからこの一枚を毎回通す。

---

## canonical slip（一番滑りやすい所）— FULL L7 の遺伝タグ

**FULL L7 = 分裂 ＋ 遺伝**。Gray-Scott(U,V) に遺伝タグ場 `T` を足すとき、境界はここ：

1. **⭕ 発現**：`T` を **founder（種）にだけ**付け、**娘のタグは力学で継承**させる（`step_tagged` の双安定
   反応が分裂とともにタグを両娘へ運ぶ）。継承は**測定**（bistable purity・両系統存続）で確かめる。
2. **❌ drift**：分裂のたびに**娘へタグを直接代入**する／全スポットに**タグを command** する／`U,V→U,V,T` で
   `T` を最初から全域に敷いて「継承した風」に見せる。これは遺伝を**入れ込んで**いる＝ L7 ではない。
3. **判定の一言**：「daughters carry the parent's tag — **not commanded**」。命令したら drift。

（実装上の対応：`make_initial_tagged` は founder のみ種付け、`spot_tags` が継承結果を測る。
分裂だけ＝タグ継承を測っていない → **L7-partial** と正直に呼ぶ。）

---

## THE RULE

```
発現だけを Level として主張する。
  → 構造は t=0 の始原条件に入っていない（種・ノイズ・対称・founder タグまで）。
  → Level は measures（assess_level / higher_levels）で判定＝ measured。自作の成功ゲートで底上げしない。
  → 深くしたいなら「入れ込む」のでなく、始原条件か法則クラスを変えて genesis を 0 から回し直す。
  → partial は partial と呼ぶ（3条件揃わない L7 は L7-partial）。
```

---

## 創発 vs drift（対照表）

| | ⭕ 創発（OK・measured） | ❌ drift（NG・target_encoded） |
|---|---|---|
| 由来 | 成長 / 分裂 / 自己組織が **t=0 から** | 完成形を **IC / genesis に埋める** |
| IC | 種・ノイズ・対称・ランダム位相・founder タグのみ | 目標パターン・巻き数・分裂後の配置・娘タグ代入 |
| 例（L2） | 一様＋ノイズ → 位相巻き渦が育つ | `vortex_charges` で巻きを種に置く |
| 例（L3） | REST＋ノイズ → 循環ロールが自発 | 初期速度場・回転方向を与える |
| 例（L7） | founder タグ → **娘が継承**（力学） | 娘にタグ代入 / `T` を全域 command |
| 判定 | 第8監査 clean・tier=measured | target_encoded・GREEN 剥奪・role F |

---

## 「この Level を主張してよいか」YES チェックリスト

各項目 **YES** でなければ主張しない（NO があれば **STOP** → IC を種/ノイズ/対称へ戻し 0 から回し直す）。

- [ ] **t=0 から** run したか？（途中状態から始めていないか）
- [ ] 完成形を**初期条件に入れていない**か？（三角形・液滴・巻き数・分裂後の 2 つ・双曲の木・√c4・娘タグ）
- [ ] その構造は**測定で現れた**か？（画像の印象でなく数：成長率・S(k)・欠陥・循環・スポット数・purity）
- [ ] Level は **measures**（`assess_level` / `higher_levels`）で判定したか？（自作の成功ゲートで底上げしていないか）
- [ ] 飛ばした Level はないか？（`L4→L7` の間を測ったか）／揃わないなら **partial** と呼んだか？
- [ ] **同じ数学 ≠ 同じもの**：tier（`measured` / `interpretive` / `analogy` / `frontier`）を付けたか？
      （渦線≒宇宙ひも・spots≠life・もつれ→重力＝線形化 は **analogy**。生命語・断定語を使わない）

---

## repo での適用（現状の線引き）

- **Gray-Scott(U,V) だけ = L7-partial**（自己複製・分裂のみ）。
- **遺伝タグ `T` を founder に種付けし、娘が継承（測定で確認）= FULL L7**（分裂＋遺伝）。
  `genesis` に完成パターンを埋めない。継承を **command したら L7 ではない**。
- 同じ線引きを全 Level に適用：**発現は主張してよい／入れ込みは主張しない**。迷ったら partial か frontier に落とす。

> 迷ったときの合言葉：**「それは育ったのか、置いたのか？」**（Did it grow, or did I put it there?）
