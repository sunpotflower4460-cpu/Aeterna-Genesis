# H001 — Hopf の真の大域化（arrested-Newton／高解像度で任意初期→L*）

- **状態**: resolved（κ∝dx⁴ 仮説は **dead-end**／広義の大域化は frontier 継続）
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

## verdict
- [ ] promising → 実装
- [x] **dead-end（κ∝dx⁴ 較正）** → 理由を上に記録（`_archive/` に要約）。size 則自体は L=44/52 で GREEN（e016 Stage1）。
- [ ] promoted
- 広義の「真の大域化」は **frontier 継続**（別の安定化＝トポロジー保存離散化／真の arrested-Newton／64³ で原因特定）。

## メモ
「真の大域 basin（任意初期→L*）」は固定格子では**原理的に有界**（下は解像限界、上は箱/カットオフ）。
だから「大域化」は**basin を広げる**の意で、無限大域は主張しない（床）。誇張しない。
