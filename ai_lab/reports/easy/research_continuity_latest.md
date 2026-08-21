# Research Continuity — read before changing direction

latest strict burst: `dream-20260821-0340`
continuity digest: `5c536c19f6708c563ef4`

過去の重要点を次の研究へ渡す handoff です。元の証拠を置き換えません。

## Must carry forward

- `geometry:triangle-vs-control-separation` [strict-geometry] — 三角形を特別扱いせず対照と比較し続ける。 triangle=0/2, control=17/18, triangle_required=False.
- `energy:vertex-asymmetry-vs-geometry` [strict-local-energy] — 局所エネルギーは幾何で関係を選んだ後に測る。 pairs=29, pair-only=24, triads=22, split-asym=None, no-split-asym=0.161709, energy-before-geometry=0. 因果・力・結合エネルギーとはまだ呼ばない。
- `deep:deep-ee841262151c` [strict-deep-time] — Deep-Time deep-ee841262151c: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `deep:deep-eddd2955c6d8` [strict-deep-time] — Deep-Time deep-eddd2955c6d8: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `deep:deep-e873384a7436` [strict-deep-time] — Deep-Time deep-e873384a7436: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `deep:deep-e70934626453` [strict-deep-time] — Deep-Time deep-e70934626453: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `deep:deep-e62530140130` [strict-deep-time] — Deep-Time deep-e62530140130: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `deep:deep-df9ab0a1047a` [strict-deep-time] — Deep-Time deep-df9ab0a1047a: status=F7_OBSERVED, effective F=7, prefix=MATCH, long-lived=False, transition=True. 同じt=0/prefix監査を優先し、低いraw depthだけを物理的退行と解釈しない。
- `crossworld:shadow-semantics` [cross-world-shadow] — Cross-Worldの共通fingerprintは同じ物理・保存則・普遍法則を意味しない。start purityと再現性を別に監査する。
- `ops:instrument:predictive-holdout` [research-operations] — 繰り返し環境と未経験環境を分け、過去依存が単なる残響ではなく将来の応答改善に使われるか？
- `ops:instrument:metric-from-relations` [research-operations] — 座標なしの関係だけから、再現性のある距離・近傍・次元候補を後付けで定義できるか？
- `ops:instrument:lineage-accounting` [research-operations] — 持続する一個体が二つへ分かれた場合に、量の収支と特徴の継承を追えるか？
- `ops:instrument:identity-continuity` [research-operations] — 構成要素が動いても同じまとまりと言える量を、結果形状を使わず定義できるか？
- `ops:instrument:growth-accounting` [research-operations] — 外部から一様な供給だけを与えた補助実験で、形を指定せず成長・分化・収支が同時に起きるか？
- `ops:instrument:damage-recovery` [research-operations] — 自然にできたまとまりを後から部分的に乱したとき、同じ統計的個性へ戻るか？
- `x:X-fa3969eebd` [strict/open-ended-followup] — X-fa3969eebd: status=REPEATED_SPECIFIC_CANDIDATE; same=9/19, nearby=?, control=0/19. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-f023a067af` [strict/open-ended-followup] — X-f023a067af: status=REPEATED_SPECIFIC_CANDIDATE; same=8/17, nearby=?, control=0/17. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-e64f84a189` [strict/open-ended-followup] — X-e64f84a189: status=REPEATED_SPECIFIC_CANDIDATE; same=8/8, nearby=?, control=0/8. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-deea6a8f25` [strict/open-ended-followup] — X-deea6a8f25: status=REPEATED_SPECIFIC_CANDIDATE; same=5/18, nearby=?, control=0/18. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-dcc459d23a` [strict/open-ended-followup] — X-dcc459d23a: status=REPEATED_SPECIFIC_CANDIDATE; same=34/43, nearby=?, control=0/43. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-d7d980689e` [strict/open-ended-followup] — X-d7d980689e: status=REPEATED_SPECIFIC_CANDIDATE; same=4/7, nearby=?, control=0/7. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-a428f23471` [strict/open-ended-followup] — X-a428f23471: status=REPEATED_SPECIFIC_CANDIDATE; same=2/5, nearby=?, control=0/5. 回数だけでなく、何を変えると消えるかを追う。
- `x:X-8df32b076a` [strict/open-ended-followup] — X-8df32b076a: status=REPEATED_SPECIFIC_CANDIDATE; same=2/4, nearby=?, control=0/4. 回数だけでなく、何を変えると消えるかを追う。
- `x-mechanism:X-b991d59a4d` [x-mechanism-exploratory] — 平均振幅で正規化したときXの特徴が消えるかを別seed・別介入で反証し、単純な増幅を未知構造と誤認していないか確認する。
- `relation-instrument:identity-continuity` [pure-genesis-relation-instruments] — 結果形状やnode IDを使わず追った関係構造は、time-shuffle対照より長く同一候補として持続するか？ fresh law/sizeと観測閾値holdoutでleadを壊しに行く。
- `science-direction:science-turing-spatial-control-analogy` [science-bridge/free-hypothesis] — If the local control timescale varies smoothly in space, does anonymous organization change in a reproducible way?
- `science-direction:science-kzm-slow-quench-analogy` [science-bridge/free-hypothesis] — Do slower environmental changes alter defect and anonymous-transition statistics?
- `science-direction:science-kzm-fast-quench-analogy` [science-bridge/free-hypothesis] — Do faster environmental changes alter defect and anonymous-transition statistics in the opposite regime?
- `science-direction:science-active-droplet-local-supply-analogy` [science-bridge/free-hypothesis] — Does a localized supply of field amplitude create a later growth-to-instability sequence rather than merely a larger static structure?
- `free:fast_quench` [free-hypothesis] — strictな一様開始のまま急冷速度だけで未知遷移の頻度が変わるか
- `science:doi:10.1146/annurev-conmatphys-031214-014710` [science-bridge] — 既存科学の文脈: Motility-Induced Phase Separation — Persistent self-driven motion can itself generate phase separation even without ordinary attractive interactions.. 論文の主張はAeternaの証拠ではなく、反証可能な実験の材料としてのみ使う。
- `science:doi:10.1098/rstb.1952.0012` [science-bridge] — 既存科学の文脈: The Chemical Basis of Morphogenesis — A spatially homogeneous state can become unstable and develop structure through reaction and transport, with small disturbances acting as triggers.. 論文の主張はAeternaの証拠ではなく、反証可能な実験の材料としてのみ使う。
- `science:doi:10.1038/s41467-026-69940-w` [science-bridge] — 既存科学の文脈: Kibble-Zurek mechanism and beyond in a holographic superfluid disk — Crossing a continuous transition at finite rate connects quench timescales to spontaneous symmetry breaking and topological-defect production.. 論文の主張はAeternaの証拠ではなく、反証可能な実験の材料としてのみ使う。
- `science:doi:10.1038/nphys3984` [science-bridge] — 既存科学の文脈: Growth and division of active droplets provides a model for protocells — A chemically driven material supply can make droplets grow until shape instabilities produce division-like daughter droplets.. 論文の主張はAeternaの証拠ではなく、反証可能な実験の材料としてのみ使う。
- `relation-instrument:metric-from-relations` [pure-genesis-relation-instruments] — 関係だけから得た距離・近傍・次元候補は、匿名label置換・relation rewire・holdoutを越えて残るか？ 現在は測定可能だがleadなし。負の結果を保ち、別law/sizeで探索する。
- `relation-instrument:lineage-accounting` [pure-genesis-relation-instruments] — 持続した親候補の後に持続する2候補が現れ、親→娘の構造収支が無関係pair対照を上回るか？ 現在は測定可能だがleadなし。負の結果を保ち、別law/sizeで探索する。

## Integrity

- Free Hypothesis / Science Bridge は strict-zero evidence に混ぜない。
- 反証・0/3再現・WEAKENED・長寿命だが進まない状態も捨てない。
- Deep-Time の低い raw depth を監査なしに物理的退行と解釈しない。
- 詳細な根拠は Research Memory / immutable manifest / Git history を参照する。

## Handoff coverage

1つの研究系統だけでworking handoffを埋めないための表示です。全履歴は `lessons` と元ledgerに残ります。

- `cross-world`: 1
- `free-hypothesis`: 1
- `relation-instruments`: 3
- `research-operations`: 6
- `science-bridge`: 8
- `strict-deep-time`: 6
- `strict-geometry`: 1
- `strict-local-energy`: 1
- `unknown-x`: 8
- `x-mechanism`: 1

manifest relation: `MATCH`
