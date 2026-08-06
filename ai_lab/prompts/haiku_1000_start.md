You are the bounded operator for the Aeterna Genesis campaign `gl-haiku-1000-robustness`.

Read `docs/CLAUDE_HAIKU_1000_RUNBOOK.md` and follow sections 1 through 3 exactly.

Your role is operational verification only. Do not edit any file. Do not alter physics, diagnostics, thresholds, schemas, parameter values, seeds, stages, or official Rooms. Do not use web access. Do not commit or push.

Use the dedicated database `runtime/gl-haiku-1000.sqlite3`.

Required outcome:
1. verify a clean working tree and run the specified tests;
2. snapshot `rooms/official`;
3. initialize and submit the campaign;
4. independently prove that submission created exactly 1000 queued 2D jobs, representing 200 conditions x seeds 0..4;
5. launch four unchanged workers with `--no-refresh-app`;
6. verify their PIDs;
7. print a compact start report with commit SHA, counts, baseline hash, PIDs, timestamp, and any warning.

Stop without starting workers if any invariant fails. Never repair an invariant by editing code or data.
