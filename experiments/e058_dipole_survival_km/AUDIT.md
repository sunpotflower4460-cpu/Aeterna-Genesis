# e058 渦ダイポールepisodeの打ち切り対応生存時間分析（H021キャンペーン反復7・role V/N）

外部監査2件（GPT・別Claude、2026-07-16）が e055/e056 の測定手法に指摘した統計的弱点——「独立 seed 集合の
最大値比較」「観測窓終了時点で束縛中のペアを死亡として扱っている（打ち切りの誤処理）」——を、Observer v2
（`vortex_tracking_v2` のグローバル割当トラッカー＋`dipole_episodes` のフレーム毎 episode 検出＋
`survival_analysis` の Kaplan-Meier）で正しく再測定する。

## 測定結果（full・L=96・τ_Q=200・観測窓1600 step=201 snapshot・20 seed 独立新規範囲）
- **393 episode**（20 seed 合計）を検出。
- **KM 中央値生存時間 = 6 frame**（物理時間 2.4）。
- **制限付き平均生存時間 RMST = 10.39 frame**（tau=89 frame まで）。
- **打ち切り割合 = 3.8%**（393 中 15）——観測窓はほぼ全ての episode の完全な生涯を捉えている。
- 分布の形：短命なもの（1〜数 frame）が大多数、長寿命の裾（20 frame 超が52件、50 frame 超が7件、
  最大89 frame）を持つ。

## 正直な評価
1. **打ち切りはほぼ問題にならなかった**：3.8% という低い打ち切り割合は、e055/e056 が懸念した
   「観測窓が短すぎて死亡と生存を区別できない」という問題が、この観測窓長（baseline の1600 step）では
   実質的に効いていないことを示す。これは Kaplan-Meier で正しく検証して初めて言える——独立 seed 集合の
   最大値比較では分からなかった。
2. **e056 の定性的結論（無限持続の証拠なし）を、正しい統計手法の上で確認**：393件という十分な標本数・
   低打ち切り率のもとで、生存時間分布は有限の中央値（6 frame）と有限の RMST（10.39 frame）を持つ。
   もし真に無限持続する個体が紛れ込んでいれば、打ち切り件数がもっと多いはずだが、そうなっていない。
3. **【重要】v1(e055/e056)との数値差（358 vs 6）は矛盾ではない——測定対象が違う**：
   - v1 の `mutual_neighbor_durations` は「2つのトラックが共存する全期間にわたり相互最近傍であり続けたか」
     を判定する。この設計は、そもそも**ある程度長く共存したトラックペア**にしか適用されない（片方の
     トラックがすぐ消えれば重複期間自体が短く、"duration" として記録されにくい）。
   - v2 の `dipole_episodes` は**フレーム毎**に相互最近傍を判定し、一瞬だけ最近傍になった後すぐ離れる
     ような短命な束縛イベントも**全て**episodeとして数える。
   - 結果、v2 の母集団は v1よりずっと広く（393件 vs e055の10 seedで約170件）、中央値は大きく下がる。
     これは「渦ペアの寿命が実は短かった」という訂正ではなく、**「短命な束縛イベントの方が多数派だが
     v1の設計では見えていなかった」**という、より完全な描像が得られたということ。長寿命の裾
     （20 frame超が52件・最大89 frame）は v1 が見ていた「長く持続するペア」と対応する。

## Discipline
- **role V（secondary N）**：新しい発見というより、e055/e056 の問いを正しい手法で再測定する検証実験。
  定性的結論（無限持続の証拠なし）は e056 と整合するため N も secondary で残す。
- **e055/e056 の元データ・artifact は一切変更していない**（no_touch）。本実験は独立した新規測定
  （新規 seed 範囲2001-2020、e052〜e057 のいずれとも重複なし）。
- **物理は完全凍結・再利用**：e052 と同一の damped GPE KZ クエンチ。新しい propagator は追加していない。
- **8th 監査**：`target_encoded=false`。

## Observer v2 の設計修正（開発中の発見）
`dipole_episodes.detect_episodes` の初期実装は、フレーム毎の運動学的チェック（COM速度と分離ベクトルの
直交性・分離変化率）を**episode継続のハード条件**にしていたが、これは単一ステップの位置決定ノイズに敏感で、
本物の並進ダイポールでも頻繁にepisodeを分断してしまうバグを合成テストでなく実データで発見した。
修正：episode の継続条件は「パートナー同一性＋分離距離の上限」のみとし、運動学的な質（直進性・分離安定性）は
episode全体の要約統計（`straightness`・`mean_sep_rate`・`kinematics_ok`）として報告する設計に変更した。

## 次（H021 キャンペーン 反復8 の候補）
- 3D 渦線計測器（V階層、seeded ring 検証）— PR-C。
- Evidence Contract v2 への Goldstone≠drift 禁止リスト・external_correspondence・hole/torus段階ゲート追記。
- 用語統一（「自走」→「自己形成渦ダイポールの自発並進」）。

## Reproduce
```
python experiments/e058_dipole_survival_km/dipole_survival_km.py            # full（20 seed、約1分）
python experiments/e058_dipole_survival_km/dipole_survival_km.py --quick    # smoke
pytest tests/test_e058_dipole_survival_km.py tests/test_vortex_tracking_v2.py tests/test_dipole_episodes.py tests/test_survival_analysis.py -q
```
