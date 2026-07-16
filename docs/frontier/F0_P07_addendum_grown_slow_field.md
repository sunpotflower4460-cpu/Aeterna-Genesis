# F0 追記 — P07「E候補：遅い履歴場 `s` 自体が未分化クエンチから育つか」

> **docs-only 事前追記（F0 addendum）。** 本体 `F0_P07_field_slow_field_basin.md` の §3/§13/§16 で
> **後段送り**にした **E候補**を、実装前に反証可能な形へ凍結する。physics code は追加するが（新実験 e051）、
> schema・既存 experiments・measures.py・rooms/official・app は**触らない**。**実装は本追記の承認後**。
> 前段の到達点：S1=e049（`slow_field_basin_memory_candidate`）、S2=e050（`robust_…`：g帯 onset≈0.3・
> 解像度 L=32/48/64 安定・seed 0.318±0.013・2D→3D 生存 0.257）。いずれも **role S（ψ も s も置く）**。

## 0. なぜ「置いた／育った」がここで本質か
S1/S2 は「遅い場 `s` を**置いて**、その結合で帰還 basin の履歴（hysteresis 過剰）が出る」ことを matched OFF 差で
示した（role S）。北極星は **育ったのか置いたのか**。G001（正式3D Room）は **置いた法則（GL）＋育った構造（渦線）**
＝E の Genesis 基準。本追記の問いは同じ基準を **記憶場そのもの**へ当てる：

> **記憶を担う `s` の空間構造は、我々が置いたテンプレートなのか、未分化クエンチ（`s(t=0)=0`）から育ったのか。
> 育った `s` だけで、matched OFF を超える帰還 basin の履歴（hysteresis 過剰）が出るか。**

法則（fast/slow 双方向局所結合）は G001 の GL と同様に**置く**。争点は **s の構造（記憶を担うパターン）が育つか**。

## 1. 中心問い（測定可能な一文・実装前に凍結）
同一の局所法則の下で `s(t=0)=0`（構造ゼロ・未分化）から出発し、`s` の構造を `|ψ|²` の履歴から**自己組織**させた
とき、`g>0` の hysteresis 面積が matched `g=0` OFF を前登録マージン超で上回り、かつその `s` が
**瞬時 `|ψ|²` のコピーでない（履歴 lag を持つ）**か。

## 2. 条件（他を完全一致させた3系＋育ち計量）
すべて同一格子・同一 seed・同一掃引 schedule・同一 dt・同一 step 数。
| ID | g | s の初期 | 意味 | role 的位置 |
|---|---|---|---|---|
| **OFF** | 0 | s 受動 | hysteresis 基準（掃引率・臨界緩和 confound） | 対照 |
| **grown** | >0 | **s(t=0)=0（未分化）**、`|ψ|²` 履歴から育つ | **E候補**：置かない記憶場 | E候補 |
| **placed** | >0 | s(t=0)=秩序 well を直接偏らせる**構造テンプレート** | 「置いた」参照 | role S template |

- **育ち計量** `struct(s)` ＝ `s` の空間構造（`std(s)` と勾配エネルギー `mean(|∇s|²)`）。
  grown は `struct(s;t=0)=0` → 成長。placed は `struct(s;t=0)>0`。**「s(t=0)=0 は最強の“育った”主張（s に何も置かない）」**。
- **記憶量**：`excess_grown = area(grown) − area(OFF)`、`excess_placed = area(placed) − area(OFF)`。
- **非コピー（履歴）check**：`s` と瞬時 `|ψ|²` の平均二乗差（lag）が前登録床超なら「現在のコピーでない＝履歴」。

## 3. 反証可能な予測（実装前）
- **E1**：`excess_grown > MARGIN`（`s(t=0)=0` から育った記憶で basin 履歴が出る）。
- **E2**：`|excess_grown − excess_placed|` が小 or grown ≳ 一定割合 → 育った s は置いたテンプレの弱い影ではない。
- **E3**：`struct(s;grown)` が t=0 の 0 から有意に成長（記憶パターンが育った直接証拠）。
- **E4（履歴）**：grown の `s` が瞬時 `|ψ|²` と lag を持つ（copy collapse でない）。

## 4. 分類（成功/失敗を実装前に固定）
- **`grown_slow_field_memory_candidate`（E候補）**：E1∧E3∧E4 かつ OFF excess≈0。→ **育った記憶場**の候補。
- **`placed_template_required`（S に留まる）**：`excess_grown ≤ MARGIN` かつ `excess_placed > MARGIN`。
  記憶は s を**置いた**ときだけ → 創発でない → role S。
- **`common_attractor`（null）**：grown も OFF も同じ hysteresis（差なし）→ basin 選択なし。
- **`memory_copy_collapse`**：E4 不成立（s≈瞬時 |ψ|²）→ 履歴でない。
- **`energy_instability` / `numerical_failure`**：総エネルギー非有界・非有限。

## 5. PUT IN / NOT PUT IN
**PUT IN**：fast/slow 2場と局所法則（e049/e050 と同一）、周期境界、`s(t=0)=0`（grown）／構造テンプレ（placed 参照のみ）、
環境 `g`・`τ`・`Ds`、数値法、seed、掃引 schedule。
**NOT PUT IN（grown 系）**：`s` への目標巻き・目標欠陥・basin テンプレート・回復コマンド・runtime 介入・oracle・
結果依存の停止。**grown 系の `s` には一切の構造を置かない（t=0 で厳密に 0）。**

## 6. 育ったのか置いたのか（第一監査）／関係したのか同じ attractor へ崩れただけか（第二監査）
1. **育った**：grown 系は `s(t=0)=0`。記憶を担う `s` 構造は `struct(s)` の 0→有意成長で示す（§3 E3）。placed 参照は
   同じ効果が**置いても**出ることの上限で、grown がその影でないことを `excess_grown/excess_placed` で示す。
2. **関係した vs 同じ attractor**：matched `g=0` OFF が唯一の判別器。`excess_grown` は必ず **ON−OFF 差**。
   OFF と分離しなければ `common_attractor`（null）で不支持。
3. **履歴か現在のコピーか（第三監査）**：§3 E4 の lag check。

## 7. no-touch / 実施
`genesis/diagnostics/measures.py`・`rooms/official/**`・既存 `experiments/**`・`schemas/**`・`genesis/registry/**`・
`docs/TRUST_MAP.md`・`docs/WHITE_CEILINGS.md`・app は不変。**新規実験 e051 と test と CI 行の追加のみ**、
継続性ガバナンス（evidence_index / result_integrity）は規定どおり再生成。
**role は結果を見てから確定**：E候補ゲート（§4）を通れば primary E・confidence C（候補）・target_encoded=false、
通らなければ honest に role S（`placed_template_required`）で記録。**成功 run だけ残さない・失敗も台帳へ。**

## 8. 次元
2D を主測定、`s(t=0)=0` grown の記憶が **3D でも出るか**を1点確認（e050 の次元非依存 `_lap` を再利用）。

**役割**: preregistration 追記（F0 addendum）／**実装**: e051（本追記承認後）／**採番**: e051（既存 e050 の次）／
**repo 変更**: docs 1ファイル（本書）＝先行、その後 e051。
