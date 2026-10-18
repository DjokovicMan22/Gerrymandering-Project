#!/usr/bin/env python3
"""Measure diversity of geographically constrained, independently seeded warmups.

All seeds start from the same reference district plan, so even *passing*
pairwise-distance gates does not establish independent draws from stationarity.
The file stores hashes and metrics only; precinct assignments are NOT uploaded.
Exit 2 means that candidate starts failed the predeclared diversity threshold.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from redistricting.ensemble.partition import build_initial_partition, load_graph
from redistricting.ensemble.start_diversity import (
    WarmStartConfig, compare_seeded_endpoints, warm_endpoint,
)
from verify_graph import digest
from verify_snapshots import check_one


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--warmup-steps", type=int, default=800)
    ap.add_argument("--seeds", type=int, nargs="+", default=[101, 202, 303, 404])
    ap.add_argument("--epsilon", type=float, default=0.005)
    ap.add_argument("--max-cut-edges", type=int, default=760)
    ap.add_argument("--max-split-counties", type=int, default=18)
    ap.add_argument("--max-split-county-mcd", type=int, default=20)
    ap.add_argument("--min-pairwise-distance", type=float, default=0.05)
    ap.add_argument("--min-reference-distance", type=float, default=0.05)
    args = ap.parse_args()

    if len(args.seeds) < 2 or len(args.seeds) != len(set(args.seeds)):
        ap.error("At least two distinct seeds are required")
    config = WarmStartConfig(
        epsilon=args.epsilon,
        steps_including_reference=args.warmup_steps,
        max_cut_edges=args.max_cut_edges,
        max_split_counties=args.max_split_counties,
        max_split_county_mcd=args.max_split_county_mcd,
    )
    config.validate()
    source_hashes = digest(args.graph)
    if source_hashes["git_blob_sha1"] != "a4dfe70818f87b97924781216f3d86a672cfc66a":
        raise ValueError("Michigan input blob SHA does not match the pinned public source")

    graph = load_graph(args.graph)
    reference = build_initial_partition(graph, "CD", "PRE20D", "PRE20R")
    initial = dict(reference.assignment.items())
    endpoints = {}
    rows = []
    for seed in args.seeds:
        candidate, meta = warm_endpoint(reference, seed, config)
        # This checks the actual precinct node set, graph contiguity, population,
        # and separately recovers political and geographic summaries.
        independent = check_one(graph, {str(n):str(d) for n,d in candidate.items()},
                                args.epsilon, len(reference))
        for name, observed in meta["final_geographic_proxies"].items():
            if independent[name] != observed:
                raise ValueError(f"Independent endpoint geographic score disagreed: {name}")
        if abs(independent["max_population_deviation"] -
               meta["final_max_population_deviation"]) > 1e-10:
            raise ValueError("Independent endpoint population computation disagreed")
        rows.append(meta)
        endpoints[seed] = candidate
        print("ENDPOINT", seed, ":", meta, flush=True)

    comparisons, passed = compare_seeded_endpoints(
        initial, endpoints,
        minimum_pairwise_distance=args.min_pairwise_distance,
        minimum_reference_distance=args.min_reference_distance,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output / "warm_start_summaries.csv", index=False)
    pd.DataFrame(comparisons).to_csv(args.output / "label_invariant_distances.csv", index=False)
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": source_hashes,
        "config": asdict(config),
        "seeds": args.seeds,
        "minimum_pairwise_distance": args.min_pairwise_distance,
        "minimum_reference_distance": args.min_reference_distance,
        "all_distance_gates_pass": passed,
        "status": "DIVERSE_ENDPOINTS_NOT_STATIONARY" if passed else "INSUFFICIENT_START_DIVERSITY",
        "warning": (
            "All warmups begin from the same enacted map, with independently "
            "seeded stochastic paths; distance is label-invariant exact "
            "precinct disagreement, not proof of independent stationary starts."
        ),
        "reference_assignment_sha256": __import__(
            "redistricting.ensemble.start_diversity", fromlist=["assignment_digest"]
        ).assignment_digest(initial),
    }
    (args.output / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(pd.DataFrame(comparisons).to_string(index=False), flush=True)
    print(payload["status"], flush=True)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
