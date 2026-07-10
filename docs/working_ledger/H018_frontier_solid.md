# H018 — フロンティアを SOLID に（分業／離散作用の平滑化／3D DS 病理の定量化）

- **状態**: **frontier（機構を実証・GREEN、`experiments/e030_*`・`e031_*`・`e032_*`）**
- **起票者**: Claude Code / 2026-07-10
- **狙う Type**: D（深い未踏の仮説）——ただし measured は物理量のみ、床は隠さない。
- **依拠する既知事実**: H017（e029）が名指した三つの続きフロンティア：
  (1) **より鋭い分業モデル**（e029 は協力の安定化＝必要条件のみ、分業・生殖体細胞分化は未達）。
  (2) **e023 の曲率治癒＝BD 作用の揺らぎ問題（H007/H008）**——離散作用が使い物になるか。
  (3) **e022 の 3D（2+1）DS 係数**——2D の純数が 3D で普遍性を保つか（d>2 病理）。

## 仮説
1. **分業**：群れ適応度が投資配分に**凸**（⟨x^a⟩·⟨(1-x)^a⟩, a>1）なら、専門化（生殖体細胞分化）が
   進化的に創発する（Michod の適応度凸性理論）。凹なら generalist が最適。
2. **離散作用の平滑化**：Benincasa-Dowker 生作用は N とともに揺らぎ支配（H008）だが、
   Glaser-Surya のメソスケール平滑化が揺らぎを damp し、曲率信号を（部分的に）拾えるか。
3. **3D DS 病理**：2+1 の DS 分子数は面積則（∝切り口長）を保つが、係数（数/w）は密度依存で
   ドリフトする（2D の密度非依存な純数と違う）＝d>2 IR 病理。

## 結果（GREEN・物理量ゲートのみ）
**e030 分業**（`division_of_labor.py`）：専門家割合が凸性とともに単調上昇（a=0.5→4 で 0.26→0.85、
凹の 3.3 倍以上）、凸群れは生殖系列 proxy(x>0.8) と体細胞 proxy(x<0.2) を同一群れ内に共存(1.0)。
ゲート：`convex_returns_drive_specialization`／`specialization_rises_with_convexity`／`germ_soma_differentiation`。
→ **e029 の必要条件を超え、分業の機構（凸性→専門化→生殖体細胞分化）を GREEN で示した。**

**e031 離散作用の平滑化**（`smearing.py`）：生 BD 作用の std が N とともに増大（81→228→285）＝
揺らぎ支配を定量化、Glaser-Surya 平滑化が std を 1/7〜1/40 に damp。曲率バンプは拾える(9.96→26.49)が
揺らぎ(std 40.88)に対し ~1σ＝**床**。ゲート：`raw_action_fluctuation_dominated`／`smearing_damps_fluctuations`。
`_bd_raw` は core.causet.bd_action_2d と一致（chain/antichain=N を test で検証）。
→ **H008 の障害を定量化（治療でなく）。曲率抽出は有限 N で床。正直に frontier のまま。**

**e032 3D DS 病理**（`horizon_3d.py`）：2+1 面積則は成立（数∝w、R²>0.85、full 0.98–0.99）だが
係数（数/w）が密度でドリフト（99→400、比 4.02×／密度比 9.0）＝2D の純数と違い普遍性を失う。
ゲート：`area_law_holds_2plus1`／`coefficient_density_dependent`。
→ **なぜ 2D（e022）が SOLID で 3D が床か、を定量化。Barton 系 cured 分子は未再現＝frontier のまま。**

ゲート名は物理量（specialist fraction／BD action std／molecule count・coefficient）。
「生殖/体細胞/分業/エントロピー/地平線/BH」は analogy（docstring/AUDIT）。robustness は
seed batch・格子/eps/box 高さを変えてもゲート成立（各 `robustness.json`）。

## verdict
- [x] **frontier（機構を実証・GREEN）**：分業（e030）は凸性→専門化を GREEN で示した。
- [x] **frontier（障害を定量化）**：離散作用の揺らぎ（e031）と 3D DS 係数のドリフト（e032）は
  **障害を定量化**した——治療ではない（cured 分子・曲率抽出は未達＝正直な床）。
- **未解決（正直に）**：e031/e032 は cure でなく obstacle-quantification。曲率信号は ~1σ、
  3D 係数は普遍数でない。ここで示したのは**機構と障害の定量化**であって解ではない。

## メモ
「分業を解いた／離散重力を作った／BH エントロピーを導いた」でなく「凸リターンが分業を駆動する・
平滑化が生作用の揺らぎを抑える・3D DS 係数は普遍性を失う」を数で。確認でなく発見を、誇張なく、床つきで。
e031/e032 は**障害を正直に定量化**（fake cure を作らない＝LAW.md SOLID-only）。
