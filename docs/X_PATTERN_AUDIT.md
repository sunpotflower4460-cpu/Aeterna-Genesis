# X_PATTERN_AUDIT — 「名無し変化 X-…」は何だったか（P2・2026-09-25）

> 再現：`python tools/audit/xpattern_audit.py --seeds 20 --workers 3`
> 画像：`python tools/audit/xpattern_snapshots.py X-72162ca538 X-dcc459d23a X-6ceabe0fd8 X-29d79aabf4`
> 出力：`audit/xpatterns.jsonl`（1 パターン 1 行・全出現つき）、`audit/xpatterns_summary.json`、`audit/png/`
> 対象：凍結点 `faac01d` の `ai_lab/discoveries/emergence_graph.json`（256 パターン・延べ 40,404 観測）

## 結論（先に）

**監査した範囲では、X パターンに通常の TDGL クエンチ物理を超えるものは見つからなかった。**
延べ観測の **82%** は、次のどれかで説明できた。
- クエンチ後の振幅成長（H3：61.4%）
- 飽和した後の緩和（H3b：9.5%）
- 渦の数の変化（H2：10.4%）
- 渦対の消滅（H1：0.8%）

どれでも説明できない `UNEXPLAINED` は **0 件**。
2026-09 時点の `CURRENT_RESEARCH.md` が「いま一番見るべきもの」として挙げていた X-72162ca538、X-e64f84a189、X-dcc459d23a は、**3 つとも振幅成長（H3）**だった。
bot 自身の `x_mechanisms.json` も、同じ 4 パターンに「振幅スケール追従（AMPLITUDE_SCALE_TRACKING）・渦数変化 0」と判定していた。見出しは、その判定が出た後も更新されていなかった。

claim tier：**measured**（2D quick TDGL・`open_ended._probe` を無改変で使用）。範囲の限界は下の「限界」を参照。

## X パターンとは何か（仕組み）

`ai_lab/dream/open_ended.py` の手順は次のとおり。
1. 2D TDGL クエンチ（48²・quick）の途中で、大域スカラー 11 個を時系列に取る。
   - mean_amp、amp_std、phase_coherence
   - spectral_entropy、spectral_k_rms、spectral_anisotropy
   - gradient_rms、defect_count、net_topological_charge、high_amp_fraction
2. run ごとの 10–90 パーセンタイル幅で規格化したジャンプを求める。
3. 上位 5 成分の「符号＋大きさ（S/M/L）」を並べた文字列の sha256 を ID にする。

「既知」のラベルが付くのは、渦の数が 0↔1 をまたぐときだけ。そのため、次のような**通常の物理は構造上すべて「名無し」になる**。
- 振幅の成長（秩序化）
- 6→4 のような対消滅
- 粗大化

## 方法

- **Stage A（全 256 件・計算なし）**：指紋に含まれる量と向きで分類した。
- **Stage B（199 件・t=0 から再実行）**：`unknown_followups.json` に再現用の始原条件（`search_focus`）があるパターンが対象。
  - それぞれを新しい決定的 seed 20 個で、無改変の `_probe` から回し直した。
  - 対象パターンが出た回ごとに、直前と直後のスナップショットで次のラベルを付けた。

| ラベル | 判定 |
|---|---|
| H1 pair_annihilation | 渦数が偶数だけ減り、正味の位相巻き数は不変 |
| H4 last_defects_vanish | 渦数が 0 になる（有限箱で粗大化が終わる） |
| H2 defect_count_change | その他の渦数変化（奇数の増減＝検出のゆらぎや境界を含む） |
| H3 amplitude_ordering | 渦数は不変。平均振幅が上がり、しかもまだ最終平坦値の 95% 未満 |
| H3b amplitude_relaxation | 渦数は不変。振幅はすでに飽和している（平滑化・緩和） |
| UNEXPLAINED | 上のどれでもない |

- 出現回の 80% 以上を 1 つのラベルが説明すれば、それをパターンの判定とする。そうでなければ MIXED。20 seed で一度も出なければ NOT_REPRODUCED。
- **H6（ビン境界）**：指紋の閾値（0.15／0.35／0.8）を ±10% 動かしても ID が変わらないかを調べた。
- 再実装した指紋関数が、既定の閾値で元の ID と一致することを、出現ごとに assert で確認した。

## 結果

### Stage A：指紋の形（256 件）

| 分類 | パターン数 | 延べ観測 |
|---|---:|---:|
| AMPLITUDE_GROWTH（振幅系の量がすべて＋） | 36 | 24,957 |
| SPECTRAL_REARRANGEMENT（スペクトル系が中心） | 119 | 8,468 |
| DEFECT_GAIN（渦数＋） | 60 | 4,401 |
| CHARGE_CHANGE（正味の巻き数が変わる） | 14 | 1,005 |
| AMPLITUDE_MIXED | 17 | 976 |
| DEFECT_LOSS（渦数−） | 10 | 597 |

### Stage B：再実行による判定（199 件・各 20 seed）

| 判定 | パターン数 | 延べ観測（全体比） |
|---|---:|---:|
| H3 amplitude_ordering | 61 | 24,825（61.4%） |
| H2 defect_count_change | 29 | 4,192（10.4%） |
| H3b amplitude_relaxation | 11 | 3,856（9.5%） |
| H1 pair_annihilation | 3 | 307（0.8%） |
| MIXED（中身は H1/H2/H3/H3b/H4 の混合） | 4 | 414（1.0%） |
| NOT_REPRODUCED（20 seed で一度も出ず） | 91 | 6,009（14.9%） |
| 未検査（再現用の始原条件が無い） | 57 | 801（2.0%） |
| **UNEXPLAINED** | **0** | **0** |

- **H3 の出現時の特徴**（413 回）
  - 直前の平均振幅は、最終平坦値に対して中央値 **0.31**（90 パーセンタイルで 0.72）＝まだ育っている途中。
  - 時刻はクエンチ時間の中央値 **1.41 倍**。
  - つまり「クエンチ後に場がノイズから立ち上がる」瞬間を捉えている。
- **NOT_REPRODUCED の 91 件**
  - 84 件は bot 自身も WEAKENED／VERIFYING としていたもの。
  - 残り 7 件は bot が REPEATED_SPECIFIC_CANDIDATE としていたもの：X-1352a18de1、X-00fec0a70d、X-4d85090b5c、X-113869eb22、X-88394247b7、X-5f268a2c0b、X-d83e71ea67。いずれも指紋は振幅・スペクトル・巻き数の変化で、渦の生成や消滅の範囲に収まる形。
- **ビン境界に弱いもの**：閾値を ±10% 動かすと ID が変わる出現が半数以上あるパターンが **57 件**。見出しの X-e64f84a189 も含む。ID の一部は、物理ではなく量子化の境目の産物である。

### 画像（t=0 から再実行・直前 | 直後）

- `audit/png/X-72162ca538_amp.png`（見出し 1 位）
  - 空間模様はそのままで、全体が明るくなるだけ。
  - 平均 |ψ| は 0.023 → 0.038、渦数は 2 → 2。
- `audit/png/X-dcc459d23a_amp.png`：同じく振幅の立ち上がり。平均 |ψ| は 0.017 → 0.025、渦数は 0 → 0。
- `audit/png/X-6ceabe0fd8_phase.png`：最後の渦が消える（H4）。渦数 1 → 0、正味の巻き数 1 → 0。
- `audit/png/X-29d79aabf4_phase.png`：粗大化の途中の対消滅。渦数 50 → 46、正味の巻き数 0 → 0。

## 限界・弱点

- 2D・quick（48²）の TDGL だけが対象（X の元データがすべてそうなので）。3D や別の白での X は存在しない。
- ラベルは、スナップショット 2 枚の大域量だけで付けている。H1 は位置の追跡をしていないので、「偶数だけ減り、巻き数が保存される」という必要条件での判定になる。
- NOT_REPRODUCED は「20 seed で出なかった」という意味で、「存在しない」ではない。
  - bot の再現率（例：X-72162ca538 は 13/15）とこちらの再現率（12/20）は、同じ手順でおおむね一致している。
  - 出現率が低いパターンは、20 seed では拾えないことがある。
- 57 件は再現用の始原条件が台帳に無いので、Stage A の分類だけ。

## 何を残すか（P3 への申し送り）

- `audit/xpatterns.jsonl` が、全 256 パターンの正本の要約になる（指紋・観測数・分類・判定・全出現の数値）。
- UNEXPLAINED が 0 件なので、「全データを丸ごと保持すべき X」は無い。`emergence_graph.json` と `unknown_followups.json` は凍結点から復元できる。
- 今後 X と同種の検出器を使うなら、「既知」の文脈に次を最初から入れること。
  - 振幅の成長と飽和
  - 渦数の増減（0↔1 以外も）
  - 対消滅
