#!/usr/bin/env python3
"""Check saved ReCom assignments and rescore 2016/2020 on the SAME maps.

Uses the project's current artificial-bridge convention. This is NOT an
independent verification that those bridge edges represent real geography.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from redistricting.ensemble.partition import load_graph  # noqa: E402
from metric_reconciliation import crosscheck_metrics  # noqa: E402


def exact_gap(d: list[float], r: list[float]) -> float:
    """Reproduce existing pipeline's floor-half-plus-one winning threshold."""
    waste_d = waste_r = two_party = 0.0
    for dv, rv in zip(d, r, strict=True):
        total = dv + rv
        if total <= 0:
            continue
        threshold = math.floor(total / 2) + 1
        two_party += total
        if dv > rv:
            waste_d += max(0.0, dv - threshold)
            waste_r += rv
        elif rv > dv:
            waste_d += dv
            waste_r += max(0.0, rv - threshold)
        else:
            waste_d += dv
            waste_r += rv
    return (waste_r - waste_d) / two_party if two_party else float("nan")


def check_one(graph: nx.Graph, assignment: dict, epsilon: float,
              expected_districts: int) -> dict:
    graph_ids = {str(n) for n in graph.nodes}
    if set(assignment) != graph_ids:
        raise ValueError(f"assignment node set differs: missing={len(graph_ids - set(assignment))}, extra={len(set(assignment) - graph_ids)}")
    district_nodes = defaultdict(set)
    totals = defaultdict(float)
    for node, data in graph.nodes(data=True):
        label = str(assignment[str(node)])
        district_nodes[label].add(node)
        pop = float(data["TOTPOP"])
        if not math.isfinite(pop) or pop < 0:
            raise ValueError(f"invalid population on node {node}")
        totals[label] += pop
    if len(totals) != expected_districts:
        raise ValueError(f"Expected {expected_districts} districts, got {len(totals)}")
    if any(not nx.is_connected(graph.subgraph(nodes)) for nodes in district_nodes.values()):
        raise ValueError("At least one district is disconnected in the model graph")
    ideal = sum(totals.values()) / expected_districts
    deviation = max(abs(pop / ideal - 1) for pop in totals.values())
    if deviation > epsilon + 1e-12:
        raise ValueError(f"Population violation: {deviation:.8f} > {epsilon:.8f}")

    row = {"districts": len(totals), "max_population_deviation": deviation,
           "cut_edges": sum(assignment[str(u)] != assignment[str(v)] for u, v in graph.edges)}
    # Descriptive geographical fragmentation proxies, not legal constraints.
    # Keys verified directly against pinned Michigan mi.json nodes.
    if all("COUNTYFIPS" in attrs for _, attrs in graph.nodes(data=True)):
        county_to_districts = defaultdict(set)
        for node, attrs in graph.nodes(data=True):
            county_to_districts[str(attrs["COUNTYFIPS"])].add(str(assignment[str(node)]))
        row["split_county_groups"] = sum(len(ds) > 1 for ds in county_to_districts.values())
    if all("COUNTYFIPS" in attrs and "MCDFIPS" in attrs
           for _, attrs in graph.nodes(data=True)):
        subdivision_to_districts = defaultdict(set)
        for node, attrs in graph.nodes(data=True):
            label = (str(attrs["COUNTYFIPS"]), str(attrs["MCDFIPS"]))
            subdivision_to_districts[label].add(str(assignment[str(node)]))
        row["split_county_subdivision_name_groups"] = sum(
            len(ds) > 1 for ds in subdivision_to_districts.values()
        )
    for yr in ("16", "20"):
        dv, rv = defaultdict(float), defaultdict(float)
        for node, data in graph.nodes(data=True):
            label = str(assignment[str(node)])
            d, r = float(data[f"PRE{yr}D"]), float(data[f"PRE{yr}R"])
            if not all(map(math.isfinite, (d, r))) or min(d, r) < 0:
                raise ValueError(f"Invalid vote counts on node {node}, election {yr}")
            dv[label] += d
            rv[label] += r
        labels = sorted(district_nodes)
        ds = [dv[label] for label in labels]
        rs = [rv[label] for label in labels]
        shares = [d / (d + r) for d, r in zip(ds, rs) if d + r > 0]
        if not shares:
            raise ValueError("All district votes are zero")
        row[f"dem_seats_{yr}"] = sum(d > r for d, r in zip(ds, rs))
        row[f"efficiency_gap_{yr}"] = exact_gap(ds, rs)
        row[f"statewide_dem_share_{yr}"] = sum(ds) / (sum(ds) + sum(rs))
    return row



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--assignments", type=Path, nargs="+", required=True)
    ap.add_argument("--epsilon", type=float, default=0.005)
    ap.add_argument("--districts", type=int, default=13)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--metric-files", type=Path, nargs="+, help="Corresponding original plan-level CSVs for cross-check")
    args = ap.parse_args()
    if not 0 < args.epsilon < 1 or args.districts < 2:
        ap.error("Invalid epsilon or district count")
    graph = load_graph(args.graph)
    rows = []
    for path in args.assignments:
        snapshots = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(snapshots, dict) or not snapshots:
            raise ValueError(f"{path} has no saved snapshots")
        for step, assignment in sorted(snapshots.items(), key=lambda item: int(item[0])):
            if not isinstance(assignment, dict):
                raise ValueError("Expected JSON mapping node id -> district id")
            row = check_one(graph, assignment, args.epsilon, args.districts)
            row.update(chain=path.name, step=int(step),
                       assignment_sha256=hashlib.sha256(
                           json.dumps(assignment, sort_keys=True).encode()).hexdigest())
            rows.append(row)
    verified = pd.DataFrame(rows)
    if args.metric_files:
        crosscheck_metrics(verified, args.metric_files)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    verified.to_csv(args.output, index=False)
    print(f"PASS: verified {len(rows)} saved full assignments -> {args.output}")
    print("Note: unsaved transitions, physical bridges, and legal constraints are not verified.")
    if args.metric_files:
        print("PASS: recomputed snapshot statistics agree with original chain CSVs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
