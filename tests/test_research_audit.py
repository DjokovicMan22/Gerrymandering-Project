"""Synthetic regression tests for the Stage 1–3 validation utilities.

No real Michigan data and no production MCMC chain is executed by these tests.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import pytest
from networkx.readwrite import json_graph

ROOT = Path(__file__).resolve().parents[1]
MOD_DIR = ROOT / "scripts" / "research_audit"
sys.path.insert(0, str(MOD_DIR))

import verify_graph
import analyze_chains


def sample_graph():
    graph = nx.path_graph(4)
    for n in graph:
        graph.nodes[n].update({
            "PRECINCTID": f"precinct-{n}", "CD": 1 if n < 2 else 2,
            "TOTPOP": 100, "PRE16D": 10, "PRE16R": 10,
            "PRE20D": 12, "PRE20R": 8,
        })
    return graph


def test_json_graph_roundtrip_and_integrity(tmp_path):
    data = json_graph.adjacency_data(sample_graph())
    path = tmp_path / "tiny.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    graph = verify_graph.read_graph(path)
    report = verify_graph.validate(graph)
    assert report["errors"] == []
    assert report["nodes"] == 4 and report["edges"] == 3
    assert report["district_count"] == 2
    assert report["total_population"] == 400
    assert report["max_population_deviation"] == pytest.approx(0.0)
    assert report["reference_cut_edges_without_bridges"] == 1
    assert all(report["district_graph_contiguous_without_bridges"].values())
    assert len(verify_graph.digest(path)["sha256"]) == 64
    assert len(verify_graph.digest(path)["git_blob_sha1"]) == 40


def test_duplicate_precinct_and_invalid_votes_fail():
    graph = sample_graph()
    graph.nodes[1]["PRECINCTID"] = "precinct-0"
    graph.nodes[2]["PRE20D"] = -1
    errors = verify_graph.validate(graph)["errors"]
    assert any("duplicated" in e for e in errors)
    assert any("invalid PRE20D" in e for e in errors)


def test_missing_field_fails():
    graph = sample_graph()
    del graph.nodes[3]["TOTPOP"]
    report = verify_graph.validate(graph)
    assert any("missing fields" in e for e in report["errors"])


def test_chain_reader_rejects_step_duplicates(tmp_path):
    frame = pd.DataFrame({"step": [0, 1, 1, 3, 4, 5, 6, 7, 8, 9],
                          **{name: [1.0] * 10 for name in analyze_chains.FIELDS}})
    paths = [tmp_path / f"chain_{i}.csv" for i in (1, 2)]
    for path in paths:
        frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicated"):
        analyze_chains.read_chains(paths, burn_in=1)


def test_chain_reader_requires_equal_budgets(tmp_path):
    paths = [tmp_path / f"chain_{i}.csv" for i in (1, 2)]
    for index, path in enumerate(paths):
        frame = pd.DataFrame({"step": range(12 + index),
                              **{name: [1.0] * (12 + index)
                                 for name in analyze_chains.FIELDS}})
        frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="matched"):
        analyze_chains.read_chains(paths, burn_in=2)


def test_chain_reader_preserves_post_burn_in(tmp_path):
    paths = [tmp_path / f"chain_{i}.csv" for i in (1, 2)]
    for index, path in enumerate(paths):
        frame = pd.DataFrame({"step": range(12),
                              **{name: [float(index + j) for j in range(12)]
                                 for name in analyze_chains.FIELDS}})
        frame.to_csv(path, index=False)
    chains = analyze_chains.read_chains(paths, burn_in=3)
    assert len(chains) == 2
    assert all(len(df) == 9 for df in chains.values())
    assert all(df["step"].iloc[0] == 3 for df in chains.values())
