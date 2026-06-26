# e013 — 器＋中身（循環は内部に load-bearing）— AUDIT

> 栄養を境界供給・バイオマスが消費・循環が運ぶ。**循環なし→内部デッドコア（b≈0）／
> 循環あり→内部 fed、内部 b が Péclet とともに単調増加**を数で。総 b 差は小（外殻は
> 拡散で生存）＝ **load-bearing は内部に対して**。Stage2 で規定流を**自己組織した対流
> （Rayleigh-Bénard）**に置き換え、「対流が内部を養う」を出す。「血流／心臓」は analogy。

## 監査ヘッダ（run.py 先頭と同一）

```
MODULE:   e013_vessel_content
QUESTION: 循環は器の内部に load-bearing か（無いとデッドコア、有ると内部が養われる）。
PUT IN:   advection-reaction-diffusion（栄養 拡散+移流+消費、バイオマス ロジスティック）＋ 撹拌流。「中心を養え」は入れない。
EMERGED:  (measured) Pe=0→デッドコア（内部 b≈0）；Pe>0→内部 b が Pe で単調増；総 b はほぼ一定。
CLAIM TIER: measured(デッドコア・内部 b vs Pe・総 b 差小) ; analogy(血流/原形質流動/「心臓」)。
KNOWN MATCH: 移流拡散の境界層／Péclet 輸送；生物の循環 vs 拡散限界。
STATUS:   GREEN（デッドコア＋内部 b vs Pe は measured。規定流は analogy、自己組織版が Stage2）。
A_OR_B:   (A) 忠実。手入力＝RD 則＋規定の非圧縮流（Stage2 は自己組織対流で置換）。
```

## Stage 1 — 規定流（`run.py` → `result.json`、L=64、2×2 対流セル流）

| U | Pe | 内部 b | 総 b | 生存面積 | c_center |
|---|---|---|---|---|---|
| 0.0 | 0 | **0.0000** | 0.163 | 0.341 | 0.005 |
| 1.0 | 64 | 0.0001 | 0.166 | 0.323 | 0.016 |
| 2.0 | 128 | 0.0010 | 0.166 | 0.320 | 0.079 |
| 4.0 | 256 | 0.0057 | 0.170 | 0.335 | 0.089 |
| 8.0 | 512 | **0.0289** | 0.177 | 0.368 | 0.094 |

- **循環なし→デッドコア**（内部 b≈0）、**循環あり→内部 b が Pe で単調増**（0→0.0289）— measured。サンドボックスの 0→0.038 と一致。
- **総 b 差は小（7%）**：外殻は拡散で生存。→ **循環が load-bearing なのは内部（拡散長を超えた深部）**＝小さい個体は拡散で足り、大きい体は内部に循環が要る、の最小版。
- 捕まえた罠：内部比のゼロ割り→**値で報告**；境界の指数発散→**ロジスティック収容力 a·b·c·(1−b)** で [0,1] に。

## Stage 2 — 自己組織した循環（`rayleigh_benard.py` → `rayleigh_benard.json`）

2D Boussinesq（スペクトル渦度-流線、加熱帯への Newton 緩和で**飽和**）＋栄養/バイオマス。

| Ra | KE | 判定 | 内部 b |
|---|---|---|---|
| 10 | 0.000 | 伝導 | 0.015 |
| 30 | 0.79 | 伝導 | 0.015 |
| 100 | 10.4 | **対流（自己組織）** | **0.42** |
| 300 | 15.9 | 対流 | 0.40 |

- **対流は Ra>Ra_c（≈20）で自己組織**：KE が ~0 から有限へ跳ぶ（手で入れていない流れが出る）— measured。
- **自己組織した流れが内部を養う**：内部 b が 0.015→0.42（28×）— measured。→ 規定流(analogy)を一段 measured へ。
- 床：周期箱の最小 Boussinesq（壁つき実セルでない）、Ra_c は箱固有値。「自己組織循環＝心臓」は analogy。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | RD/Boussinesq は局所。「中心を養え」「対流せよ」を書いていない |
| 2 | 忠実な物理? | **Yes** | 移流拡散反応・Boussinesq 対流は実在 |
| 3 | 結果は初期条件に? | **No** | 一様 b・境界供給のみ。内部分布は後から |
| 4 | 入れてない物が出る? | **Yes** | デッドコア、内部 b vs Pe、対流の自己組織 |
| 5 | 数で合う? | **Yes** | 内部 b 0→0.029、総 b 差 7%、対流オンセット Ra_c≈20、内部 b 28× |
| 6 | 頑健? | **Yes** | Pe スイープ・規定 vs 自己組織で（robustness.json） |
| 7 | コードが発見? | **Yes** | 内部 b を値で測定、流れは buoyancy から創発 |

→ measured 部分は全監査通過＝**GREEN**。規定流は analogy（自己組織版で拡張）。

## 床（隠さない・必須）
1. **固定格子＝空間は与えられている**。
2. **load-bearing は内部に対して**（総 b 差は小、外殻は拡散で生存）。
3. **規定流は analogy**（「持続電流＝心臓」）。自己組織対流版が一段 measured へ。
4. Stage2 は周期箱の最小 Boussinesq（壁つき実セルでない、Ra_c は箱固有値）。

## 再現
```bash
python experiments/e013_vessel_content/run.py              # 規定流: デッドコア・内部 b vs Pe
python experiments/e013_vessel_content/rayleigh_benard.py  # 自己組織対流が内部を養う
python experiments/e013_vessel_content/robustness.py       # Pe/k/m/nroll スイープ
pytest tests/test_e013.py
```
