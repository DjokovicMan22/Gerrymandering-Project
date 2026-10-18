"""Synthetic adversarial tests for geographic fragmentation proxies.

No Michigan file is required. Counts use source precinct grouping identifiers,
not independently certified municipal boundaries.
"""
from __future__ import annotations

import networkx as nx
import pytest

from redistricting.ensemble.geographic import (
    GeographicCaps, GeographicEvaluator, count_split_groups,
)


class FakePartition:
    def __init__(self, graph, assignment):
        self.graph = graph
        self.assignment = assignment
        self._cuts = {(u, v) for u, v in graph.edges
                      if assignment[u] != assignment[v]}

    def __getitem__(self, key):
        assert key == "cut_edges"
        return self._cuts


def graph_with_group_keys():
    g = nx.path_graph(6)
    for node in g:
        g.nodes[node]["COUNTYFIPS"] = "001" if node < 3 else "003"
        g.nodes[node]["MCDFIPS"] = ("101" if node % 3 < 2 else "102")
    return g


def test_count_group_splits_as_distinct_groups_not_border_edges():
    g = graph_with_group_keys()
    ref = FakePartition(g, {0: "A", 1: "A", 2: "B",
                            3: "B", 4: "B", 5: "B"})
    evaluator = GeographicEvaluator(g, GeographicCaps(2, 1, 0))
    assert evaluator.score(ref) == {
        "cut_edges": 1,
        "split_counties": 1,
        "split_county_mcd": 0,
    }
    assert evaluator.validate_reference(ref) == evaluator.score(ref)
    assert evaluator(ref)


def test_county_and_municipality_caps_reject_real_split():
    g = graph_with_group_keys()
    a = FakePartition(g, {0: "A", 1: "B", 2: "B",
                          3: "B", 4: "A", 5: "B"})
    assert GeographicEvaluator(g, GeographicCaps(max_split_counties=1))(a) is False
    assert GeographicEvaluator(g, GeographicCaps(max_split_county_mcd=1))(a) is False
    assert GeographicEvaluator(g, GeographicCaps(max_cut_edges=2))(a) is False


def test_source_key_is_county_plus_mcd_not_mcd_alone():
    g = graph_with_group_keys()
    assignment = {0: "A", 1: "A", 2: "A", 3: "B", 4: "B", 5: "B"}
    ev = GeographicEvaluator(g, GeographicCaps(None, 0, 0))
    assert ev.score(FakePartition(g, assignment))["split_county_mcd"] == 0


def test_invalid_source_attributes_fail_closed():
    g = graph_with_group_keys()
    del g.nodes[0]["MCDFIPS"]
    with pytest.raises(ValueError, match="Missing or invalid MCDFIPS"):
        GeographicEvaluator(g, GeographicCaps(max_split_county_mcd=1))
    # A county-only cap does not require a missing MCD attribute.
    GeographicEvaluator(g, GeographicCaps(max_split_counties=1))


def test_invalid_caps_and_initial_state_are_rejected():
    with pytest.raises(ValueError, match="nonnegative integer"):
        GeographicCaps(max_cut_edges=-1)
    with pytest.raises(ValueError, match="nonnegative integer"):
        GeographicCaps(max_split_counties=1.0)
    g = graph_with_group_keys()
    ref = FakePartition(g, {0: "A", 1: "A", 2: "B",
                            3: "B", 4: "B", 5: "B"})
    with pytest.raises(ValueError, match="Starting map exceeds"):
        GeographicEvaluator(g, GeographicCaps(max_cut_edges=0)).validate_reference(ref)


def test_only_needed_fields_must_be_present():
    g = nx.path_graph(2)
    partition = FakePartition(g, {0: "A", 1: "B"})
    ev = GeographicEvaluator(g, GeographicCaps(max_cut_edges=1))
    assert ev(partition)
    assert ev.score(partition) == {"cut_edges": 1}


def test_count_split_groups_counts_each_partition_group_once():
    groups = {"county1": (0, 1, 2), "county2": (3, 4, 5)}
    assignment = {0: 1, 1: 2, 2: 3, 3: 4, 4: 4, 5: 4}
    assert count_split_groups(assignment, groups) == 1
