# Free Hypothesis Lab — latest

これは **Pure/strict evidence ではありません**。大胆な介入から、strict側で試す次の問いを発見する sandbox です。

## 1. 急冷速度だけで探索統計は再現可能に変わるか
- provenance: `DRIVEN_EXPLORATORY`
- rationale: fast_quench runner は一般的な exploratory quench 比較を実行し、X fingerprint 判定や slow-side paired X holdout は行わない。したがって以前の X-c41277c11b 固有の問いをこの lane の結果で検証したとは扱わず、ここでは quench-timescale の抽象的 stress test に限定する。X 固有の future-seed paired holdout は X-mechanism lane に残す。
- orientation priority: 2.06166
- strictへ戻す問い: strictな一様開始のまま急冷速度だけで未知遷移の頻度が変わるか
- strict evidenceに数える: **NO**

## 2. 円ではなく楕円形の0領域にする
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 円で差が出ても円固有なのか異方性/有限サイズなのかを分解する
- orientation priority: 0.449465
- strictへ戻す問い: 特定形状を置かず、異方的な有限サイズ制約だけでも同じ差が残るか
- strict evidenceに数える: **NO**

## 3. 0が存在できる場所そのものを丸くしたら何が変わるか
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 三角形が分離に特別とは限らないため、個々の形ではなく全体系の境界曲率・閉じ込めが効く可能性を探索する。
- orientation priority: 0.385527
- strictへ戻す問い: 円を置かず、境界曲率や有限サイズだけが変化境界を支配するかをランダム境界ensembleで確認する
- strict evidenceに数える: **NO**

## 4. 途中で一度だけランダムな場所へエネルギーを入れる
- provenance: `DRIVEN_EXPLORATORY`
- rationale: 静的配置ではなく摂動への応答性そのものを調べる
- orientation priority: 0.224511
- strictへ戻す問い: 外部キックなしでも内部揺らぎへの応答・修復・分岐の同じ統計が現れるか
- strict evidenceに数える: **NO**

## 5. 非常にゆっくり環境を変える
- provenance: `DRIVEN_EXPLORATORY`
- rationale: 時間を与えること自体が重要か、quench速度が重要かを切り分ける
- orientation priority: 0.159087
- strictへ戻す問い: strictな一様開始のままquench時定数だけを変えた時にも同じ遷移が残るか
- strict evidenceに数える: **NO**

## 6. 0全体へ一様に追加エネルギーを与える
- provenance: `DRIVEN_EXPLORATORY`
- rationale: 局所エネルギー配置と関係崩壊の対応が一定しないため、まず総量と局在を分離する
- orientation priority: 0.113295
- strictへ戻す問い: 形を与えず初期揺らぎのエネルギー尺度だけを変えると同じ変化境界が現れるか
- strict evidenceに数える: **NO**

## 7. リング状のエネルギー界面は関係網の形成や分岐を変えるか
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 局所エネルギー偏りと幾何崩壊の時間順序が一定していないため、総量と空間配置を大胆に分離してみる。
- orientation priority: 0.101102
- strictへ戻す問い: リング形状を置かず、曲率を持つ界面が自発形成した場合にも同じ変化が起きるか
- strict evidenceに数える: **NO**

## 8. 0へ周期的に環境エネルギーを与えたら内部時間尺度と共鳴するか
- provenance: `DRIVEN_EXPLORATORY`
- rationale: Deep-Timeで短時間には見えない変化が出るため、時間尺度そのものが機構の手掛かりかもしれない。
- orientation priority: 0.046098
- strictへ戻す問い: 外部周期を置かず、内部時定数の比だけで同様の周期・分岐が自発するか
- strict evidenceに数える: **NO**
