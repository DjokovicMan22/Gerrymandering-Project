#!/usr/bin/env python3
"""Build pinned, label-independent KNN component geography for model comparison.

IMPORTANT: only a geometry-proximity sensitivity model, not a certification
that artificial shoreline, island or water links comply with Michigan law.
The enacted reference is checked AFTER edges are selected and never used to
choose them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import networkx as nx
from gerrychain import Graph

from geometric_knn_sensitivity import contacts
from geometry_bridge_validation import align_precincts,git_blob
from verify_graph import read_graph,digest

GRAPH_HASH="a4dfe70818f87b97924781216f3d86a672cfc66a"
ZIP_HASH="07bce18dabbcca9d549e28995a8156fd6978d7db"


def build(g,polys,matching,k):
    # Rank from the same 50-neighbor pool used by the source sensitivity audit.
    # A search stopping at K candidates can change the selected top-K edges.
    proposals=contacts(g,list(polys.geometry),matching,50)
    prepared=g.copy()
    chosen=[]
    seen=set()
    for row in proposals:
        if row["rank"]>k:
            continue
        u,v=int(row["u"]),int(row["v"])
        key=tuple(sorted((u,v)))
        if key in seen:
            continue
        seen.add(key)
        prepared.add_edge(u,v,source_geometry_proximity=True,
                          legally_certified=False,
                          polygon_distance_meters=row["distance_m"])
        chosen.append({"u":u,"v":v,"distance_m":row["distance_m"]})
    if len(chosen)!=13:
        raise ValueError(f"K=3 source-sensitivity protocol requires exactly 13 unique links, got {len(chosen)}")
    if not nx.is_connected(prepared):
        raise ValueError("Geometry candidate still disconnects statewide graph")
    ref_parts={}
    for label in {str(x["CD"]) for _,x in prepared.nodes(data=True)}:
        nodes={n for n,attrs in prepared.nodes(data=True) if str(attrs["CD"])==label}
        ref_parts[label]=nx.number_connected_components(prepared.subgraph(nodes))
    if len(ref_parts)!=13 or any(v!=1 for v in ref_parts.values()):
        raise ValueError(f"Geometry candidate cannot represent enacted map: {ref_parts}")
    return prepared,chosen


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out-graph",type=Path,required=True)
    p.add_argument("--out-manifest",type=Path,required=True)
    p.add_argument("--k",type=int,default=3)
    args=p.parse_args()
    if args.k!=3:
        p.error("K=3 was fixed after source sensitivity; other K requires new protocol")
    if digest(args.graph)["git_blob_sha1"]!=GRAPH_HASH or git_blob(args.zip)!=ZIP_HASH:
        raise ValueError("Input source bytes unexpectedly changed")
    with zipfile.ZipFile(args.zip) as archive:
        shp=[name for name in archive.namelist() if name.lower().endswith(".shp")]
        if len(shp)!=1:
            raise ValueError("Expected one precinct polygon shapefile")
    graph=read_graph(args.graph)
    polys=gpd.read_file(f"zip://{args.zip.resolve()}!{shp[0]}").to_crs("EPSG:32616")
    verified=align_precincts(graph,polys)
    prepared,added=build(graph,polys,verified["mapping"],args.k)
    args.out_graph.parent.mkdir(parents=True,exist_ok=True)
    args.out_manifest.parent.mkdir(parents=True,exist_ok=True)
    args.out_graph.write_text(json.dumps(nx.adjacency_data(prepared)))
    # Check again via both independent parsing paths.
    verified_nx=read_graph(args.out_graph)
    verified_gc=Graph.from_json(str(args.out_graph))
    if (len(verified_nx)!=4756 or verified_nx.number_of_edges()!=graph.number_of_edges()+len(added)
            or len(verified_gc)!=4756 or verified_gc.number_of_edges()!=verified_nx.number_of_edges()):
        raise ValueError("Serialized proximity model lost nodes or edges")
    output={
        "status":"DISTRICT_BLIND_GEOMETRY_PROXIMITY_MODEL_NOT_LEGAL_CONTIGUITY_CERTIFICATION",
        "graph_source_sha1_git_blob":GRAPH_HASH,
        "precinct_geometry_git_blob":ZIP_HASH,
        "method":"3 closest external precinct polygons from each disconnected component",
        "source_ranking_candidate_pool_size":50,
        "district_labels_used_in_bridge_selection":False,
        "enacted_district_contiguity_validated_after_selection":True,
        "all_original_4756_nodes_retained":True,
        "original_graph_edge_count":graph.number_of_edges(),
        "augmented_graph_edge_count":prepared.number_of_edges(),
        "inserted_edges":added,
        "max_proximity_edge_meters":max(v["distance_m"] for v in added),
        "added_edge_count":len(added),
        "serialized_graph_sha256":hashlib.sha256(args.out_graph.read_bytes()).hexdigest(),
        "legal_and_water_island_geography_certified":False,
        "warning":"Model adjacency uses physical polygon distances and a KNN choice; this does not certify water or island rules, COI, VRA or Michigan legal eligibility.",
    }
    args.out_manifest.write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
