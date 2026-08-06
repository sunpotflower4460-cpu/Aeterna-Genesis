You are the bounded monitor for the Aeterna Genesis campaign `gl-haiku-1000-robustness`.

Read `docs/CLAUDE_HAIKU_1000_RUNBOOK.md` and perform exactly one monitoring pass from section 4.

Do not edit source files or campaign data. Do not modify SQLite rows. Do not retry failed jobs. Do not change physics, diagnostics, thresholds, parameters, seeds, or stages. Do not approve or create coarse/full-3D work. Do not use web access.

Generate the deterministic report, inspect current statuses, worker PIDs, recent logs, disk space, and official-tree integrity.

A worker restart is permitted only when queued jobs remain, running is zero, and no worker PID is alive. The restarted command must use the same dedicated DB and unchanged campaign. Otherwise make no changes.

Print:
- stage/status counts;
- 2D and local-3D completion/pass counts;
- failure count and first error lines;
- live worker count;
- official-tree integrity;
- whether progress is evident;
- exactly one final state token:
  RUNNING_NORMALLY
  READY_FOR_FINAL
  INFRASTRUCTURE_ATTENTION_REQUIRED
  INTEGRITY_FAILURE
