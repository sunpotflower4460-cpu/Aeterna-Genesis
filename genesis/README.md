# genesis/ — Genesis 物理基盤（0 から立ち上げる場）

三層移行（`docs/GENESIS_MAP.md`）の **Genesis Physics** 層。未分化な始原条件（`genesis.yaml`）を **t=0 から
途中介入なし**で発展させ、差・局在・運動…がどこまで自然に育つかを**測定量**で判定する（`docs/EMERGENCE_LEVELS.md`）。

```
genesis/
├─ models/         場の法則（参照: ginzburg_landau = 複素 TDGL クエンチ・2D/3D 同一コード）
├─ diagnostics/    測定量で創発 Level を判定（秩序変数成長・構造因子・巻き欠陥）
├─ runners/        共通 Runner（genesis→run: manifest/summary/emergence/checksum, no-write 正実装）
└─ registry/       機械可読レジストリ（models/solvers/diagnostics/invariants/param_ranges）
```

## 使い方（Runner）
```bash
python genesis/runners/runner.py --mode 2d-screen --quick --no-write   # 2D 探索 smoke（書き込まない）
python genesis/runners/runner.py --mode local-3d  --quick --no-write   # 3D 局所 smoke
python genesis/runners/runner.py --mode full-3d                        # 正式 3D（重い・PR6 の Room が使用）
```

- **`--no-write`** は完全計算して結果を書かないだけ（見せかけでない）。
- **checksum で再現性**：同じ `genesis`＋`seed`＋`mode` は同一の場 checksum を返す。
- **mode は物理を変えない**（格子/step のみ）。**正式な到達 Level 判定は `full-3d` から**
  （2D/局所3D は候補・事前計算＝`docs/DIMENSION_POLICY.md`）。

## 規律
- 完成構造（渦線・roll・膜）を初期条件に置かない。欠陥/パターン/波長は**入れずに**測る。
- 保存量/収支（自由エネルギー drift）を記録。可視化用データと計算用データを分離（`render.schema.json`）。
- 正式 Room は `rooms/`（PR6〜）。Runner は Room を**上書きしない**——昇格コマンド経由でのみ追加。
