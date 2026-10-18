"""Regression tests for actual warm-start Partition reconstruction and cohort provenance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import networkx as nx
import pandas as pd
import pytest
from gerrychain import Graph, Partition

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research_audit"))

from analyze_diversified_chains import check_cohort
from run_diversified_chains import reconstruct_warmed_partition
from redistricting.ensemble.partition import make_updaters
from redistricting.ensemble.start_diversity import assignment_digest


def test_warmup_map_really_becomes_chain_step_zero():
    graph = nx.cycle_graph(6)
    for i in graph.nodes:
        graph.nodes[i].update({
            "TOTPOP": 100,
            "PRE20D": 40,
            "PRE20R": 60,
            "CD": "A" if i < 3 else "B",
        })
    partition = Partition(
        graph=Graph.from_networkx(graph),
        assignment="CD",
        updaters=make_updaters(),
    )
    warmed_assignment = {
        i: ("A" if i in (1, 2, 3) else "B") for i in range(6)
    }
    warmed = reconstruct_warmed_partition(partition, warmed_assignment)
    assert dict(warmed.assignment.items()) == warmed_assignment
    assert dict(partition.assignment.items()) != warmed_assignment
    assert assignment_digest(dict(warmed.assignment.items())) == assignment_digest(warmed_assignment)
    assert warmed["population"]["A"] == 300
    assert warmed["population"]["B"] == 300
    assert len(warmed["cut_edges"]) == 2
    assert sum(warmed["dem_votes"].values()) == 240


def test_reconstruction_rejects_missing_nodes_and_changed_districts():
    graph = nx.path_graph(4)
    for i in graph.nodes:
        graph.nodes[i].update(TOTPOP=100, PRE20D=50, PRE20R=50)
    ref = Partition(
        graph=Graph.from_networkx(graph),
        assignment={0:"A", 1:"A", 2:"B", 3:"B"},
        updaters=make_updaters(),
    )
    with pytest.raises(ValueError, match="node set"):
        reconstruct_warmed_partition(ref, {0:"A", 1:"B", 2:"B"})
    with pytest.raises(ValueError, match="district-label"):
        reconstruct_warmed_partition(ref, {0:"A", 1:"A", 2:"A", 3:"A"})


def _write_four_chains(tmp_path):
    references = []
    metas = []
    chains = []
    ref = {"step":0, "dem_seats":7, "efficiency_gap":.003333,
           "mean_median":-.014, "cut_edges":681,
           "max_population_deviation":.004}
    for i, seed in enumerate((101, 202, 303, 404)):
        stem = f"mi_2020_diverse_closer_warm{seed}_sample{1000+seed}_201steps"
        plan = tmp_path / f"{stem}_plan_metrics.csv"
        metadata = tmp_path / f"{stem}_metadata.json"
        reference = tmp_path / f"{stem}_reference.json"
        # The sample first state is deliberately NOT the enacted reference.
        pd.DataFrame({
            "step": list(range(201)),
            "dem_seats": [5 + i] * 201,
            "efficiency_gap": [-.15 + i*.01] * 201,
            "mean_median": [-.02] * 201,
            "cut_edges": [720] * 201,
            "max_population_deviation": [.003] * 201,
        }).to_csv(plan, index=False)
        meta = {
            "condition":"closer", "warmed_step0_is_reference":False,
            "warmup_metadata":{"seed":seed,
                               "warmup_states_including_reference":800,
                               "final_assignment_sha256":str(seed)*8},
            "sample_seed": 1000 + seed,
            "source_sha256":"a" * 64, "source_git_blob":"b" * 40,
            "sample_steps_including_warm_start":201,
            "warmup_distance_from_enacted":{"fraction_different":.12 + .01*i},
            "final_sample_distance_from_warm_start":{"fraction_different":.1},
            "geographic_proxy_caps":{"max_cut_edges":760,
                                     "max_split_counties":18,
                                     "max_split_county_mcd":20},
            "reference_election_scores":ref,
        }
        metadata.write_text(json.dumps(meta), encoding="utf-8")
        reference.write_text(json.dumps(ref), encoding="utf-8")
        chains.append(plan)
        metas.append(metadata)
        references.append(reference)
    return chains, metas, references, ref


def test_reference_scores_come_from_reference_json_not_warmed_step_zero(tmp_path):
    chains, metas, references, original = _write_four_chains(tmp_path)
    scores, infos = check_cohort(chains[::-1], metas, references[::-1], "closer")
    assert scores["dem_seats"] == original["dem_seats"] == 7
    assert pd.read_csv(chains[0]).iloc[0]["dem_seats"] == 5
    assert len(infos) == 4


def test_metadata_mismatch_aborts_instead_of_silently_pooling(tmp_path):
    chains, metas, references, _ = _write_four_chains(tmp_path)
    changed = json.loads(metas[0].read_text())
    changed["warmup_metadata"]["final_assignment_sha256"] = "202" * 8
    metas[0].write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="Warmup maps"):
        check_cohort(chains, metas, references, "closer")


def test_reference_mismatch_aborts(tmp_path):
    chains, metas, references, _ = _write_four_chains(tmp_path)
    bad = json.loads(references[0].read_text())
    bad["cut_edges"] = 999
    references[0].write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="reference disagreement"):
        check_cohort(chains, metas, references, "closer")
