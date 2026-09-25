---
description: 次の実験の提案を research/inbox/ に置く（採否は人間が決める）
argument-hint: <一行の要旨>
---
提案：`$ARGUMENTS`

`research/inbox/YYYY-MM-DD-<slug>.md` を、次の front-matter と本文で作ってください。

```markdown
---
proposer: claude
white: <対象の白>
change_kind: parameter | initial_condition | law_variant   # law_variant は厳しい監査の対象
status: proposed
---
## 問い
## 始原側で何を変えるか（途中に機能を足さない）
## 予想する測定（何が出たら何が言えるか・出なかったら何が言えるか）
## コスト（格子・ステップ・時間の目安）
## 「置いた」になる危険と、その避け方
```

提案は**始原条件の変更だけ**にする（AGENTS.md「AI が変更してよいもの」）。うえきさんが `research/decisions/` へ移して採否を決めるまで、実行しない。
