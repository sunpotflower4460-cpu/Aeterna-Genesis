# Epistemic Progress Ratchet v10

## 目的

Adaptive Research Yield v9 は、追加の frontier 計算を「成功しそうな道」ではなく「情報量の高い反証可能な問い」へ配るようにした。

v10 ではさらに、各 burst のあとに次を問う。

> **前回と同じことをもう一度やっただけではなく、何か一つでも研究上の問いを前へ進めたか？**

ここでいう「前進」は、新しい派手な現象が毎回出ることではない。自然現象の発生は保証できないし、保証しようとすると target encoding や結果選別につながる。

代わりに、毎回の追加計算が少なくとも次のどれかを行うよう planning を ratchet する。

- まだ試していない start-side intervention cell を試す
- decision-relevant な既試験 cell に fresh seed の独立追試を足す
- Root candidate の未試験 operator ablation を一つ進める
- F-reference の response/depth 境界を新しい条件で調べる
- 同じ target が飽和したことを記録し、別 target/lane へ回す

つまり「現象が出たか」だけでなく、**分からない範囲が狭くなったか**を前進として扱う。

## Question signature

frontier の追加実験には compact な question key を付ける。

例:

```text
x|X-abc123|drive_strength|0.75
f|white:117|quench_duration|1.28
root|RLAW-xyz|relation_trend
```

これは物理的 observable ではない。研究計画上、同じ問いを何回使ったかを識別する bookkeeping だけである。

過去 history に無い key を優先し、同じ key の routine repeat は後回しにする。

## X-pattern

v9 の specificity / exact / nearby / contrast / recent-study ranking は維持する。

その上に intervention coverage を加える。

- 同程度に specific な X が複数ある場合、未試験 cell が多い X を優先する
- 一つの X について standard low/high を試し終えた後は、generic な closer/stronger factor で境界を細かくする
- factor は既存 knob range 内に clip される
- target pattern や morphology を見て factor を選ばない
- baseline は毎 study fresh seed で残す

したがって巨大な recurrence count だけでは frontier budget を独占できない。

## F-reference

F0-F7 は引き続き human-written reference path の一つであり、自然の公式経路でも Emergence Level でもない。

v10 では同じ F candidate に対して、毎 burst 同じ先頭 knob だけを繰り返すことを避ける。未試験 question cell を先に使い、coverage が埋まった candidate は allocation score を下げる。

F-depth の変化は simulator 内の mechanism question を狭めるための観測であり、fundamental cause / force / binding energy / biological division の主張にはならない。

## Root ablation

同じ top Root law に対して、以前に外した operator を何度も先頭から外すのではなく、まだ外していない active operator を優先する。

特に `relation_trend` を外す試験は hidden history assumption の監査として重要だが、結果が良くてもその operator を fundamental law に昇格させない。

## Progress audit

各 frontier report に `progress_ratchet` を追加する。

主な値:

- `status`
- `new_question_keys`
- `replicated_question_keys`
- `novel_question_fraction`
- `lane_novel_questions`
- `lane_replicated_questions`
- `lane_knowledge_units`
- `advance_events`
- `next_burst_escape_required`

`lane_knowledge_units` は planning stall 検知用の内部点数であり、物理的 confidence や scientific truth ではない。

raw recurrence count だけは progress と数えない。

## Stall / saturation

同じ lane が frontier budget を使いながら compact knowledge gain を出せない状態が続いたら、floor を外して score を下げる。

また current target の question coverage が埋まった場合も、その target/lane の優先度を下げる。

目的は「同じことを回し続ける」のを自動的に止め、別の specific X、別の Root operator、別の falsification question へ移ること。

## Negative result

negative result は、事前に定義した問いを閉じるなら前進になりうる。

たとえば「drive_strength をこの範囲で変えても X の有無が変わらなかった」は、少なくともその試験範囲について単純な一要因説明を弱める追加証拠になる。ただし少数 sample で mechanism を否定したとは言わない。

## 絶対にしないこと

Progress Ratchet は次を行わない。

- target morphology / X outcome / triangle / vortex charge / split location/time を seed する
- 結果を見て scientific success gate を変更する
- Rooms を promote する
- official Emergence Levels を変更する
- F-path を自然な正解ルートとする
- recurrence を新しい物理法則と呼ぶ
- planning score を物理 observable と呼ぶ
- negative result を都合よく削除する

## 毎回前進の意味

v10 が保証しようとするのは、

> **毎 burst で新しい自然現象が出ること**

ではない。

保証に近づけるのは、

> **同じ計算予算を、未試験の対照・独立追試・境界精密化・未試験 ablation・飽和からの route change のどれかへ使い、分からない範囲を少しでも減らすこと**

である。

これなら、結果を置かずに「毎回しっかり研究が前へ進む」に近づける。