from ai_lab.dream.upstream_run_gate import (
    CORE_RESEARCH_STEP,
    EXECUTED,
    NOOP,
    NOOP_STEP,
    RESEARCH_JOB,
    UNKNOWN,
    WATCHDOG_STEP,
    classify_jobs_payload,
)


def payload(core="success", watchdog="success", noop="skipped"):
    return {
        "jobs": [
            {
                "name": RESEARCH_JOB,
                "steps": [
                    {"name": WATCHDOG_STEP, "conclusion": watchdog},
                    {"name": NOOP_STEP, "conclusion": noop},
                    {"name": CORE_RESEARCH_STEP, "conclusion": core},
                ],
            }
        ]
    }


def test_real_research_run_is_not_noop():
    result = classify_jobs_payload(payload(core="success", noop="skipped"))
    assert result["classification"] == EXECUTED
    assert result["noop"] is False


def test_explicit_watchdog_skip_is_noop():
    result = classify_jobs_payload(payload(core="skipped", watchdog="success", noop="success"))
    assert result["classification"] == NOOP
    assert result["noop"] is True


def test_skipped_core_without_explicit_backup_step_fails_closed():
    result = classify_jobs_payload(payload(core="skipped", watchdog="success", noop="skipped"))
    assert result["classification"] == UNKNOWN
    assert result["noop"] is False


def test_missing_or_renamed_core_step_fails_closed():
    data = payload()
    data["jobs"][0]["steps"] = [
        {"name": WATCHDOG_STEP, "conclusion": "success"},
        {"name": NOOP_STEP, "conclusion": "success"},
    ]
    result = classify_jobs_payload(data)
    assert result["classification"] == UNKNOWN


def test_missing_research_job_fails_closed():
    result = classify_jobs_payload({"jobs": [{"name": "something-else", "steps": []}]})
    assert result["classification"] == UNKNOWN
