"""Synthetic evidence that the bridge audit detects county mismatches."""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
from gerrychain import Graph

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"/"research_audit"))
from audit_bridge_geography import bridge_audit_from_graph


def disconnected_graph(same_county):
    g=nx.Graph()
    g.add_node(0,CD="A",COUNTYFIPS="001",MCDFIPS="11")
    g.add_node(1,CD="A",COUNTYFIPS="001" if same_county else "003",
               MCDFIPS="12")
    return Graph.from_networkx(g)


def test_consistent_county_is_still_not_gis_certification():
    audit=bridge_audit_from_graph(disconnected_graph(True))
    assert audit["components_before"]==[1,1]
    assert audit["components_after"]==1
    assert audit["artificial_bridge_count"]==1
    assert audit["artificial_bridges"][0]["same_source_county"] is True
    assert audit["independent_gis_contiguity_certified"] is False
    assert "UNVERIFIED" in audit["county_label_audit_status"]


def test_different_counties_are_detected_not_silently_treated_as_valid():
    audit=bridge_audit_from_graph(disconnected_graph(False))
    assert audit["artificial_bridges"][0]["same_source_county"] is False
    assert audit["county_label_audit_status"].startswith("AT_LEAST_ONE")
    assert audit["artificial_bridges"][0]["same_enacted_district"] is True
    assert audit["artificial_bridges"][0]["county_legal_contiguity_verified"] is False
