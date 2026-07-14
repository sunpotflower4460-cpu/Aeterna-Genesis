"""Frontier Campaign M2-D: use the existence gate as the OBJECTIVE of a broad search for a stable localized
individual to measure drift on. ANTI_DRIFT-clean: we MEASURE where a stable individual exists, we do NOT hunt
a moving model. Across the documented grid (5 physical axes) the three-component RD yields NO compact
localized STATIONARY single individual -- it dies, the "+" state fills, or the background fragments into a
labyrinth. So the drift measurement is BLOCKED by an existence frontier UPSTREAM of drift (N0, white/domain-
specific). Combined with M2-B (the one white with a stable individual, SH, has no drift mode), this is the M2
"scissors": a white has EITHER a stable individual OR the drift mechanism, not both, in this repo's whites.
no_touch: measures.py untouched. Physical quantity (localization/stationarity) FIRST.
"""

from genesis.models import three_component_rd as rd


def test_existence_scan_finds_no_stable_individual():
    """Representative grid spanning die / fill / fragment: the existence gate PASSES nowhere -> no stable
    compact single stationary individual exists to linearise (existence frontier upstream of drift)."""
    grid = [{"k1": 0.02}, {"k1": 0.0}, {"k3": 1.0, "k1": 0.0}, {"Dv": 1.0, "Dw": 80.0, "k1": 0.01}]
    res = rd.existence_scan(grid, N=64, settle=3000, seed=1)
    assert len(res) == len(grid)
    assert all(r["gate"] == "REFUSED" for r in res)              # no stable individual anywhere in the grid
    assert sum(1 for r in res if r["gate"] == "PASSED") == 0
    # every refusal names a physical reason (not a silent skip)
    assert all(r.get("reason") in ("no_localized_individual", "not_stationary", "blow_up") for r in res)


def test_existence_scan_is_deterministic():
    """Same seed -> identical verdicts (reproducible no-go, not seed-luck)."""
    grid = [{"k1": 0.0}, {"k3": 1.0, "k1": 0.0}]
    a = rd.existence_scan(grid, N=64, settle=3000, seed=1)
    b = rd.existence_scan(grid, N=64, settle=3000, seed=1)
    assert [x["gate"] for x in a] == [x["gate"] for x in b]
    assert [x["count"] for x in a] == [x["count"] for x in b]
