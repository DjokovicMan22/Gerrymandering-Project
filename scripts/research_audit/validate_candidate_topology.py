#!/usr/bin/env python3
"""Fail closed if a proximity-only Michigan graph cannot represent enacted plan.

The candidate links are non-legal, polygon-distance-based model proposals.
This audit deliberately checks *after* selecting links WITHOUT district labels.
Never silently add a sixth district-conditioned link to make enacted contiguous.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import networkx as nx

from verify_graph import digest, read_graph

PINNED_JSON="a4dfe70818f87b97924781216f3d86a672cfc66a"


def evaluate_candidate(graph:nx.Graph, manifest:dict)->dict:
    if manifest.get("graph_git_blob")!=PINNED_JSON:
        raise ValueError("Unexpected source blob")
    if manifest.get("physical_land_or_legal_island_contiguity_verified") is not False:
        raise ValueError("Only unc ertified candidate manifest may be used for this audit".replace("unc ertified","uncertified"))
    aug=graph.copy()
    add=manifest.get("edges",[])
    if not add or any(set(row)!={"u","v","separation_m"} for row in add):
        raise ValueError("Malformed edge manifest")
    inserted=set()
    for row in add:
        u,v=row["u"],row["v"]
        if u not in graph or v not in graph or u==v or graph.has_edge(u,v):
            raise ValueError(f"Invalid or already-existing bridge: {u},{v}")
        key=tuple(sorted((u,v)))
        if key in inserted:
            raise ValueError("Duplicate synthetic bridge")
        inserted.add(key)
        aug.add_edge(u,v,synthetic_geography_candidate=True,
                     physical_topology_certified=False,
                     polygon_separation_m=float(row["separation_m"]))
    orig_components=nx.number_connected_components(graph)
    if len(add)!=orig_components-1:
        raise ValueError("Expected component-connecting spanning-tree edge count")
    labels=sorted({str(data["CD"]) for _,data in aug.nodes(data=True)})
    per_cd={}
    for district in labels:
        nodes=[node for node,attr in aug.nodes(data=True) if str(attr["CD"])==district]
        sub=aug.subgraph(nodes)
        pieces=sorted((len(comp) for comp in nx.connected_components(sub)),reverse=True)
        per_cd[district]={"node_count":len(nodes),"component_sizes":pieces,
                          "component_count":len(pieces),
                          "connected_under_candidate_graph":len(pieces)==1}
    cut_artificial=[
        {"u":r["u"],"v":r["v"],
         "label_u":str(graph.nodes[r["u"]]["CD"]),
         "label_v":str(graph.nodes[r["v"]]["CD"])}
        for r in add if str(graph.nodes[r["u"]]["CD"])!=str(graph.nodes[r["v"]]["CD"])
    ]
    return {
        "original_source_components":orig_components,
        "candidate_graph_components":nx.number_connected_components(aug),
        "candidate_graph_connected":nx.is_connected(aug),
        "reference_districts":len(labels),
        "each_enacted_district_connected":all(v["connected_under_candidate_graph"] for v in per_cd.values()),
        "per_enacted_district":per_cd,
        "synthetic_boundary_cuts":cut_artificial,
        "candidate_uses_enacted_labels":False,
        "legal_geographic_contiguity_proven":False,
        "scientific_gate":(
            "PROXIMITY_GRAPH_REJECTED_FOR_ENACTED_BASELINE"
            if (not nx.is_connected(aug) or
                not all(v["connected_under_candidate_graph"] for v in per_cd.values()))
            else "ENACTED_BASELINE_TOPOLOGICALLY_CONNECTED_BUT_NOT_LEGALLY_CERTIFIED"
        ),
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if digest(args.graph)["git_blob_sha1"]!=PINNED_JSON:
        raise ValueError("Graph has changed")
    graph=read_graph(args.graph)
    result=evaluate_candidate(graph,json.loads(args.manifest.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2),flush=True)
    # Scientific invalidity is a reported gate rather than a code failure.
    return 0


if __name__=="__main__":
    raise SystemExit(main())
