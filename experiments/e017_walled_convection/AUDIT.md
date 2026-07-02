# e017 — 壁つき Rayleigh-Bénard（教科書の臨界 Rayleigh 数）— AUDIT

> e013 の自己組織対流は**周期箱**で、その線形オンセット Ra_c≈20 は箱固有値＝周期性の
> **artifact**。ここでは**壁つき**の線形安定性問題を解き、古典的臨界 Rayleigh 数を
> **<0.4%** で復元する：no-slip Ra_c≈1708、free-slip Ra_c≈657.5。Stage2 は壁つき DNS で
> Nu(Ra)>1 と内部 delivery（内部給餌）を出す。

## 監査ヘッダ（rb_linear_stability.py 先頭と同一）

```
MODULE:   e017_walled_convection (Stage 1: linear onset)
QUESTION: 壁つき線形安定性問題は教科書の Ra_c（no-slip 1708・free-slip 657.5）を復元するか。
PUT IN:   線形化した marginal Boussinesq (D^2-a^2) 演算子＋壁 BC（no-slip / free-slip）。Ra_c は入れない。
EMERGED:  (measured) Ra_c=1713.9@a_c=3.12(no-slip)・657.3@2.22(free-slip)：教科書と<0.4%。周期 Ra_c~20 は artifact。
CLAIM TIER: measured(両 BC の Ra_c・a_c が教科書一致) ; interpretive(周期箱オンセットは artifact)。
KNOWN MATCH: Rayleigh 1916 / Jeffreys / Chandrasekhar（Ra_c=1707.76, 657.5）。
STATUS:   GREEN（両臨界数を<0.4%で復元）。
A_OR_B:   (A) 忠実。手入力＝線形化方程式＋BC、臨界数は読み出し。
```

## Stage 1 — 線形安定性（`rb_linear_stability.py` → `results/rb_linear_stability.json`）

marginal（成長率0）Boussinesq を z∈[0,1] で、水平波数 a に対し：
`(D²−a²)²W = a²·Ra·Θ`、`(D²−a²)Θ = −W`。一般化固有値問題 A x = Ra B x（x=(W,Θ)）を
解き、Ra を a で最小化：

| BC | Ra_c | a_c | 教科書 | 誤差 |
|---|---|---|---|---|
| no-slip（剛体壁） | **1713.9** | 3.117 | 1707.76 @ 3.117 | **0.36%** |
| free-slip（応力自由） | **657.3** | 2.221 | 657.51 @ 2.221 | **0.04%** |

- **座標なしの臨界数を読み出し**（Ra_c は入れていない）— measured。サンドボックス
  1713.9/657.3 と一致。
- **捕まえた罠（設計者が踏んだ）**：壁の**接線条件を one-sided ステンシルで定義しないと**
  固有値問題が発散（free-slip の D²W=0 を未定義にすると ~2.6e11＝ゼロ行）。
  no-slip は DW=0（D1 one-sided）、free-slip は D²W=0（D2 one-sided）、Θ=0 両壁。
- no-slip > free-slip（剛体壁の方が対流が立ちにくい）＝物理どおり。

## Stage 2 — 壁つき DNS（`rb_dns.py`）

no-slip 壁つき 2D Boussinesq DNS（vorticity-streamfunction、Thom の壁渦度 BC）。
Ra>Ra_c で Nu(Ra)>1（対流が伝導を上回る＝内部熱輸送）、境界供給スカラー c の内部到達
（delivery）が Ra とともに増える＝e013 の自己組織給餌の壁つき実セル版。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 線形化方程式＋BC のみ。Ra_c を書いていない |
| 2 | 忠実な物理? | **Yes** | Boussinesq 線形安定性・壁 BC は実在 |
| 3 | 結果は初期条件に? | **No** | 固有値問題（初期条件なし）、Ra_c は読み出し |
| 4 | 入れてない物が出る? | **Yes** | 教科書の 1708/657.5 が数で出る |
| 5 | 数で合う? | **Yes** | <0.4%（両 BC） |
| 6 | 頑健? | **Yes** | 解像度 N で収束（N=60/64 で <0.4%） |
| 7 | コードが発見? | **Yes** | 固有値を読み出し、Ra_c を書き込まない |

→ measured（両 BC の臨界数）＝**GREEN**。線形 onset（振幅は Stage2 DNS）。

## 床（隠さない・必須）
1. **線形 onset のみ**（振幅なし）。飽和した流れ・非線形熱輸送は Stage2 DNS。
2. **固定 1D 格子（z 方向）**。動的幾何でなく与えられた層。
3. 接線 BC は**必ず one-sided ステンシル**（free-slip D²W=0 / no-slip DW=0）＝罠回避。
4. 周期箱の Ra_c≈20（e013）は箱固有値の **artifact**（壁つきが物理値）。

## 再現
```bash
python experiments/e017_walled_convection/rb_linear_stability.py  # Ra_c(no-slip/free-slip)
python experiments/e017_walled_convection/rb_dns.py               # 壁つき DNS: Nu(Ra), 内部 delivery
pytest tests/test_e017.py
```
