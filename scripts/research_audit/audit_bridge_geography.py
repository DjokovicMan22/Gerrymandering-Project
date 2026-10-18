#!/usr/bin/env python3
"""Audit artificial precinct-graph bridge county identity against source labels.

This is NOT a geographic contiguity certification: FIPS agreement cannot prove
land adjacency or legally applicable island-contiguity treatment. An observed
cross-county bridge is a concrete source-data inconsistency requiring review.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
from gerrychain import Graph

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from redistricting.ensemble.partition import _connect_components_within_district
from verify_graph import digest

BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"


def bridge_audit_from_graph(graph) -> dict:
    """Return sufficient facts for independent review without inferring geometry."""
    source=graph.get_nx_graph()
    original_components=sorted([len(x) for x in nx.connected_components(source)],reverse=True)
    # This mutates only an in-memory graph loaded exclusively for the audit.
    added=_connect_components_within_district(graph)
    records=[]
    for u,v,chosen_cd in added:
        left,right=source.nodes[u],source.nodes[v]
        county_left=str(left.get("COUNTYFIPS", "")).strip()
        county_right=str(right.get("COUNTYFIPS", "")).strip()
        cd_left=str(left.get("CD","")).strip()
        cd_right=str(right.get("CD","")).strip()
        county_consistent=bool(county_left and county_right and
                               county_left not in ("None","nan") and
                               county_right not in ("None","nan") and
                               county_left==county_right)
        records.append({
            "node_a":str(u),"node_b":str(v),
            "cd_a":cd_left,"cd_b":cd_right,"chosen_cd":str(chosen_cd),
            "county_a":county_left or None,"county_b":county_right or None,
            "mcd_a":str(left.get("MCDFIPS", "")),"mcd_b":str(right.get("MCDFIPS", "")),
            "same_source_county":county_consistent,
            "same_enacted_district":cd_left==cd_right==str(chosen_cd),
            "physical_land_adjacent":None,
            "island_status_from_authoritative_geometry":None,
            "county_legal_contiguity_verified":False,
            "reason": "Artificial algorithmic graph connection, not an externally verified border.",
        })
    status=("COUNTY_LABELS_MATCH_BUT_PHYSICAL_GEOGRAPHY_UNVERIFIED"
            if all(x["same_source_county"] for x in records)
            else "AT_LEAST_ONE_COUNTY_LABEL_MISMATCH_OR_MISSING")
    return {
        "node_count":len(source),
        "components_before":original_components,
        "components_after":nx.number_connected_components(source),
        "artificial_bridge_count":len(records),
        "artificial_bridges":records,
        "county_label_audit_status":status,
        "independent_gis_contiguity_certified":False,
        "constitutional_source":"https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6",
        "official_mapping_data":"https://www.michigan.gov/micrc/mapping-process/mapping-data",
        "legal_rule_note":(
            "Article IV section 6(13)(b) treats island areas as contiguous by land "
            "to the county of which they are part; numerical graph connections "
            "between districts or counties do not establish that rule."
        ),
        "research_warning":(
            "County FIPS agreement is only a necessary source-data plausibility "
            "check for this modeling assumption, not legal/topological validation. "
            "Official water, county, and precinct geometries must be inspected."
        ),
    }


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if digest(args.graph)["git_blob_sha1"] != BLOB:
        raise ValueError("Graph bytes do not match pinned Michigan source")
    graph=Graph.from_json(str(args.graph))
    result=bridge_audit_from_graph(graph)
    result["source_git_blob"]=BLOB
    result["generated_utc"]=datetime.now(timezone.utc).isoformat()
    if result["node_count"]!=4756 or result["artificial_bridge_count"]!=5:
        raise ValueError("Unexpected 2020 Michigan topology or bridge count; refuse stale audit")
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2),flush=True)
    print("CAUTION: this report is a SOURCE-ATTRIBUTE audit, NOT island/county topology certification.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
