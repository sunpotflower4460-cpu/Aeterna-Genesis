# aquaria/ — 人間とAIが共有する宇宙水槽台帳

`aquaria/` は、Aeterna-Genesis の **研究意図・水槽アイディア・探索方向**を共有する planning layer。

ここにある情報は **科学的証拠ではない**。実際の証拠は Room / run / report / discovery に残る。

- `registry.json` — どんな Aquarium（研究系列）があるか
- `notebook.json` — 人間とAIの idea / question / direction / decision メモ

## Aquarium と Room

Aquarium は「何を見たい・何を試したい」という研究系列。
Room は「実際にその前提条件で t=0 から走った宇宙の記録」。

一つの Aquarium から、複数の Recipe・Run・Room が分岐してよい。

## 書いてよいこと

- 人間の「こんな系を見たい」
- AIの「この過去証拠が使えそう」
- 次に試す前提条件
- 条件境界をどう刻むか
- 何がまだ測れないか
- どのinstrumentが必要か

## 書いてはいけないこと

planning data をそのまま「発見」「物理的成功」「公式Level」と扱わない。

`intent.goal` は探索計画が読んでよいが、**物理ソルバは読まない**。結果を直接作る命令へ変換してはいけない。

詳細は [`docs/UNIVERSE_AQUARIUM.md`](../docs/UNIVERSE_AQUARIUM.md)。
