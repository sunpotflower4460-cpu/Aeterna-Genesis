# research/sessions — 水槽ラボの記録

水槽ラボ（`python -m tools.lab.server`、`docs/LAB.md`）の「系譜」タブにある「研究記録にする」で書き出したセッション。
1 つのフォルダが 1 回の書き出しで、中身は次の 3 つ（合計 1 MB 以下）。

- `summary.md`：人が読む記録。宇宙ごとの白・置いたもの・分岐・最後の状態（sha256）・事件簿の抜粋、AI の会議の要約、提案カードの結末
- `recipes.json`：再現に必要なすべて（レシピ・step・sha256）
- `thumbs/`：最後のキーフレーム

**ここにあるのは「ラボで見たこと」で、主張ではない。** 主張にするときは次の順で進める。

1. `python -m tools.lab.replay research/sessions/<id>` で、t=0 から同じ状態（sha256）に戻ることを確かめる
2. `--packet <dir>` で観測パケットを作り直し、`/audit` で元の場から測り直す（7 監査＋第 8 監査）
3. 提案として `research/inbox/` に置き、採否は人が決める

どのセッションを commit するかは、うえきさんが決める（書き出しただけでは git に入らない。ブランチを切って PR にする）。
