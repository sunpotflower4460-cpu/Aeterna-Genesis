# PR #80 後の e060 と関係グラフ探索

2026年8月6日〜13日の研究資料を、[元コミット 2974ed0a4](https://github.com/sunpotflower4460-cpu/Aeterna-Genesis/tree/2974ed0a4a831385ad8ac355379fe0e2f8b08332)から保存した。ソース、結果、監査文書、回帰テストの57ファイルは、当時のパスと内容をこのディレクトリの下に保持している。

- [e060 の監査](experiments/e060_l4_monad_frontier/AUDIT.md)と[測定結果](experiments/e060_l4_monad_frontier/results/)には、2D の対照による較正、単一局在の探索、再現しなかった候補と長時間追試を収録した。
- [関係グラフ探索の監査](ai_lab/relational/AUDIT.md)には、PR-R1〜R9 の振動・巻き数の測定と対照比較を収録した。PR-R9 の[結果](ai_lab/relational/results_pr_r9.json)は、同じ3グラフの4条件に対する比較として読む。
- [回帰テスト](tests/)は、当時の測定器や対照の動作を検査する。

現行の研究方針と到達状況は[はしご](../../../docs/LADDER.md)を参照する。

## 当時のテストを再実行する

元コミットを別の worktree に展開して、当時の依存コードと一緒にテストする。

```sh
git worktree add --detach ../aeterna-genesis-pr80-source 2974ed0a4a831385ad8ac355379fe0e2f8b08332
cd ../aeterna-genesis-pr80-source
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q tests/test_e060_l4_monad_frontier.py tests/test_r_*.py
```
