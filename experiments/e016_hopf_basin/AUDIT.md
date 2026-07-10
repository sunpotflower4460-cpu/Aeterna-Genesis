# e016 — Hopf basin（Q_H 安定性は observed／**√c4 size 則は RETRACTED**）— AUDIT

```yaml
id: e016
role: F
claim_tier: observed          # Q_H~1/Q_H=2 topological stability, bounded basin
evidence: "Q_H=2 held (|Q_H|~2), Q_H~1 held, energy monotone; sqrt(c4) size law RETRACTED (target_encoded)"
target_encoded: true          # sqrt(c4) law: start seeded ~sqrt(c4) + under-converged flow
known_match: "Derrick 1964 L*~sqrt(c4) as THEORY; Faddeev-Niemi/Sutcliffe Q_H=1,2 stable hopfions"
open_issues: ["start-independent L* (true convergence) is frontier / H001", "fixed lattice", "high-L CV degradation"]
```

> **⚠️ 第8監査（本改訂で剥奪）**：見出しの **size=k√c4 は target_encoded** ＝ **RETRACTED**。
> size 則ループは各 c4 を `start = start_frac·√c4` で仕込み、勾配流は **未収束**（n_steps では start 非依存の
> 固定点に達しない）。決定的テスト：**(1)** 固定 c4=20 で start を変えると収束 size が start に追従（3.77→5.82）、
> **(2)** start を √c4 から**切り離す**と size/√c4 が強くドリフト（フル 1.03→0.80、drift 26%）。
> よって √c4 スケーリングは**初期条件由来**。Derrick の L*~√c4 は**既知理論（established）**だが、本モジュールは
> それを**清潔に測定していない**。生き残るのは **Q_H≈1/Q_H=2 のトポロジカル安定性**（B=curl A、size 非依存）と
> **有界 basin（observed）**。GREEN → **役割 F**。下記 (a)・原因特定(v2) の CV も同じ seeding 由来で**無効**。

## 監査ヘッダ（hopf_basin.py 先頭と同一）

```
MODULE:   e016_hopf_basin (Stage 1: size law + basin)
QUESTION: 安定化流は size=k√c4（Q_H 保持）の定量法則と（有界）basin を与え、Q_H=2 も保つか。
PUT IN:   S^2 hopfion(Q_H=1 or 2)＋Faddeev-Skyrme エネルギー＋安定化半陰的流。size/法則/basin は入れない。
EMERGED:  (measured) size=k√c4（tight fit・Q_H≈1）；保持 start の有界 basin；Q_H=2 保持（|Q_H|≈2）、エネルギー単調。
CLAIM TIER: measured(size~√c4・Q_H≈1・Q_H=2・エネルギー単調) ; observed(有界 basin) ; analogy(粒子)。
KNOWN MATCH: Derrick 1964(L*~√c4)；Faddeev-Niemi/Sutcliffe(Q_H=1,2 は安定 hopfion)。
STATUS:   F（Q_H 安定性は observed；√c4 size 則は RETRACTED＝target_encoded；真の start 非依存 L* は frontier/H001）。
A_OR_B:   (A) 忠実な法則だが、size 則の CLAIM は √c4 を初期条件に埋め込んでいた（第8監査 fail）→ 撤回。
```

## Stage 1 — size 則・basin・Q_H=2（`hopf_basin.py` → `results/hopf_basin.json`、L=44/κ=40 較正）

**(a) size 則 — REPORT-ONLY / RETRACTED（target_encoded）**：各 c4 を `start=start_frac√c4` で仕込む。
収束 size ≈ start に追従するため、fit の CV=3.5% は **√c4-seeding 由来**であって創発ではない。
**(d) 決定的 DECOUPLING テスト**（`_decoupling`）：start を全 c4 で同一に固定すると size/√c4 が
1.03→0.80（drift 26%、quick 12.7%）＝**√c4 則は初期条件を外すと消える**。→ **撤回**（role F）。

**(b) 有界 basin**：固定 c4=20 で start を広く振り、最終 Q_H を記録。**保持は有界な窓**
（下は未解像で巻き戻り、上は解離で巻き戻り＝両側有界、大域でない）。

**(c) Q_H=2**：方位角巻きを2倍にした (m,n)=(1,2) 場は |Q_H|≈1.95 から始まり、**同じ流れ**で
|Q_H|≈2.0 に保たれる（エネルギー単調）＝高電荷粒子も同じ第三で安定。

## 検証した仮説と負の結果（自分を疑う → 数で検算 → 誇張しない）
高解像度で fit 品質が落ちる場合がある：L=44 は CV=3.5%（tight）だが **L=56/κ=40 で size が
sub-√c4**（CV=6.6%・R²≈0.57）に崩れた。まず「固定 κ の biharmonic フィルタ
`1/(1+dt·κ·|k|⁴)` が高解像度で大 soliton を過減衰（|k_max|=π/dx 増）」を疑い、**κ∝dx⁴ 較正**を
仮説として `arrested_newton.py`（H001）で**検証した**。結果は**否定的**：L=52 で較正 κ（CV=3.7%）は
固定 κ（CV=3.5%）を**改善しなかった**＝単純 κ スケールでは L=56 の劣化を説明できない（**dead-end、
理由ごと H001/_archive に記録**）。

### 原因特定（`arrested_newton_v2.py` → `results/arrested_newton_v2.json`、H001 v2, promoted）
matched protocol（同じ c4=[16,20,25,30]・同じ step 数）で L=44/52/56/64 を並べると：

| L | k | R² | CV |
|---|---|---|---|
| 44 | 0.893 | 0.959 | 2.2% |
| 52 | 0.890 | 0.873 | 3.3% |
| 56 | 0.889 | 0.831 | 3.7% |
| 64 | 0.888 | 0.752 | 4.2% |

- **注（第8監査）**：この L=44–64 の CV<5% も**同じ √c4-seeding 由来**で、size 則の**創発の証拠にはならない**
  （seeding を外す (d) で崩れる）。ここで有効なのは**負の結果**：arrested-Newton は basin を広げない（下記）。
- v1 の「L=56 破局」は matched protocol では再現しない＝v1 は c4=12 を含む range＋step 差で水増しされていた。
- ただし CV は L で**単調上昇**（2.2→4.2%）、sub-√c4 decline が**細格子で steepen**（最大 c4 の k 0.883→0.86）。全体 k は L 非依存。＝**有限箱による大 soliton 圧縮**が第一候補（破局でない mild な床）。
- **arrested-Newton（heavy-ball モメンタム＋biharmonic 高 k 抑制）は basin を広げない**（plain も accel も window=[0.7,1.5]）＝**basin の有界性は固定格子で本質**（流れの質の問題でない）。
＝仮説を立て、数で検算し、破局を否定しつつ残る mild な床を正直に特徴づける（LAW.md）。

## 7監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | S²場＋エネルギー＋流れのみ。size/法則/basin を書いていない |
| 2 | 忠実な物理? | **Yes** | Faddeev-Skyrme・Derrick・Whitehead Q_H は実在 |
| 3 | 結果は初期条件に? | **Yes（fail）** | **size は start∝√c4 に埋込・流れ未収束＝√c4 は初期条件由来（撤回）** |
| 4 | 入れてない物が出る? | **Yes** | size=k√c4、有界 basin、Q_H=2 の保持 |
| 5 | 数で合う? | **Yes** | R²>0.95・CV<10%、\|Q_H\|≈2、エネルギー単調 |
| 6 | 頑健? | **Yes** | κ~独立（robustness.json、κ 20–80）、複数 c4 |
| 7 | コードが発見? | **一部** | Q_H は B=curl A（発見）；size 則は seeding 由来（発見でない） |
| **8** | **ゲート/初期条件が結論を符号化?** | **Yes（fail）** | **size=k√c4 のゲートは start∝√c4 の埋込＝target_encoded → 撤回・role F** |

→ Q_H≈1/Q_H=2 のトポロジカル安定性・エネルギー単調は observed で残る（監査 1-2,4-7 通過）。
**√c4 size 則は第8監査 fail で撤回**＝GREEN でなく **役割 F**。真の start 非依存 L* は frontier（H001）。

## 床（隠さない・必須）
1. **√c4 size 則は RETRACTED（target_encoded）**：start∝√c4 の埋込＋未収束流。decoupling で崩れる（drift 26%）。
   Derrick の L*~√c4 は既知理論だが本モジュールは清潔に測定していない。真の start 非依存 L* は **frontier（H001）**。
2. **basin は有界**（両側、大域でない）。arrested-Newton も広げない（負の結果）＝固定格子で本質。
3. 大 c4 は解像度ぎりぎり。「粒子」は analogy（Faddeev-Niemi 裏づけ）、電子ではない。固定格子。
4. 生き残る claim：**Q_H≈1／Q_H=2 のトポロジカル安定性**（B=curl A、size 非依存）・エネルギー単調＝observed。

## 再現
```bash
python experiments/e016_hopf_basin/hopf_basin.py     # size=k√c4・有界 basin・Q_H=2
python experiments/e016_hopf_basin/robustness.py     # κ 独立性（20–80）
pytest tests/test_e016.py
```
