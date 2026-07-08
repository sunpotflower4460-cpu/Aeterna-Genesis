# H001 — Hopf の真の大域化（arrested-Newton／高解像度で任意初期→L*）

- **状態**: resolved（L=56「劣化」の原因を特定＝**promoted**／κ∝dx⁴ は dead-end／真の大域 basin は frontier 継続）
- **起票者**: Claude Code / 2026-07-01
- **狙う Type**: B（→ 一部 D：真の大域 basin は frontier）
- **依拠する既知事実**: e012 Stage3（完全PDE 自己安定化、Q_H≈1 保持・エネルギー単調）、
  e016 Stage1（size=k√c4、R²≈0.97、CV≈3%）。ただし basin は**有界**（L* から遥かに小さくも
  大きくも始めると巻き戻る）＝床。絶対 L* は解像度/κ 依存。

## 仮説
勾配流（安定化半陰的）は L* 近傍しか救えないが、**arrested-Newton**（勾配流を Newton 的に
加速し、暴れる高 k を biharmonic で抑えた準ニュートン降下）や**高解像度**にすれば、
**より広い初期条件から L* へ**引き込め（basin 拡大）、より大きい c4 まで L*∝√c4 が保てる。

## 試験（方法）
`experiments/e016_hopf_basin/arrested_newton.py`。安定化流に line-search/加速（過緩和）を足し、
同じ初期条件集合で「勾配流のみ」vs「arrested-Newton」の basin 幅（保持する start 倍率域）を比較。
Q_H・エネルギー単調・収束 size を測る。高 c4（例 36,49）で L*∝√c4 が保てるか。

## 結果（`arrested_newton.py` → `results/arrested_newton.json`）
- **確定した measured**：size 則は **L=44 と L=52 の両方で tight（CV=3.5%）**（√c4 が保たれる）。
- **検証した仮説＝否定**：L=56 で fit が劣化（CV=6.6%・R²≈0.57）したのを「固定 κ の過減衰」と疑い、
  **κ∝dx⁴ 較正**を試験。L=52 で較正 κ=20.5（CV=3.7%）は固定 κ=40（CV=3.5%）を**改善しなかった**
  → **単純 κ スケールでは L=56 の劣化を説明できない**（負の結果）。
- したがって「高解像度で fit が落ちる」原因は**未特定の開いた床**。真の大域化（任意初期→L*）も未達（固定格子で有界）。

## 結果 v2（`arrested_newton_v2.py` → `results/arrested_newton_v2.json`、matched protocol L-series＋arrested-Newton）
**L=56 劣化の原因を特定した**（曖昧なまま放置しない）：

| L | k | R² | CV | k_per_c4 (c4=16→30) |
|---|---|---|---|---|
| 44 | 0.893 | 0.959 | **2.2%** | 0.93→0.883 |
| 52 | 0.890 | 0.873 | **3.3%** | 0.94→0.87 |
| 56 | 0.889 | 0.831 | **3.7%** | 0.95→0.87 |
| 64 | 0.888 | 0.752 | **4.2%** | 0.95→0.86 |

- **原因特定（promoted）**：v1 の「L=56 で CV=6.6%・R²=0.57 の**破局的劣化**」は、**同一プロトコル（同じ c4=[16,20,25,30]・同じ step 数）では再現しない**。v1 の数字は c4=12 を含む広い range＋step 数の違いで**水増しされていた**。matched protocol では全 L で **CV<5%**＝size 則は L=44/52/56/64 で保たれる。
- **残る本物の床（mild・単調）**：ただし CV は L とともに**単調に上昇**（2.2→4.2%）、sub-√c4 の k-decline が**細格子で steepen**（最大 c4 の k が 0.883→0.86, L=44→64）。全体 k は L 非依存（0.893→0.888）。＝**有限箱による大 soliton の圧縮**が第一候補（κ∝dx⁴ は v1 で否定済み）。破局ではなく、特徴づけられた mild な床。
- **arrested-Newton（heavy-ball モメンタム＋biharmonic 高 k 抑制）は basin を広げない**：plain も accel も保持 window mult=[0.7,1.5]（幅 0.80）。エネルギー単調性はモメンタムで overshoot し得るので正直に記録。→ **basin の有界性は流れの質の問題でなく固定格子で本質的**。

## verdict
- [x] **promoted（L=56 劣化の原因特定）**：破局的劣化は再現せず＝プロトコル水増し。size 則は全 L で CV<5%。claim_ledger e016 §に追記。
- [x] **dead-end（κ∝dx⁴ 較正）**：`_archive/` に要約済み。
- [ ] promising
- 残件：**残る mild・単調な finite-box decline の定量分離**（箱サイズを dx 固定で変える対照）と**真の大域 basin**（arrested-Newton でも広がらず＝固定格子で有界が本質）は **frontier 継続**。トポロジー保存離散化（Task 4）は未着手として残す。

## メモ
「真の大域 basin（任意初期→L*）」は固定格子では**原理的に有界**（下は解像限界、上は箱/カットオフ）。
だから「大域化」は**basin を広げる**の意で、無限大域は主張しない（床）。誇張しない。
