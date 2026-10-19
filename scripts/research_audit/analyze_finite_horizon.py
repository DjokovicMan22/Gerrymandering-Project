#!/usr/bin/env python3
"""Cohort-complete independent finite-horizon randomization summaries.

Inferences are about the exact T-recorded-state seeded ReCom perturbation
procedure, conditional on a label-blind precinct-proximity topology and the
given exploratory hard caps. They are NOT stationary legal-plan probabilities.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

CAPS={
    "closer":(760,18,20),
    "relaxed":(850,24,49),
}
EXPECTED_SEEDS=set(range(10001,10033))
METRICS=[
    "endpoint_dem_seats","endpoint_efficiency_gap","endpoint_cut_edges",
    "endpoint_split_counties","endpoint_split_county_mcd",
    "endpoint_fraction_precincts_different_from_reference",
]


def wilson(successes:int,n:int,z:float=1.959963984540054)->list[float]:
    if n<1 or not (0<=successes<=n):
        raise ValueError("Bad Wilson interval counts")
    p=successes/n
    den=1+z*z/n
    center=(p+z*z/(2*n))/den
    margin=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return [max(0,center-margin),min(1,center+margin)]


def require_complete(files:list[Path],condition:str,graph_sha:str|None=None)->pd.DataFrame:
    if len(files)!=4 or len({p.name for p in files})!=4:
        raise ValueError("Require four separately produced 8-seed CSVs per condition")
    parts=[]
    for path in files:
        df=pd.read_csv(path, dtype={"endpoint_sha256":"string", "model_graph_sha256":"string", "reference_assignment_sha256":"string"})
        if len(df)!=8:
            raise ValueError(f"Wrong number of endpoint replicates in {path}")
        parts.append(df)
    df=pd.concat(parts,ignore_index=True)
    required=set(METRICS)|{
        "condition","rng_seed","steps_including_enacted_reference",
        "model_graph_sha256","reference_assignment_sha256",
        "endpoint_sha256","reference_efficiency_gap","reference_dem_seats",
        "reference_cut_edges","independently_rescored_endpoint",
        "legal_and_stationary_map_distribution_certified",
        "endpoint_max_population_deviation","geographic_attempts",
        "extra_proposal_calls_beyond_recorded_transitions",
        "geographic_rejections","endpoint_split_counties",
        "endpoint_split_county_mcd"
    }
    missing=required-set(df.columns)
    if missing:
        raise ValueError(f"Missing endpoint validation and identity fields: {missing}")
    if set(df["condition"])!={condition}:
        raise ValueError("Cohort mixes different geography conditions")
    if set(df["rng_seed"].astype(int))!=EXPECTED_SEEDS or df["rng_seed"].duplicated().any():
        raise ValueError("Missing/duplicated fixed independent RNG seed")
    if set(df["steps_including_enacted_reference"].astype(int))!={801}:
        raise ValueError("Mismatched algorithmic time horizon")
    if not bool(df["independently_rescored_endpoint"].eq(True).all()):
        raise ValueError("Unverified sampled endpoint found")
    if not bool(df["legal_and_stationary_map_distribution_certified"].eq(False).all()):
        raise ValueError("Unfounded stationary/legal certification flag")
    for key in ("model_graph_sha256","reference_assignment_sha256"):
        if df[key].nunique()!=1:
            raise ValueError(f"Inconsistent common graph or enacted reference: {key}")
        if not isinstance(df[key].iloc[0],str) or len(df[key].iloc[0])!=64:
            raise ValueError(f"Invalid SHA: {key}")
    if graph_sha is not None and df["model_graph_sha256"].iloc[0]!=graph_sha:
        raise ValueError("Cross-condition graph SHA differs")
    for key in ("reference_efficiency_gap","reference_dem_seats","reference_cut_edges"):
        if df[key].nunique()!=1:
            raise ValueError(f"Reference score drift across independent runs: {key}")
    for key in METRICS+[
        "endpoint_max_population_deviation","geographic_attempts",
        "geographic_rejections","extra_proposal_calls_beyond_recorded_transitions",
    ]:
        if not np.isfinite(pd.to_numeric(df[key],errors="coerce")).all():
            raise ValueError(f"Invalid nonfinite score/counter in {key}")
    if (df["endpoint_max_population_deviation"]>.005+1e-12).any():
        raise ValueError("Invalid population in one or more endpoints")
    caps=CAPS[condition]
    for key,cap in zip(("endpoint_cut_edges","endpoint_split_counties",
                        "endpoint_split_county_mcd"),caps):
        if (df[key]>cap).any():
            raise ValueError(f"Invalid sampled {key} under fixed geography cap")
    if (df["geographic_attempts"]<800).any() or (
            df["extra_proposal_calls_beyond_recorded_transitions"]<0).any():
        raise ValueError("Unexpected hidden proposal accounting")
    if ((df["geographic_rejections"]>df["geographic_attempts"])|
        (df["geographic_rejections"]<0)).any():
        raise ValueError("Geographic proposal rejection count impossible")
    if ((df["endpoint_fraction_precincts_different_from_reference"]<0)|
        (df["endpoint_fraction_precincts_different_from_reference"]>1)).any():
        raise ValueError("Invalid exact node-disagreement fraction")
    if not bool(df["endpoint_sha256"].str.len().eq(64).all()):
        raise ValueError("Invalid endpoint assignment digest")
    return df.sort_values("rng_seed").reset_index(drop=True)


def summarize(df:pd.DataFrame, condition:str)->dict:
    if len(df)!=32:
        raise ValueError("Need 32 end-point replicates for Monte Carlo CIs")
    rng=np.random.default_rng(161803)
    metrics={}
    for col in METRICS:
        values=df[col].to_numpy(float)
        indices=rng.integers(0,len(values),size=(10000,len(values)))
        sampled=values[indices].mean(axis=1)
        metrics[col]={
            "mean":float(values.mean()),
            "median":float(np.median(values)),
            "sd_across_seeds":float(values.std(ddof=1)),
            "bootstrap_95pct_ci_for_finite_horizon_mean":[float(v) for v in
                np.quantile(sampled,[.025,.975])],
        }
    ref=float(df["reference_efficiency_gap"].iloc[0])
    n=len(df)
    exceed=int((df["endpoint_efficiency_gap"]>=ref).sum())
    return {
        "condition":condition,"independent_seeded_endpoint_count":n,
        "unique_endpoint_sha256_count":int(df["endpoint_sha256"].nunique()),
        "reference_efficiency_gap":ref,
        "reference_dem_seats":int(df["reference_dem_seats"].iloc[0]),
        "reference_cut_edges":int(df["reference_cut_edges"].iloc[0]),
        "fraction_endpoint_EG_at_least_reference":exceed/n,
        "fraction_endpoint_EG_at_least_reference_wilson_95pct_interval":
            wilson(exceed,n),
        "geographic_rejection_fraction_per_seed_mean":
            float((df["geographic_rejections"]/df["geographic_attempts"]).mean()),
        "average_hidden_proposal_retries":
            float(df["extra_proposal_calls_beyond_recorded_transitions"].mean()),
        "model_graph_sha256":df["model_graph_sha256"].iloc[0],
        "metric_summaries":metrics,
        "scientific_disposition":(
            "FINISHED ALGORITHM-DEFINED FINITE-HORIZON ROBUSTNESS ANALYSIS ONLY. "
            "Not a converged stationary ensemble, legally valid map probability, "
            "or evidence of intention/illegality. Bootstrap intervals describe "
            "independent seeded endpoints conditional on this model."
        ),
    }


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--closer",type=Path,nargs="+",required=True)
    ap.add_argument("--relaxed",type=Path,nargs="+",required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    closer=require_complete(args.closer,"closer")
    relaxed=require_complete(args.relaxed,"relaxed",closer["model_graph_sha256"].iloc[0])
    if any(closer[k].iloc[0]!=relaxed[k].iloc[0] for k in
           ("reference_assignment_sha256","reference_efficiency_gap",
            "reference_dem_seats","reference_cut_edges")):
        raise ValueError("Not comparable: enacted reference differs between geography conditions")
    result={
        "experiment":"fixed-801-state independent-seed Michigan perturbation sensitivity",
        "sampling_distribution":(
            "law of one final state from 801 recorded GerryChain ReCom states, "
            "all chains starting at the same enacted reference on KNN3 source "
            "geometry, subject to the documented condition-specific constraints"
        ),
        "conditions":{
            "closer":summarize(closer,"closer"),
            "relaxed":summarize(relaxed,"relaxed")
        },
        "not_a_stationary_legal_plan_ensemble":True,
        "not_a_randomization_p_value":True,
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    pd.concat([closer,relaxed],ignore_index=True).to_csv(
        args.out.parent/"independent_endpoints_64.csv",index=False)
    args.out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
