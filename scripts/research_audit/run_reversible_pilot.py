#!/usr/bin/env python3
"""Reversible-boundary-MH Michigan feasibility pilot, independently audited.

A small exact-state proof of detailed balance accompanies this trial. The
policy/legal relevance of uniformly sampling the accessible *labeled*
proxy-constrained precinct maps is not established. Sampling success is
operational evidence only; no outlier probability or convergence is claimed.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from gerrychain import Partition

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from redistricting.ensemble.chain import partition_statistics, save_chain_outputs
from redistricting.ensemble.partition import (
    build_initial_partition, ideal_population, load_graph, make_updaters,
)
from redistricting.ensemble.reversible import BoundaryMH, BoundaryMHConfig
from redistricting.ensemble.start_diversity import (
    WarmStartConfig, assignment_digest, label_invariant_distance, warm_endpoint,
)
from verify_graph import digest
from verify_snapshots import check_one

PINNED_UPSTREAM_BLOB = "a4dfe70818f87b97924781216f3d86a672cfc66a"


def execute(args: argparse.Namespace) -> dict:
    if args.states < 2 or args.snapshot_interval < 1:
        raise ValueError("Positive chain size and snapshot interval required")
    if (args.states - 1) % args.snapshot_interval:
        raise ValueError("Require snapshot_interval dividing (states-1)")
    if args.warm_seed == args.sample_seed:
        raise ValueError("Warmup and local MH RNG seeds must differ")
    if not (0 < args.flip_probability < 1):
        raise ValueError("Use both local reversible kernels in this pilot")

    graph_source = digest(args.graph)
    if graph_source["git_blob_sha1"] != PINNED_UPSTREAM_BLOB:
        raise ValueError("Input graph is not pinned source")
    graph = load_graph(args.graph)
    reference = build_initial_partition(graph, "CD", "PRE20D", "PRE20R")
    if len(reference) != 13 or len(graph) != 4756:
        raise ValueError("Unexpected 2020 Michigan graph")
    initial_reference = dict(reference.assignment.items())
    warm_cfg = WarmStartConfig(
        epsilon=args.epsilon, steps_including_reference=args.warm_steps,
        max_cut_edges=args.max_cut_edges,
        max_split_counties=args.max_split_counties,
        max_split_county_mcd=args.max_split_county_mcd,
    )
    warm, warm_meta = warm_endpoint(reference, args.warm_seed, warm_cfg)
    if args.expected_warm_sha and warm_meta["final_assignment_sha256"] != args.expected_warm_sha:
        raise ValueError("Reconstructed seeded warm start does not match pinned SHA-256")

    from_reference = label_invariant_distance(initial_reference, warm)
    if from_reference["fraction_different"] < 0.05:
        raise ValueError("Warm-start distance from enacted is less than 5%")
    independent_start = check_one(graph,
                                  {str(n): str(d) for n,d in warm.items()},
                                  args.epsilon, len(reference))
    for metric, original in warm_meta["final_geographic_proxies"].items():
        if independent_start[metric] != original:
            raise ValueError(f"Independent geographical rescore mismatch for {metric}")

    current = Partition(graph=reference.graph, assignment=warm,
                        updaters=make_updaters())
    config = BoundaryMHConfig(
        epsilon=args.epsilon, seed=args.sample_seed,
        flip_probability=args.flip_probability,
        max_cut_edges=args.max_cut_edges,
        max_split_counties=args.max_split_counties,
        max_split_county_mcd=args.max_split_county_mcd,
    )
    mh = BoundaryMH(current, config)
    target = ideal_population(reference)
    plan_rows, district_rows = [], []
    snapshots = {}
    enacted_reference_row, _ = partition_statistics(reference, 0, target)
    spatial_probe_rows = []
    spatial_checkpoints = set(range(0, args.states, args.spatial_interval)) | {args.states-1}
    # The first state is the independently regenerated *warmed* map.
    for step in range(args.states):
        if step > 0:
            old = current
            event = mh.step(old)
            current = event.partition
            if current is not old:
                old.parent = None
        else:
            from redistricting.ensemble.reversible import MHStep
            event = MHStep(current, "initial", "initial", 0, 0, 0, 0)

        row, per_district = partition_statistics(current, step, target)
        row.update(mh.geography.score(current))
        row.update({
            "proposal_type": event.move,
            "transition_outcome": event.outcome,
            "mh_q_forward": event.q_forward,
            "mh_q_reverse": event.q_reverse,
            "mh_alpha": event.acceptance_probability,
            "nodes_changed_since_previous": event.node_changes,
            "state_changed_since_previous": int(event.outcome == "accepted"),
            "mh_attempted_total": mh.counts["attempted"],
            "mh_accepted_total": mh.counts["accepted"],
            "mh_population_rejected_total": mh.counts["population_rejected"],
            "mh_contiguity_rejected_total": mh.counts["contiguity_rejected"],
            "mh_geography_rejected_total": mh.counts["geography_rejected"],
            "mh_ratio_rejected_total": mh.counts["mh_rejected"],
        })
        plan_rows.append(row)
        district_rows.extend(per_district)
        if step % args.snapshot_interval == 0:
            snapshots[step] = {
                str(n): str(d) for n,d in current.assignment.items()
            }
        if step in spatial_checkpoints:
            candidate = dict(current.assignment.items())
            spatial_probe_rows.append({
                "step": step,
                "reference_fraction_different":
                    label_invariant_distance(initial_reference, candidate)["fraction_different"],
                "warm_start_fraction_different":
                    label_invariant_distance(warm, candidate)["fraction_different"],
                "assignment_sha256": assignment_digest(candidate),
            })
        if step % 500 == 0 or step == args.states - 1:
            print(f"MH step {step}/{args.states-1}, "
                  f"accepted={mh.counts['accepted']}/{mh.counts['attempted']}, "
                  f"pop_reject={mh.counts['population_rejected']}, "
                  f"geo_reject={mh.counts['geography_rejected']}, "
                  f"cuts={row['cut_edges']}",flush=True)

    counters = mh.conservation_audit()
    if counters["attempted"] != args.states - 1:
        raise AssertionError("Not exactly one attempted proposal per recorded transition")
    if assignment_digest(snapshots[0]) != warm_meta["final_assignment_sha256"]:
        raise AssertionError("Sample did not start at the cryptographically checked warm map")

    final_assignment = {str(n): str(d) for n,d in current.assignment.items()}
    meta = {
        "kernel": "boundary_uniform_choice_local_flip_swap_mh_v1",
        "stationary_target": (
            "Uniform on each finite communicating class of feasible labeled assignments. "
            "No claim of irreducibility across all proxy-constrained assignments."
        ),
        "detailed_balance": (
            "For flips q=n_neighbors_to_target/(2*number_of_current_boundary_edges); "
            "reverse uses candidate boundary count. For swaps q=1/boundary_edges. "
            "Separate constant-probability mixture is reversible and "
            "acceptance=min(1,q_reverse/q_forward)."
        ),
        "source_sha256": graph_source["sha256"],
        "source_blob_sha1": graph_source["git_blob_sha1"],
        "warm_seed": args.warm_seed,
        "sample_seed": args.sample_seed,
        "config": asdict(config),
        "states": args.states,
        "warm_states": args.warm_steps,
        "snapshot_interval": args.snapshot_interval,
        "spatial_interval": args.spatial_interval,
        "warmed_step0_is_reference": False,
        "reference_election_scores": enacted_reference_row,
        "warm_start_sha256": warm_meta["final_assignment_sha256"],
        "sample_end_sha256": assignment_digest(final_assignment),
        "from_reference": from_reference,
        "final_from_warm": label_invariant_distance(warm, final_assignment),
        "initial_reference_geographic": mh.geography.score(reference),
        "initial_warm_geographic": mh.geography.score(
            Partition(graph=reference.graph,assignment=warm,updaters=make_updaters())
        ),
        "counters": counters,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "important_limitations": [
            "5 unverified artificial source-graph island bridges.",
            "Only proxy county and MCD grouping constraints, not Michigan legal criteria.",
            "No proof that flip/swap local kernel is irreducible among all feasible maps.",
            "Stationarity and spatial mixing not established by detailed balance alone.",
            "Short pilot outcomes are not reliable enacted-map tail probabilities.",
        ],
    }
    stem=(f"mi_2020_reversible_{args.condition}_warm{args.warm_seed}_"
          f"sample{args.sample_seed}_{args.states}states")
    paths=save_chain_outputs(pd.DataFrame(plan_rows),
                             pd.DataFrame(district_rows),
                             snapshots, args.output_root / "chains",
                             stem, metadata=meta)
    reports=args.output_root / "reports"
    reports.mkdir(parents=True,exist_ok=True)
    (reports/(stem+"_reference.json")).write_text(
        json.dumps(enacted_reference_row, indent=2), encoding="utf-8"
    )
    pd.DataFrame(spatial_probe_rows).to_csv(
        reports/(stem+"_spatial_probes.csv"), index=False
    )
    summary={
        "condition":args.condition,
        "warm_seed":args.warm_seed,
        "sample_seed":args.sample_seed,
        "states":args.states,
        "attempted":counters["attempted"],
        "accepted":counters["accepted"],
        "acceptance_fraction":counters["accepted"]/counters["attempted"],
        "flip_accepted":counters["flip_accepted"],
        "swap_accepted":counters["swap_accepted"],
        "population_rejected":counters["population_rejected"],
        "contiguity_rejected":counters["contiguity_rejected"],
        "geography_rejected":counters["geography_rejected"],
        "mh_rejected":counters["mh_rejected"],
        "distinct_score_rows":len(pd.DataFrame(plan_rows)[
            ["dem_seats","efficiency_gap","cut_edges"]].drop_duplicates()),
        "initial_distance_from_enacted":from_reference["fraction_different"],
        "final_distance_from_warm":meta["final_from_warm"]["fraction_different"],
        "report_warning":"Reversibility, not convergence, established for this local MH model.",
    }
    pd.DataFrame([summary]).to_csv(reports/(stem+"_summary.csv"), index=False)
    (reports/(stem+"_audit.json")).write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("REVERSIBLE_MH_PILOT",summary,flush=True)
    return summary


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph",type=Path,required=True)
    parser.add_argument("--output-root",type=Path,required=True)
    parser.add_argument("--condition",choices=("closer","relaxed"),required=True)
    parser.add_argument("--warm-seed",type=int,required=True)
    parser.add_argument("--sample-seed",type=int,required=True)
    parser.add_argument("--expected-warm-sha")
    parser.add_argument("--epsilon",type=float,default=.005)
    parser.add_argument("--flip-probability",type=float,default=.5)
    parser.add_argument("--warm-steps",type=int,default=800)
    parser.add_argument("--states",type=int,default=2001)
    parser.add_argument("--snapshot-interval",type=int,default=100)
    parser.add_argument("--spatial-interval",type=int,default=1000)
    parser.add_argument("--max-cut-edges",type=int,required=True)
    parser.add_argument("--max-split-counties",type=int,required=True)
    parser.add_argument("--max-split-county-mcd",type=int,required=True)
    args=parser.parse_args()
    if args.spatial_interval < 1:
        parser.error("--spatial-interval must be positive")
    execute(args)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
