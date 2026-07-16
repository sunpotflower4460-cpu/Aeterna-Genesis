# Evidence index (generated — do not edit by hand)

Auto-derived from `experiments/*/experiment.yaml` + `rooms/official/*/emergence.json` by `tools/build_evidence_index.py`. CI (`--check`) fails if this drifts from the sources. The human narrative maps (`docs/TRUST_MAP.md`, `docs/WHITE_CEILINGS.md`) are separate and unchanged.

## Emergence ladder (official Rooms)
| room | white | reached_level | candidate_level |
|---|---|---|---|
| room-g001-a | g001_ginzburg_landau_quench | 2 | 3 |
| room-g002-a | g002_boussinesq_convection | 1 | 3 |
| room-g003-a | g003_model_h_phase_field | 2 | 5 |

## Experiments (46) — role tally: E=23, F=9, N=2, S=7, V=5
| id | role | tier | dim | target_encoded | genesis_role | title |
|---|---|---|---|---|---|---|
| e001 | E | measured | 2D | False | behavior_dictionary | GPE 渦歳差 |
| e002 | E | measured | 2D | False | behavior_dictionary | GPE 二渦 |
| e003 | E | measured | 3D | False | behavior_dictionary | GPE 渦リング |
| e004 | S | analogy | 2D | False | sidebranch_analogy | オクターブ/ホログラフィー |
| e008 | E | measured/interpretive | 2D | False | genesis_candidate | 同時共創発 |
| e009 | F | observed | 2D | False | sidebranch_analogy | 探索（トーラス電流・種成長） |
| e010 | E | measured | 2D | False | genesis_candidate | KZ コヒーレンス長 |
| e011 | E | measured | 2D | False | behavior_dictionary | 欠陥の化学 |
| e012 | E+V | measured | 3D | False | behavior_dictionary | Hopf 安定化（第三） |
| e013 | S+E | measured | 2D | False | genesis_candidate | 器＋中身 |
| e014 | E | measured | graph | False | measurement_tool | 因果→次元 |
| e015 | E | measured | 2D | False | design_hypothesis | 器の閉じ（駆動依存） |
| e016 | F | observed | 3D | True | behavior_dictionary | Hopf basin（√c4 撤回） |
| e017 | V | established | 2D | False | measurement_tool | 壁つき RB |
| e018 | E | measured | 2D | False | design_hypothesis | 膜小胞 |
| e019 | S | measured | 2D | False | design_hypothesis | 結合 |
| e020 | N | measured | 2D | False | negative_constraint | 小胞分裂（負の結果） |
| e021 | E | measured | 2D | False | design_hypothesis | 自己受信 |
| e022 | V | measured | 2D | False | measurement_tool | 地平線台帳 |
| e023 | E | measured | graph | False | measurement_tool | 順序→時空 |
| e024 | F | measured | 1D | False | design_hypothesis | 器のエンジン |
| e025 | S+E | measured | 2D | True | design_hypothesis | 生きた器（三器官／autopoietic） |
| e026 | F | measured | 2D | False | negative_constraint | 分裂会計 |
| e027 | F | measured | 2D | False | sidebranch_analogy | 進化・大転移（エージェント） |
| e028 | E | measured | 2D | False | design_hypothesis | トポロジカル記憶 |
| e029 | F | frontier | 2D | False | design_hypothesis | 共進化・大転移 frontier |
| e030 | F | frontier | 2D | False | design_hypothesis | 分業（群選択） |
| e031 | F | frontier | graph | False | measurement_tool | 因果作用の平滑化 |
| e032 | F | frontier | 3D | False | measurement_tool | 3D DS 病理 |
| e033 | E+V | measured | 2D | False | genesis_candidate | 分業＝場（Cahn-Hilliard） |
| e034 | E+V | measured | 2D | False | behavior_dictionary | 空間協力＝場（Nagumo） |
| e035 | E+V | measured | 2D | False | genesis_candidate | Red Queen＝場（Hopf） |
| e036 | E+V | measured | 2D | False | behavior_dictionary | 適応＝場（replicator-mutator） |
| e037 | E | measured | 2D | False | behavior_dictionary | 生態的 PGG（協力＝場） |
| e038 | E | measured | 2D | False | behavior_dictionary | 連続形質進化（object tracking） |
| e039 | E | measured | 2D | False | behavior_dictionary | 分化（morphogen＋Turing） |
| e040 | E | measured | 2D | False | behavior_dictionary | 協力＝RPS スパイラル |
| e041 | S | measured | 2D | False | design_hypothesis | ボトルネック（幾何） |
| e043 | E | measured | 2D | False | behavior_dictionary | 場の宇宙（6過程統合） |
| e044 | E | measured | 2D | False | behavior_dictionary | 場の統一（協力） |
| e045 | N | measured | 2D | False | negative_constraint | 内生ニッチ（負の結果） |
| e046 | V+N | measured/established | graph | False | measurement_tool | トポロジカル状態容量（独立ホロノミーチャネル=b₁） |
| e047 | V+N | measured/established | 3D | False | measurement_tool | 球→トーラス F1（測定器の固定形状検証＋固定形状での自由エネルギー交差） |
| e048 | V+N | measured | mixed | False | measurement_tool | field/slow-field basin 判定器の校正（P07/F1・置いた既知basin上での測定） |
| e049 | S+N | measured/observed | 2D | False | design_hypothesis | 遅い履歴場による basin 記憶（P07/S1・ON vs matched OFF・2D） |
| e050 | S+N | measured/observed | mixed | False | design_hypothesis | 遅い場 basin 記憶の robustness＋3D昇格（P07/S2・g帯・解像度・seed・2D→3D） |

## Diagnostics modules (10)
`angular_modes`, `corroborate`, `coupled_spectrum`, `gauge_aligned_distance`, `higher_levels`, `measures`, `plaquette_ledger`, `topology3d`, `topology_betti`, `winding_reliability`

