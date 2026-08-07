from ai_lab.dream import deep_time


def test_next_effective_rung_skips_horizons_shorter_than_base_observation():
    # Ordinary quick geometry sees ~26 physical-time units. With tau=4, 4tau=16 is shorter,
    # so Deep Time must jump to 16tau=64 rather than relabeling the same short observation.
    assert deep_time.next_effective_rung(tau_ref=4.0, base_physical_time=26.0, last_rung=0.0) == 16.0


def test_next_effective_rung_requires_material_extension():
    # With tau=8, 4tau=32 is technically longer than 26 but only by ~23%.  That is not enough to
    # call it Deep Time under the 1.5x rule, so a fresh lead jumps to 16tau=128.
    assert deep_time.next_effective_rung(tau_ref=8.0, base_physical_time=26.0, last_rung=0.0) == 16.0


def test_deep_time_ladder_is_monotone_and_bounded():
    assert deep_time.next_effective_rung(tau_ref=8.0, base_physical_time=26.0, last_rung=4.0) == 16.0
    assert deep_time.next_effective_rung(tau_ref=8.0, base_physical_time=26.0, last_rung=16.0) == 64.0
    assert deep_time.next_effective_rung(tau_ref=8.0, base_physical_time=26.0, last_rung=64.0) is None


def test_candidate_key_depends_on_full_start_condition_and_seed():
    a = {"family": "white", "knobs": {"quench_duration": 8.0}, "seed": 1}
    b = {"family": "white", "knobs": {"quench_duration": 8.0}, "seed": 2}
    assert deep_time._candidate_key(a) != deep_time._candidate_key(b)
