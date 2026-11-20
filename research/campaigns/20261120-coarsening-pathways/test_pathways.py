"""Regression checks on exact budgets, periodic separation and tagged transport."""
import csv
import subprocess
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pytest

from coarsening_runs import PLAN, read_json, trials_for
from conformation_balance import conformation_balance
from mobility import MOBILITY_PLAN, trials_for as mobility_trials
from pathways import Snapshot, material_budget, number_budget, observe_transitions, region_gap_at_least
from survey import check_prefix
from track_domains import RegionFrame


def region_frame(labels, positions):
    by_molecule = labels.ravel(order="F")[positions]
    sizes = np.bincount(labels.ravel(), minlength=3)
    sizes[0] = 0
    return RegionFrame(labels, by_molecule, sizes, np.bincount(by_molecule, minlength=len(sizes)))


def test_matrix_differs_in_exactly_the_intended_mobility():
    main = trials_for(read_json(PLAN))
    conditions = mobility_trials(read_json(MOBILITY_PLAN))
    assert len(main) == len(conditions) == 6
    assert {job.n for job in main} == {56, 64}
    for condition in conditions:
        baseline = main[0].case | {"D_I": 100, "D_B": 100, "id": condition.case["id"], "kex": 150}
        changed = {key: value for key, value in condition.case.items() if baseline.get(key) != value}
        assert changed == {"D_" + condition.case["id"][-1]: 25}


def test_census_records_all_signed_changes():
    counts = {"many-to-one": (2, 1), "one-to-many": (1, 3), "many-to-many": (3, 2)}
    transition = {"events": [{"kind": kind, "sources": [None]*first, "targets": [None]*last}
                             for kind, (first, last) in counts.items()],
                  "unlinked_before": 1, "unlinked_after": 2, "before_regions": 7, "after_regions": 8}
    assert number_budget(transition) == {"one-to-one": 0, "many-to-one": -1,
                                         "one-to-many": 2, "many-to-many": -1,
                                         "unmatched_loss": -1, "unmatched_appearance": 2}
    with pytest.raises(ValueError, match="census"):
        number_budget(transition | {"after_regions": 9})


def test_moving_masks_can_have_balanced_inventory_with_nonzero_flux():
    a = np.zeros((4,)*3, dtype=int, order="F")
    b = np.zeros_like(a, order="F")
    a[0:2, 0, 0] = 1
    b[1:3, 0, 0] = 2
    old = np.array([0, 1, 3])
    new = np.array([0, 1, 2])
    budget = material_budget(region_frame(a, old), region_frame(b, new), old, new, 1, 2)
    assert budget["inventory_delta"] == 0
    assert budget["fixed_start_mask"]["net"] == 0
    assert budget["fixed_end_mask"]["unique_outside_to_inside"] == 1
    assert budget["twice_symmetric_hop_flux"] == 1
    assert budget["twice_symmetric_boundary_term"] == -1


def test_fixed_mask_net_equals_explicit_periodic_hop_ledger():
    n = 6
    mask = np.zeros((n,)*3, dtype=int, order="F")
    mask[:2, :, :] = 1
    starts = np.array([0, 10, 8])
    positions = starts.copy()
    movement = [(0, -1), (1, 1), (1, 1), (0, -1), (2, -1), (2, 1), (2, -1)]
    net = 0
    flat = mask.ravel(order="F")
    for molecule, hop in movement:
        source = positions[molecule]
        destination = source // n * n + (source % n + hop) % n
        assert destination not in positions
        positions[molecule] = destination
        net += int(flat[destination]) - int(flat[source])
    budget = material_budget(region_frame(mask, starts), region_frame(mask, positions),
                             starts, positions, 1, 1)
    assert budget["twice_symmetric_hop_flux"] == 2 * net
    assert budget["inventory_delta"] == net
    assert budget["twice_symmetric_boundary_term"] == 0


def test_periodic_gap_counts_the_shorter_path():
    mask = np.zeros((8,)*3, dtype=int)
    mask[1, 2, 2], mask[7, 2, 2] = 1, 2
    assert region_gap_at_least(mask, 1, 2)
    assert not region_gap_at_least(mask, 1, 3)


def test_shrinking_donor_with_same_ids_in_dilute_phase_then_recipient():
    settings = read_json(PLAN)["domains"]
    n = 20
    labels = np.zeros((n,)*3, dtype=int, order="F")
    labels[10:14, 1:5, 1:5] = 2
    recipient = np.flatnonzero(labels.ravel(order="F") == 2)
    positions = np.arange(n**3).reshape((n,)*3, order="F")
    donor = positions[1:5, 1:5, 1:5].ravel()
    bath = positions[2:10, :6, 9].ravel()
    snapshots, frames = [], []
    for i in range(8):
        membership = labels.copy(order="F")
        if i < 3:
            membership[1:6 if i == 0 else 5, 1:6 if i <= 1 else 5, 1:5] = 1
        remaining = [30, 24, 18, 0, 0, 0, 0, 0][i]
        tagged = np.concatenate((donor[:remaining], bath[remaining:30]))
        if i == 7:
            tagged[:7] = recipient[30:37]
        sites = np.concatenate((tagged, recipient[:30], bath[30:40]))
        density = np.where(membership > 0, 64, 0).astype(np.uint8)
        snapshots.append(Snapshot(i * 50, sites, density))
        frames.append(region_frame(membership, sites))
    rows = observe_transitions(snapshots, frames, settings)
    removed, = rows[2]["losses"]
    assert removed["status"] == "strict_separated_loss"
    assert removed["sites_before_loss"] == [100, 80, 64]
    assert removed["material_before_loss"] == [30, 24, 18]
    assert removed["cohort_dilute_at_loss"] == 30
    assert removed["witnessed_same_id_routes"] == 7
    assert removed["expected_routes_uniform_dilute_cohort"] == 30 * 7 / 40
    truncated = observe_transitions(snapshots[:-1], frames[:-1], settings)
    assert truncated[2]["losses"][0]["transport_censored"] is True


def test_prefix_requires_same_state_even_if_the_ledger_agrees(tmp_path):
    old = tmp_path / "old.zip"
    history = {f"state-0-{name}.bin": b"baseline" for name in
               ("cells", "conformers", "positions", "displacements")}
    history["series.csv"] = b"time,B\n0,10\n"
    with ZipFile(old, "w") as archive:
        for name, data in history.items():
            archive.writestr(name, data)
    memory = BytesIO()
    with ZipFile(memory, "w") as archive:
        for name, data in (history | {"state-0-positions.bin": b"changed"}).items():
            archive.writestr(name, data)
    with ZipFile(memory) as archive, pytest.raises(ValueError, match="positions"):
        check_prefix(archive, old)


def test_observer_keeps_repeated_hops_and_conformation_direction(tmp_path):
    header = Path(__file__).with_name("fixed_boundary_observer.hpp")
    source = tmp_path / "exercise.cpp"
    source.write_text('''#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>
#include "fixed_boundary_observer.hpp"

int main(int argc, char** argv) {
  FixedBoundaryObserver audit(argv[1], 4);
  audit.hop(1, 0, 3);
  audit.sample(1200);
  audit.hop(1, 0, 1);
  audit.hop(1, 1, 3);
  audit.hop(1, 3, 1);
  audit.hop(2, 3, 2);
  audit.hop(3, 3, 1);
  audit.sample(1250);
}
''')
    masks = np.tile(np.array([1, 1, 2, 0], dtype="<i4"), 8)
    (tmp_path / "observer-masks.bin").write_bytes(masks.tobytes())
    binary = tmp_path / "exercise"
    subprocess.run(["g++", "-std=c++17", "-I", str(header.parent), str(source), "-o", str(binary)], check=True)
    subprocess.run([str(binary), str(tmp_path)], check=True)
    with (tmp_path / "boundary-hops.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 8
    for row in rows:
        counts = tuple(int(row[field]) for field in ("in_I", "out_I", "in_B", "out_B"))
        assert counts == ((1, 1, 0, 0) if row["label"] == "1" else (0, 0, 1, 0))


def test_conformation_balance_matches_both_inventories():
    terms = conformation_balance(-3, 5, 8, 6, 5, 5)
    assert terms == {"delta_I": -3, "delta_B": 5, "net_I_hops": 2, "net_B_hops": 0, "net_I_to_B": 5}
    with pytest.raises(ValueError, match="conversion"):
        conformation_balance(-3, 6, 8, 6, 5, 5)
