import copy

import pytest

from genesis.runners import runner
from genesis_orchestrator import campaign, db


def test_grid_compiles_deterministically():
    doc = {
        "schema_version": 1,
        "campaign_id": "test-campaign",
        "title": "test",
        "seeds": [0, 1],
        "hypotheses": [
            {
                "id": "h01",
                "statement": "test",
                "search": {
                    "grid": {
                        "noise_amplitude": [0.001, 0.003],
                        "quench_duration": [6.0, 8.0],
                    }
                },
            }
        ],
    }
    jobs = campaign.compile_campaign(doc)
    assert len(jobs) == 8
    assert len({job["job_id"] for job in jobs}) == 8
    assert all(job["stage"] == "2d-screen" for job in jobs)
    assert jobs[0]["genesis"]["model"] == runner._DEMO_GENESIS["model"]


def test_parent_model_lineage_mismatch_is_rejected(tmp_path):
    root = tmp_path
    (root / "schemas").mkdir()
    (root / "rooms").mkdir()
    (root / "genesis" / "registry").mkdir(parents=True)
    (root / "schemas" / "campaign.schema.json").write_text(
        (campaign.repo_root() / "schemas" / "campaign.schema.json").read_text()
    )
    (root / "genesis" / "registry" / "param_ranges.yaml").write_text(
        (campaign.repo_root() / "genesis" / "registry" / "param_ranges.yaml").read_text()
    )
    (root / "rooms" / "catalog.json").write_text(
        '{"rooms":[{"room_id":"room-other","genesis_model":"some_other_law"}]}'
    )
    doc = {
        "schema_version": 1,
        "campaign_id": "lineage-test",
        "title": "lineage",
        "parent_room": "room-other",
        "hypotheses": [
            {
                "id": "h01",
                "statement": "must reject",
                "search": {"variants": [{"overrides": {"noise_amplitude": 0.001}}]},
            }
        ],
    }
    with pytest.raises(ValueError, match="refusing to label one law"):
        campaign._semantic_validate(doc, root)


def test_db_claim_and_gated_next_stage(tmp_path):
    path = tmp_path / "queue.sqlite3"
    db.init_db(path)
    db.add_campaign(path, campaign_id="camp-001", title="x", document={}, source_path=None)
    genesis = copy.deepcopy(runner._DEMO_GENESIS)
    first = {
        "job_id": db.make_job_id("camp-001", "h01-v000", "2d-screen", 0),
        "campaign_id": "camp-001",
        "hypothesis_id": "h01",
        "trial_id": "h01-v000",
        "parent_room": "room-g001-a",
        "model": genesis["model"],
        "stage": "2d-screen",
        "stage_index": 0,
        "pipeline": ["2d-screen", "local-3d", "coarse-global-3d", "full-3d"],
        "approval_stages": ["coarse-global-3d", "full-3d"],
        "seed": 0,
        "quick": True,
        "genesis": genesis,
        "overrides": {"noise_amplitude": 0.001},
        "min_reached_level": 1,
        "status": "queued",
        "approved": True,
    }
    assert db.add_jobs(path, [first]) == 1
    claimed = db.claim_next(path)
    assert claimed and claimed["status"] == "running"
    db.finish_job(path, claimed["job_id"], result_room="room-x", reached_level=1,
                  checksum="abc", measured={}, output_dir="rooms/candidates/room-x")
    finished = db.get_job(path, claimed["job_id"])
    local = db.add_next_stage(path, finished, genesis)
    assert local and local["stage"] == "local-3d" and local["status"] == "queued"
    claimed_local = db.claim_next(path)
    assert claimed_local and claimed_local["stage"] == "local-3d"
    db.finish_job(path, claimed_local["job_id"], result_room="room-y", reached_level=1,
                  checksum="def", measured={}, output_dir="rooms/candidates/room-y")
    finished_local = db.get_job(path, claimed_local["job_id"])
    coarse = db.add_next_stage(path, finished_local, genesis)
    assert coarse and coarse["stage"] == "coarse-global-3d"
    assert coarse["status"] == "waiting_approval"
    assert db.claim_next(path) is None
    assert db.approve(path, campaign_id="camp-001", stage="coarse-global-3d") == 1
    assert db.claim_next(path)["stage"] == "coarse-global-3d"


@pytest.mark.parametrize("mode", ["2d-screen", "local-3d"])
def test_recorded_runner_is_checksum_identical_to_common_runner(mode):
    from genesis.runners.recorded_runner import run_recorded

    genesis = copy.deepcopy(runner._DEMO_GENESIS)
    plain = runner.run(genesis, mode=mode, quick=True)
    recorded = run_recorded(genesis, mode=mode, quick=True)
    assert recorded["manifest"]["checksum"] == plain["manifest"]["checksum"]
    assert recorded["manifest"]["summary"] == plain["manifest"]["summary"]
    field = recorded["recorder"].field_doc()
    assert field["nframes"] > 0
    assert field["dimension"] == (2 if mode == "2d-screen" else 3)
