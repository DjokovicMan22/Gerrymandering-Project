#!/usr/bin/env python3
"""Print-ready, colorblind/greyscale-safe research graphics from actual 64 endpoints.

Reuses the previously verified original-source validation and paired-seed
statistics verbatim. Only VISUAL PRESENTATION differs from the earlier figures.
No invented data, model inference or legal-status claims.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter
import numpy as np
import pandas as pd

from stage4_make_figures import validate_inputs, paired_contrasts

INK = "#161e2a"
SLATE = "#546675"
FAINT = "#dfe4e8"
TIGHT = "#163957"
RELAXED = "#838d97"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9.2,
    "axes.labelsize": 9.8,
    "xtick.labelsize": 8.6,
    "ytick.labelsize": 8.6,
    "legend.fontsize": 8.6,
    "axes.edgecolor": INK,
    "axes.linewidth": .70,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.labelcolor": INK,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.transparent": False,
})

def frame(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(direction="out", length=3, width=.65, pad=4)
    ax.grid(False)

def finish(fig, ax, base: Path):
    frame(ax)
    fig.subplots_adjust(left=.115, right=.985, top=.965, bottom=.165)
    base.parent.mkdir(parents=True,exist_ok=True)
    for suffix in (".pdf", ".svg", ".png"):
        path=base.with_suffix(suffix)
        opts={"bbox_inches":"tight", "pad_inches":.10}
        if suffix==".png":opts["dpi"]=320
        fig.savefig(path, **opts)
        if path.stat().st_size<3700:
            raise ValueError("Empty or unexpectedly small figure: "+str(path))
    plt.close(fig)

def ecdf(frame_data:pd.DataFrame, out:Path):
    fig,ax=plt.subplots(figsize=(6.65,3.55))
    for label, col, ls, name in (
        ("closer", TIGHT, "-", "Tighter constraints"),
        ("relaxed", RELAXED, "--", "Relaxed constraints"),
    ):
        values=np.sort(frame_data.loc[frame_data.condition==label,
                                      "endpoint_efficiency_gap"].to_numpy(float))
        ax.step(values,np.arange(1,len(values)+1)/len(values),where="post",
                color=col,lw=1.6,ls=ls,label=f"{name} ($n=32$)")
    reference=float(frame_data.reference_efficiency_gap.iloc[0])
    ax.axvline(reference,color=INK,lw=.9,ls=":",alpha=.8)
    ax.annotate("Enacted reference",xy=(reference,.12),xytext=(6,0),
                textcoords="offset points",va="center",rotation=90,
                color=SLATE,fontsize=8)
    ax.set_xlabel("Terminal efficiency gap")
    ax.set_ylabel("Empirical cumulative proportion")
    ax.yaxis.set_major_locator(MaxNLocator(5))
    ax.set_ylim(0,1.02)
    ax.legend(loc="upper left",frameon=False,handlelength=2.8,
              borderaxespad=.25,labelspacing=.28)
    finish(fig,ax,out)

def pairplot(frame_data:pd.DataFrame, out:Path):
    one=frame_data[frame_data.condition=="closer"].set_index("rng_seed").sort_index()
    two=frame_data[frame_data.condition=="relaxed"].set_index("rng_seed").sort_index()
    if not np.array_equal(one.index,two.index): raise ValueError("Seed pairing changed")
    x=one.endpoint_efficiency_gap.to_numpy(float)
    y=two.endpoint_efficiency_gap.to_numpy(float)
    low=min(x.min(),y.min())-.008
    high=max(x.max(),y.max())+.008
    fig,ax=plt.subplots(figsize=(5.35,4.65))
    ax.plot([low,high],[low,high],ls="--",lw=.8,color=SLATE,zorder=1,label="Equal score")
    ax.scatter(x,y,facecolor="white",edgecolor=TIGHT,
               s=25,alpha=.96,linewidth=.85,zorder=3,label="Paired seed endpoint")
    ax.set_xlim(low,high);ax.set_ylim(low,high)
    ax.set_aspect("equal",adjustable="box")
    ax.set_xlabel("Tighter constraints: efficiency gap")
    ax.set_ylabel("Relaxed constraints: efficiency gap")
    ax.legend(loc="upper left",frameon=False,handlelength=2.2,
              borderaxespad=.35,labelspacing=.3)
    finish(fig,ax,out)

def movement(frame_data:pd.DataFrame, out:Path):
    fig,ax=plt.subplots(figsize=(6.65,3.65))
    for label, marker, edge, face, name in (
        ("closer","o",TIGHT,TIGHT,"Tighter constraints"),
        ("relaxed","s",RELAXED,"white","Relaxed constraints"),
    ):
        part=frame_data[frame_data.condition==label]
        ax.scatter(
            100*part.endpoint_fraction_precincts_different_from_reference.to_numpy(float),
            part.endpoint_efficiency_gap.to_numpy(float),
            marker=marker,s=23,lw=.85,edgecolor=edge,facecolor=face,
            alpha=.86,label=f"{name} ($n=32$)",zorder=3)
    ax.axhline(float(frame_data.reference_efficiency_gap.iloc[0]),
               color=SLATE,ls=":",lw=.8,zorder=1)
    ax.set_xlabel("Precinct assignments differing from reference (%)")
    ax.set_ylabel("Terminal efficiency gap")
    ax.legend(frameon=False,loc="lower left",handletextpad=.5,
              borderaxespad=.3,labelspacing=.32)
    finish(fig,ax,out)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoints",type=Path,required=True)
    parser.add_argument("--summary",type=Path,required=True)
    parser.add_argument("--out-dir",type=Path,required=True)
    args=parser.parse_args()
    data, _=validate_inputs(args.endpoints,args.summary)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    ecdf(data,args.out_dir/"figure1_terminal_EG_ECDF")
    pairplot(data,args.out_dir/"figure2_paired_seed_EG")
    movement(data,args.out_dir/"figure3_spatial_change_vs_EG")
    stats=paired_contrasts(data)
    manifest={
        "display_version":"journal typography 2.0; print/greyscale compatible; no panel titles or intrusive footers",
        "original_64_endpoints_sha256":hashlib.sha256(args.endpoints.read_bytes()).hexdigest(),
        "original_aggregate_sha256":hashlib.sha256(args.summary.read_bytes()).hexdigest(),
        "input_verified_by":"stage4_make_figures.validate_inputs",
        "original_model_graph_sha256":str(data.model_graph_sha256.iloc[0]),
        "figures":[p.name for p in sorted(args.out_dir.glob("figure*"))],
        "statistical_summary":stats,
        "inference_scope":"fixed-horizon experimental model comparison only; NOT a legally neutral map sampling distribution",
    }
    (args.out_dir/"stage4_journal_figure_manifest.json").write_text(
        json.dumps(manifest,indent=2),encoding="utf-8")
    print("STAGE4_JOURNAL_FIGURES_PASS",json.dumps(stats,indent=2),flush=True)
if __name__=="__main__":
    main()
