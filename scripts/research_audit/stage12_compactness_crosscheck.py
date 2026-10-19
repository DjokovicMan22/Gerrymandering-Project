#!/usr/bin/env python3
"""Independently recompute Michigan Polsby–Popper, Reock and hull compactness.

Uses source ZIP polygons, not saved district geometries or the original Week 2
metric implementation. Reock uses GEOS minimum_bounding_radius instead of the\noriginal randomized circle code. A passed check does not certify legal geography\nor the underlying raw RDH polygon joins.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
from shapely import minimum_bounding_radius

from geometry_bridge_validation import align_precincts, git_blob
from verify_graph import read_graph, digest

ZIP_BLOB = "07bce18dabbcca9d549e28995a8156fd6978d7db"
GRAPH_BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"


def recompute(graph_path: Path, zip_path: Path, table_path: Path) -> dict:
    if digest(graph_path)["git_blob_sha1"] != GRAPH_BLOB:
        raise ValueError("Wrong original source graph bytes")
    if git_blob(zip_path) != ZIP_BLOB:
        raise ValueError("Wrong original precinct polygon ZIP bytes")
    with ZipFile(zip_path) as z:
        shps = [x for x in z.namelist() if x.lower().endswith(".shp")]
        if len(shps) != 1:
            raise ValueError(f"Expected one source shapefile, found {shps}")
    polygons = gpd.read_file(f"zip://{zip_path.resolve()}!{shps[0]}")
    if polygons.crs is None:
        raise ValueError("Source polygon coordinate system is missing")
    if polygons.crs.is_geographic:
        raise ValueError("Original Week 2 projection is not independently established for geographic CRS")
    if not polygons.geometry.is_valid.all():
        raise ValueError("Invalid source polygon geometry requires explicit correction protocol")
    graph = read_graph(graph_path)
    alignment = align_precincts(graph, polygons)
    mapping = alignment["mapping"]
    if len(mapping) != len(graph) or len(set(mapping.values())) != len(graph):
        raise ValueError("Polygon alignment is not one-to-one")
    polygon_to_district = {int(idx): str(graph.nodes[int(node)]["CD"])
                           for node, idx in mapping.items()}
    frame = polygons[["geometry"]].copy()
    frame["CD"] = [polygon_to_district[i] for i in range(len(frame))]
    dissolved = frame.dissolve(by="CD")
    archived = pd.read_csv(table_path)
    if len(archived) != 13 or archived["CD"].duplicated().any():
        raise ValueError("Expected 13 unique saved Week 2 districts")
    archived["CD"] = archived["CD"].astype(str)
    stored = archived.set_index("CD")
    if set(stored.index) != set(dissolved.index):
        raise ValueError("District labels disagree between original polygons and Week 2 table")
    rows = []
    for label, row in dissolved.iterrows():
        geom = row.geometry
        area = float(geom.area)
        perimeter = float(geom.length)
        hull_area = float(geom.convex_hull.area)
        if area <= 0 or perimeter <= 0 or hull_area <= 0:
            raise ValueError(f"Degenerate dissolved district geometry: {label}")
        radius = float(minimum_bounding_radius(geom))
        if not math.isfinite(radius) or radius <= 0:
            raise ValueError(f"Invalid minimum enclosing circle radius for district {label}")
        metrics = {
            "area": area, "perimeter": perimeter, "convex_hull_area": hull_area,
            "reock": area / (math.pi * radius**2),
            "polsby_popper": 4 * math.pi * area / perimeter**2,
            "convex_hull_ratio": area / hull_area,
        }
        for metric, value in metrics.items():
            reference = float(stored.loc[label, metric])
            if not math.isclose(value, reference,
                                rel_tol=1e-4 if metric == "reock" else 2e-6,
                                abs_tol=1e-7):
                raise ValueError(
                    f"District {label} {metric} mismatches saved Week 2: "
                    f"independent {value}, archive {reference}"
                )
        rows.append({"district": label, **metrics,
                     "saved_Week2_Polsby_Reock_and_hull_match": True})
    return {
        "source_graph_git_blob_sha1": GRAPH_BLOB,
        "source_precinct_zip_git_blob_sha1": ZIP_BLOB,
        "source_geometry_crs": str(polygons.crs),
        "source_alignment_method": alignment["method"],
        "districts_recomputed": len(rows),
        "all_13_Polsby_Reock_and_hull_scores_reconciled": True,
        "district_metrics": rows,
        "Reock_independently_recomputed": True,
        "Reock_method": "GEOS minimum_bounding_radius via Shapely; independent of project randomized circle implementation",
        "legal_geography_certified": False,
        "raw_RDH_source_joins_reconstructed": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--table", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = recompute(args.graph, args.zip, args.table)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print("STAGE1_INDEPENDENT_GEOMETRY_COMPACTNESS_RECONCILIATION_PASS",
          result["districts_recomputed"], "districts", result["source_geometry_crs"])


if __name__ == "__main__":
    main()
