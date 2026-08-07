#!/usr/bin/env python3
"""Run shorter ReCom ensembles for Week 6 population-tolerance sensitivity."""
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
    parser.add_argument("--election", choices=("2020", "2016"), default="2020")
    parser.add_argument("--epsilons", nargs="+", type=float, default=[0.01, 0.03])
    parser.add_argument("--steps", type=int, default=3_000)
    parser.add_argument("--seeds", nargs="+", type=int, default=[101, 202, 303])
    parser.add_argument("--node-repeats", type=int, default=2)
    parser.add_argument("--snapshot-interval", type=int, default=0)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-run chains even when all expected outputs already exist.",
    )
    return parser.parse_args()


def epsilon_slug(epsilon: float) -> str:
    percent = 100 * epsilon
    if abs(percent - round(percent)) < 1e-10:
        return f"eps{int(round(percent))}pct"
    text = f"{percent:.3f}".rstrip("0").rstrip(".").replace(".", "p")
    return f"eps{text}pct"


def main() -> None:
    args = parse_args()
    if args.steps < 2:
        raise SystemExit("--steps must be at least 2")
    if not args.seeds:
        raise SystemExit("Provide at least one seed")
    for epsilon in args.epsilons:
        if not 0 < epsilon < 1:
            raise SystemExit(f"Invalid epsilon: {epsilon}")

    dem_column = f"PRE{args.election[-2:]}D"
    rep_column = f"PRE{args.election[-2:]}R"
    graph_path = (
        PROJECT_ROOT
        / "data"
        / "raw"
        / args.state
        / args.state
        / f"{args.state}.json"
    )
    graph = load_graph(graph_path)
    initial_partition = build_initial_partition(
        graph,
        assignment_column="CD",
        dem_column=dem_column,
        rep_column=rep_column,
    )
    target_population = ideal_population(initial_partition)

    chain_dir = PROJECT_ROOT / "outputs" / "chains" / "week6"
    trace_dir = PROJECT_ROOT / "outputs" / "figures" / "week6" / "traces"
    chain_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    print(f"State: {STATE_NAMES[args.state]}")
    print(f"Election layer: {args.election}")
    print(f"Nodes: {len(graph):,}; edges: {graph.number_of_edges():,}")
    print(f"Districts: {len(initial_partition)}")
    print(f"Ideal population: {target_population:,.2f}")

    for epsilon in args.epsilons:
        slug = epsilon_slug(epsilon)
        for chain_number, seed in enumerate(args.seeds, start=1):
            run_name = (
                f"{args.state}_{args.election}_{slug}_chain{chain_number}_"
                f"{args.steps}steps_seed{seed}"
            )
            expected_paths = [
                chain_dir / f"{run_name}_plan_metrics.csv",
                chain_dir / f"{run_name}_district_metrics.csv",
                chain_dir / f"{run_name}_metadata.json",
                trace_dir / f"{run_name}_traces.png",
            ]
            if not args.overwrite and all(path.exists() for path in expected_paths):
                print(f"Skipping existing run: {run_name}")
                continue

            print("\n" + "=" * 72)
            print(
                f"Running {run_name}: tolerance ±{100 * epsilon:.2f}%, "
                f"seed {seed}, {args.steps:,} steps"
            )
            config = ChainConfig(
                total_steps=args.steps,
                epsilon=epsilon,
                node_repeats=args.node_repeats,
                seed=seed,
                snapshot_interval=args.snapshot_interval,
            )
            plan_metrics, district_metrics, snapshots = run_recom_chain(
                initial_partition, config
            )
            metadata = {
                "week": 6,
                "investigation": "population_tolerance_sensitivity",
                "state": args.state,
                "state_name": STATE_NAMES[args.state],
                "graph_path": str(graph_path.relative_to(PROJECT_ROOT)),
                "assignment_column": "CD",
                "population_column": "TOTPOP",
                "dem_column": dem_column,
                "rep_column": rep_column,
                "election": args.election,
                "steps_including_initial_plan": args.steps,
                "epsilon": epsilon,
                "node_repeats": args.node_repeats,
                "seed": seed,
                "ideal_population": target_population,
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "note": (
                    "Step 0 is the enacted plan. This is a shorter Week 6 "
                    "sensitivity ensemble, not proof of uniform sampling or mixing."
                ),
            }
            paths = save_chain_outputs(
                plan_metrics,
                district_metrics,
                snapshots,
                chain_dir,
                run_name,
                metadata,
            )
            trace_path = trace_dir / f"{run_name}_traces.png"
            make_trace_plots(
                plan_metrics,
                trace_path,
                title=(
                    f"{STATE_NAMES[args.state]} Week 6 trace — "
                    f"±{100 * epsilon:.1f}% population tolerance"
                ),
            )
            print("Saved:")
            for path in paths.values():
                print(f"  {path.relative_to(PROJECT_ROOT)}")
            print(f"  {trace_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
