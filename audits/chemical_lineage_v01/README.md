# 化学系の系譜・組成の持ち越し監査（chemical_lineage_v01）

**役割**：独立した V/Q 系の監査（抽象化学系）。Genesis の正式な Room、experiments/eNNN、3D 創発 Level、生命の主張とは無関係。

## 問い
1. 親の組成は、子の未来を変えるか（Q1）。
2. その違いは単純な材料の持ち越し以上か（Q2）。
3. 組成の持続は進化可能性を意味するか（Q3。v0.1 では検証しない）。

## 実行
```bash
python -m pytest audits/chemical_lineage_v01/tests -q                 # 単体テスト
python audits/chemical_lineage_v01/run_audit.py --smoke --out <新しい空のディレクトリ>   # スモーク（採点しない）
python audits/chemical_lineage_v01/run_audit.py --out <新しい空のディレクトリ>            # 本実行（results/formal_v01 等、新規のみ）
```
- `--out` は必須。既存の空でないディレクトリには書かない。

## ファイル
- `MODEL_CONTRACT.md`（方程式・対照・判定規則）、`LITERATURE_AND_ASSUMPTIONS.md`、`LIMITATIONS.md`、`PRE_REGISTRATION.json`、`AUDIT.md`（結果と監査）
- `species.py`、`reaction_network.py`、`thermodynamics.py`、`solver.py`、`transfer_protocol.py`、`controls.py`、`observers.py`、`statistics.py`、`run_audit.py`、`visualize.py`、`strict_json.py`
- `tests/`：T01–T20 の単体テスト
