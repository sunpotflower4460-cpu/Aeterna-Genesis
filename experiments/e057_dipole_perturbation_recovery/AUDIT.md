# e057 長寿命渦ペアへの摂動後回復テスト（H021キャンペーン反復6・初めての本当のLevel4テスト）

e055/e056 は「渦ペアがどれだけ長く存在し続けるか」を測ったが、Level4本来の判定基準
（`recovers_after_perturbation`）はまだ何も測っていなかった。本実験はそれを初めて直接測る：
既に十分な期間（20 snapshot以上）相互最近傍のまま結合しているペアに対し、**近くに**（真上ではない）
局所的な複素ノイズ摂動を与え、無摂動の統制群（matched control）と比較して、ペアが同一のものとして
存続する（回復する）かを見る。

## プロトコル（決定的再現・matched control）
1. 標準の damped GPE KZ クエンチ（e052 と同一、L=96・τ_Q=200）を実行し、事後に相互最近傍の ±ペアで
   PRE_BOUND_MIN=20 snapshot 以上すでに結合しているものを探す（最長のものを選ぶ）。
2. 同じ seed を決定的に再実行し、その介入時点（結合が20 snapshot に達した瞬間）の psi を厳密に再構築する
   （浮動小数点決定性により、同一 seed・同一ステップ数なら同一の psi が得られる）。
3. **Branch A（control）**：この psi をそのまま無摂動で N_FOLLOWUP=800 step 継続。
   **Branch B（perturbed）**：同じ psi の独立コピーに、ペア中点から5グリッド単位オフセット・半径5・
   振幅1.0 の局所複素ノイズ摂動をランダムな角度で加えてから、同じ800 step 継続。
4. 両ブランチで、介入時点の元のペア（charges と位置で同定）が RECOVERY_MIN=12 snapshot 以上、相互最近傍の
   結合ペアとして存続するかを判定。

## 開発中に見つけた座標系バグ（修正済み）
初期実装では摂動マスクを `core.vortex` の規約（x=配列の行インデックス、y=列インデックス）と逆順に組んでいた
ため、摂動が意図した場所と異なる場所にかかっていた。修正前は直接ペアへ命中させる操作チェック（manipulation
check）でさえ常に「回復」を示しており、これがバグの兆候だった。修正後は直接命中で明確にペアが破壊される
ことを確認したうえで、本実験の「近傍だが直撃ではない」摂動パラメータを設計した。回帰テスト
`test_perturbation_mask_uses_correct_xy_convention` で固定。

## 測定結果（full・10 seed 独立新規範囲）
| seed | 介入前結合(snapshot) | control 回復 | perturbed 回復 |
|---|---|---|---|
| 1801 | 301 | ✓ (全期間) | ✗ (1 snapshotで崩壊) |
| 1802 | 301 | ✓ (全期間) | ✗ (1 snapshotで崩壊) |
| 1803 | 301 | ✓ (全期間) | ✓ (全期間) |
| 1804 | 251 | ✓ (全期間) | ✓ (全期間) |
| 1805 | 260 | ✓ (全期間) | ✗ (1 snapshotで崩壊) |
| 1806 | 301 | ✓ (全期間) | ✓ (全期間) |
| 1807 | 301 | ✓ (全期間) | ✓ (全期間) |
| 1808 | 132 | ✓ (全期間) | ✓ (全期間) |
| 1809 | 301 | ✓ (全期間) | ✓ (全期間) |
| 1810 | 301 | ✓ (全期間) | ✓ (全期間) |

**control：10中10で回復**（統制群として想定通り——無摂動なら元々持続していたペアはそのまま続く）。
**perturbed：10中7で回復、10中3は摂動直後（1 snapshot）に崩壊。**

## 正直な評価
- **多数派（70%）は近傍の擾乱から回復する**——これは Level4 の `recovers_after_perturbation` に対する、
  初めての、直接的で肯定的な証拠。渦ペアという構造は、少なくともある程度、周囲の局所的な乱れに対して
  頑健である。
- **しかし少数派（30%）は本当に破壊される**——摂動が genuinely 効いている証拠でもあり（バグではない、
  座標系修正後の直接命中テストで確認済み）、同時に「常に回復する」という強い主張はできない、ということ。
- **role を F（secondary E）とした理由**：「Level4 に到達した」と確定させるにはまだ早い。70%という
  数字は摂動の強度・オフセット・角度分布・追跡窓長に依存する可能性が高く、パラメータ感度は未検証。
  また Level4 の他の2基準（`tracked_id_lifetime>τ` は e055/e056 で部分的、`inside_outside_contrast>θ` は
  未測定）と合わせないと Level4 全体の判定は完結しない。

## Discipline
- **物理は完全凍結・再利用**：e052 と同一の KZ クエンチ・閾値。新しい propagator は追加していない
  （摂動は既存の damped GPE の psi に対する加法的なノイズ注入のみ）。
- **matched control**：control と perturbed は同一の介入時点 psi（決定的再現で一致）から分岐し、
  同一の follow-up step 数・同一の判定基準で比較。
- **育ったのか置いたのか**：ペアは IC に置いていない（`seeded_structure: false`）。摂動は「環境からの
  局所的な乱れ」という扱いで、ペアの運動や巻きを直接指定していない。
- **独立 seed**：1801-1810 は e052〜e056 のいずれとも重複しない新規範囲。
- **no_touch**：`genesis/diagnostics/measures.py` 等、不変。
- **8th 監査**：`target_encoded=false`。

## 次（H021 キャンペーン 反復7 の候補）
- 摂動強度・オフセット・追跡窓長に対する感度解析（70%という数字がロバストか）。
- Level4 の残る基準（`inside_outside_contrast`）の直接測定。
- 3D 昇格・sep_max スケーリング修正は並行して残る。

## Reproduce
```
python experiments/e057_dipole_perturbation_recovery/dipole_perturbation_recovery.py            # full（10 seed、約1.5分）
python experiments/e057_dipole_perturbation_recovery/dipole_perturbation_recovery.py --quick    # smoke
pytest tests/test_e057_dipole_perturbation_recovery.py -q
```
