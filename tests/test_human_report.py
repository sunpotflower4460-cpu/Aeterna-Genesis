from ai_lab.dream import human_report
from ai_lab.dream import report as night_report


def _sample_report():
    return {
        "burst_id": "dream-technical-id",
        "generated_at": "2026-08-10T00:00:00+00:00",
        "counts": {
            "experiments": 2148,
            "expanded_trials": 2048,
            "native_jobs": 100,
            "new_behavior": 4,
            "reproduced": 8,
            "promotion_ready": 0,
            "stage_promoted": 0,
            "dimension_failure": 0,
            "negative_result": 0,
            "rare_event": 0,
            "numerical_warning": 0,
            "new_region": 125,
        },
        "headline_event_id": "X-b991d59a4d",
        "headline": None,
        "events": [],
        "honesty": {},
        "pure_genesis_r0": {
            "law_trials": 24,
            "top_laws": [{"id": "RLAW-secret", "priority": 0.55}],
            "root_integrity_audit": {
                "permutation_quotient_enabled": True,
                "critic_questions": [{"id": "RQC-secret"}],
            },
        },
        "zero_to_fission_path": {
            "deepest_code": "F4",
            "deepest_label": "三角形などの一時的な安定配置になる",
        },
        "one_line": "X-b991d59a4d repeated across seed values and amp_std increased",
    }


def test_first_read_starts_with_destination_then_current_position():
    summary = human_report.build_summary(_sample_report())
    md = human_report.render_markdown(summary)
    destination = md.index("要するに、目的地はどこか")
    current = md.index("現在地はどこか")
    achieved = md.index("今回できたこと")
    not_yet = md.index("まだできていないこと")
    next_q = md.index("次に確かめること")
    assert destination < current < achieved < not_yet < next_q


def test_first_read_hides_raw_ids_english_metrics_and_numbers():
    report = _sample_report()
    summary = human_report.build_summary(report)
    md = human_report.render_markdown(summary)
    assert human_report.first_read_violations(md) == []
    assert "X-b991d59a4d" not in md
    assert "RLAW-secret" not in md
    assert "amp_std" not in md
    assert "2048" not in md
    # The technical evidence is preserved in the source report rather than deleted.
    assert report["headline_event_id"] == "X-b991d59a4d"
    assert report["counts"]["experiments"] == 2148


def test_nightly_default_markdown_uses_human_summary_but_keeps_technical_renderer():
    report = _sample_report()
    report["human_summary"] = human_report.build_summary(report)
    first_read = night_report.render_markdown(report)
    technical = night_report.render_technical_markdown(report)
    assert "要するに、目的地はどこか" in first_read
    assert human_report.first_read_violations(first_read) == []
    assert "dream-technical-id" in technical
    assert "2148" in technical
