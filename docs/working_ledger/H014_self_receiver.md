# H014 — 自己受信（芯が自分の巻きを読む・生きた器の同一性）

- **状態**: proposed（サンドボックス検証済み・**repo 実装予定** `experiments/e021_self_receiver/`）
- **起票者**: Claude / 2026-07-09（指示書 §3 より）
- **狙う Type**: B（床つき measured）。
- **依拠する既知事実**: 渦・反渦の対消滅（位相スリップ）、駆動散逸液滴、巻き保存。

## 仮説（H014 + vessel_alive）
- **Stage1（自己受信）**: 外場ゼロで ring winding = core winding（w=−2..2）／芯位置ジッタで不変／
  癒し長外で clean／w=2 は二つに分裂しリングは総2。
- **Stage2（vessel_alive, 4ゲート）**: `self_maintains`（bulk|ψ|²=0.99）／`death_on_undrive`（→0.02）／
  `identity_survives_body_damage`（巻き+1 保持＋再生）／`identity_dies_to_its_anti`（反渦で巻き 1→0、閾値~15、
  芯|ψ| 回復が対消滅の署名）。

## repo 実装（予定）
`experiments/e021_self_receiver/`（Stage1＋Stage2）。`core/holonomy.py`（ring_winding）を使用。
GREEN ゲート名は物理量のみ（winding / bulk_amp）。「自己・同一性・死」は analogy（docstring/AUDIT）。

## 床
- 有限駆動散逸液滴が windingless vacuum に浮く設定（読み取り環 R は一つの芯のみ囲む）。
  「自己を受信する」は analogy——measured なのは巻き・|ψ|²。

## verdict
- [ ] proposed → e021 実装で判定。
