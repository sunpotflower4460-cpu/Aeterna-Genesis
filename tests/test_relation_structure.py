from __future__ import annotations

import numpy as np

from genesis.diagnostics import relation_structure as rs


def _cycle(nodes, weight=1.0):
    ids = list(nodes)
    return [(ids[i], ids[(i + 1) % len(ids)], weight) for i in range(len(ids))]


def test_relation_matrix_instrument_uses_no_coordinates_or_target_geometry() -> None:
    r = np.zeros((8, 8), dtype=float)
    for i in range(7):
        r[i, i + 1] = r[i + 1, i] = 1.0 + i * 0.03
    # Distinct weak background avoids a giant threshold tie while remaining relation-only.
    for i in range(8):
        for j in range(i + 1, 8):
            if r[i, j] == 0:
                r[i, j] = r[j, i] = 0.01 + (i * 8 + j) * 1e-5
    graph = rs.graph_from_relation_matrix(r, edge_quantile=0.75)
    measured = rs.metric_with_controls(graph, seed=7)
    assert graph["coordinate_input_used"] is False
    assert graph["target_geometry_used"] is False
    assert graph["relation_matrix_labels_have_physical_identity"] is False
    assert measured["permutation_control_passed"] is True
    assert measured["physical_space_claim"] is False
    assert measured["fundamental_dimension_claim"] is False
    assert measured["gravity_claim"] is False


def test_label_permutation_preserves_relation_metric_signature() -> None:
    graph = rs.make_graph(10, [(i, i + 1, 1.0 + i * 0.01) for i in range(9)])
    a = rs.metric_with_controls(graph, seed=3, rewire_replicates=2)
    b = rs.metric_with_controls(rs.permute_graph_labels(graph, seed=99), seed=3, rewire_replicates=2)
    assert a["canonical_signature_digest"] == b["canonical_signature_digest"]
    assert a["component_sizes"] == b["component_sizes"]
    assert a["permutation_control_passed"] is True
    assert a["dimension_candidate"] is not None
    # A finite line-like relation graph should have roughly one-dimensional ball growth, but this is
    # only a graph diagnostic and never a physical-dimension assertion.
    assert 0.5 <= float(a["dimension_candidate"]) <= 1.5


def test_identity_tracker_ignores_node_labels_and_rejects_whole_system_as_individual() -> None:
    g1 = rs.make_graph(8, _cycle([0, 1, 2, 3], 1.0))
    g2 = rs.make_graph(8, _cycle([4, 6, 1, 7], 1.02))
    g3 = rs.make_graph(8, _cycle([2, 5, 0, 6], 1.04))
    result = rs.identity_continuity([g1, g2, g3], seed=4)
    assert result["association_rule_uses_node_labels"] is False
    assert result["observed"]["longest_track_frames"] == 3
    assert result["target_body_shape_used"] is False
    assert result["organism_claim"] is False
    assert result["life_claim"] is False

    whole = rs.make_graph(4, _cycle([0, 1, 2, 3], 1.0))
    whole_result = rs.identity_continuity([whole, whole, whole], seed=5)
    assert whole_result["observed"]["track_count"] == 0


def test_lineage_accounting_requires_persistent_parent_daughters_and_control_excess() -> None:
    parent0 = rs.make_graph(12, _cycle(range(8), 1.0))
    parent1 = rs.make_graph(12, _cycle([8, 3, 10, 1, 6, 11, 4, 7], 1.02))
    daughters_edges = (
        _cycle([0, 1, 2, 3], 1.0)
        + _cycle([4, 5, 6, 7], 1.0)
        + [(8, 9, 10.0)]
    )
    daughters2_edges = (
        _cycle([2, 8, 5, 11], 1.02)
        + _cycle([0, 4, 7, 9], 0.98)
        + [(1, 6, 10.0)]
    )
    daughter0 = rs.make_graph(12, daughters_edges)
    daughter1 = rs.make_graph(12, daughters2_edges)
    out = rs.lineage_accounting([parent0, parent1, daughter0, daughter1])
    assert out["candidate_event_count"] >= 1
    assert out["controlled_candidate_count"] >= 1
    assert out["status"] == "CONTROLLED_LINEAGE_ACCOUNTING_CANDIDATE"
    assert out["node_labels_used_as_parent_daughter_identity"] is False
    assert out["biological_cell_division_claim"] is False
    assert out["reproduction_claim"] is False
    assert out["heredity_claim"] is False


def test_series_keeps_metric_identity_and_lineage_claims_separate() -> None:
    graphs = [
        rs.make_graph(8, _cycle([0, 1, 2, 3], 1.0 + 0.02 * i))
        for i in range(5)
    ]
    out = rs.analyze_graph_series(graphs, seed=11)
    assert out["metric"]["instrument"] == "metric-from-relations"
    assert out["identity"]["instrument"] == "identity-continuity"
    assert out["lineage"]["instrument"] == "lineage-accounting"
    integrity = out["integrity"]
    assert integrity["target_morphology_seeded"] is False
    assert integrity["changes_dynamics"] is False
    assert integrity["physical_space_claim"] is False
    assert integrity["organism_or_life_claim"] is False
    assert integrity["biological_cell_division_claim"] is False
