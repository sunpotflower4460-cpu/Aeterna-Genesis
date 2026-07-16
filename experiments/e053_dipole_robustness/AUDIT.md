# e053 自己形成±渦ダイポールのLevel3自走 — ロバスト性検証（H021キャンペーン反復2）

e052（反復1）は「6 seed 中 3 seed で Level 3」を、マージン薄く（jitter床超過 約10〜12%）、role F（frontier
candidate）として正直に保留した。e049(S1)→e050(S2) と同じ構造で、本実験はその候補が **seed数拡大と解像度3段
（L=64/96/128）を越えて残るか**を検証する。**物理・観測器・閾値は e052 から完全に凍結**（re-tune していない）
——変えたのは grid size L と seed 数のみ。

## 測定結果（full・44 seed 独立・新規 seed 範囲）
| L | n seeds | Level2到達 | Level3到達 | 割合 | 95% Wilson CI | 平均マージン |
|---|---|---|---|---|---|---|
| 64 | 12 | 12/12 | 6/12 | 50.0% | [25.4%, 74.6%] | 1.171 |
| 96 | 24 | 24/24 | 15/24 | 62.5% | [42.7%, 78.8%] | 1.301 |
| 128 | 8 | 8/8 | 6/8 | 75.0% | [40.9%, 92.8%] | 1.204 |

**3解像度すべてで Level 3 到達（有限サイズで消えない、むしろ僅かに増加傾向）。** マージン分布
（L=1.05〜1.70）も全て閾値を明確に超え、e052 反復1の際どい水準（1.10〜1.16 相当）より健全。
**判定：`robust_level3_candidate_confirmed`。**

## 正直な評価
- **役割を E に引き上げた理由**：3段の解像度・44 seed という十分な統計で頑健、有限サイズ効果でなく、
  マージンに境界ぎりぎりの事例がない。運動は非 seeded（`target_encoded=false`、ペアは IC に置いていない）。
- **しかし universal ではない**：到達率は50〜75%——**全ての単一連続 t=0 run が Level 3 に届くわけではない**。
  これは確率的クエンチの自然な帰結（KZ タングルの中で孤立ペアが生き残るかは run ごとに違う）であり、
  「大多数の run が届く」という統計的主張として正直に記録する。100% でないことを隠さない。
- **【重要】Level 4 の「単一自走個体」問題とは別問題**：`docs/WHITE_CEILINGS.md` が論じる「単一に閉じ込め∧
  drift 閾値超∧分裂閾値の手前」という codimension≥2 のナイフエッジ（SH ソリトンの m=1 Goldstone 問題）は
  **1個の局在構造**の自走を問う。本実験が測ったのは **2個の渦（±ペア）が組になって並進する**現象＝
  Level 3。両者を混同しない——L4 の単一個体自走はまだ未解決のまま残っている。

## Discipline
- **物理は完全再利用**：e052 と同一の damped GPE KZ クエンチ（`core.field.step_damped_2d`）・同一の
  `genesis/diagnostics/level3_motion.py` 観測器・同一の FROZEN 閾値。新しい propagator も新しい判定基準も
  追加していない。
- **独立 seed**：e052 の seed 1-6 とは重複しない新規範囲（201-212 / 101-124 / 301-308）——同じ run の
  再解析ではなく、新しい独立レプリケーション。
- **no_touch**：`genesis/diagnostics/measures.py`・`rooms/official/**`・既存 experiments/schema/registry 不変。
- **8th 監査**：`target_encoded=false` かつ primary role=E——8th-audit の制約（target_encoded=true な結果は
  E/V を主張できない）に抵触しない。target_encoded=false なので問題なし。

## 天井地図への反映
`docs/working_ledger/H021_frontier_campaign_0_to_far.md` に確定として追記。`docs/WHITE_CEILINGS.md` への
反映は次の一手で行う（Level 4 の単一個体問題と混同しないよう、Level 3（渦ペア並進）として明記する）。

## 次（H021 キャンペーン 反復3 の候補）
- 3D 昇格（e050 パターン踏襲）。
- 別の quench 速度 τ_Q・damping γ での再現性（同じ白の中でのパラメータ感度）。
- Level 4（単一個体の自走）方向への新しい白の探索——これは本実験とは別の、より難しい問い。

## Reproduce
```
python experiments/e053_dipole_robustness/dipole_robustness.py            # full（44 seed、約3分）
python experiments/e053_dipole_robustness/dipole_robustness.py --quick    # smoke
pytest tests/test_e053_dipole_robustness.py -q
```
