# Emergent Field Frontier — 一様場から何が育つかを試す自動探索

## 目的

Adaptive Dream の通常 burst で、既存の Gray-Scott 局所反応拡散則を使い、**空間的に一様な背景 + 微小な非構造ノイズ**だけから時刻 0 で開始する小さな探索レーンを常時回す。

問いは次の一つ。

> founder spot・node・edge・branch・network を置かずに、均一な場の揺らぎが持続する差・局在・連結した形態へ自然に増幅される条件はあるか。

このレーンは「脳を作る」ものではない。結果が脳・神経・ネットワークに似て見えても、その言葉を物理判定へ使わない。

## 入れているもの

- 既存 `genesis/models/gray_scott.py` の Gray-Scott 方程式
- periodic boundary
- 一様な U/V 背景
- iid のゼロ平均ノイズ
- Gray-Scott の通常パラメータ `Du / Dv / F / k`
- 一様背景量 `v_background`
- ノイズ振幅

探索範囲は `genesis/registry/param_ranges.yaml` の `model_specific.gray_scott_uniform_noise` に固定する。

## 入れていないもの

- founder spot
- Gaussian seed spot
- node / edge / graph
- branch を作る命令
- Hebbian rule
- plasticity
- neuron / brain
- target image similarity
- 欲しい形を生成する reward
- morphology による physics feedback

つまり dynamics は「結果が何に見えるか」を知らない。

## 観測器

`ai_lab/dream/emergent_field.py::observe_morphology` は simulation 完了後だけに動く。

初期ノイズの標準偏差を基準に固定閾値を作り、以下を測る。

- fluctuation gain
- localized region count
- strong core count
- largest region area
- active fraction
- filamentarity proxy
- late field persistence
- corridor candidate count

`corridor candidate` は **「低い閾値で一つにつながった領域の内部に、より高い閾値の独立した core が複数ある」**という幾何学的記述だけを意味する。

これを edge / connection / network と呼ばない。

## 自動探索への接続

`Adaptive Dream v8` に `--emergent-field-trials` を追加した。既定値は 12 なので、production workflow が明示 flag を書かなくても通常 burst で自動実行される。

`strict_goal_loop` はこの値を v8 へ転送し、`production_protocol.py` は値が 0 以下になった場合を production research lane の accidental disable として検出する。

結果は通常実行では:

`ai_lab/reports/easy/emergent_field_latest.json`

へ保存し、v8 report には compact summary だけを埋め込む。

## 探索方法

各 trial の条件は結果を見る前に deterministic Halton sampling で決める。

そのため:

- morphology が出た trial の近くへ自動的に寄ることはまだしない
- network-like な見た目を reward にしない
- negative trial も捨てない

`observation_priority` は人間が結果を見る順番を整理するためだけの値で、scientific score / official Level / promotion gate ではない。

## Pure Genesis R0 との関係

これは Pure Genesis R0 の証拠ではない。

Gray-Scott は最初から:

- 2D 空間
- 局所近傍
- 反応拡散則

を与えているため、R0 より下流の **spatial reference frontier** として扱う。

Pure Genesis R0 の「関係だけから何が育つか」と、このレーンの「既存局所場で一様状態から何が育つか」を並行して観測することに意味がある。

## 次の段階: 局所塑性

今回の実装には plasticity を入れない。

もしこのレーンで、再現性のある局在・持続・複数 core を含む連結領域などが観測された場合のみ、次の問いとして:

> 局所的な flux / reaction history によって局所物性が変化する、現実的な構成則を導入すると何が変わるか。

を検討する。

その場合は既存 Gray-Scott の parameter change ではなく、**`mutation_type: law_variant`** として別監査にする。Hebbian rule や `strengthen_edge(a,b)` のように欲しい意味を直接コードへ入れない。

## 合言葉

> 点を作ったのか、それとも揺らぎから点らしい局在を測ったのか。
>
> 線を引いたのか、それとも局所場が勝手につながったのか。

後者だけを frontier evidence として残す。