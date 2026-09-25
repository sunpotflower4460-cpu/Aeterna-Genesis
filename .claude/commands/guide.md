---
description: 水槽ラボ（ライブ）の相棒になる。観測パケットを読み（画像も見て）、話し、提案カードを出す
---

水槽ラボの「中心」の AI の代わりに、Claude Code として会議に参加する（`docs/LAB.md`「AI の会議」）。
API キーが無いとき、ラボは観測パケットを `lab/state/latest/` に置いている。

1. `lab/state/latest/packet.md`（事件簿）と `request.md`（うえきさんの言葉）を読む。
   同じフォルダの PNG を Read で見る。画像の説明は `packet.json` の `caption`。見た目は「見た目（未測定）」と明記する。
2. 次の順で、うえきさんにやさしい日本語で答える：
   いま起きていること（測定・規則名を引く）／見た目の印象（未測定）／別の説明（数値の作り物・閾値・置いたもの）／次に試すなら。
3. 試す価値があれば提案カードを出す（最大 3 件。実行はアプリでうえきさんが押したときだけ）：
   `python -m tools.lab.propose --parent A --set F=0.04 --why "…" --predict "…" --put-in "…"`
   摂動なら `--perturb cut_half` や `--perturb drop_seed --arg y=0.3 --arg x=0.7`。
   つまみは場の法則（law）のものだけ。範囲外はラボが断るので、そのエラーを読んで直す。
4. 短い要約を会議にも残す：`python -m tools.lab.propose --say "…"`。
5. 「育ったのか、置いたのか？」を守る（skill `physics-integrity`）。ラボで見えたことは下見。主張にするなら `/audit` を通す。

`--lan` で動かしているときは `LAB_TOKEN`（起動時に表示）を環境変数に入れる。
