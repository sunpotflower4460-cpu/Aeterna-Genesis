# e055 自己形成±渦ダイポールの生存時間分布（H021キャンペーン反復4・role F）

e052/e053/e054 は「Level 3（自走）に到達したか」を固定の観測窓（201 snapshot）とマージン閾値で pass/fail
判定してきた。北極星（Level 4：持続的個体性）へさらに近づく前段として、本実験は根本的な問いへ戻る：
**そもそも自己形成した ±ペアはどれくらいの時間、相互最近傍のまま存在し続けるのか？** 観測窓を3倍に延ばし、
straightness/speed ゲート抜きの生の持続時間分布を測る（`genesis/diagnostics/level3_motion.py` に新規
`mutual_neighbor_durations` を追加・measures.py は不変）。

## 測定結果（full・L=96固定・τ_Q=200・観測窓4800 step=600 snapshot・10 seed 独立新規範囲）
| seed | 最長持続(snapshot) | 最長持続(物理時間) | 中央値割合 |
|---|---|---|---|
| 1301 | 202 | 80.80 | 0.038 |
| 1302 | 192 | 76.80 | 0.097 |
| 1303 | 165 | 66.00 | 0.053 |
| 1304 | **358** | **143.20** | 0.076 |
| 1305 | 151 | 60.40 | 0.110 |
| 1306 | 179 | 71.60 | 0.037 |
| 1307 | 171 | 68.40 | 0.098 |
| 1308 | 142 | 56.80 | 0.060 |
| 1309 | 157 | 62.80 | 0.057 |
| 1310 | 153 | 61.20 | 0.028 |

**全体最長：358 snapshot（物理時間143.2）**。e052/e053/e054 が使っていた観測窓（201 snapshot）を
**10 seed中2 seedで超えた**（1301: 202、1304: 358）。

## 何が分かったか（正直に）
1. **観測窓のトランケーション問題を実測で発見**：e052/e053/e054 の201 snapshot窓では、少なくとも一部の
   ペアは「まだ続いていたのに窓が終わったから記録が止まった」可能性がある。これは e052/e053/e054 の
   **Level3判定そのものは覆さない**（persist_min=15 snapshotという遥かに緩い基準は短い窓でも余裕で満たされる）
   が、「ペアがどれくらい長く続くか」を過小評価していた可能性を示す誠実な追加知見。
2. **単純な線形拡大ではない（部分的な飽和の兆候）**：観測窓を3倍（201→601 snapshot）にしても、最長持続は
   約1.5〜2倍（201→358 前後）にしか伸びなかった。もし真に無限に持続する個体があれば窓を伸ばすほど最長値も
   伸び続けるはずだが、大半のペア（10中8）は142〜202 snapshotという狭い帯に収まる——**特徴的な有限寿命
   スケール（物理時間で概ね60〜150）がある**ことを示唆する。
3. **しかし「飽和した」と断定はしない**：本実験は1つの窓長（3倍）としか比較していない。真に飽和曲線を
   引くには、さらに長い窓（6倍・9倍）で最長値が頭打ちになることを確認する必要がある。**この判定は次段に
   持ち越す**——性急に「transient」とも「persistent」とも言わない。

## Discipline
- **role F**（frontier）：Level4 の直接証拠ではない（`recovers_after_perturbation`・tracked ID 同一性は
  未測定）。「飽和か無限成長か」を明言せず、正直に unresolved と記録。
- **育ったのか置いたのか**：ペアは IC に置いていない（`seeded_structure: false`）。観測窓を延ばしただけで
  物理法則・閾値は e052 から完全に凍結。
- **no_touch**：`genesis/diagnostics/measures.py` 不変。新規 `mutual_neighbor_durations` は同ファイル内の
  追加関数（既存関数は変更なし）。e052/e053/e054 の artifact・数値も一切変更していない。
- **8th 監査**：`target_encoded=false`。primary role=F は E/V の制約対象外。

## 次（H021 キャンペーン 反復5 の候補）
- さらに長い観測窓（6倍・9倍）での最長持続時間の飽和検証。
- 飽和が確認できたら：長寿命ペアへの摂動（局所ノイズ注入等）を加え、`recovers_after_perturbation` を
  直接測る初めての Level4 テストへ。
- 3D 昇格・sep_max のスケーリング修正（e054 の既知交絡）は並行して残る。

## Reproduce
```
python experiments/e055_dipole_survival_time/dipole_survival_time.py            # full（10 seed、約2分）
python experiments/e055_dipole_survival_time/dipole_survival_time.py --quick    # smoke
pytest tests/test_e055_dipole_survival_time.py tests/test_level3_motion.py -q
```
