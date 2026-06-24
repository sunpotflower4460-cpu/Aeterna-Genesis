# claim_ledger — 全主張の claim tier 台帳

すべての主張に tier を付ける（LAW.md §3）。**誇張も卑下も禁止。**
tier を上げるときは新しい測定で裏づける。

tier: `measured | observed | interpretive | analogy | frontier`

---

## e001 — GPE 渦の歳差運動  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | トラップ中の渦は GPE だけから歳差する（半径ほぼ一定の円運動） | **measured** | `result.json`：累積回転 462.5°、半径 mean 10.58（min 10.01/max 11.35） |
| 2 | 累積回転は単調に増え、8000步で 360° を超える | **measured** | `result.json`：462.5°、rotation_monotonic=True（参照 ≈466°） |
| 3 | 循環は量子化（渦の巻き数＝整数 +1） | **measured** | `core/vortex.py` 巻き数、`result.json`：charge=1, circulation_quantized=True |
| 4 | +1 渦は反時計回りに歳差（循環と同符号） | **measured** | 累積回転が正、`result.json` |
| 5 | エネルギー・ノルムが保存（保存系の split-step） | **measured** | energy_drift 4.1e-8, norm_drift 1.1e-12 |
| 6 | 歳差は R0・Ω を変えても持続（頑健） | **measured** | `robustness.json`：9/9 ケース PASS |
| 7 | この歳差は BEC 実験の渦ダイナミクスと一致する | **analogy** | 既知の BEC/GPE 結果との構造的一致（Anderson et al. 等） |
| 8 | GPE は平均場の有効理論であり最終法則ではない（(B) は未着手） | **interpretive** | 入力＝場の方程式そのもの（AUDIT.md `A_OR_B`） |

---

## 今後（e002+）

各モジュールを GREEN にした時点で、その主張と tier をここに追記する。
空欄を埋めるたびに、白から構造が立ち上がる順番（docs/00_grand_map.md）を一段進める。
