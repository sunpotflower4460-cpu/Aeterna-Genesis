# Free Hypothesis Lab — latest

これは **Pure/strict evidence ではありません**。大胆な介入から、strict側で試す次の問いを発見する sandbox です。

## 1. 急激に環境を変える
- provenance: `DRIVEN_EXPLORATORY`
- rationale: slow対照として急冷側も同時に置く
- orientation priority: 2.033317
- strictへ戻す問い: strictな一様開始のまま急冷速度だけで未知遷移の頻度が変わるか
- strict evidenceに数える: **NO**

## 2. 中心と外側でquench速度を変える
- provenance: `SPATIALLY_DRIVEN_EXPLORATORY`
- rationale: 条件依存Xがあるため、同じ平均条件でも空間的不均一で遷移がどう変わるかを見る
- orientation priority: 0.276117
- strictへ戻す問い: 空間パターンを指定せず、局所時定数の不均一だけで同様の組織化が起こるか
- strict evidenceに数える: **NO**

## 3. 円ではなく楕円形の0領域にする
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 円で差が出ても円固有なのか異方性/有限サイズなのかを分解する
- orientation priority: 0.27449
- strictへ戻す問い: 特定形状を置かず、異方的な有限サイズ制約だけでも同じ差が残るか
- strict evidenceに数える: **NO**

## 4. 0が存在できる場所そのものを丸くしたら何が変わるか
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 三角形が分離に特別とは限らないため、個々の形ではなく全体系の境界曲率・閉じ込めが効く可能性を探索する。
- orientation priority: 0.210147
- strictへ戻す問い: 円を置かず、境界曲率や有限サイズだけが変化境界を支配するかをランダム境界ensembleで確認する
- strict evidenceに数える: **NO**

## 5. リング状のエネルギー界面は関係網の形成や分岐を変えるか
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 局所エネルギー偏りと幾何崩壊の時間順序が一定していないため、総量と空間配置を大胆に分離してみる。
- orientation priority: 0.109509
- strictへ戻す問い: リング形状を置かず、曲率を持つ界面が自発形成した場合にも同じ変化が起きるか
- strict evidenceに数える: **NO**

## 6. 0の中心へ局所エネルギーを一度だけ入れる
- provenance: `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- rationale: 局所集中が名無し遷移の引き金になるかを大胆に探索する
- orientation priority: 0.096062
- strictへ戻す問い: 中心位置を指定せずランダムな局所エネルギー集中でも同じ機構が現れるか
- strict evidenceに数える: **NO**

## 7. 非常にゆっくり環境を変える
- provenance: `DRIVEN_EXPLORATORY`
- rationale: 時間を与えること自体が重要か、quench速度が重要かを切り分ける
- orientation priority: 0.000122
- strictへ戻す問い: strictな一様開始のままquench時定数だけを変えた時にも同じ遷移が残るか
- strict evidenceに数える: **NO**

## 8. 0へ周期的に環境エネルギーを与えたら内部時間尺度と共鳴するか
- provenance: `DRIVEN_EXPLORATORY`
- rationale: Deep-Timeで短時間には見えない変化が出るため、時間尺度そのものが機構の手掛かりかもしれない。
- orientation priority: 4e-06
- strictへ戻す問い: 外部周期を置かず、内部時定数の比だけで同様の周期・分岐が自発するか
- strict evidenceに数える: **NO**
