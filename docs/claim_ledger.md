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

## e002 — GPE 二渦の相互作用  (STATUS: GREEN)

| # | 主張 | tier | 裏づけ |
|---|---|---|---|
| 1 | 同符号の二渦は GPE だけから互いの周りを回り合う（共回転、間隔ほぼ一定） | **measured** | `result.json`：累積回転 322.9°（単調増加）、間隔 mean 14.89（13.77–17.02、±20%以内）、中心移動 0.00 |
| 2 | 逆符号の二渦は対になって並進する（渦双極子、回転≈0） | **measured** | `result.json`：回転 0.0°、中心移動 21.16（単調増加）、間隔 mean 31.55 |
| 3 | 循環は量子化（各芯の巻き数＝±1） | **measured** | `core/vortex.py`、`result.json`：同符号 charges=[+1]、逆符号 charges=[−1,+1] |
| 4 | エネルギー・ノルムが保存（一様背景・周期境界の保存系） | **measured** | 同符号 E/N drift 2.0e-5/1.6e-12、逆符号 2.4e-5/3.4e-13（e001 より大きい理由は AUDIT §5.2） |
| 5 | 挙動の質（同符号=共回転／逆符号=並進）は間隔 d を変えても保たれ、速さの d 依存も物理どおり | **measured** | `robustness.json`：6/6 PASS。同符号は近いほど速く回り（596>323>100°）、双極子は近いほど速く進む（35>29>25） |
| 6 | 点渦理論には Biot-Savart を入れていない——相互作用は場から出た | **measured** | PUT IN は GPE＋2渦の初期条件のみ（AUDIT.md `PUT IN`） |
| 7 | この二渦ダイナミクスは点渦理論／超流体実験と構造的に一致する | **analogy** | 同符号=共回転・逆符号=並進という定性的一致（定量照合で measured に上げ得る） |
| 8 | 同符号対は静止解でないため音波が蓄積。クリーン窓を間隔で自己検出し劣化前で打ち切る | **interpretive** | AUDIT.md §5.1–5.2（窓の外の発散も隠さず明記） |
| 9 | 同符号対は周期トーラス上で正味循環 +2（鏡像で補償、L≫間隔で副次的） | **interpretive** | AUDIT.md §5.3（理想二体極限には開放/壁境界が必要） |

---

## 今後（e003+）

各モジュールを GREEN にした時点で、その主張と tier をここに追記する。
空欄を埋めるたびに、白から構造が立ち上がる順番（docs/00_grand_map.md）を一段進める。
