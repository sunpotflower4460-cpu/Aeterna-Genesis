---
description: Room / 実験 / X パターンを7監査＋第8監査＋決定性で点検する
argument-hint: <room-id | eNNN | X-xxxxxxxxxx>
---
対象：`$ARGUMENTS`

`LAW.md` の7監査と、`docs/PHYSICS_INTEGRITY.md` の第8監査に Yes/No で答え、根拠のファイルと行を示してください。

1. 規則は結果に言及していないか（局所か）
2. 忠実な物理か
3. 結果は初期条件に入っていなかったか（「育ったのか、置いたのか？」）
4. 入れていない随伴現象も出るか
5. 現実と**数で**合うか
6. パラメータを変えても頑健か
7. コードは結論を主張せず、測定して発見しているか
8. 評価ゲート・初期条件・方程式に、結論と同型の因果が埋め込まれていないか

加えて次を確認する。
- **決定性**：同じ seed で再実行し、記録された checksum（`runs/*/checksum.json` など）と一致するか。一致しなければ、その事実を書く。
- **次元**：2D の結果を 3D の主張に使っていないか（`docs/DIMENSION_POLICY.md`）。
- **X パターン**の場合：`ai_lab/dream/open_ended.py` の指紋は大域スカラーのジャンプを量子化したものなので、渦対消滅・粗大化・クエンチ終了・有限箱・数値誤差・ビン境界のどれで説明できるかを先に確かめる。

結論は GREEN / YELLOW / RED と claim tier（measured / observed / interpretive / analogy / frontier）で出す。GREEN 以外を「成功」と呼ばない。
