#!/usr/bin/env python3
"""Figure 1: measured synthetic Michigan graph edges on exact pinned precinct polygons.

Visualizes the original project's five enacted-label-selected artificial edges,
not natural/shared-land borders. Each line connects shortest points on polygon
geometries; it does not imply a road, water passage, or legal island rule.
The plotted precinct locations are representative points, not raw polygon edges.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.ops import nearest_points

from verify_graph import read_graph
from geometry_bridge_validation import (
    analyze, align_precincts, git_blob, ZIP_GIT_BLOB, JSON_GIT_BLOB,
)

INK="#203349"
RED="#A3443A"
BASE="#9CAAB3"
PAPER="#ffffff"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,required=True)
    p.add_argument("--zip",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    args=p.parse_args()
    # analyze() independently validates original JSON/ZIP Git blobs,
    # alignments and reproduces the original five edges from old code.
    measured=analyze(args.graph,args.zip)
    edges=measured["artificial_bridge_polygon_distances"]
    if len(edges)!=5 or measured["source_graph_blob"]!=JSON_GIT_BLOB or measured["original_precinct_zip_blob"]!=ZIP_GIT_BLOB:
        raise ValueError("Pinned original source or exactly five historic bridges not verified")
    if measured["legal_geography_certification"] is not False:
        raise ValueError("Geography must not be represented as legally certified")
    graph=read_graph(args.graph)
    with zipfile.ZipFile(args.zip) as zf:
        paths=[x for x in zf.namelist() if x.endswith(".shp")]
        if len(paths)!=1:raise ValueError("Wrong original precinct shapefile package")
    frame=gpd.read_file(f"zip://{args.zip.resolve()}!{paths[0]}").to_crs("EPSG:32616")
    alignment=align_precincts(graph,frame)
    mapping=alignment["mapping"]
    representative=frame.geometry.representative_point()
    px=representative.x.to_numpy(); py=representative.y.to_numpy()
    plt.rcParams.update({
        "font.family":"serif","font.serif":["STIXGeneral","DejaVu Serif"],
        "mathtext.fontset":"stix","font.size":9.0,
        "pdf.fonttype":42,"svg.fonttype":"none",
        "figure.facecolor":"white","axes.facecolor":"white",
        "savefig.facecolor":"white",
    })
    fig,ax=plt.subplots(figsize=(6.7,4.55))
    ax.scatter(px/1000,py/1000,s=.75,c=BASE,alpha=.53,rasterized=False,zorder=1)
    output=[]
    for index,row in enumerate(sorted(edges,key=lambda e:-e["polygon_distance_meters"]),start=1):
        u,v=int(row["node_a"]),int(row["node_b"])
        gu=frame.geometry.iloc[mapping[str(u)]]
        gv=frame.geometry.iloc[mapping[str(v)]]
        a,b=nearest_points(gu,gv)
        distance=float(a.distance(b))
        if abs(distance-float(row["polygon_distance_meters"]))>1e-6:
            raise ValueError("Recomputed shortest-segment distance differs from independent source polygon audit")
        km=distance/1000.
        ax.plot([a.x/1000,b.x/1000],[a.y/1000,b.y/1000],
                color=RED,lw=1.35,ls=(0,(3.2,1.8)),zorder=4,solid_capstyle="round")
        ax.scatter([a.x/1000,b.x/1000],[a.y/1000,b.y/1000],
                   s=17,facecolors="white",edgecolors=RED,linewidths=1.0,zorder=5)
        # Keep distances in the formal numbered figure caption. Five nearby
        # overlapping inline labels obscure the original geography at print size.
        output.append({"label":index,"node_a":u,"node_b":v,
                       "distance_km":round(km,6),
                       "same_enacted_district":bool(row["same_enacted_district"]),
                       "same_source_county":row["county_a"]==row["county_b"],
                       "nearest_segment_endpoints_projected_km":[
                         [round(a.x/1000,4),round(a.y/1000,4)],
                         [round(b.x/1000,4),round(b.y/1000,4)]],
                      })
    ds=sorted(x["distance_km"] for x in output)
    if min(ds)<35 or max(ds)<270 or max(ds)>290:
        raise ValueError("Measured historic 42–280 km bridge evidence does not match source report")
    ax.set_aspect("equal","box")
    ax.set_xticks([]);ax.set_yticks([])
    for spine in ax.spines.values():spine.set_visible(False)
    ax.margins(.045)
    ax.legend(handles=[
        Line2D([0],[0],marker=".",linestyle="None",color=BASE,
               markersize=8,label="Source precinct representative points"),
        Line2D([0],[0],linestyle=(0,(3,1.8)),color=RED,linewidth=1.5,
               marker="o",markerfacecolor="white",markersize=4.3,
               label="Project-added artificial connection"),
    ],loc="lower left",frameon=False,fontsize=8,ncol=1,
    borderaxespad=.12,handlelength=2.8)
    fig.subplots_adjust(left=.02,right=.98,top=.97,bottom=.06)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    stem=args.out_dir/"figure_topology_artificial_bridges"
    for ext in ("pdf","svg","png"):
        opts={"bbox_inches":"tight","pad_inches":.09}
        if ext=="png":opts["dpi"]=300
        fig.savefig(stem.with_suffix("."+ext),**opts)
        if stem.with_suffix("."+ext).stat().st_size<4500:
            raise ValueError("Missing/empty publication graph")
    plt.close(fig)
    meta={
        "status":"PASS_SOURCE_VERIFIED_FIVE_BRIDGES_VISUALIZED",
        "original_graph_git_blob":JSON_GIT_BLOB,
        "source_polygon_zip_git_blob":ZIP_GIT_BLOB,
        "source_graph_sha256":hashlib.sha256(args.graph.read_bytes()).hexdigest(),
        "source_polygon_zip_sha256":hashlib.sha256(args.zip.read_bytes()).hexdigest(),
        "crs":"EPSG:32616",
        "precinct_count":len(frame),
        "plot_points":"representative point for each original polygon",
        "bridge_segment_definition":"nearest points on original polygons of each originally project-added graph connection",
        "not_a_legal_contiguity_map":True,
        "not_a_redistricting_null_model":True,
        "annotation":"Short dashed lines are diagrammatic existing project synthetic edges, not water/road/passable or legal adjacency",
        "connections":output,
    }
    (args.out_dir/"stage4_topology_figure_manifest.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("STAGE4_SOURCE_VERIFIED_GEOMETRY_PLATE_PASS",json.dumps(meta),flush=True)

if __name__=="__main__":
    main()
