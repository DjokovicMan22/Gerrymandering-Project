#!/usr/bin/env python3
"""Independent seeded finite-horizon Michigan plan perturbations.

This replaces a failed *stationary legal-plan ensemble* claim with a narrower
but statistically identifiable target: a single final plan after exactly T
recorded GerryChain ReCom steps begun at the enacted reference and subject to
fully documented *exploratory* graph-proximity and fragmentation constraints.

Replicates use independent fixed RNG streams and only ONE endpoint per seed,
so cross-replicate Monte Carlo uncertainty does not require chain R-hat or ESS.
That does NOT validate the transition distribution as a legal-neutral null,
or make empirical endpoint ranks legitimate enacted-map p-values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))

from redistricting.ensemble.partition import (
    load_graph,build_initial_partition,ideal_population,
)
from redistricting.ensemble.chain import ChainConfig,run_recom_chain,partition_statistics
from redistricting.ensemble.start_diversity import (
    assignment_digest,label_invariant_distance
)
from verify_snapshots import check_one


def score_matches(archived, independent):
    comparisons={
        "cut_edges":"cut_edges",
        "max_population_deviation":"max_population_deviation",
        "dem_seats":"dem_seats_20",
        "efficiency_gap":"efficiency_gap_20",
        "split_counties":"split_counties",
        "split_county_mcd":"split_county_mcd",
    }
    for old,new in comparisons.items():
        if old not in archived or new not in independent:
            raise ValueError(f"Missing independent-scoring metric: {old}/{new}")
        if not np.isfinite(float(archived[old])) or not np.isfinite(float(independent[new])):
            raise ValueError("Nonfinite endpoint metric")
        if abs(float(archived[old])-float(independent[new]))>1e-9:
            raise ValueError(f"Endpoint {old} mismatches independently recomputed {new}")


def experiment(args)->list[dict]:
    if args.count<1 or args.seed_first<1 or args.total_steps<3:
        raise ValueError("Positive cohort size, seed and time horizon required")
    manifest=json.loads(args.manifest.read_text(encoding="utf-8"))
    sha=hashlib.sha256(args.graph.read_bytes()).hexdigest()
    if sha!=manifest["serialized_graph_sha256"]:
        raise ValueError("The derived KNN geometry graph does not match source-based construction manifest")
    if (manifest.get("method")!="3 closest external precinct polygons from each disconnected component"
            or manifest.get("legal_and_water_island_geography_certified") is not False
            or manifest.get("added_edge_count")!=13):
        raise ValueError("Wrong or mischaracterized geometric model")
    graph=load_graph(args.graph)
    initial=build_initial_partition(graph)
    if len(graph)!=4756 or len(initial)!=13 or graph.number_of_edges()!=12391:
        raise ValueError("Unexpected source/adjacency model")
    fixed_source={str(n):str(d) for n,d in initial.assignment.items()}
    reference_score,_=partition_statistics(initial,0,ideal_population(initial))
    independent_reference=check_one(graph,fixed_source,args.epsilon,13)
    # There are no geographic source metrics attached to plain partition_statistics;
    # directly compare the independently scored reference and its seat/gap values.
    for key,other in (("cut_edges","cut_edges"),("dem_seats","dem_seats_20"),
                      ("efficiency_gap","efficiency_gap_20")):
        if abs(float(reference_score[key])-float(independent_reference[other]))>1e-9:
            raise ValueError("Enacted reference score differs under independent source-graph rescoring")
    rows=[]
    for seed in range(args.seed_first,args.seed_first+args.count):
        config=ChainConfig(
            total_steps=args.total_steps,seed=seed,epsilon=args.epsilon,
            node_repeats=2,snapshot_interval=args.total_steps-1,
            max_cut_edges=args.max_cut_edges,
            max_split_counties=args.max_split_counties,
            max_split_county_mcd=args.max_split_county_mcd,
        )
        plans,_,snapshots=run_recom_chain(initial,config)
        if len(plans)!=args.total_steps or set(snapshots)!={0,args.total_steps-1}:
            raise ValueError("Missing required chain initial/terminal states")
        if assignment_digest(snapshots[0])!=assignment_digest(fixed_source):
            raise ValueError("Run did not start from the predeclared enacted reference")
        final=snapshots[args.total_steps-1]
        independent=check_one(graph,final,args.epsilon,13)
        last=plans.iloc[-1].to_dict()
        score_matches(last,independent)
        diff=label_invariant_distance(fixed_source,final)
        attempted=int(plans["geographic_proposals_attempted_total"].iloc[-1])
        geo_rejections=int(plans["geographic_proposals_rejected_total"].iloc[-1])
        row={
            "condition":args.condition,
            "rng_seed":seed,
            "steps_including_enacted_reference":args.total_steps,
            "model_graph_sha256":sha,
            "reference_assignment_sha256":assignment_digest(fixed_source),
            "reference_dem_seats":reference_score["dem_seats"],
            "reference_efficiency_gap":reference_score["efficiency_gap"],
            "reference_cut_edges":reference_score["cut_edges"],
            "endpoint_sha256":assignment_digest(final),
            "endpoint_fraction_precincts_different_from_reference":diff["fraction_different"],
            "endpoint_dem_seats":int(last["dem_seats"]),
            "endpoint_efficiency_gap":float(last["efficiency_gap"]),
            "endpoint_cut_edges":int(last["cut_edges"]),
            "endpoint_split_counties":int(last["split_counties"]),
            "endpoint_split_county_mcd":int(last["split_county_mcd"]),
            "endpoint_max_population_deviation":float(last["max_population_deviation"]),
            "recorded_states_changed":int(plans["state_changed_since_previous"].sum()),
            "geographic_attempts":attempted,
            "geographic_rejections":geo_rejections,
            "geographic_rejection_fraction":geo_rejections/max(1,attempted),
            "independently_rescored_endpoint":True,
            "legal_and_stationary_map_distribution_certified":False,
        }
        if attempted!=args.total_steps-1:
            raise ValueError("Unexpected proposal-attempt tally; cannot compare fixed steps")
        rows.append(row)
        print("INDEPENDENT_FINITE_HORIZON_ENDPOINT",json.dumps(row),flush=True)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output,index=False)
    return rows


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--graph",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--condition",choices=("closer","relaxed"),required=True)
    p.add_argument("--seed-first",type=int,required=True)
    p.add_argument("--count",type=int,default=4)
    p.add_argument("--total-steps",type=int,default=801)
    p.add_argument("--epsilon",type=float,default=.005)
    p.add_argument("--max-cut-edges",type=int,required=True)
    p.add_argument("--max-split-counties",type=int,required=True)
    p.add_argument("--max-split-county-mcd",type=int,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    expected=(760,18,20) if args.condition=="closer" else (850,24,49)
    if (args.max_cut_edges,args.max_split_counties,args.max_split_county_mcd)!=expected:
        p.error("This preregistration fixes geographic cap combinations")
    experiment(args)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
