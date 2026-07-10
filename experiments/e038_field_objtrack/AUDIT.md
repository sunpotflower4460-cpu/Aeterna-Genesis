# e038 — 連続形質進化を「場」から（object tracking・de novo・standing variation なし）— AUDIT

```yaml
id: e038
role: E
claim_tier: measured
evidence: "低い一様形質(tau=0.2, 最適1.0)から de novo 変異+選択で平均形質が ~0.9 へ上昇(standing variation なし)／形質は連続(占有 bin≥4)／移動最適点を追跡(lag ~0.24)"
target_encoded: false
known_match: "replicator-mutator / de novo 適応(cf e036)／standing variation vs de novo の区別"
open_issues: ["HYBRID: 動力学は純 Gray-Scott 場だが形質は tissue ごとの追跡ラベル(均質化する場でない)＝床", "fitness→kill 結合は課した／「進化」は analogy"]
```

> **場化 wave2（H019 深化）**。e036 は形質**密度**を進化させた。純粋な形質**場**は均質化（大域拡散が変異を消す）し
> standing variation が要る。**object tracking**が両方を解決するか——emergent な GS spots の tissue ごとに形質 τ を保持、
> 成長端で継承＋変異（de novo）、選択（τが最適に近い→kill 低→適）で**低く播いた形質が上昇**するか。role E（hybrid 床）。

## 入れたもの（PUT IN）
- Gray-Scott 反応拡散場。各 spot の tissue が連続形質 τ を保持。分裂/成長**端**で隣接親 τ を継承＋微小変異。
  fitness が τ を局所 kill に結合（τ が最適1.0 に近い→kill 低→適）。**全 tissue を低い一様 τ=0.2 で播く**（standing variation なし）。
- 「平均形質が上昇」は**入れていない**——測定。

## 測定（`results/objtrack.json`、full）
- **de novo 上昇**：平均形質 0.20 → ~0.90（standing variation なしで de novo 変異＋選択が最適へ登る）。
- **連続分布維持**：占有 bin 6–7（離散種に潰れない）。
- **移動最適点追跡**：red queen lag ~0.24。

GREEN gates: `de_novo_continuous_adaptation`（0.2 播種→>0.6）／`trait_stays_continuous`（占有 bin≥4）／
`moving_optimum_tracked`（lag<0.35）。

**罠**: **低い一様形質**（standing variation なし）で播き、端継承＋変異が変異を de novo 生成。上昇は**入れていない**
——選択（fitness→kill）が法、de novo 変異だけで低播種から登れるかが測定対象。

## 7＋8監査
| # | 監査 | 判定 | 理由 |
|---|---|---|---|
| 1 | 規則が結果を名指す? | **No** | 「上昇」を書いていない。GS 場＋形質規則のみ |
| 2 | 忠実な物理? | **Yes** | Gray-Scott 反応拡散＝established。形質追跡は最小の局所規則 |
| 3 | 結果は初期条件に? | **No** | 低い一様 τ=0.2（変異なし）。上昇は後から |
| 4 | 入れてない物が出る? | **Yes** | de novo 上昇・連続分布・追跡（どれも入れていない） |
| 5 | 数で合う? | **Yes** | 0.2→0.90、占有 bin≥4、lag 0.24 |
| 6 | 頑健? | **Yes** | 変異率・seed を変えても上昇（`robustness.json`） |
| 7 | コードが発見? | **Yes** | 上昇・分布・lag を測定。結果を書き込まない |
| **8** | ゲート/初期条件が結論を符号化? | **No（false）** | 低播種で standing variation を排除。上昇は de novo 変異＋選択の測定 |

## claim tier
- **measured**: de novo 上昇、連続分布、移動最適点 lag。
- **interpretive**: object tracking が連続形質進化を場で均質化なしに走らせる。
- **analogy / KNOWN MATCH**: replicator-mutator / de novo 適応（cf e036）。

## 床（隠さない）
1. **HYBRID**：動力学は純 GS 場だが形質は tissue ごとの**追跡ラベル**（均質化する場でない）。fitness→kill は課した。
2. 「進化/適応」は analogy。**同じ数学≠同じもの**。
3. **(A) 忠実**：場の法則＋形質規則は手入力。

## 再現
```bash
python experiments/e038_field_objtrack/objtrack.py --quick --no-write
pytest tests/test_e038.py
```
