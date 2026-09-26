# 監査用報告：P7-1 ゴール・マップ・AI の選択／P7-2 AI の研究員

- 日付：2026-09-26
- 対象 PR：#151（P7-1）と、この PR（P7-2）
- 読み手：別の Claude（監査役）。人向けのやさしい説明はチャットに書いた。
- この段は**道具の追加**で、物理の結果は含まない。`genesis/models/*`・`core/*`・測定器は変更していない。

## 1. 主張と claim tier

| # | 主張 | tier | 根拠 |
|---|---|---|---|
| C1 | ゴールの条件は、ラボが測った時系列だけで判定される（「値が ○ 時間続けて成り立った」） | measured（合成系列・GS の宇宙） | `tests/test_lab_goals.py` |
| C2 | `speed` は、塊が 1 つのときだけ計算される。「いま」の表示は最新のサンプルの値（無ければ —） | measured | 同上。P7-2 で、古い値を「いま」と出していたのを直した |
| C3 | 研究員が使えるのは 9 つの道具だけ。許されていない白、範囲外のつまみ、始め方のつまみを使った分岐、人の宇宙を進める・閉じることは、すべて断られる | measured（偽の provider） | `tests/test_lab_researcher.py`：`test_refusals_stay_inside_the_goal`、`test_cannot_run_or_close_a_universe_it_did_not_make` |
| C4 | 予算（宇宙の数・ステップ・USD・分）は研究員全員で共有され、超えない。ステップは残りに合わせて切り詰める | measured | `test_step_budget_trims_then_stops`、`test_parallel_researchers_share_budget_and_map` |
| C5 | 止めるボタン（1 人・全員）とゴールの一時停止で、研究員は次の道具の呼び出しの前に止まる | measured | `test_stop_button_and_pause_end_researchers`、`test_server_starts_and_stops_researchers`（ワーカープロセスのハブ） |
| C6 | 研究員の行動は、名前付きでマップ・「いまやっていること」・記録に残る | measured | 上のテストと `test_a_researcher_tries_observes_notes_and_finishes` |
| C7 | Opus 5.5 の研究員への呼び出しは、送る内容が正しい。model、effort=medium、thinking なし、9 つの道具がすべて strict、履歴は追記のみ | measured（本物の anthropic 1.8.0 を、API を真似たローカルのサーバーに向けて・1 回） | この container で作成 → 20 コマ進める → 終える、の流れを確かめた（スクリプトは scratch で、リポジトリには入れていない） |
| C8 | DeepSeek（標準ライブラリで直接つなぐ）の研究員は、OpenAI 形式の function calling で動く。キーは送信内容にも状態にも出ない | measured（偽の `post`） | `test_deepseek_researcher_loop_uses_function_calling` |
| C9 | GPT（OpenAI 互換）の研究員も同じ形で動く | measured（本物の openai 3.19.2 を、ローカルの偽サーバーに向けて・1 回） | 作る → 終える、tool_choice=auto、履歴 system/user/assistant/tool |
| C10 | 中心の AI を別の model に替えると、会話の履歴を新しく始める。履歴の形式が違う model どうしで混ざらず、画像の生のバイトも入らない | measured | `test_core_history_restarts_when_the_core_model_changes`。P7-2 で DeepSeek／GPT にも道具を使える会話を足したときに見つけた不具合の修正 |

## 2. 測定と再現手順

```bash
pip install -r requirements.txt
python -m pytest -q tests/test_lab_goals.py tests/test_lab_researcher.py     # 15 件・約 5 秒
python -m pytest -q -m "not slow"                                            # 739 passed（この container）
(cd app && npm install && npm run typecheck && npm run build)
python -m tools.lab.server        # 「ゴール」タブ → 新しいゴール → 研究員を足す → 始める
```

画面の撮影には、決まった手順を順に呼ぶ偽の研究員を使った（撮影専用、リポジトリ外）。撮影に写っている発言と数値は、実際の AI の出力ではない。数値は、偽の研究員が実際に宇宙を作って進めたときの測定値である。

## 3. 限界・弱点（正直に）

- **本物の AI ではまだ動かしていない**。
  - Opus 5.5・DeepSeek・GPT で、実際の API キーを使って研究員を動かしたことはない。
  - 道具を選ぶ賢さ、予算の使い方、同じことを重ねない協調は、未評価。
- **協調は緩い**。
  - 研究員どうしは、毎ターンの「状況」（予算・宇宙・いまやっていること・マップの新しい 30 件）で互いを知るだけ。
  - 仕事の割り当て（ロック）はしていない。同じ試行を重ねることはあり得る。
- **予算の超過**。
  - USD は、1 回のやりとり（最大 8 往復）が終わってから数える。そのため 1 回分だけ上限を超え得る。
  - 分は壁時計で数える（ゴールごと、研究員の人数では掛けない）。
- **ほかの制限**。
  - 研究員の状態（やりとり）はメモリだけにある。ラボを再起動すると消え、進行中のゴールは「止めている」に戻る。記録（journal）とマップは残る。
  - 判定は「選んだ数値を満たした」だけで、個体・生命などの意味は持たない。
  - 条件の選び方しだいで、簡単に「達成」になる（例：`spots >= 0`）。
- **Gemini は研究員になれない**（道具を渡す経路を作っていない）。見る係だけ。

## 4. 規律チェック

- **no_touch**
  - `genesis/models/*`・`core/*`・`genesis/diagnostics/*` は変更していない。
  - ハブには `run`（N コマを 1 コマずつ測りながら進める）を足しただけで、物理は同じ関数を呼ぶ。
- **置いたもの**
  - 研究員が作った宇宙・分岐・摂動は、すべて研究員の名前付きで、時刻付きの出来事としてマップ・活動・記録・レシピに入る。
  - 研究員の宇宙は一時停止で生まれ、研究員が run した分だけ進む。
- **AI の権限**
  - 動けるのはラボの中だけ。コード・ファイル・git・main には触れない。道具がそれ以外を持たない。
  - 提案カードは、人が押すまで実行されない（P6 と同じ）。
- **秘密**：キーは環境変数だけで扱う。研究員の状態・送信内容に出ないことをテストした。
- **自動化**
  - bot の trigger は戻していない。
  - 研究員は、うえきさんがゴールの「始める」を押したときだけ動く。予算と止めるボタンがある。

## 5. 次の一手

1. うえきさんの PC で、実際のキーを使って研究員 1 人（Opus 5.5）を小さい予算（$0.3・10 分）で動かし、道具の使い方を見る。
2. P7-3：波の白（Klein–Gordon φ⁴／sine-Gordon）。光らしさ（エネルギー保存・可逆・光円錐）をテストしてから、壁やオシロンが置かずに生まれるかを測る。

## 追記（同日）：仮説から選べるゴール・まとめて試す・やさしい説明（#152 の続き・#153）

| # | 主張 | tier | 根拠 |
|---|---|---|---|
| C11 | `research/hypotheses.json` の仮説（H1〜H6）は、どれも測り方・反証・置いたものを持つ。すぐ始められるものはそのままゴールとして通り、準備中のものは足りないものを言って断る | measured | `tests/test_lab_goals.py::test_hypotheses_catalog_is_well_formed_and_ready_ones_become_goals` |
| C12 | 「まとめて試す」の各組み合わせは、t=0 からのレシピで、水槽で動かすのと同じ状態（sha256 一致）と同じ判定になる。1 プロセスと 2 プロセスで結果が同じ | measured | `tests/test_lab_sweep.py::test_variants_match_the_live_lab_and_replay` |
| C13 | 研究員の sweep は、許された白とステップ予算の中でだけ動く。記録と、専門用語なしの言いかえ（plain）がマップに残る | measured（偽の provider） | `tests/test_lab_sweep.py::test_researcher_sweeps_inside_budget_and_records_it` |
| C14 | 「やさしい説明」は、ゴールの数字（評価・sweep・活動・予算）だけから機械的に作られる。「数字の目安で『生きている』などの意味はない」という注意が必ず入る | measured | 同上と `test_plain_text_without_criteria_or_activity` |

限界：
- sweep の順位は「満たした条件の数＋条件ごとの最長の続き方」で決めている。この重みの付け方は選択であって、物理ではない。
- 「AI にもっとやさしく」は、偽の provider でしか確かめていない。言いかえの正しさ（誇張しないこと）は、指示でしか縛れていない。
- 撮影では H1 の 6 通りを実際に回した。その結果、条件（点 1 つが 100 時間続く）を満たすものは無かった（1 通りあたり 60 コマ＝約 180 時間）。
