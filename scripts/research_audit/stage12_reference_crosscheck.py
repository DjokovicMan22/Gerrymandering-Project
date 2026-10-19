#!/usr/bin/env python3
"""Independently reconstruct enacted reference scores from source graph nodes.

No GerryChain metric updaters or archived CSV scores are used to compute the
reference. Archive step zero is read only AFTER graph scores are calculated.
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

import networkx as nx
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_graph import read_graph, digest

GRAPH_GIT_BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"
SEEDS = (101, 202, 303)


def score_graph(graph: nx.Graph) -> dict:
    if graph.number_of_nodes() != 4756 or graph.number_of_edges() != 12378:
        raise ValueError("Not the pinned 4,756-node/12,378-edge Michigan source model")
    if not all("CD" in a and "TOTPOP" in a for _, a in graph.nodes(data=True)):
        raise ValueError("Missing reference assignments or population")
    groups = defaultdict(list)
    for node, attrs in graph.nodes(data=True):
        groups[str(attrs["CD"])].append(attrs)
    if len(groups) != 13:
        raise ValueError("Expected 13 reference districts")
    population = {d: sum(float(a["TOTPOP"]) for a in attrs) for d, attrs in groups.items()}
    ideal = sum(population.values()) / 13
    if not math.isclose(sum(population.values()), 10077331, abs_tol=1e-6):
        raise ValueError("Wrong statewide population")
    reference = {
        "district_count": 13,
        "total_population": sum(population.values()),
        "max_population_deviation": max(abs(v / ideal - 1) for v in population.values()),
        "cut_edges": sum(graph.nodes[u]["CD"] != graph.nodes[v]["CD"] for u, v in graph.edges),
        "elections": {},
    }
    for yr in ("16", "20"):
        wasted_d = wasted_r = total_votes = 0.0
        shares = []
        seats = 0
        district_rows = []
        for label, attrs in sorted(groups.items(), key=lambda x: int(x[0])):
            dv = sum(float(a[f"PRE{yr}D"]) for a in attrs)
            rv = sum(float(a[f"PRE{yr}R"]) for a in attrs)
            if not all(math.isfinite(x) and x >= 0 for x in (dv, rv)) or dv + rv <= 0:
                raise ValueError(f"Invalid district two-party vote counts in {yr}, district {label}")
            t = dv + rv
            total_votes += t
            shares.append(dv / t)
            threshold = math.floor(t / 2) + 1
            if dv > rv:
                seats += 1
                wasted_d += max(0.0, dv - threshold)
                wasted_r += rv
            elif rv > dv:
                wasted_d += dv
                wasted_r += max(0.0, rv - threshold)
            else:
                wasted_d += dv
                wasted_r += rv
            district_rows.append({"district": label, "dem_votes": dv, "rep_votes": rv,
                                  "population": population[label]})
        reference["elections"]["20" if yr == "20" else "16"] = {
            "dem_seats": seats,
            "efficiency_gap": (wasted_r - wasted_d) / total_votes,
            "mean_median": float(np.median(shares) - np.mean(shares)),
            "dem_votes": sum(row["dem_votes"] for row in district_rows),
            "rep_votes": sum(row["rep_votes"] for row in district_rows),
            "district_vote_and_population_summaries": district_rows,
        }
    return reference


def verify_against_packet(reference: dict, packet: Path) -> dict:
    verified = {}
    with ZipFile(packet) as z:
        for year in ("2016", "2020"):
            yr = year[-2:]
            for idx, seed in enumerate(SEEDS, start=1):
                name = f"outputs/chains/week4/mi_{year}_chain{idx}_7000steps_seed{seed}_plan_metrics.csv"
                original = pd.read_csv(io.BytesIO(z.read(name))).iloc[0]
                target = reference["elections"][yr]
                for metric in ("dem_seats", "efficiency_gap", "mean_median"):
                    if not math.isclose(float(original[metric]), target[metric], abs_tol=2e-8):
                        raise ValueError(f"{name}: independently computed {metric}={target[metric]} disagrees with archive step zero={float(original[metric])}")
                for metric in ("cut_edges", "max_population_deviation"):
                    if not math.isclose(float(original[metric]), reference[metric], abs_tol=2e-8):
                        raise ValueError(f"{name}: independently computed {metric} disagrees with archive step zero")
                verified[name] = True
    return verified


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--packet", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    source_digest = digest(args.graph)
    if source_digest["git_blob_sha1"] != GRAPH_GIT_BLOB:
        raise ValueError("Input graph bytes do not match pinned original source")
    reference = score_graph(read_graph(args.graph))
    verified = verify_against_packet(reference, args.packet)
    payload = {
        "graph_sha256": source_digest["sha256"],
        "graph_git_blob_sha1": GRAPH_GIT_BLOB,
        "independently_computed_reference": reference,
        "original_archive_step0_files_crosschecked": verified,
        "all_six_2016_2020_archived_references_match": len(verified) == 6,
        "original_transition_histories_replayed": False,
        "upstream_Census_VEST_raw_joins_recreated": False,
        "legal_contiguity_certified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    print("STAGE12_INDEPENDENT_REFERENCE_RECONCILIATION_PASS", len(verified))
    for yr, data in reference["elections"].items():
        print("REFERENCE", yr, data["dem_seats"], data["efficiency_gap"],
              data["dem_votes"], data["rep_votes"])


if __name__ == "__main__":
    main()
