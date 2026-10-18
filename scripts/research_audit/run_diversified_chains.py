#!/usr/bin/env python3
"""Reproduce a pinned Michigan warmup, then sample from that *different* map.

Warmups are separately seeded trajectories from one common enacted ancestor.
The sampling chain receives a distinct, explicitly recorded RNG seed. The
enacted map—not the warmed step 0—is the comparison reference. Neither the
ReCom target stationary distribution nor legal-plan uniformity is established.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gerrychain import Partition  # noqa: E402
from redistricting.ensemble.chain import (  # noqa: E402
    ChainConfig, partition_statistics, run_recom_chain, save_chain_outputs,
)
from redistricting.ensemble.partition import (  # noqa: E402
    build_initial_partition, ideal_population, load_graph, make_updaters,
)
from redistricting.ensemble.start_diversity import (  # noqa: E402
    WarmStartConfig, assignment_digest, label_invariant_distance, warm_endpoint,
)
from verify_graph import digest  # noqa: E402
from verify_snapshots import check_one  # noqa: E402

EXPECTED_BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"


def reconstruct_warmed_partition(reference: Partition, assignment: dict) -> Partition:
    """Build the start from the warmup assignment, not the enacted node attribute."""
    left = dict(reference.assignment.items())
    if set(left) != set(assignment):
        raise ValueError("Warm assignment node set differs from the reference graph")
    if set(left.values()) != set(assignment.values()):
        raise ValueError("Warm assignment changes the district-label set")
    if len(left) != len(assignment):
        raise ValueError("Warmup assignment contains duplicate nodes")
    warmed = Partition(
        graph=reference.graph,
        assignment=dict(assignment),
        updaters=make_updaters("PRE20D", "PRE20R"),
    )
    if assignment_digest(dict(warmed.assignment.items())) != assignment_digest(assignment):
        raise ValueError("Reconstructed Partition lost the warmup assignments")
    return warmed


def execute(args: argparse.Namespace) -> dict:
    if args.warm_seed == args.sample_seed:
        raise ValueError("warm and sampling seeds must be distinct")
    if args.steps < 3 or args.snapshot_interval < 1 or (args.steps - 1) % args.snapshot_interval:
        raise ValueError("Need >=3 steps and a snapshot interval dividing (steps - 1)")
    if args.warm_steps < 2:
        raise ValueError("Need >=2 warmup states")
    graph_hash = digest(args.graph)
    if graph_hash["git_blob_sha1"] != EXPECTED_BLOB:
        raise ValueError("Source graph differs from the pinned upstream Git blob")
    graph = load_graph(args.graph)
    reference = build_initial_partition(graph, "CD", "PRE20D", "PRE20R")
    if len(reference) != 13 or len(graph) != 4756:
        raise ValueError("Unexpected Michigan district/node counts")

    warm_config = WarmStartConfig(
        epsilon=args.epsilon,
        steps_including_reference=args.warm_steps,
        max_cut_edges=args.max_cut_edges,
        max_split_counties=args.max_split_counties,
        max_split_county_mcd=args.max_split_county_mcd,
    )
    warm_assignment, warm_meta = warm_endpoint(reference, args.warm_seed, warm_config)
    if args.expected_warm_hash and warm_meta["final_assignment_sha256"] != args.expected_warm_hash:
        raise ValueError(
            "Warmup is not reproducible: endpoint hash differs from prior verified pilot. "
            f"Got {warm_meta['final_assignment_sha256']}, expected {args.expected_warm_hash}"
        )
    original = dict(reference.assignment.items())
    warmed = reconstruct_warmed_partition(reference, warm_assignment)
    original_distance = label_invariant_distance(original, warm_assignment)
    if original_distance["fraction_different"] < args.min_initial_distance:
        raise ValueError(
            f"Insufficient dispersed warm start: {original_distance['fraction_different']:.6f} "
            f"< {args.min_initial_distance:.6f}"
        )

    independent = check_one(
        graph, {str(node): str(district) for node, district in warm_assignment.items()},
        args.epsilon, len(reference),
    )
    for key, expected in warm_meta["final_geographic_proxies"].items():
        if independent[key] != expected:
            raise ValueError(f"Independent warm start geographic discrepancy: {key}")
    if abs(independent["max_population_deviation"] -
           warm_meta["final_max_population_deviation"]) > 1e-10:
        raise ValueError("Independent population score discrepancy")

    sample_config = ChainConfig(
        total_steps=args.steps,
        epsilon=args.epsilon,
        seed=args.sample_seed,
        snapshot_interval=args.snapshot_interval,
        max_cut_edges=args.max_cut_edges,
        max_split_counties=args.max_split_counties,
        max_split_county_mcd=args.max_split_county_mcd,
    )
    # run_recom_chain independently seeds Python and NumPy with sample_seed.
    plan, districts, snapshots = run_recom_chain(warmed, sample_config)
    if len(plan) != args.steps or len(snapshots) != 1 + (args.steps - 1)//args.snapshot_interval:
        raise ValueError("Unexpected sampled metrics/snapshot counts")
    if assignment_digest(snapshots[0]) != assignment_digest(warm_assignment):
        raise ValueError("Sampled chain step 0 does not match audited warm start")

    # Sparse exact spatial probes, not merely scalar vote or cut-edge traces.
    # Checkpoints are aligned to saved snapshots and span the sampled path.
    checkpoint_steps = sorted({
        args.snapshot_interval *
        (((args.steps - 1) * fraction // 4) // args.snapshot_interval)
        for fraction in range(5)
    })
    spatial_probes = []
    for step in checkpoint_steps:
        candidate = snapshots[step]
        spatial_probes.append({
            "step":step,
            "reference_fraction_different":
                label_invariant_distance(original, candidate)["fraction_different"],
            "warm_start_fraction_different":
                label_invariant_distance(warm_assignment, candidate)["fraction_different"],
            "assignment_sha256":assignment_digest(candidate),
        })

    endpoint = snapshots[args.steps - 1]
    endpoint_vs_reference = label_invariant_distance(original, endpoint)
    endpoint_vs_warmup = label_invariant_distance(warm_assignment, endpoint)
    ideal = ideal_population(reference)
    reference_row, _ = partition_statistics(reference, 0, ideal)
    sample_dir = args.output_root / "chains"
    stem = (
        f"mi_2020_diverse_{args.condition}_warm{args.warm_seed}_"
        f"sample{args.sample_seed}_{args.steps}steps"
    )
    info = {
        "source_git_blob": graph_hash["git_blob_sha1"],
        "source_sha256": graph_hash["sha256"],
        "condition": args.condition,
        "origin": "pinned Michigan enacted reference",
        "warmed_step0_is_reference": False,
        "warmup_metadata": warm_meta,
        "min_initial_distance_gate": args.min_initial_distance,
        "warmup_distance_from_enacted": original_distance,
        "sample_seed": args.sample_seed,
        "sample_steps_including_warm_start": args.steps,
        "snapshot_interval": args.snapshot_interval,
        "epsilon": args.epsilon,
        "geographic_proxy_caps": warm_config.caps.__dict__,
        "final_sample_distance_from_enacted": endpoint_vs_reference,
        "final_sample_distance_from_warm_start": endpoint_vs_warmup,
        "spatial_probe_steps": checkpoint_steps,
        "reference_election_scores": reference_row,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "interpretation": (
            "All warmups trace independent seeded paths from one enacted ancestor. "
            "No stationary-law, legal-plan-uniformity, or genuine GIS topology certification."
        ),
    }
    output_paths = save_chain_outputs(
        plan, districts, snapshots, sample_dir, stem, metadata=info,
    )
    report_dir = args.output_root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(spatial_probes).to_csv(
        report_dir / (stem + "_spatial_probes.csv"), index=False
    )
    (report_dir / (stem + "_reference.json")).write_text(
        json.dumps(reference_row, indent=2), encoding="utf-8"
    )
    (report_dir / (stem + "_audit.json")).write_text(
        json.dumps(info, indent=2), encoding="utf-8"
    )
    changed = plan["state_changed_since_previous"].iloc[1:]
    post = plan.loc[plan["step"] >= args.burn_in]
    diagnostic = {
        "condition": args.condition,
        "warm_seed": args.warm_seed,
        "sample_seed": args.sample_seed,
        "steps": args.steps,
        "burn_in": args.burn_in,
        "post_burnin": len(post),
        "initial_distance_from_enacted": original_distance["fraction_different"],
        "final_distance_from_enacted": endpoint_vs_reference["fraction_different"],
        "final_distance_from_warm": endpoint_vs_warmup["fraction_different"],
        "changed_step_fraction": float(changed.mean()),
        "geographic_rejection_fraction": float(
            plan["geographic_proposals_rejected_total"].iloc[-1] /
            plan["geographic_proposals_attempted_total"].iloc[-1]
        ),
        "post_mean_dem_seats": float(post["dem_seats"].mean()),
        "post_mean_efficiency_gap": float(post["efficiency_gap"].mean()),
        "post_mean_cut_edges": float(post["cut_edges"].mean()),
        "post_mean_split_counties": float(post["split_counties"].mean()),
        "post_mean_split_county_mcd": float(post["split_county_mcd"].mean()),
        "warm_assignment_sha256": warm_meta["final_assignment_sha256"],
        "sample_end_assignment_sha256": assignment_digest(endpoint),
    }
    pd.DataFrame([diagnostic]).to_csv(
        report_dir / (stem + "_summary.csv"), index=False
    )
    print("SAMPLED_FROM_VERIFIED_DIVERSE_START", diagnostic, flush=True)
    print("saved", {key: str(path) for key, path in output_paths.items()}, flush=True)
    return diagnostic


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--condition", choices=("closer", "relaxed"), required=True)
    ap.add_argument("--warm-seed", type=int, required=True)
    ap.add_argument("--sample-seed", type=int, required=True)
    ap.add_argument("--warm-steps", type=int, default=800)
    ap.add_argument("--steps", type=int, default=4001)
    ap.add_argument("--burn-in", type=int, default=1000)
    ap.add_argument("--snapshot-interval", type=int, default=50)
    ap.add_argument("--epsilon", type=float, default=0.005)
    ap.add_argument("--max-cut-edges", type=int, required=True)
    ap.add_argument("--max-split-counties", type=int, required=True)
    ap.add_argument("--max-split-county-mcd", type=int, required=True)
    ap.add_argument("--expected-warm-hash")
    ap.add_argument("--min-initial-distance", type=float, default=0.05)
    args = ap.parse_args()
    if args.burn_in < 1 or args.burn_in >= args.steps - 8:
        ap.error("Burn-in must be >=1 and leave at least nine post-burn-in states")
    if not 0 <= args.min_initial_distance <= 1:
        ap.error("Invalid initial-distance gate")
    execute(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
