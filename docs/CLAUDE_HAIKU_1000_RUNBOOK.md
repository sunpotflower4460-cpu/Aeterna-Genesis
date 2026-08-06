# Claude Code Haiku: 1000-trial Genesis campaign runbook

## Purpose

Run a scientifically defensible quick screening campaign without GitHub Actions or macOS.

- Deterministic Python code performs all physics and measurements.
- Claude Code using a Haiku-class model acts only as operator and auditor.
- The campaign starts with exactly **1000 independent 2D trials**:
  - 200 parameter conditions
  - 5 seeds per condition
- Only measured survivors continue to `local-3d`.
- This campaign does **not** run `coarse-global-3d` or `full-3d`.
- Nothing in this workflow may write to or promote into `rooms/official/`.

The campaign definition is:

```text
ai_lab/campaigns/gl-haiku-1000.yaml
```

## Why this is 200 conditions x 5 seeds

A one-seed scan of 1000 unique points has broad coverage but cannot distinguish a robust region from a lucky seed.

This design spends the same 1000 initial runs on:

- 20 logarithmically spaced noise amplitudes over the complete allowed range `1e-5..1e-2`
- 10 quench durations
- 5 independent seeds

The quench grid is deliberately nonuniform. It is dense around `4.0`, where the seed-0 pilot produced persistent local-3D defects, while keeping `2.0` and `12.0` as fast/slow boundary controls. This is a screening design, not proof that `4.0` is universally optimal.

## Fixed paths

Run all commands from the repository root.

```bash
CAMPAIGN_ID=gl-haiku-1000-robustness
CAMPAIGN=ai_lab/campaigns/gl-haiku-1000.yaml
DB=runtime/gl-haiku-1000.sqlite3
RUN_DIR=runtime/gl-haiku-1000
REPORT_DIR=ai_lab/reports/gl-haiku-1000-robustness
BASELINE=$RUN_DIR/official-baseline.json
WORKERS=4
```

Use a dedicated SQLite file. The common queue is intentionally not used, so unrelated queued campaigns cannot be claimed by these workers.

## Hard rules for Haiku

Haiku is an operator and auditor, not an adaptive scientist.

It must not:

1. edit the model, runner, diagnostics, thresholds, schema, campaign YAML, or parameter registry;
2. change a parameter after submission;
3. delete failed, rejected, or inconvenient results;
4. retry a scientific failure;
5. retry an infrastructure failure with changed inputs;
6. approve or create coarse/full-3D jobs;
7. write to `rooms/official/`;
8. describe a quick-grid association as a universal causal optimum;
9. silently repair a stale `running` row in SQLite;
10. commit, push, merge, or promote results unless a human separately requests it.

A retry is allowed only when all of the following are true:

- the failure is clearly infrastructural rather than a measured scientific outcome;
- the original condition and seed are unchanged;
- the original error remains recorded;
- the retry is explicitly reported.

The default monitor does not retry automatically.

## Claude Code model selection

Do not assume that the literal alias `haiku` is available. Set the full Haiku-class model identifier available to the configured Anthropic, Bedrock, or Vertex account:

```bash
export CLAUDE_HAIKU_MODEL='<full-model-id-available-to-this-account>'
```

Claude Code supports non-interactive `-p` mode, JSON/text output, `--max-turns`, explicit model selection, and tool allow/deny lists. Keep the model identifier external so this runbook does not become stale when Anthropic changes model names.

## 1. Preflight

Haiku must execute and verify each step. Stop on the first mismatch.

```bash
git status --porcelain
git rev-parse HEAD
python -m pytest \
  tests/test_genesis_orchestrator.py \
  tests/test_haiku_1000_campaign.py \
  -q
```

Requirements:

- working tree is clean;
- tests pass;
- the campaign compilation test confirms exactly 1000 initial jobs;
- at least 10 GB free disk is recommended;
- no live PID from a previous run exists in `$RUN_DIR`.

Check disk:

```bash
df -h .
```

Create directories:

```bash
mkdir -p "$RUN_DIR/logs" "$REPORT_DIR"
```

Snapshot the official tree before any work:

```bash
python tools/autopilot_campaign_report.py snapshot \
  --path rooms/official \
  --output "$BASELINE"
```

## 2. Initialize and submit

```bash
python -m genesis_orchestrator --db "$DB" init

python -m genesis_orchestrator --db "$DB" submit "$CAMPAIGN"

python -m genesis_orchestrator --db "$DB" status \
  --campaign "$CAMPAIGN_ID" \
  --json > "$RUN_DIR/status-after-submit.json"
```

The submit command must report:

```text
submitted gl-haiku-1000-robustness: 1000 initial 2D job(s)
```

Haiku must independently verify:

- 1000 rows;
- all rows are `2d-screen`;
- all rows are `queued`;
- 200 distinct `trial_id` values;
- each `trial_id` has seeds `0,1,2,3,4`;
- no `coarse-global-3d` or `full-3d` rows.

Do not start workers if any count differs.

## 3. Start four workers

The workers perform the calculations. Haiku only launches and records them.

```bash
for i in $(seq 1 "$WORKERS"); do
  nohup env PYTHONUNBUFFERED=1 \
    python -m genesis_orchestrator --db "$DB" work --no-refresh-app \
    > "$RUN_DIR/logs/worker-$i.log" 2>&1 &
  echo $! > "$RUN_DIR/worker-$i.pid"
done
```

Verify each PID:

```bash
for f in "$RUN_DIR"/worker-*.pid; do
  pid=$(cat "$f")
  kill -0 "$pid"
done
```

The start report must include:

- repository commit SHA;
- campaign ID and DB path;
- exact initial-job count;
- condition/seed decomposition;
- official-tree baseline SHA-256;
- worker count and PIDs;
- start timestamp;
- confirmation that no source file was edited.

## 4. Periodic monitor

Recommended cadence: every 30 minutes. The operating system scheduler should call Claude Code; Claude itself should not remain open as the daemon.

First generate deterministic machine reports:

```bash
python tools/autopilot_campaign_report.py report \
  --db "$DB" \
  --campaign "$CAMPAIGN_ID" \
  --expected-initial 1000 \
  --expected-seeds 5 \
  --official-baseline "$BASELINE" \
  --out-dir "$REPORT_DIR"
```

Then check:

```bash
python -m genesis_orchestrator --db "$DB" status \
  --campaign "$CAMPAIGN_ID" \
  --json > "$RUN_DIR/status-latest.json"

for f in "$RUN_DIR"/worker-*.pid; do
  pid=$(cat "$f")
  if kill -0 "$pid" 2>/dev/null; then
    echo "$f alive"
  else
    echo "$f stopped"
  fi
done

tail -n 80 "$RUN_DIR"/logs/worker-*.log
df -h .
```

The monitor report should contain only:

- total jobs by stage and status;
- completed initial 2D count;
- 2D passes;
- local-3D jobs created/completed/passed;
- failed jobs and first error line;
- live worker count;
- official-tree integrity result;
- whether progress increased since the previous report;
- one of:
  - `RUNNING_NORMALLY`
  - `READY_FOR_FINAL`
  - `INFRASTRUCTURE_ATTENTION_REQUIRED`
  - `INTEGRITY_FAILURE`

### Safe worker restart

A worker restart is allowed only when:

- `queued > 0`;
- `running == 0`;
- no worker PID is alive.

In that case, launch the same command with the same DB and unchanged campaign. Record that a worker process was restarted.

If `running > 0` but no worker PID is alive, report a stale-running infrastructure condition and stop. Do not modify SQLite automatically.

If failed jobs exist, retain them and continue the rest of the campaign. Do not retry automatically.

## 5. Completion condition

The campaign is ready for finalization only when all are true:

- initial 2D count is exactly 1000;
- `queued == 0`;
- `running == 0`;
- `waiting_approval == 0`;
- every initial job is terminal;
- every created local-3D job is terminal;
- every 2D pass has exactly one corresponding local-3D job;
- all job IDs are unique;
- no output path begins with `rooms/official`;
- current official-tree hash equals the baseline hash.

Run the strict report:

```bash
python tools/autopilot_campaign_report.py report \
  --db "$DB" \
  --campaign "$CAMPAIGN_ID" \
  --expected-initial 1000 \
  --expected-seeds 5 \
  --official-baseline "$BASELINE" \
  --out-dir "$REPORT_DIR" \
  --require-complete
```

A nonzero exit code means Haiku must not issue a success report.

Refresh the Observatory data only after the strict report succeeds:

```bash
python -m genesis_orchestrator --db "$DB" refresh-app
```

## 6. Deterministic output files

The report helper writes:

```text
ai_lab/reports/gl-haiku-1000-robustness/
├── summary.json
├── ranked_conditions.csv
├── failures.json
└── haiku_context.json
```

Ranking is transparent and lexicographic:

1. local-3D passes across the five expected seeds;
2. minimum local-3D reached level;
3. mean local-3D reached level;
4. 2D passes;
5. mean measured local-3D defect count;
6. shorter quench duration as a deterministic tie-break;
7. lower noise amplitude as a final deterministic tie-break.

This rank is a screening priority, not an official scientific score.

## 7. Haiku final report requirements

Haiku reads only the deterministic outputs and logs. It must report:

- whether the campaign completed with integrity;
- exact job counts by stage/status;
- exact 2D and local-3D pass counts;
- number of parameter conditions with 5/5 local-3D passes;
- top 10 conditions with:
  - noise amplitude;
  - quench duration;
  - 2D pass count;
  - local-3D pass count;
  - minimum and mean local-3D level;
  - mean local-3D defect count;
- all failures, separated into scientific outcomes and infrastructure errors;
- observable parameter trends, clearly labeled as associations;
- limits:
  - quick grids;
  - only five seeds;
  - only two varied knobs;
  - no coarse/full-3D confirmation;
- a recommended follow-up confirmation set of at most 10 conditions.

The follow-up recommendation must not create or run another campaign automatically.

## 8. Suggested Claude Code invocations

### Start

```bash
claude -p \
  --model "$CLAUDE_HAIKU_MODEL" \
  --output-format text \
  --max-turns 12 \
  --allowedTools "Read,Bash(git:*),Bash(python:*),Bash(mkdir:*),Bash(nohup:*),Bash(kill:*),Bash(cat:*),Bash(df:*),Bash(tail:*),Bash(date:*),Bash(seq:*)" \
  --disallowedTools "Edit,Write,WebFetch,WebSearch" \
  "$(cat ai_lab/prompts/haiku_1000_start.md)" \
  | tee "$RUN_DIR/haiku-start-report.txt"
```

### Monitor

```bash
claude -p \
  --model "$CLAUDE_HAIKU_MODEL" \
  --output-format text \
  --max-turns 6 \
  --allowedTools "Read,Bash(python:*),Bash(kill:*),Bash(cat:*),Bash(df:*),Bash(tail:*),Bash(date:*),Bash(nohup:*),Bash(seq:*)" \
  --disallowedTools "Edit,Write,WebFetch,WebSearch" \
  "$(cat ai_lab/prompts/haiku_1000_monitor.md)" \
  | tee -a "$RUN_DIR/haiku-monitor.log"
```

### Finalize

```bash
claude -p \
  --model "$CLAUDE_HAIKU_MODEL" \
  --output-format text \
  --max-turns 8 \
  --allowedTools "Read,Bash(python:*),Bash(cat:*),Bash(tail:*),Bash(date:*)" \
  --disallowedTools "Edit,Write,WebFetch,WebSearch" \
  "$(cat ai_lab/prompts/haiku_1000_finalize.md)" \
  > "$REPORT_DIR/final_report.md"
```

Do not use `--dangerously-skip-permissions`.

## 9. Scheduling example

A Linux timer or cron entry may invoke the monitor every 30 minutes. The scheduler is responsible for recurrence; Haiku performs one bounded audit and exits.

Example cron command:

```cron
*/30 * * * * cd /path/to/Aeterna-Genesis && /path/to/run-haiku-monitor.sh
```

Store authentication outside the repository. Do not commit API keys, cloud credentials, or Claude session tokens.
