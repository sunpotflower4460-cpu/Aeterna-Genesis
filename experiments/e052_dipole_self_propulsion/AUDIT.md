# e052 自己形成 ±渦ダイポールの Level 3 自走（H021 キャンペーン 反復1・role F/frontier candidate）

`docs/working_ledger/H021_frontier_campaign_0_to_far.md` の最初の一手。北極星「0から最も遠くに行く」を、
単一連続 t=0 run で **Level 3**（EMERGENCE_LEVELS.md：`com_velocity≠0 AND circulation≠0`・非 seeded）まで
届くかを測る。e002（PLACED ±渦ペアは GPE 局所法則だけで並進する、role E/analogy）に対し、本実験は
**ペア自体を置かない**——一様+ノイズの Level 0 IC から Kibble-Zurek クエンチで自然発生した渦が、周囲の
欠陥タングルの中で識別可能な dipole 並進として生き残るか、という別の・まだ測っていない問い。

## 物理は 100% 再利用（新しい propagator を足さない）
`core.field.step_damped_2d` と e010 と同一の KZ クエンチレシピ（μ ランプ→hold→追加発展）をそのまま使用。
新規はクエンチ後に `core.vortex.find_vortices` で渦位置をスナップショットし、新しい観測器
`genesis/diagnostics/level3_motion.py`（**measures.py 非touch**・LT-1/2/3 と同じ「observers を足す、
物理を足さない」パターン）で frame-to-frame 追跡・dipole 判定するだけ。

## 観測器の設計（level3_motion.py）と、途中で見つけた設計ミスの記録
最初の設計は「ミスマッチな ± ペアリングを shuffle null にする」だったが、合成テストで**汚染バグ**を発見：
真のダイポールの片方のメンバーが別のミスマッチペアにも登場すると、その COM 速度に本物の信号が漏れ込み、
null 分布を人為的に押し上げてしまう（少数欠陥ほど深刻）。**修正**：null を「全トラックの単発ステップ幅の
中央値」（母集団統計・特定ペアに汚染されにくい）と「n ステップのランダムウォークが期待する直進性 1/√n」
という 2 つの自己較正床に置き換えた。3 つの合成シナリオ（真のダイポール／箱全体の一様ドリフト／純ジッター、
デコイ20対）で判別を確認（`tests/test_level3_motion.py`）：一様ドリフトは「床も一緒に上がる」ため正しく
非判定になる（数値ドリフトを個体の自走と誤認しない）。

## 測定結果（full・6 seed）
| seed | L1/L2 | Level3 | candidates | verdict | best mean_sep | best straightness | v_snapshot | v_phys(=/0.4) | v_theory=1/(2d) | 比 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | **True** | 6 | level3_dipole_candidate | 2.71 | 0.535 | 0.0548 | 0.137 | 0.184 | 0.74 |
| 2 | 2 | False | 8 | not_separated_from_jitter_floor | – | – | – | – | – | – |
| 3 | 2 | **True** | 7 | level3_dipole_candidate | 3.48 | 0.672 | 0.0668 | 0.167 | 0.144 | 1.16 |
| 4 | 2 | False | 7 | not_separated_from_jitter_floor | – | – | – | – | – | – |
| 5 | 2 | **True** | 10 | level3_dipole_candidate | 2.39 | 0.650 | 0.0919 | 0.230 | 0.209 | 1.10 |
| 6 | 2 | False | 4 | not_separated_from_jitter_floor | – | – | – | – | – | – |

**6 seed 中 3 seed が Level 3 に到達**（`level3_dipole_survives_in_budget`）。全 6 seed が Level 2 には到達
（L2 天井を再確認しつつ、一部で Level 3 へ抜けた）。

## 正直な評価（なぜ role F・confidence C か）
1. **物理的妥当性のシグナルは強い**：3 つの候補すべてで観測並進速度が点渦誘導速度 `v ~ 1/(2d)` と**同じ桁・
   同じ 1/d 傾向**（比 0.74〜1.16、格子離散化・damping・多体背景を考えれば妥当な散らばり）。これは
   level3_motion.py が本物の渦ペア力学を捉えている、独立した物理的裏付け。
2. **しかし統計的に薄い**：jitter 床超過はどの候補も約 **10〜12%**（margin=3× のうち僅かに超過）で、
   seed 依存性も強い（6中3）。**e049(S1)→e050(S2) と同じパターンでロバスト性検証が必要**——単発の
   candidate を「Level 3 到達」と確定させない。
3. **育ったのか置いたのか**：完全に育った（`seeded_structure: false`、渦もペアも IC に置いていない、クエンチ
   法則・ノイズ振幅のみが「入れたもの」）。
4. **8th 監査**：`target_encoded: false`（ペア/運動の目標なし、測定は事後の追跡のみ）。`role primary=F` は
   `{E,V}` に含まれないため 8th-audit 制約に抵触しない。

## Discipline
- **no_touch**：`genesis/diagnostics/measures.py`・`rooms/official/**`・既存 experiments/schema/registry
  不変。新しい観測器は別ファイル。
- **Level N+1 を足さない**：本実験は e010 の run を改造していない——**新しい L0 run**（同じ法則、独立 seed）
  を追加発展させてクエンチ後も観測を続けているだけ。
- **失敗も資産**：3/6 seed は honest に「not_separated_from_jitter_floor」と記録（隠さない）。

## 次（H021 キャンペーン 反復2 の候補）
- seed 数を増やし統計を固める（S2 スタイル robustness）。
- track_every・persist_min・margin の感度解析（結果依存で変えない——次回は事前に凍結してから）。
- 3D 昇格（e050 パターンを踏襲）。
- 別の quench 速度 τ_Q での再現性。

## Reproduce
```
python experiments/e052_dipole_self_propulsion/dipole_self_propulsion.py            # full（6 seed、約17秒）
python experiments/e052_dipole_self_propulsion/dipole_self_propulsion.py --quick    # smoke
pytest tests/test_level3_motion.py tests/test_e052_dipole_self_propulsion.py -q
```
