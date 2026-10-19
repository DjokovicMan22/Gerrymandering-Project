#!/usr/bin/env python3
"""Produce reproducible publication figures and paired model-conditional sensitivity.

Input is the *successful* Stage 3 aggregate artifact, never manually keyed
endpoints or simulated substitute values. 64 terminal maps are one per seed
per condition. Bootstrap pairs across shared RNG seed labels, not chain steps.
None of the figures estimates the distribution of legally valid Michigan maps.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GRAPH = "14355742f58291f4c26267982de07a21037c347f7598a68f032e0d68ea1d542c"
EXPECTED = {"closer": {"seats":7.21875,"eg":0.020097611163367158},
            "relaxed":{"seats":6.8125,"eg":-0.012680650212416425}}
AXES={"endpoint_efficiency_gap":"Efficiency gap (R wasted − D wasted) / votes",
      "endpoint_dem_seats":"Democratic seats under 2020 presidential overlay",
      "endpoint_fraction_precincts_different_from_reference":"Fraction of precincts assigned differently"}
LABELS={"closer":"Tighter proxy caps", "relaxed":"Relaxed proxy caps"}
LIMITATIONS=("FINITE HORIZON • 32 independent RNG endpoints per condition • "
             "experimental proximity graph • NOT a neutral legal-plan null")


def validate_inputs(endpoints_path:Path,summary_path:Path):
    frame=pd.read_csv(endpoints_path)
    summary=json.loads(summary_path.read_text(encoding="utf-8"))
    if len(frame)!=64:
        raise ValueError(f"Expected exactly 64 independently scored terminal maps, got {len(frame)}")
    if summary.get("not_a_stationary_legal_plan_ensemble") is not True or (
        summary.get("not_a_randomization_p_value") is not True):
        raise ValueError("Original aggregate does not carry required inferential disclaimers")
    needed={"condition","rng_seed","endpoint_efficiency_gap","endpoint_dem_seats",
            "endpoint_cut_edges","endpoint_fraction_precincts_different_from_reference",
            "model_graph_sha256","reference_efficiency_gap","reference_dem_seats",
            "endpoint_sha256","independently_rescored_endpoint",
            "legal_and_stationary_map_distribution_certified"}
    if missing:=needed-set(frame.columns):
        raise ValueError(f"Missing original derived columns: {sorted(missing)}")
    if set(frame["condition"])!={"closer","relaxed"}:
        raise ValueError("Unexpected geographic-cap cohort")
    if set(frame["model_graph_sha256"])!={GRAPH}:
        raise ValueError("Wrong or mixed graph SHA-256")
    if not frame["independently_rescored_endpoint"].eq(True).all():
        raise ValueError("Unverified terminal map score found")
    if not frame["legal_and_stationary_map_distribution_certified"].eq(False).all():
        raise ValueError("Erroneous legal-map/stationarity certification")
    if frame["endpoint_sha256"].nunique()!=64:
        raise ValueError("Duplicated terminal assignment digest across 64 maps")
    for condition in EXPECTED:
        x=frame[frame["condition"]==condition]
        if len(x)!=32 or set(x["rng_seed"])!=set(range(10001,10033)):
            raise ValueError(f"{condition}: missing independent RNG seed or duplicate")
        if abs(x["endpoint_dem_seats"].mean()-EXPECTED[condition]["seats"])>1e-9:
            raise ValueError("Audited seat mean does not match original report")
        if abs(x["endpoint_efficiency_gap"].mean()-EXPECTED[condition]["eg"])>1e-9:
            raise ValueError("Audited efficiency gap mean does not match original report")
        original=summary["conditions"][condition]
        if abs(float(original["metric_summaries"]["endpoint_efficiency_gap"]["mean"])-
               x["endpoint_efficiency_gap"].mean())>1e-12:
            raise ValueError("Original Stage 3 summary EG does not reconcile with its CSV")
        if abs(float(original["metric_summaries"]["endpoint_dem_seats"]["mean"])-
               x["endpoint_dem_seats"].mean())>1e-12:
            raise ValueError("Original Stage 3 summary seats do not reconcile with its CSV")
    if frame["reference_efficiency_gap"].nunique()!=1:
        raise ValueError("Reference changed across conditions")
    return frame,summary


def figure_footer(ax):
    ax.text(0,-.22,LIMITATIONS,transform=ax.transAxes,ha="left",va="top",
            fontsize=8.25,color="#475569")
    ax.figure.subplots_adjust(bottom=.29,top=.89,left=.15,right=.96)


def save(ax,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    ax.figure.savefig(path.with_suffix(".svg"),bbox_inches="tight",metadata={
        "Creator":"Stage 4 reproducible source-endpoint plotting script"})
    ax.figure.savefig(path.with_suffix(".png"),dpi=220,bbox_inches="tight")
    plt.close(ax.figure)
    for suffix in (".svg",".png"):
        if path.with_suffix(suffix).stat().st_size<4000:
            raise ValueError("Figure missing, suspiciously small or corrupt")


def plot_ecdf(frame:pd.DataFrame,out:Path):
    fig,ax=plt.subplots(figsize=(8.8,5.2))
    for condition in ("closer","relaxed"):
        vals=np.sort(frame.loc[frame["condition"]==condition,"endpoint_efficiency_gap"].to_numpy(float))
        y=np.arange(1,len(vals)+1)/len(vals)
        ax.step(vals,y,where="post",lw=2,label=f"{LABELS[condition]} (n={len(vals)})")
    ref=float(frame["reference_efficiency_gap"].iloc[0])
    ax.axvline(ref,color="#111827",ls=":",lw=1.8,
               label=f"Enacted reference ({ref:+.4f})")
    ax.set(xlabel=AXES["endpoint_efficiency_gap"],ylabel="Proportion of terminal maps at or below x",
           title="Figure 1. Finite-horizon endpoint efficiency-gap distributions")
    ax.set_ylim(0,1.025)
    ax.grid(alpha=.2)
    ax.legend(loc="upper left",frameon=False,fontsize=9)
    figure_footer(ax);save(ax,out)


def plot_paired(frame:pd.DataFrame,out:Path):
    a=frame[frame.condition=="closer"].set_index("rng_seed").sort_index()
    b=frame[frame.condition=="relaxed"].set_index("rng_seed").sort_index()
    x=a.endpoint_efficiency_gap.to_numpy(float)
    y=b.endpoint_efficiency_gap.to_numpy(float)
    if not np.array_equal(a.index,b.index):
        raise ValueError("Seeds not paired exactly")
    lim=min(np.r_[x,y])-.01
    hi=max(np.r_[x,y])+.01
    fig,ax=plt.subplots(figsize=(7.0,6.2))
    ax.scatter(x,y,s=47,alpha=.8,edgecolor="white",linewidth=.6)
    ax.plot([lim,hi],[lim,hi],color="#111827",ls="--",lw=1.2,label="Equal scores")
    ref=float(frame["reference_efficiency_gap"].iloc[0])
    ax.axhline(ref,color="#64748b",ls=":",lw=1,label="Reference EG")
    ax.axvline(ref,color="#64748b",ls=":",lw=1)
    ax.set_xlim(lim,hi);ax.set_ylim(lim,hi)
    ax.set_xlabel("Tighter proxy caps: efficiency gap")
    ax.set_ylabel("Relaxed proxy caps: efficiency gap")
    ax.set_title("Figure 2. Endpoint efficiency-gap sensitivity by seed")
    ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=9)
    figure_footer(ax);save(ax,out)


def plot_movement(frame:pd.DataFrame,out:Path):
    fig,ax=plt.subplots(figsize=(8.8,5.2))
    for condition in ("closer","relaxed"):
        x=frame[frame.condition==condition]
        ax.scatter(x.endpoint_fraction_precincts_different_from_reference.to_numpy(float)*100,
                   x.endpoint_efficiency_gap.to_numpy(float),
                   label=f"{LABELS[condition]} (n={len(x)})",s=48,alpha=.8,
                   edgecolor="white",linewidth=.5)
    ref=float(frame["reference_efficiency_gap"].iloc[0])
    ax.axhline(ref,color="#111827",ls=":",lw=1.6,
               label="Enacted reference efficiency gap")
    ax.set(xlabel="Precincts reassigned relative to reference (%)",
           ylabel=AXES["endpoint_efficiency_gap"],
           title="Figure 3. Spatial movement and conditional partisan score")
    ax.grid(alpha=.2);ax.legend(frameon=False,fontsize=9)
    figure_footer(ax);save(ax,out)


def paired_contrasts(frame:pd.DataFrame)->dict:
    a=frame[frame.condition=="closer"].set_index("rng_seed").sort_index()
    b=frame[frame.condition=="relaxed"].set_index("rng_seed").sort_index()
    if not np.array_equal(a.index,b.index) or len(a)!=32:
        raise ValueError("Improperly paired exploratory model seeds")
    rng=np.random.default_rng(20261018)
    indexes=rng.integers(0,32,size=(20000,32))
    metrics=["endpoint_dem_seats","endpoint_efficiency_gap",
             "endpoint_cut_edges","endpoint_fraction_precincts_different_from_reference"]
    results={}
    for field in metrics:
        differences=(a[field]-b[field]).to_numpy(float)
        bootstrap=differences[indexes].mean(axis=1)
        results[field]={
            "unit":"percentage points" if field=="endpoint_fraction_precincts_different_from_reference" else "raw units",
            "mean_closer_minus_relaxed":float(differences.mean()*100 if field.endswith("from_reference") else differences.mean()),
            "paired_bootstrap_95pct_CI_closer_minus_relaxed":[float(v) for v in
                (np.quantile(bootstrap,[.025,.975])*100 if field.endswith("from_reference") else
                 np.quantile(bootstrap,[.025,.975]))],
        }
    return {
        "n_seed_labels_per_condition":32,
        "rng_seed_range":"10001-10032",
        "reference_conditioning":"Both runs start at the enacted map",
        "estimand":"difference of expected 800-transition endpoint metrics, conditional on the exact KNN3 model and two exploratory cap regimes",
        "paired_seed_caution":"Pairing is by predeclared seed identifier, NOT geographic plan matching or identical proposal streams; differences are algorithm-conditional and not a causal attribution to any single cap.",
        "paired_mean_difference":results,
        "not_a_neutral_map_inference":True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--endpoints",type=Path,required=True)
    p.add_argument("--summary",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    args=p.parse_args()
    data,original=validate_inputs(args.endpoints,args.summary)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    plot_ecdf(data,args.out_dir/"figure1_terminal_EG_ECDF")
    plot_paired(data,args.out_dir/"figure2_paired_seed_EG")
    plot_movement(data,args.out_dir/"figure3_spatial_change_vs_EG")
    contrasts=paired_contrasts(data)
    result={
        "source_64_independent_endpoints_sha256":hashlib.sha256(args.endpoints.read_bytes()).hexdigest(),
        "original_stage3_aggregate_sha256":hashlib.sha256(args.summary.read_bytes()).hexdigest(),
        "model_graph_sha256":GRAPH,
        "plot_files":sorted(p.name for p in args.out_dir.glob("figure*")),
        "comparison":contrasts,
        "inference_scope":"Exploratory fixed-horizon 800-step perturbation experiment, NOT a legal neutral-plan probability",
    }
    (args.out_dir/"stage4_figure_data_manifest.json").write_text(json.dumps(result,indent=2),
                                                               encoding="utf-8")
    print("STAGE4_FIGURES_VERIFIED",json.dumps(contrasts,indent=2),flush=True)


if __name__=="__main__":
    main()
