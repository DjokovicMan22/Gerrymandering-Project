#!/usr/bin/env python3
"""Run one reproducible ReCom chain for Michigan or Missouri."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from redistricting.diagnostics import make_trace_plots
from redistricting.ensemble import (
    ChainConfig,
    build_initial_partition,
    ideal_population,
    load_graph,
    run_recom_chain,
    save_chain_outputs,
)

STATE_NAMES = {"mi": "Michigan", "mo": "Missouri"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=STATE_NAMES, default="mi")
    parser.add_argument("--steps", type=int, default=1_000)
    parser.add_argument("--epsilon", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--node-repeats", type=int, default=2)
    parser.add_argument("--election", choices=("2020", "2016"), default="2020")
    parser.add_argument("--chain-id", default="chain1")
    parser.add_argument(
        "--snapshot-interval",
        type=int,
        default=0,
        help="Save full assignments every N steps; 0 disables snapshots.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dem_column = f"PRE{args.election[-2:]}D"
    rep_column = f"PRE{args.election[-2:]}R"
    graph_path = PROJECT_ROOT / "data" / "raw" / args.state / args.state / f"{args.state}.json"

    graph = load_graph(graph_path)
    partition = build_initial_partition(
        graph,
        assignment_column="CD",
        dem_column=dem_column,
        rep_column=rep_column,
    )
    target_population = ideal_population(partition)
    run_name = f"{args.state}_{args.election}_{args.chain_id}_{args.steps}steps_seed{args.seed}"

    print(f"State: {STATE_NAMES[args.state]}")
    print(f"Nodes: {len(graph):,}; edges: {graph.number_of_edges():,}")
    print(f"Districts: {len(partition)}")
    print(f"Ideal population: {target_population:,.2f}")
    print(f"Population tolerance: ±{100 * args.epsilon:.2f}%")

    config = ChainConfig(
        total_steps=args.steps,
        epsilon=args.epsilon,
        node_repeats=args.node_repeats,
        seed=args.seed,
        snapshot_interval=args.snapshot_interval,
    )
    plan_metrics, district_metrics, snapshots = run_recom_chain(partition, config)

    chain_dir = PROJECT_ROOT / "outputs" / "chains" / "week4"
    metadata = {
        "state": args.state,
        "state_name": STATE_NAMES[args.state],
        "graph_path": str(graph_path.relative_to(PROJECT_ROOT)),
        "assignment_column": "CD",
        "population_column": "TOTPOP",
        "dem_column": dem_column,
        "rep_column": rep_column,
        "election": args.election,
        "steps_including_initial_plan": args.steps,
        "epsilon": args.epsilon,
        "node_repeats": args.node_repeats,
        "seed": args.seed,
        "ideal_population": target_population,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Step 0 is the enacted starting plan. These diagnostics do not prove mixing.",
    }
    paths = save_chain_outputs(
        plan_metrics,
        district_metrics,
        snapshots,
        chain_dir,
        run_name,
        metadata,
    )

    trace_path = PROJECT_ROOT / "outputs" / "figures" / "week4" / f"{run_name}_traces.png"
    make_trace_plots(
        plan_metrics,
        trace_path,
        title=f"{STATE_NAMES[args.state]} ReCom trace diagnostics ({args.steps:,} steps)",
    )

    print("\nSaved:")
    for path in paths.values():
        print(f"  {path.relative_to(PROJECT_ROOT)}")
    print(f"  {trace_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
