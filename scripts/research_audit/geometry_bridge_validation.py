#!/usr/bin/env python3
"""Source-matched Michigan precinct polygon audit: no silent topology repair.

Uses the *original* published Veomett Michigan shapefile package matching the
graph producer, checks original ZIP Git blob bytes, and aligns by PROVEN exact
row attributes or identifier matches. A failed alignment cannot be replaced
by row-order guesswork. Reports physical planar polygon distance for synthetic
bridge endpoint candidates. Distances alone do not establish Michigan's
statutory island/county contiguity rules or aquatic/road transport.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

import geopandas as gpd
import networkx as nx
import pandas as pd

from verify_graph import digest, read_graph
from audit_bridge_geography import county_component_reachability

ZIP_GIT_BLOB="07bce18dabbcca9d549e28995a8156fd6978d7db"
JSON_GIT_BLOB="a4dfe70818f87b97924781216f3d86a672cfc66a"


def git_blob(path: Path) -> str:
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()


def find_source_column(cols, candidates):
    upper={str(c).upper():c for c in cols}
    for name in candidates:
        if name.upper() in upper:
            return upper[name.upper()]
    return None


def align_precincts(graph:nx.Graph, frame:gpd.GeoDataFrame)->dict:
    """Prefer a verifiable one-to-one stable ID join; otherwise row attribute proof.

    The Shapefile can truncate columns; population+CD+county+precinct triple
    may still be duplicated. Never claim geometric alignment from such fields
    without checking that all source nodes align to shape records.
    """
    if len(graph)!=len(frame):
        raise ValueError(f"Source JSON nodes {len(graph)} != ZIP geometries {len(frame)}; no alignment")
    if frame.geometry.isna().any() or frame.geometry.is_empty.any():
        raise ValueError("Missing or empty precinct geometry")
    nodes=sorted(graph, key=lambda n: int(n) if str(n).isdigit() else str(n))
    candidate_ids=[
        ("PRECINCT20","PRECINCT20"),("GEOID20","GEOID20"),
        ("PRECINCT","PRECINCT"),("GEOID","GEOID")
    ]
    for left,right in candidate_ids:
        key=find_source_column(frame.columns,[right])
        if not key or not all(graph.nodes[n].get(left) is not None for n in nodes):
            continue
        left_values={str(n):str(graph.nodes[n][left]).strip() for n in nodes}
        right_values={str(i):str(v).strip() for i,v in frame[key].items()}
        if len(set(left_values.values())) != len(left_values) or len(set(right_values.values())) != len(right_values):
            continue
        reverse={v:int(k) for k,v in right_values.items()}
        if set(reverse)==set(left_values.values()):
            return {
                "method":"exact_unique_identifier",
                "source_field":left,
                "shape_field":str(key),
                "mapping":{str(n):reverse[v] for n,v in left_values.items()},
            }

    # Explicitly test known numeric node-index order rather than assuming it.
    if set(graph)==set(range(len(graph))):
        pairs=[("TOTPOP",("TOTPOP","POP20")),("CD",("CD",)),
               ("COUNTYFIPS",("COUNTYFIPS","COUNTYFP20","COUNTYFP"))]
        checks=[]
        for attribute, options in pairs:
            column=find_source_column(frame.columns,options)
            if column is None:
                continue
            matches=0
            for n in graph:
                source=graph.nodes[n].get(attribute)
                target=frame.iloc[n][column]
                if str(source).strip()==str(target).strip() or (
                        attribute=="TOTPOP" and source is not None and
                        float(source)==float(target)):
                    matches+=1
            checks.append({"attribute":attribute,"shape_field":str(column),"matches":matches})
        if len(checks)>=2 and all(c["matches"]==len(graph) for c in checks):
            return {
                "method":"proven_complete_node_index_alignment",
                "checks":checks,
                "mapping":{str(n):int(n) for n in graph},
            }
    raise ValueError("Cannot prove one-to-one JSON precinct to ZIP geometry alignment; no geometric verdict")


def geometry_distances(graph,frame,alignment, synthetic_pairs):
    result=[]
    mapped=alignment["mapping"]
    geom=frame.geometry
    for u,v in synthetic_pairs:
        a=geom.iloc[mapped[str(u)]]
        b=geom.iloc[mapped[str(v)]]
        d=float(a.distance(b))
        inter=a.intersection(b)
        result.append({
            "node_a":str(u),"node_b":str(v),
            "county_a":str(graph.nodes[u].get("COUNTYFIPS")),
            "county_b":str(graph.nodes[v].get("COUNTYFIPS")),
            "same_enacted_district":str(graph.nodes[u].get("CD"))==str(graph.nodes[v].get("CD")),
            "polygon_distance_meters":d,
            "polygon_geometry_touches_or_overlaps":bool(d<=1e-7),
            "shared_border_length_meters":float(a.boundary.intersection(b.boundary).length),
            "unverified_water_or_bridge_connection":True,
        })
    return result


def analyze(graph_path:Path,zip_path:Path):
    if digest(graph_path)["git_blob_sha1"]!=JSON_GIT_BLOB:
        raise ValueError("Graph SHA mismatch")
    if git_blob(zip_path)!=ZIP_GIT_BLOB:
        raise ValueError("Shapefile ZIP Git blob mismatch")
    with zipfile.ZipFile(zip_path) as zf:
        names=zf.namelist()
        shp=[n for n in names if n.lower().endswith(".shp")]
        if len(shp)!=1:
            raise ValueError(f"Expected exactly one precinct .shp file in original ZIP, got {shp}")
    graph=read_graph(graph_path)
    frame=gpd.read_file(f"zip://{zip_path.resolve()}!{shp[0]}")
    if frame.crs is None:
        raise ValueError("Shapefile has no declared CRS")
    projected=frame.to_crs("EPSG:32616")
    alignment=align_precincts(graph,projected)
    comps=sorted(nx.connected_components(graph),key=len,reverse=True)
    artificial=[]
    for c in comps[1:]:
        main=comps[0]
        choices=[(u,v) for u in c for v in main
                 if str(graph.nodes[u].get("CD"))==str(graph.nodes[v].get("CD"))]
        if not choices:
            # Historical bridge algorithm sometimes connects to the second component.
            # Reconstruct the selected five artificial endpoint pairs explicitly below.
            pass
    # Source-reverified historical bridge endpoints from existing deterministic algorithm.
    from gerrychain import Graph
    from redistricting.ensemble.partition import _connect_components_within_district
    augmented=Graph.from_json(str(graph_path))
    edges=_connect_components_within_district(augmented)
    synthetic_pairs=[(u,v) for u,v,_ in edges]
    metrics=geometry_distances(graph,projected,alignment,synthetic_pairs)
    return {
        "source_graph_blob":JSON_GIT_BLOB,
        "original_precinct_zip_blob":ZIP_GIT_BLOB,
        "precinct_geometry_count":len(projected),
        "crs_used_for_distance":"EPSG:32616",
        "source_alignment_method":alignment["method"],
        "alignment_checks":alignment.get("checks"),
        "synthetic_bridge_count":len(metrics),
        "artificial_bridge_polygon_distances":metrics,
        "all_artificial_connections_are_geometrically_touching":all(x["polygon_geometry_touches_or_overlaps"] for x in metrics),
        "county_component_reachability":county_component_reachability(graph),
        "legal_geography_certification":False,
        "warning":"Polygon distance audits the selected node pairs, not statutory island-contiguity or available transportation links. A water connection requires separate legal GIS evidence.",
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph",type=Path,required=True)
    ap.add_argument("--zip",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    result=analyze(args.graph,args.zip)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
