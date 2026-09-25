# 水槽ラボ（ライブ）— 使い方と約束

記録された水槽（`app/public/aquarium/`）を**再生する**だけでなく、白を t=0 から**その場で動かし**、つまみや摂動で分岐させた「パラレル宇宙」を並べて見比べるための道具。

## 起動（自分の PC）

```bash
pip install -r requirements.txt
(cd app && npm install && npm run build)     # 画面（初回と、画面を更新したとき）
python -m tools.lab.server                   # → http://127.0.0.1:8765/#lab
python -m tools.lab.server --lan             # 同じ Wi-Fi のスマホからも。表示される URL（token 付き）を開く
```

画面を開発するときは `npm run dev` と `python -m tools.lab.server` を同時に動かす（Vite が `/api` をラボに中継する）。
記録の水槽（最初の画面）の「● ライブで動かす」からも入れる。静的な公開版（Cloudflare）にはラボのサーバーがないので、このボタンは出ない。

## できること

| 操作 | 何が起きるか | 記録 |
|---|---|---|
| 新しい宇宙 | 白を選び、seed と「始め方」「場の法則」のつまみを決めて t=0 から始める | 作成（レシピ） |
| 場の法則を変える → **分岐して試す** | いまの状態を複製し、変えたつまみ**だけ**が違う宇宙を横に並べる（推奨） | 分岐（親・分岐した step・変更） |
| 場の法則を変える → この宇宙を変える | 動いている宇宙の係数を途中で変える | 出来事 `set` |
| 摂動（種を置く・半分を消す・ノイズ） | 手で加える介入。分岐にも、この宇宙にもできる | 出来事 `perturb` |
| 比べる | 白ごとに、測定値の時系列を宇宙ごとの線で重ねる | — |
| 系譜 | どの宇宙がどこから何を変えて分かれたか | — |

同時に動かせる宇宙は CPU コア数まで（既定。`--max-universes`）。1 宇宙 = 1 プロセス。
実測（1 コア）：3D 48³ の TDGL は 1 ステップ約 7 ms、2D は 0.2〜2 ms。4 コアなら 3D を 4 つ同時に回せる。

## 約束（AGENTS.md と同じ）

- **物理は変えない**：`tools/lab/whites.py` は各モデルの `make_initial` / `step` を呼ぶだけの薄い包み。
  `tests/test_lab_determinism.py` が、モデルを直接回した結果とビット単位で同じことを確かめる。
- **変えたことは全部「置いたもの」**：つまみ（`law`）の変更・摂動は時刻つきの出来事としてレシピに入り、画面の「置いたもの」に出る。
  「始め方」（`start`）のつまみは t=0 でしか選べない。
- **どの宇宙も t=0 から再現できる**：レシピ = 白 + seed + 初期つまみ + 出来事の列。分岐は「親のレシピ + 1 つの出来事」。
  `tools.lab.universe.replay(recipe, steps)` で同じ sha256 になる（テスト済み）。
- **見え方は表示だけ**：フレームは uint8（各コマの min..max）。「固定の範囲」「コマごとに伸ばす」の切替、しきい・濃さ・起伏は表示のみ。
- **記録はローカル**：`lab/sessions/<日時>/journal.jsonl` と `universes.json`（git 管理外）。研究記録にするときは、人が選んで `research/sessions/` に書き出す（L4）。
- **主張にする前に**：ラボで見えたものは「下見」。主張にするなら、レシピを t=0 から再実行して測り（`/audit`）、`research/inbox/` に提案として置く。

## 構成

```
tools/lab/whites.py    白の登録簿（つまみ・レンズ・摂動・測定）
tools/lab/universe.py  1 つの宇宙（状態・出来事・レシピ・replay・フレーム）
tools/lab/hub.py       宇宙ごとのワーカープロセス、分岐、最新フレーム
tools/lab/server.py    JSON API + SSE + app/dist の配信（標準ライブラリのみ）
tools/lab/journal.py   セッションの記録
app/src/lab/           ライブ画面（drei <View> で 1 つの WebGL に複数の水槽）
```

## 観測パケット（AI に渡すもの）

どの AI にも同じものを渡す（`tools/lab/observe.py`）。画面の「AI に渡すもの」タブで、人も同じものを見られる。
押すたびに `lab/sessions/<日時>/packets/NNN/`（`packet.md`・`packet.json`・PNG）に保存される。

| 層 | 中身 | 読める AI |
|---|---|---|
| 事件簿（文章） | 測定の時系列と、キーフレーム上の塊の追跡から、**規則で機械的に**出した出来事。各行に規則名と閾値：`count-change`（数の増減）、`jump(k=6,5%)`、`settled(last 20%,1%)`、`period(acf>0.5)`、`track:split/merge/birth/death`、`track:motion-summary`、`置いた（介入）` | すべて（文章しか読めない AI もこれで「見る」） |
| キーフレーム | 等間隔＋介入の直前・直後、差分（後−前）。3D は 3 方向の投影。**時刻・レンズ・色の範囲・明るさの意味は画像の隣に文章で**付ける（焼き込まない） | 画像を読める AI |
| 動き | キーフレーム 16 コマの連番（固定の色範囲）。`ffmpeg` があれば mp4 も | 動画を読める AI |
| レシピと天井 | 置いたもの・つまみ・分岐、`research/index.json` の測定済みの天井 | すべて |

- 解釈はしない（「分裂した」は規則 `track:split` が当てはまった、という意味だけ）。1 マス前後の移動は形の変化や量子化でも起こる、と事件簿に明記する。
- 追跡は表示用フレーム（2D は間引きなし・uint8 量子化）で行う。証拠にするなら `/audit` で元の場から測り直す。
- サーバーなしでも作れる：`python -m tools.lab.observe --white sh --frames 40 --out /tmp/pk`（Claude Code が読むときなど）。

## AI の会議（「AI と話す」タブ）

「見てもらう」を押すと、並んでいる宇宙の観測パケットを AI たちに渡す（`tools/lab/council.py`）。

| 役 | 既定 | 渡すもの | 書くこと |
|---|---|---|---|
| 見る係 | Gemini（動画も）／GPT（画像） | 事件簿＋画像＋動き | 何が起きているように**見えるか**。すべて「見た目（未測定）」のラベル付き（付け忘れてもラボが付ける） |
| 別の視点 | DeepSeek（OpenAI 互換） | 事件簿（画像を読めない model なら文章だけ） | 同じ事件簿の別の説明（数値の作り物・閾値・置いたもの）と、見分ける試し方 |
| 中心 | Opus 5.5（`claude-opus-5-5`） | 全部＋上の 2 つの報告＋あなたの言葉 | 測定・見た目・別の見方の照合を 1 行ずつ示し、あなたと話し、**提案カード**を出す |

- 見る係と別の視点は並行して呼ばれ、中心はそのあとに答える。「話す」で中心との会話を続けられる（中心は必要なら `ask_colleague` で他の係にもう一度聞き、`look_again` で最新の事件簿を取り直す）。
- **提案カードは実行されない**。カードの「分岐して試す」を人が押したときだけ、親の宇宙のいまの状態から分岐する。つまみは場の法則（law）のものと範囲の中だけ（ラボが検証し、範囲外や始め方のつまみは中心に差し戻す）。
- 費用は AI ごとに表示し（使用量 × `lab/config.toml` の単価）、1 日の上限（既定 3 ドル）を超えたらその日は呼ばない。

### 設定

```bash
pip install -r requirements-lab.txt                  # anthropic / openai / google-genai（使うものだけでよい）
cp tools/lab/config.example.toml lab/config.toml     # model ID と単価を書く（DeepSeek・Gemini・GPT は各社の資料で確認）
export ANTHROPIC_API_KEY=…  DEEPSEEK_API_KEY=…  GEMINI_API_KEY=…   # キーは環境変数だけ。ファイルに書かない
python -m tools.lab.server                           # 起動時に、どの役が使えるかを表示する
```

- キーが無い役は飛ばす（1 つだけでも動く）。キーはサーバーの中だけで使い、画面や記録には出さない。
- 外部に送るのは**シミュレーションの画像と数値と、あなたが書いた言葉だけ**。個人の情報は入れないこと。DeepSeek・Google・OpenAI・Anthropic のサーバー（国外を含む）で処理される。
- 確認の範囲：Anthropic（anthropic 1.8.0）と OpenAI 互換（openai 3.19.2）は、本物の SDK を、API を真似たローカルのサーバーに向けて通した（ストリーム・ツール呼び出し・使用量）。**Gemini（google-genai）はまだ通していない**。実際のキーで初めて使うときは、短い会話で動作を確かめる。CI は偽の provider で役の順序・ラベル・提案カード・上限・キーの秘匿を確かめる。

### キーが無いとき：Claude Code が相棒

中心の AI が使えないと、「見てもらう」はパケットを `lab/state/latest/`（`packet.md`・画像・`request.md`）に置く。
このリポジトリで Claude Code を開き **`/guide`** と打つと、Claude Code が同じパケットを読み（画像も見て）、チャットで話し、
`python -m tools.lab.propose --parent A --set F=0.04 --why "…"` で提案カードをアプリに出す（`--say "…"` で会議に発言も残せる）。

## これから（P6 の残り）

- **L4**：研究記録への書き出し（`research/sessions/`）、replay コマンド。
- **L5**：2D の白をブラウザ GPU で動かす「下見」版（スマホだけで完結）。
