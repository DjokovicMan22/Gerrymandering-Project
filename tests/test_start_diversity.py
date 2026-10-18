"""Fast, adversarial tests for exact district-label-invariant start diversity."""
from __future__ import annotations

import pytest

from redistricting.ensemble.start_diversity import (
    WarmStartConfig,
    assignment_digest,
    compare_seeded_endpoints,
    label_invariant_distance,
    normalized_assignment,
)


def test_swapping_entire_district_labels_does_not_create_diversity():
    enacted = {i: "A" if i < 5 else "B" for i in range(10)}
    relabeled = {i: "B" if i < 5 else "A" for i in range(10)}
    out = label_invariant_distance(enacted, relabeled)
    assert out["different_nodes"] == 0
    assert out["fraction_different"] == 0
    assert out["optimally_matched_nodes"] == 10


def test_optimal_relabeling_not_naive_label_matching():
    a = {i: ("A" if i < 4 else "B") for i in range(8)}
    b = {i: ("X" if i < 3 else "Y") for i in range(8)}
    out = label_invariant_distance(a, b)
    # Match A->X (3), B->Y (4): exactly one different node.
    assert out["different_nodes"] == 1
    assert out["fraction_different"] == pytest.approx(1/8)


def test_thirteen_districts_exact_permutation_solver():
    a = {i: i // 4 for i in range(52)}
    b = {i: (i // 4 + 7) % 13 for i in range(52)}
    assert label_invariant_distance(a, b)["different_nodes"] == 0
    b[0] = b[4]
    result = label_invariant_distance(a, b)
    assert result["different_nodes"] == 1


def test_same_nodes_same_number_of_districts_required():
    with pytest.raises(ValueError, match="same nonempty precinct node set"):
        label_invariant_distance({0: 1, 1: 2}, {0: 1})
    with pytest.raises(ValueError, match="same district count"):
        label_invariant_distance({0: 1, 1: 2}, {0: 1, 1: 1})
    with pytest.raises(ValueError, match="same nonempty precinct"):
        label_invariant_distance({}, {})


def test_hash_is_order_invariant_and_rejects_colliding_node_conversions():
    a = {1: "A", 2: "B"}
    assert assignment_digest(a) == assignment_digest({2:"B", 1:"A"})
    with pytest.raises(ValueError, match="collide"):
        normalized_assignment({1:"A", "1":"B"})


def test_diversity_gate_detects_same_map_with_different_labels():
    reference = {i: "A" if i < 4 else "B" for i in range(8)}
    seeds = {
        101: {i: "B" if i < 4 else "A" for i in range(8)},
        202: dict(reference),
    }
    rows, passed = compare_seeded_endpoints(reference, seeds,
                                            minimum_reference_distance=.05,
                                            minimum_pairwise_distance=.05)
    assert len(rows) == 3
    assert passed is False
    assert all(row["fraction_different"] == 0 for row in rows)


def test_gate_succeeds_for_different_unlabeled_partitions():
    ref = {i: ("A" if i < 3 else "B") for i in range(8)}
    first = {i: ("A" if i < 2 else "B") for i in range(8)}
    second = {i: ("A" if i < 5 else "B") for i in range(8)}
    rows, passed = compare_seeded_endpoints(ref, {101:first, 202:second},
                                            minimum_reference_distance=.1,
                                            minimum_pairwise_distance=.1)
    assert passed
    assert sorted(round(row["fraction_different"], 3) for row in rows) == [.125, .25, .375]


def test_invalid_warmup_config_and_thresholds_rejected():
    with pytest.raises(ValueError, match="warmup"):
        WarmStartConfig(steps_including_reference=1).validate()
    with pytest.raises(ValueError, match="cap"):
        WarmStartConfig(max_cut_edges=None, max_split_counties=None,
                        max_split_county_mcd=None).validate()
    with pytest.raises(ValueError, match="thresholds"):
        compare_seeded_endpoints({0:1,1:2}, {1:{0:1,1:2}, 2:{0:1,1:2}},
                                 minimum_pairwise_distance=1.1)
