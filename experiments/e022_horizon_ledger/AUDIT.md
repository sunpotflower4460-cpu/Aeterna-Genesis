# e022 — 地平線の台帳（受信としてのループ・DS 分子）— AUDIT

> 受信弧（H009+H010）。**ギャップ（非観測領域）が観測側に渡すのは一つの量子化数だけ**（AB リング）＝受信、
> そして**地平線の台帳＝Dou-Sorkin 分子**がパラメータフリーな数（密度不変・T(β)→π²/6・地平線プロファイル依存）
> であることを測る。二段とも GREEN。**2D は SOLID、3D（2+1）DS 係数は FLOOR**（DS d>2 IR 病理、GREEN に入れない）。
> ゲート名は物理量（spectrum / count）——「エントロピー・受信・地平線」は analogy（docstring/AUDIT）。

## 測定（`--quick` 再現値 ／ サンドボックス正典値）

### Stage1 ab_gap（`results/ab_gap.json`）— ギャップは一つの数を渡す（Aharonov-Bohm）
| 量 | 再現 | 正典（egap0.py） |
|---|---|---|
| ゲージ不変（同一 loop-sum の局所位相 → dE） | **8.9e-16** | ~1e-15 |
| 周期性（Φ vs Φ+1 量子 → dE） | **8.9e-16** | ~1e-15 |
| 局所平坦（基底密度 std、flat=1/N） | **7.5e-16** | ~1e-15 |

GREEN gates: `gauge_invariant` / `periodic_mod_one_quantum` / `locally_flat`。
**罠**: 囲む磁束＝ボンド位相の**loop-sum**（同じ loop-sum の乱れた局所場は同一スペクトル）。

### Stage2 ledger（`results/ledger.json`）— 地平線の台帳＝DS 分子
| 量 | quick 再現 | 正典（egap3a2/elink_bump） |
|---|---|---|
| β-曲線 ⟨n⟩→π²/6（=1.645） | β=1:0.90/16:1.73（T(β) を追従） | T(1)=1.063・T(16)=1.585・π²/6 |
| 密度不変（β=1、ρ=250/1000） | spread **0.067**（<0.15） | 密度非依存の純数 |
| 台帳は w(u,0) のみ読む：flat/spot_on/ridge | **1.0 / 0.655 / 0.655**（spot==ridge） | 0.665==0.667、flat 1.06 |

GREEN gates: `ds_traces_T_beta` / `ds_density_independent` / `ledger_reads_horizon_profile`。
**罠**: DS 数は u,v の独立単調再スケールで不変（β=B/A のみに依存）・密度非依存＝純数。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「一つの数」「密度不変」「T(β)」「w(u,0) のみ」を書いていない。リング/DS 規則のみ |
| 2 | 忠実な物理? | **Yes** | Aharonov-Bohm・Byers-Yang・Dou-Sorkin 分子は実在 |
| 3 | 結果は初期条件に? | **No** | flux/sprinkle は入力だが、不変性・T(β)・プロファイル依存は後から測定 |
| 4 | 入れてない物が出る? | **Yes** | loop-sum のみ通過、密度不変の純数 π²/6、w(u,0) 依存（入れていない） |
| 5 | 数で合う? | **Yes** | 正典を tol 内で再現（上表） |
| 6 | 頑健? | **Yes** | seed 掃引で不変性・密度独立・プロファイル依存は不変（`robustness.json`） |
| 7 | コードが発見? | **Yes** | スペクトル差・DS 数を測定。答えを書き込まない |

→ 二段とも忠実な **measured（2D SOLID）**。GREEN。

## claim tier
- **measured**: AB 受信（ゲージ不変・周期性・平坦）、DS 台帳（密度不変・T(β)→π²/6・地平線プロファイル依存）。
- **interpretive**: ギャップ/地平線は一つの受信数を渡す；地平線のエントロピー台帳は地平線ライン上のプロファイルのみ読む。
- **analogy / KNOWN MATCH**: Aharonov-Bohm、Dou-Sorkin エントロピー分子、π²/6 地平線係数、面積則。

## 床（隠さない・必須）
1. **3D（2+1）DS 係数は DS d>2 IR 病理で FLOOR**（box 依存、GREEN ゲートに入れない）。線形性（面積則）が robust。
   Barton 系分子が cured 版＝frontier。
2. 有限リング（周期は mod 1 量子）。DS β-曲線は多 seed で π²/6 に収束（quick は少 seed で許容 tol）。
3. 「エントロピー/受信/地平線/BH」は analogy（DS 数・loop 数）。**ブラックホールを作ったのではない**。

## 再現
```bash
python experiments/e022_horizon_ledger/ab_gap.py --quick --no-write
python experiments/e022_horizon_ledger/ledger.py --quick --no-write
pytest tests/test_e022.py
```
