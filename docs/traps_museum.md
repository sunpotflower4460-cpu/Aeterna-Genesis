# traps_museum.md — 失敗の博物館（堂々巡り防止）

> **これは何か**：踏んだ罠・死んだ筋・撤回した主張を、**理由ごと**残す。AI が「0 から大量に試す」とき、
> ここを先に読めば同じ穴に落ちない。**失敗を隠すと堂々巡りになる**——だから失敗こそ資産。
> 各項目は「何をやったら / 何が起きたか / なぜ罠か / 回避」。
>
> 併読：[`PIECES.md`](PIECES.md)（tier 付き成果）、[`honest_floors.md`](honest_floors.md)（原理的な床）、
> 各実験の `AUDIT.md` / `results/`。

## 分類

- **第8監査違反**（完成形を始原条件に埋め込んだ）＝一番危険。measured に見えて target_encoded。
- **数値の罠**（積分器・clip・格子・スペクトル）＝擬似的な結果を作る。
- **測定の罠**（飽和・非厳密な次元・材料削り）＝スコア/指標が現象を測れていない。
- **概念の罠**（同じ数学≠同じもの・imposed≠emergent）＝ honest_floors と地続き。

---

## 第8監査違反（target_encoded — 完成形の埋め込み）

- **T-√c4：`size = k√c4` のホップサイズ則（撤回）** — L* ∝ √c4 を主張したが、**start に √c4 を埋め込み**
  かつ流れが未収束だった。decoupling すると √c4 依存が消え、CV も悪化。→ **GREEN 剥奪・role F**。
  真の start 非依存 L* は frontier（`H001`）。**教訓**：スケール則を主張する前に、その量を IC に入れて
  いないか・収束しているかを必ず確認。
- **T-dim2：C3「dim=2」の種埋め込み** — 2-cell 構成で corr_dim≈2 が出たが `q1_target_in_IC=true`＝
  完成形（目標の 2-cell 構造）を種に入れていた。**幾何の主張にできない**。回避：IC は種・ノイズ・対称のみ。
- **T-oracle：e025 の oracle 判定** — 成否を外部 oracle で決めていた（role 降格）。回避：判定は測定量から。
- **T-e030：分業ゲートの判別力不足** — ゲートが条件を選り分けていなかった。回避：ゲートに判別力テスト。
- **T-e016 √c4（上と同根）** — size 則の GREEN を撤回、role F。

## 数値の罠

- **T-euler：forward Euler dt=0.05 で不安定** — 陽的オイラーは剛性項で発散。回避：spectral ETD /
  半陰的 / integrating-factor（`ginzburg_landau`, `model_h` はこれ）。
- **T-clip-m：F3 の m を 0.3→0.95 に clip** — clip が結果（0.85–1.0 張り付き）を作った。**clip が測定を作る**。
  回避：clip なしで測る、clip するなら床として明記。
- **T-ch-clip：Cahn–Hilliard の clip（e033）** — 同上、φ の clip が相分離を偽装。回避：保存形で解く。
- **T-readbit：e028 の read-bit が 0→+1 に化ける** — 読み出しビットが副作用で立つ。回避：read は非破壊、
  read-miss は明示的 fallback。
- **T-kgrid：k-grid の離散化アーティファクト** — スペクトルのビン化で偽ピーク。回避：radial binning を検証。
- **T-440：Bénard の spin-up を 440Hz 的に駆動** — 駆動周波数が結果に化ける。回避：onset は静的に測る。
- **T-factor2：factor-of-2 の取り違え（0.49 vs 0.25）** — 規格化/半分の取り違いで係数が 2 倍ずれる。
  回避：解析極限（既知係数）と突き合わせる。

## 測定の罠

- **T-entropy-sat：複雑さ窓の entropy が 1.0 に飽和** — 素朴な正規化エントロピーは多くの run で 1.0 に
  張り付き、**ランキング信号を殺す**。回避：ai_lab のスコアは**非飽和な complexity measure**
  （参加率 / 構造因子のスペクトル集中度 / 有効モード数）を使い、run 間で分散が残ることをテストで担保。
- **T-crumple2：crumple 膜の「2-cell が 2D」** — 2-cell 構成が d を 2 に張り付ける副作用。measured-negative。
  回避：幾何主張は CDT/因果次元など独立手法で。
- **T-furrow：furrow が材料を削る** — 分裂の furrow 近似が質量を 2.5–6.7% 削る、noisy。回避：保存形、
  削りを床として明記（Lv7 は入口まで）。
- **T-ds002：d_s=0.02 の異常値** — スペクトル次元推定が壊れた領域。回避：戻り確率のフィット窓を検証。
- **T-BD-raw：生の Benincasa–Dowker が揺らぐ** — smeared BD が要る。回避：平滑化 BD（frontier）。
- **T-transperc：transitive percolation → 1D に潰れる** — 有向浸透が 1 次元的に縮退。回避：次元を独立に測る。
- **T-e027std：多様性 index が std→7.7 で暴れる** — 恣意的 index。回避：index は測定に基づき、role F 明記。

## 概念の罠（→ honest_floors と地続き）

- **T-samemath：「同じ数学」を「同じもの」と読む** — メキシカンハット＝Higgs の数学、渦線≒宇宙ひも、
  もつれ→重力＝線形化 Einstein。**数学の一致は analogy であって本物ではない**。回避：tier=analogy 固定。
- **T-imposed：imposed を emergent と呼ぶ** — CDT は因果性を imposed、E3 の適応度地形は imposed。
  回避：入れたものは「入れた」と書く（床）。
- **T-sandbox：サンドボックス測定を repo の measured と混同** — P 群（AB リング等）は別チャット。
  回避：repo アンカーの無い measured は frontier 扱い、再現をこのリポジトリで取る。
- **T-hyperbolic：e004 の手作り双曲木** — 双曲構造を手で作って「出た」と言いかけた。回避：構造は結果として測る。
- **T-active-knife：active droplet の自発分裂が knife-edge** — uniform 供給だと分裂条件が刃の上、robust でない。
  回避：frontier 明記、robust 窓を探す（それ自体が探索課題）。

---

## この博物館の使い方

- ai_lab に IC family を振らせる前に、その family が **T-dim2 / T-√c4** のように完成形を埋めていないか確認。
- スコアを設計するとき **T-entropy-sat** を必ず思い出す（飽和しない measure・分散テスト）。
- measured を主張する前に **T-imposed / T-samemath / T-sandbox** を通す。
- 新しい失敗を踏んだら、**理由ごとここに追記**（`docs/working_ledger/_archive/` の死んだ筋ともリンク）。
