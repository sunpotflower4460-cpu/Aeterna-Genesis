from collections import Counter

from genesis_orchestrator import campaign


def test_haiku_campaign_compiles_to_exactly_1000_initial_trials():
    root = campaign.repo_root()
    path = root / "ai_lab" / "campaigns" / "gl-haiku-1000.yaml"
    document = campaign.load_campaign(path, root=root)
    jobs = campaign.compile_campaign(document, source_path=str(path))

    assert len(jobs) == 1000
    assert len({job["job_id"] for job in jobs}) == 1000

    trial_counts = Counter(job["trial_id"] for job in jobs)
    assert len(trial_counts) == 200
    assert set(trial_counts.values()) == {5}

    assert {job["seed"] for job in jobs} == {0, 1, 2, 3, 4}
    assert all(job["stage"] == "2d-screen" for job in jobs)
    assert all(job["pipeline"] == ["2d-screen", "local-3d"] for job in jobs)
    assert all(job["approval_stages"] == [] for job in jobs)
