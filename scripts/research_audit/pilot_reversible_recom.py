#!/usr/bin/env python3
"""Probe published ReCom variant R on Michigan; do not claim convergence.

The spanning-tree target differs from the uniform-feasible-target local MH
sampler. Arbitrary hard geographic rejections condition the proposed chain on
those constraints *if* the original ReCom R kernel is reversible with regard
to the stated law; no proof of practical mixing or legal comparability follows.

This first performance probe uses the historical augmented Michigan graph
and is NOT a legal/physical contiguity experiment.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from gerrychain.proposals import ReCom
from gerrychain.constraints import contiguous

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
from redistricting.ensemble.partition import (load_graph,build_initial_partition,
                                              ideal_population,max_population_deviation)
from redistricting.ensemble.start_diversity import WarmStartConfig,warm_endpoint,assignment_digest
from redistricting.ensemble.geographic import GeographicCaps,GeographicEvaluator
from verify_graph import digest

PIN="a4dfe70818f87b97924781216f3d86a672cfc66a"


def pilot(args):
    if digest(args.graph)["git_blob_sha1"]!=PIN:
        raise ValueError("Source graph has changed")
    graph=load_graph(args.graph)
    ref=build_initial_partition(graph)
    caps=GeographicCaps(args.max_cut_edges,args.max_split_counties,args.max_split_county_mcd)
    evaluator=GeographicEvaluator(ref.graph,caps)
    assignment,warm_meta=warm_endpoint(ref,args.warm_seed,WarmStartConfig(
        epsilon=.005,steps_including_reference=800,
        max_cut_edges=caps.max_cut_edges,
        max_split_counties=caps.max_split_counties,
        max_split_county_mcd=caps.max_split_county_mcd))
    from gerrychain import Partition
    from redistricting.ensemble.partition import make_updaters
    state=Partition(graph=ref.graph,assignment=assignment,updaters=make_updaters())
    if not evaluator(state):
        raise ValueError("Invalid starting geometry")
    target=ideal_population(state)
    proposal=ReCom.reversible(pop_col="TOTPOP",pop_target=target,
                             epsilon=.005,max_balanced_edge_cuts=args.cut_cap,
                             repeat_until_valid=False)
    rng=random.Random(args.sample_seed)
    cnt={"attempted":0,"accepted":0,"internal_hold":0,"geo_rejected":0,
         "population_rejected":0,"contiguity_rejected":0}
    sampled=[]
    for step in range(args.steps):
        old=state
        if step:
            cnt["attempted"]+=1
            candidate=proposal(state,rng=rng)  # ANY ReversibilityError is a hard failure.
            if candidate is state or dict(candidate.assignment.items())==dict(state.assignment.items()):
                cnt["internal_hold"]+=1
            elif (max_population_deviation(candidate,target)>.005+1e-12):
                cnt["population_rejected"]+=1
            elif not contiguous(candidate):
                cnt["contiguity_rejected"]+=1
            elif not evaluator(candidate):
                cnt["geo_rejected"]+=1
            else:
                state=candidate
                cnt["accepted"]+=1
                old.parent=None
        if step%max(1,args.steps//10)==0 or step==args.steps-1:
            score=evaluator.score(state)
            sampled.append({"step":step,**score,"assignment_sha256":assignment_digest(
                dict(state.assignment.items()))})
            print("VARIANT_R_STEP",step,"accepted",cnt["accepted"],
                  "internal_holds",cnt["internal_hold"],"cut",score["cut_edges"],flush=True)
    if sum(cnt[k] for k in ("accepted","internal_hold","geo_rejected",
                            "population_rejected","contiguity_rejected"))!=cnt["attempted"]:
        raise AssertionError("Proposals missing in accounting")
    result={
        "method":"GerryChain v1.0.0 published reversible ReCom R",
        "note":"TUNING PILOT ON OLD UNVERIFIED BRIDGE GRAPH, NOT GEOGRAPHIC/LEGAL VALIDITY",
        "seed":args.sample_seed,"warm_seed":args.warm_seed,
        "condition":args.condition,"steps":args.steps,
        "balanced_edge_cut_upper_bound":args.cut_cap,
        "source_graph_git_blob":PIN,
        "warm_sha256":warm_meta["final_assignment_sha256"],
        "counters":cnt,
        "realized_move_fraction":cnt["accepted"]/max(1,cnt["attempted"]),
        "snapshots":sampled,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("REVERSIBLE_RECOM_R_TUNING",json.dumps(result),flush=True)
    return 0


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graph",type=Path,required=True)
    ap.add_argument("--condition",choices=("closer","relaxed"),required=True)
    ap.add_argument("--max-cut-edges",type=int,required=True)
    ap.add_argument("--max-split-counties",type=int,required=True)
    ap.add_argument("--max-split-county-mcd",type=int,required=True)
    ap.add_argument("--warm-seed",type=int,default=101)
    ap.add_argument("--sample-seed",type=int,default=9901)
    ap.add_argument("--steps",type=int,default=201)
    ap.add_argument("--cut-cap",type=int,default=20)
    ap.add_argument("--out",type=Path,required=True)
    return pilot(ap.parse_args())


if __name__=="__main__":
    raise SystemExit(main())
