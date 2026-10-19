"""Adversarial Stage 1–2 data and archived-history integrity tests."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest
from gerrychain import Graph

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"research_audit"))
from stage12_archive_reanalysis import load_csv_bytes
from redistricting.ensemble.partition import validate_node_fields


def metric_frame():
    return pd.DataFrame({
        "step": list(range(12)),
        "dem_seats": [7]*12,
        "efficiency_gap": [0.1]*12,
        "mean_median": [0.01]*12,
        "cut_edges": [3]*12,
        "max_population_deviation": [0.004]*12,
    })


def check(df):
    return load_csv_bytes(df.to_csv(index=False).encode(),name="synthetic.csv",
                          steps=12,tolerance=.005)


def test_archive_numeric_baseline_is_finite():
    assert len(check(metric_frame()))==12


@pytest.mark.parametrize("field,bad",[
    ("dem_seats",13.5),("dem_seats",14),("cut_edges",-1),
    ("efficiency_gap",float("nan")),("mean_median",float("inf")),
    ("max_population_deviation",.006),
])
def test_archive_bad_numeric_rejected(field,bad):
    df=metric_frame()
    df.loc[3,field]=bad
    with pytest.raises(ValueError):
        check(df)


def test_archive_missing_and_duplicate_step_rejected():
    df=metric_frame()
    df.loc[3,"step"]=2
    with pytest.raises(ValueError,match="distinct"):
        check(df)
    df=metric_frame().drop(columns=["mean_median"])
    with pytest.raises(ValueError,match="missing fields"):
        check(df)


def source_graph():
    g=nx.path_graph(4)
    for n in g:
        g.nodes[n].update({"CD":1 if n<2 else 2,"TOTPOP":100,
                           "PRE20D":40,"PRE20R":60})
    return g


def validate(g):
    validate_node_fields(Graph.from_networkx(g),("CD","TOTPOP","PRE20D","PRE20R"))


def test_source_precinct_gate_accepts_valid_numeric():
    validate(source_graph())


@pytest.mark.parametrize("field,bad",[
    ("TOTPOP",float("nan")),("TOTPOP",float("inf")),("TOTPOP",-1),
    ("TOTPOP","not a number"),("PRE20D",float("nan")),
    ("PRE20R",float("-inf")),("PRE20R",-1),("PRE20D","n/a"),
])
def test_source_precinct_gate_rejects_nonfinite_negative_or_nonnumeric(field,bad):
    g=source_graph()
    g.nodes[0][field]=bad
    with pytest.raises(ValueError,match="Invalid"):
        validate(g)


def test_source_precinct_gate_rejects_missing():
    g=source_graph()
    del g.nodes[0]["PRE20D"]
    with pytest.raises(KeyError,match="Missing"):
        validate(g)


def test_source_precinct_gate_rejects_zero_two_party_vote_district():
    g=source_graph()
    for n in (2,3):
        g.nodes[n]["PRE20D"]=0
        g.nodes[n]["PRE20R"]=0
    with pytest.raises(ValueError,match="zero two-party"):
        validate(g)
