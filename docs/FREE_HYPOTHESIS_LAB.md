# Free Hypothesis Lab — 自由仮説を大胆に試し、strictへは「問い」だけ戻す

Aeterna-Genesis には二つの研究姿勢を同時に置く。

1. **Strict / Pure Genesis lane** — 「それは0から育ったのか」を裁く本線。答え・形・場所・時刻を置かない。
2. **Free Hypothesis Lab** — 「もしこうしたら何が起こる？」を大胆に試し、機構の手掛かりを拾う探索触媒。

この二つを混ぜないことが重要であり、自由仮説を萎縮させる必要はない。

## Free Labで許すこと

Free Labでは、たとえば以下を実験してよい。

- 0全体へ追加エネルギーを入れる
- 一点やランダム位置へ局所エネルギーを入れる
- リング状・殻状にエネルギーを置く
- 0が存在できる場所を円・楕円などに変える
- 外部環境を周期的に揺らす
- quenchを急激/ゆっくりにする
- 空間ごとにquench速度を変える
- 境界・有限サイズ・異方性・曲率を大胆に変える

これは「丸い細胞を最初から置いて生命を作った」と主張するためではない。

例：円形領域で分岐が増えた場合、Free Labの成果は **「円が生命の答え」ではない**。次の問いは、

- 曲率が効いたのか？
- 面積/境界長比か？
- 閉じ込めか？
- 異方性を消すことか？
- 有限サイズそのものか？

である。

その抽象的な要因を、形を置かないstrict条件へ戻して再検証する。

## Provenance class

Free Labの各試行は必ず分類される。

- `DRIVEN_EXPLORATORY`
- `SPATIALLY_DRIVEN_EXPLORATORY`
- `GEOMETRY_SCAFFOLDED_EXPLORATORY`
- `CONTROL_MATCHED_TO_FREE_LAB`

これらは **strict-zero evidenceではない**。

## Strict Bridge

Free Labからstrictへ流してよいのは、結果形状ではなく抽象的な**機構質問**だけ。

例：

`annular_energy_shell` で大きな差が出た

→ ❌ strict runにもリングを置いて「0から出た」とする

→ ⭕ 「曲率を持つ界面が効くのか？」という問いへ変換し、ランダムな界面・自然形成した界面・一様開始などで検証する

`circular_confinement` で差が出た

→ ❌ strictの初期条件を円にして自然創発扱いする

→ ⭕ 「有限サイズ」「境界曲率」「閉じ込め」のどれが効くかを分解し、target形状なしのensembleで検証する

## AI Scientist Direction Notebook

`ai_lab/discoveries/ai_scientist_directions.json` は、AIが現状の証拠を読んで独自に考えた仮説を置く planning-only notebook。

現在Free Labが直接実行できる experiment type:

- `uniform_energy_boost`
- `central_energy_pulse`
- `annular_energy_shell`
- `circular_confinement`
- `elliptic_confinement`
- `periodic_global_drive`
- `single_random_energy_kick`
- `radial_quench`
- `slow_quench`
- `fast_quench`

AIは既存typeから自由に組み替えてよい。現在の測定では表現できない新しい問いが重要なら、**新しい測定器/experiment typeを別PRで実装してよい**。ただしtruth gate・official Level・strict evidence contractは変更しない。

## 自動実行

`.github/workflows/free-hypothesis-lab.yml` が1日4回走る。

Free Labは毎回、最新の以下の状況を読む。

- recurrent unknown X-pattern
- 2渦/3渦と局所エネルギー
- triangle vs non-triangleの分離傾向
- Deep-Time候補
- AI Scientist Direction Notebook

その状態から最大8仮説を選び、各3 fresh seedで試す。全仮説には介入なしmatched controlも置く。

結果は:

- `ai_lab/reports/easy/free_hypothesis_latest.json`
- `ai_lab/reports/easy/free_hypothesis_latest.md`
- `ai_lab/discoveries/free_hypothesis_lab.json`

へ保存される。

Free Labのledgerはstrictな発見ledgerと別であり、workflowもstrict scientific ledgerをcommit対象にしない。

## 絶対境界

Free Labの面白い結果であっても、自動的に以下を行わない。

- Room promotion
- official Emergence Level変更
- Pure Genesis達成扱い
- 「新しい物理法則」の宣言
- 「生命」「細胞分裂」の宣言
- scaffolded morphologyをstrict evidenceとしてコピー

自由さと科学的誠実さは対立しない。

**Free Labでは大胆に夢を見る。Strict laneでは、その夢が本当に0から育つかを容赦なく確かめる。**
