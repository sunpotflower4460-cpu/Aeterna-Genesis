# ai_lab/dream — 2026-08〜09 の自動研究 bot の実装（停止中）

ここにあるのは、2026-08-06〜09-25 に GitHub Actions から毎時 main へ書き込んでいた自動研究（Dream loop・Free Hypothesis・
Science Bridge・postflight・continuity・maintenance）の実装である。**P0（2026-09-25）で停止した**：該当する 6 本の workflow は
`workflow_dispatch` のみで、自動では起動しない。

- 成果の評価は P2 の監査を見る：[`docs/TREASURE_AUDIT.md`](../../docs/TREASURE_AUDIT.md)、[`docs/X_PATTERN_AUDIT.md`](../../docs/X_PATTERN_AUDIT.md)。
  要点：候補 Room は天井 L2 の白（TDGL）の繰り返しで、「名無し変化 X」の再実行出現の 99.6% は通常のクエンチ物理だった。
- コードは消していない。既存の `*-ci.yml` が引き続きテストしている。
- **新しい研究の足場にはしない。** 新しい作業は `CLAUDE.md` の手順（対話・`/run-white`・`/propose`）で進める。
- 再び自動化するときは、main に直接書かない形（別ブランチ＋要約）にし、うえきさんの判断を得てから行う。
