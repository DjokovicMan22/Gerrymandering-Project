#!/usr/bin/env python3
"""Sensitivity of district-blind proximity edges; never certify legal geography."""
import argparse
import json
import math
import zipfile
from pathlib import Path
import geopandas as gpd
import networkx as nx
from shapely.strtree import STRtree
from geometry_bridge_validation import align_precincts,git_blob
from verify_graph import digest,read_graph

GRAPH_HASH="a4dfe70818f87b97924781216f3d86a672cfc66a"
ZIP_HASH="07bce18dabbcca9d549e28995a8156fd6978d7db"


def contacts(graph,geometry,matching,limit):
    components=sorted(nx.connected_components(graph),key=lambda c:(-len(c),min(c)))
    found=[]
    for ci,part in enumerate(components[1:],1):
        external=sorted(set(graph)-set(part))
        tree=STRtree([geometry[matching[str(n)]] for n in external])
        candidates={}
        radius=1000.0
        while len(candidates)<limit and radius<=150000:
            for n in sorted(part):
                inside=geometry[matching[str(n)]]
                for index in tree.query(inside.buffer(radius)):
                    outsider=external[int(index)]
                    distance=float(inside.distance(geometry[matching[str(outsider)]]))
                    if not math.isfinite(distance) or distance<0:
                        raise ValueError("Non-finite source-geometry distance")
                    entry=(distance,int(n),int(outsider))
                    if outsider not in candidates or entry<candidates[outsider]:
                        candidates[outsider]=entry
            radius*=2
        if len(candidates)<limit:
            raise ValueError("Too few source polygon neighbors for component "+str(ci))
        found.extend({"component":ci,"rank":rank,"distance_m":dist,"u":u,"v":v}
                     for rank,(dist,u,v) in enumerate(sorted(candidates.values())[:limit],1))
    return found


def summarize(graph,edges,ks):
    reports=[]
    for k in ks:
        aug=graph.copy()
        chosen=set()
        distances=[]
        for edge in edges:
            if edge["rank"]>k:
                continue
            u,v=edge["u"],edge["v"]
            key=tuple(sorted((u,v)))
            if key in chosen:
                continue
            chosen.add(key)
            distances.append(edge["distance_m"])
            aug.add_edge(u,v,proximity_candidate=True)
        parts={}
        for label in sorted({str(a["CD"]) for _,a in graph.nodes(data=True)}):
            nodes=[n for n,a in graph.nodes(data=True) if str(a["CD"])==label]
            parts[label]=sorted((len(group) for group in nx.connected_components(aug.subgraph(nodes))),reverse=True)
        reports.append({
            "k":k,"added_edges":len(chosen),
            "max_edge_distance_m":max(distances),
            "statewide_connected":nx.is_connected(aug),
            "reference_all_districts_connected":all(len(sizes)==1 for sizes in parts.values()),
            "disconnected_reference_districts":{label:sizes for label,sizes in parts.items() if len(sizes)>1},
            "cross_reference_label_edges":sum(str(graph.nodes[u]["CD"])!=str(graph.nodes[v]["CD"]) for u,v in chosen),
            "legal_status":"NOT CERTIFIED",
        })
    return reports


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--ks",type=int,nargs="+",default=[1,3,10,25,50])
    a=p.parse_args()
    if not a.ks or min(a.ks)<1:
        p.error("Positive K required")
    if digest(a.graph)["git_blob_sha1"]!=GRAPH_HASH or git_blob(a.zip)!=ZIP_HASH:
        raise ValueError("Source file pin mismatch")
    with zipfile.ZipFile(a.zip) as z:
        shp=[n for n in z.namelist() if n.lower().endswith(".shp")]
        if len(shp)!=1:
            raise ValueError("Expected one source shapefile")
    g=read_graph(a.graph)
    gdf=gpd.read_file(f"zip://{a.zip.resolve()}!{shp[0]}").to_crs("EPSG:32616")
    matching=align_precincts(g,gdf)["mapping"]
    proposed=contacts(g,list(gdf.geometry),matching,max(a.ks))
    report={"source_graph":GRAPH_HASH,"source_zip":ZIP_HASH,
            "selection_rule":"K nearest external polygons to each source component; no partisan/district input",
            "candidate_edges":proposed,
            "sensitivity":summarize(g,proposed,sorted(set(a.ks))),
            "legal_geography_certified":False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report["sensitivity"],indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
