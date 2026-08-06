# Genesis Autopilot — deterministic hypothesis campaigns

Genesis Autopilot turns a schema-validated campaign into a queue of real repository calculations:

```text
campaign YAML (AI/human authored)
  -> SQLite queue
  -> 2d-screen
  -> local-3d
  -> human approval
  -> coarse-global-3d
  -> human approval
  -> full-3d
  -> non-official candidate Room + recorded fields + discovery ledger
```

The AI is not inside the timestep loop. It may propose campaign YAML or summarize results, but the worker:

- changes only allow-listed start-side knobs that the common runner actually applies;
- starts every stage from t=0 with the same genesis and seed;
- imports the repository model stepper and measurement functions;
- never changes success thresholds, conservation code, or `rooms/official/`;
- records failed 3D transfer under `rooms/rejected_in_3d/` instead of deleting it;
- writes replayable 2D/3D `field.json` data for the existing Observatory.

## First run

```bash
python -m genesis_orchestrator init
python -m genesis_orchestrator submit ai_lab/campaigns/autopilot_example.yaml
python -m genesis_orchestrator work --once
python -m genesis_orchestrator status --campaign gl-quench-window
```

Continue automatically through ungated stages:

```bash
python -m genesis_orchestrator work
```

By default, `coarse-global-3d` and `full-3d` wait for explicit approval:

```bash
python -m genesis_orchestrator approve --campaign gl-quench-window --stage coarse-global-3d
python -m genesis_orchestrator work
python -m genesis_orchestrator approve --campaign gl-quench-window --stage full-3d
python -m genesis_orchestrator work
```

The worker refreshes `app/generated/catalog.json` and `app/public/data/` after each completed job. Open the
existing Observatory and use **AI Discovery Inbox** to inspect the candidate, its parent diff, promotion stage,
and recorded phase/density field. Disable repeated app rebuilding during a large batch with
`python -m genesis_orchestrator work --no-refresh-app`, then run:

```bash
python -m genesis_orchestrator refresh-app
```

## Campaign format

A hypothesis can use an explicit list or a Cartesian grid:

```yaml
hypotheses:
  - id: h001
    statement: ...
    seeds: [0, 1, 2]
    search:
      variants:
        - label: low-noise
          overrides: {noise_amplitude: 0.001, quench_duration: 8.0}
      # or:
      # grid:
      #   noise_amplitude: [0.001, 0.003]
      #   quench_duration: [6.0, 8.0, 12.0]
```

At this stage, only `noise_amplitude` and `quench_duration` are accepted because the common runner visibly
applies them. A campaign that names an unimplemented knob is rejected rather than dishonestly recording an
input that did not affect the physics. Additional knobs should be added only together with their real model/
initial-condition implementation and a test.

## Files written

- `runtime/genesis_autopilot.sqlite3`: transient queue state (gitignored)
- `rooms/jobs/job-auto-*.json`: compatibility status for the existing Inbox
- `rooms/candidates/room-auto-*`: surviving 2D/3D candidates with fields
- `rooms/rejected_in_3d/room-auto-*`: candidates that did not survive a 3D stage
- `ai_lab/discoveries/autopilot_ledger.json`: deterministic stage-result ledger

Formal promotion to `rooms/official/` remains a separate audited command and is intentionally not implemented
in Autopilot.

## Portable CI

GitHub ActionsやMacは使わない。LinuxコンテナでAutopilotの2D→local-3D実計算、Schema、チェックサム、
Observatoryビルドを検証する。テスト実行中のネットワークも既定で無効にする。

```bash
bash ci/run-container.sh autopilot
```

クラウドLinux VMで継続実行する場合は `ci/cloud-runner.sh` をcron/systemdから呼ぶ。
詳細は `docs/PORTABLE_CI.md`。
