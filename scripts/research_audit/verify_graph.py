#!/usr/bin/env python3
"""Stage 3 input gate: independently inspect a GerryChain JSON graph.

This is a data-integrity check, NOT a certification of geography, joins, or
legal redistricting requirements. No input data are redistributed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import networkx as nx

REQUIRED = ("CD", "TOTPOP", "PRE16D", "PRE16R", "PRE20D", "PRE20R")


def read_graph(path: Path) -> nx.Graph:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "adjacency" in data:
        graph = nx.adjacency_graph(data)
    elif "links" in data or "edges" in data:
        if "links" not in data:
            data["links"] = data["edges"]
        graph = nx.node_link_graph(data, directed=False, multigraph=False)
    else:
        raise ValueError("Unsupported JSON graph format: expected adjacency or links")
    if graph.is_directed() or graph.is_multigraph() or not graph.number_of_nodes():
        raise ValueError("Expected a nonempty, undirected simple graph")
    return graph


def digest(path: Path) -> dict[str, str | int]:
    content = path.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(content)).encode() + bytes([0]) + content).hexdigest()
    return {"sha256": hashlib.sha256(content).hexdigest(),
            "git_blob_sha1": git_blob, "size_bytes": len(content)}


def validate(graph: nx.Graph, *, population_field="TOTPOP") -> dict:
    errors: list[str] = []
    fields_missing = Counter()
    votes = Counter()
    precinct_ids = set()
    duplicates = 0
    populations = defaultdict(float)
    assignments = {}
    total_population = 0.0

    for node, a in graph.nodes(data=True):
        for field in REQUIRED:
            if field not in a or a[field] is None:
                fields_missing[field] += 1
        if fields_missing and any(a.get(f) is None for f in REQUIRED):
            continue
        pop = float(a[population_field])
        if not math.isfinite(pop) or pop < 0:
            errors.append(f"invalid population at node {node!r}")
            continue
        total_population += pop
        district = str(a["CD"])
        assignments[node] = district
        populations[district] += pop
        for f in ("PRE16D", "PRE16R", "PRE20D", "PRE20R"):
            v = float(a[f])
            if not math.isfinite(v) or v < 0:
                errors.append(f"invalid {f} at node {node!r}")
            else:
                votes[f] += v
        if "PRECINCTID" in a or "PRECINCT20" in a:
            key = str(a.get("PRECINCTID", a.get("PRECINCT20")))
            if key in precinct_ids:
                duplicates += 1
            precinct_ids.add(key)

    if fields_missing:
        errors.append("missing fields: " + repr(dict(fields_missing)))
    if duplicates:
        errors.append(f"{duplicates} duplicated PRECINCTID values")
    if len(assignments) != graph.number_of_nodes():
        errors.append("some nodes were omitted by validation")

    component_sizes = sorted((len(c) for c in nx.connected_components(graph)), reverse=True)
    connected_per_district = {}
    for district in sorted(set(assignments.values())):
        members = [node for node, value in assignments.items() if value == district]
        connected_per_district[district] = bool(members) and nx.is_connected(graph.subgraph(members))

    k = len(populations)
    ideal = total_population / k if k else 0
    max_dev = max((abs(p / ideal - 1) for p in populations.values()), default=float("nan")) if ideal else float("nan")
    cut_edges = sum(assignments.get(u) != assignments.get(v) for u, v in graph.edges)
    return {
        "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
        "connected_component_sizes": component_sizes,
        "district_count": k, "total_population": total_population,
        "ideal_population": ideal, "max_population_deviation": max_dev,
        "district_populations": dict(sorted(populations.items())),
        "district_graph_contiguous_without_bridges": connected_per_district,
        "reference_cut_edges_without_bridges": cut_edges,
        "two_party_vote_totals": dict(sorted(votes.items())),
        "precinct_id_count": len(precinct_ids), "errors": errors,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--expected-git-blob")
    p.add_argument("--expected-nodes", type=int)
    p.add_argument("--expected-population", type=float)
    args = p.parse_args()
    ids = digest(args.graph)
    results = validate(read_graph(args.graph))
    if args.expected_git_blob and ids["git_blob_sha1"] != args.expected_git_blob.lower():
        results["errors"].append("Git blob SHA-1 mismatch: wrong input bytes")
    if args.expected_nodes is not None and results["nodes"] != args.expected_nodes:
        results["errors"].append("node count mismatch")
    if args.expected_population is not None and abs(results["total_population"] - args.expected_population) > 1e-6:
        results["errors"].append("state population mismatch")
    payload = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "input": str(args.graph), "hashes": ids, "validation": results,
               "status": "PASS_DATA_INTEGRITY" if not results["errors"] else "FAIL_DATA_INTEGRITY",
               "limitation": "Does not independently verify boundary provenance, election joins, bridges, or legal validity."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print(payload["status"], "->", args.output)
    return 0 if not results["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
