# H014 — 自己受信（芯が自分の巻きを読む・生きた器の同一性）

- **状態**: **resolved (promoted)**（`experiments/e021_self_receiver/` 実装済み・全 GREEN）
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

## 結果（GREEN・物理量ゲートのみ、`experiments/e021_self_receiver/`）
**Stage1 self_receiver**（外場ゼロ）：リング巻き＝芯巻き（w=−2..+2、電流符号も追従）／芯位置ジッタ不変／
芯の外の半径で巻き量子化。ゲート：`ring_reads_core_winding` / `reading_invariant_to_core_position` /
`reading_quantized_across_radii`。
**Stage2 vessel_alive**（駆動液滴）：駆動下で巻き +1 保持（芯＝穴）／**近い反渦 d=7 で対消滅**（巻き→0・芯が
~1 に癒える）／**遠い反渦 d=30 は生存**（巻き +1）＝臨界距離。ゲート：`winding_self_maintained_under_drive` /
`winding_annihilated_by_near_anti` / `winding_survives_far_anti`。
ゲート名は物理量（winding/current/core_amp）。「自己/同一性/死」は analogy（docstring/AUDIT）。

## verdict
- [x] **promoted**（e021 実装・全 GREEN、`claim_ledger` e021 §）。
