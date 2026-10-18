#!/usr/bin/env python3
"""Create LABEL-AGNOSTIC shortest-distance graph-repair candidates from pinned GIS.

Each disconnected component is connected by exactly one edge in a minimum
spanning tree of COMPONENTS, with edge weights equal to the minimum Euclidean
distance between its precinct polygon geometries (meters in EPSG:32616).

This establishes spatial proximity, not legal island contiguity or transport
connectivity. The candidates are REVIEW-REQUIRED, never silently certified.
Crucially: the enacted district assignment CD is *not* used to choose edges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import networkx as nx
from shapely.strtree import STRtree

from geometry_bridge_validation import (
    JSON_GIT_BLOB,ZIP_GIT_BLOB,align_precincts,git_blob,
)
from verify_graph import read_graph,digest


def best_between(components:list[set], a:int, b:int, geometry:list, index:dict)->dict:
    left,right=components[a],components[b]
    # STRtree on the larger component; query every polygon in the smaller one.
    if len(left)<len(right):
        small,big=left,right
    else:
        small,big=right,left
    ordered_big=sorted(big)
    tree=STRtree([geometry[index[str(n)]] for n in ordered_big])
    best=(math.inf,None,None)
    for n in sorted(small):
        g=geometry[index[str(n)]]
        closest=tree.nearest(g)
        if closest is None:
            raise ValueError("No nearest source polygon available")
        other=ordered_big[int(closest)]
        dist=float(g.distance(geometry[index[str(other)]]))
        if not math.isfinite(dist) or dist<0:
            raise ValueError("Bad geometry distance")
        u,v=sorted((int(n),int(other)))
        candidate=(dist,u,v)
        if candidate<best:
            best=candidate
    return {
        "component_a":a, "component_b":b, "node_a":best[1],
        "node_b":best[2], "polygon_distance_meters":best[0],
    }


def geometric_mst_candidates(graph:nx.Graph, shapes:gpd.GeoDataFrame, alignment:dict)->dict:
    components=[set(x) for x in sorted(nx.connected_components(graph),
                                       key=lambda c:(-len(c),min(c)))]
    if len(components)<2:
        raise ValueError("Expected disconnected original input for bridge study")
    if not all(isinstance(n,int) for n in graph):
        raise ValueError("Candidate edge algorithm requires integer source node identifiers")
    geom=list(shapes.geometry)
    index=alignment["mapping"]
    candidates=[]
    G=nx.Graph()
    G.add_nodes_from(range(len(components)))
    for a in range(len(components)):
        for b in range(a+1,len(components)):
            best=best_between(components,a,b,geom,index)
            G.add_edge(a,b,weight=best["polygon_distance_meters"],data=best)
            candidates.append(best)
    mst=nx.minimum_spanning_tree(G,weight="weight",algorithm="kruskal")
    selected=[G.edges[a,b]["data"] for a,b in sorted(mst.edges())]
    augmented=graph.copy()
    for proposal in selected:
        u,v=proposal["node_a"],proposal["node_b"]
        if graph.has_edge(u,v):
            raise AssertionError("A disconnected-component candidate cannot already be an edge")
        augmented.add_edge(u,v,geometric_candidate=True,
                           polygon_distance_meters=proposal["polygon_distance_meters"])
    if not nx.is_connected(augmented) or len(selected)!=len(components)-1:
        raise AssertionError("Candidate component MST failed to connect graph")
    scored=[]
    for edge in selected:
        u,v=edge["node_a"],edge["node_b"]
        scored.append({
            **edge,
            "county_a":str(graph.nodes[u].get("COUNTYFIPS")),
            "county_b":str(graph.nodes[v].get("COUNTYFIPS")),
            "same_source_county":str(graph.nodes[u].get("COUNTYFIPS"))==
                                 str(graph.nodes[v].get("COUNTYFIPS")),
            "enacted_district_a":str(graph.nodes[u].get("CD")),
            "enacted_district_b":str(graph.nodes[v].get("CD")),
            "same_enacted_district_not_used_for_selection":
                str(graph.nodes[u].get("CD"))==str(graph.nodes[v].get("CD")),
            "confirmed_legal_island_or_land_contiguity":False,
        })
    return {
        "method":"minimum_spanning_tree_of_original_components_using_exact_projected_polygon_separation",
        "algorithm_does_not_consult_enacted_district_labels":True,
        "original_component_sizes":[len(c) for c in components],
        "all_pair_shortest_distances":sorted(candidates,key=lambda c:(c["component_a"],c["component_b"])),
        "selected_graph_edges":scored,
        "total_proposed_bridge_distance_meters":sum(c["polygon_distance_meters"] for c in selected),
        "maximum_proposed_bridge_distance_meters":max(c["polygon_distance_meters"] for c in selected),
        "original_node_count":len(graph),
        "original_edge_count":graph.number_of_edges(),
        "augmented_edge_count":augmented.number_of_edges(),
        "candidate_graph_is_connected":True,
        "legally_certified_geographic_contiguity":False,
        "research_warning":"Synthetic proximity graph is a sensitivity model only. Independent authoritative water/island and statutory contiguity review is required.",
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph",type=Path,required=True)
    ap.add_argument("--zip",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    if digest(args.graph)["git_blob_sha1"]!=JSON_GIT_BLOB:
        raise ValueError("Michigan graph source hash mismatch")
    if git_blob(args.zip)!=ZIP_GIT_BLOB:
        raise ValueError("Michigan polygon source hash mismatch")
    with zipfile.ZipFile(args.zip) as z:
        shp=[name for name in z.namelist() if name.lower().endswith(".shp")]
        if len(shp)!=1:
            raise ValueError("Expected exactly one source .shp")
    original=read_graph(args.graph)
    frame=gpd.read_file(f"zip://{args.zip.resolve()}!{shp[0]}").to_crs("EPSG:32616")
    alignment=align_precincts(original,frame)
    report=geometric_mst_candidates(original,frame,alignment)
    report["source_json_git_blob"]=JSON_GIT_BLOB
    report["source_zip_git_blob"]=ZIP_GIT_BLOB
    report["alignment_method"]=alignment["method"]
    report["alignment_checks"]=alignment.get("checks")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
