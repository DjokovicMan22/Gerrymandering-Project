#!/usr/bin/env python3
"""Build Week 5 outlier tables and signature statistical figures."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import PercentFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from redistricting.analysis import (
    load_chain_tables,
    rank_district_shares,
    select_representative_plans,
    summarize_enacted_outliers,
)
from redistricting.analysis.outliers import enacted_row

DISPLAY_NAMES = {
    "dem_seats": "Democratic seats",
    "efficiency_gap": "Efficiency gap",
    "mean_median": "Mean–median difference",
    "cut_edges": "Cut edges",
    "max_population_deviation": "Maximum population deviation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plan_csv",
        nargs="*",
        type=Path,
        help="Week 4 *_plan_metrics.csv files. District files are inferred.",
    )
    parser.add_argument(
        "--glob",
        dest="glob_pattern",
        help="Project-relative glob used instead of positional CSV paths.",
    )
    parser.add_argument("--burn-in", type=int, default=700)
    parser.add_argument("--name", default="mi_2020")
    parser.add_argument("--state-name", default="Michigan")
    parser.add_argument("--election-label", default="2020 presidential election")
    return parser.parse_args()


def resolve_paths(args: argparse.Namespace) -> list[Path]:
    paths = list(args.plan_csv)
    if args.glob_pattern:
        paths.extend(sorted(PROJECT_ROOT.glob(args.glob_pattern)))
    deduplicated = []
    seen = set()
    for path in paths:
        absolute = path if path.is_absolute() else PROJECT_ROOT / path
        absolute = absolute.resolve()
        if absolute not in seen:
            seen.add(absolute)
            deduplicated.append(absolute)
    if not deduplicated:
        raise SystemExit("Provide plan CSVs or --glob PATTERN.")
    return deduplicated


def metric_row(summary: pd.DataFrame, metric: str) -> pd.Series:
    matches = summary.loc[summary["metric"] == metric]
    if matches.empty:
        raise ValueError(f"No outlier summary for {metric}")
    return matches.iloc[0]


def add_histogram(
    ax,
    values: pd.Series,
    observed: float,
    title: str,
    xlabel: str,
    percentile: float,
    discrete: bool = False,
) -> None:
    values = values.dropna().astype(float)
    if discrete:
        minimum = int(np.floor(values.min()))
        maximum = int(np.ceil(values.max()))
        bins = np.arange(minimum - 0.5, maximum + 1.5, 1)
        ax.hist(values, bins=bins, density=False, edgecolor="black", alpha=0.8)
        ax.set_xticks(range(minimum, maximum + 1))
        ax.set_ylabel("Sampled plans")
    else:
        ax.hist(values, bins=40, density=True, edgecolor="white", alpha=0.85)
        ax.set_ylabel("Density")
    ax.axvline(observed, linewidth=2.4, label=f"Enacted = {observed:.4g}")
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.grid(alpha=0.22)
    ax.legend(title=f"Midrank percentile: {percentile:.1f}")


def make_signature_panel(
    pooled: pd.DataFrame,
    enacted: pd.Series,
    summary: pd.DataFrame,
    output_path: Path,
    title: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.5))
    for ax, metric, discrete in (
        (axes[0, 0], "dem_seats", True),
        (axes[0, 1], "efficiency_gap", False),
        (axes[1, 0], "mean_median", False),
        (axes[1, 1], "cut_edges", False),
    ):
        row = metric_row(summary, metric)
        add_histogram(
            ax,
            pooled[metric],
            float(enacted[metric]),
            DISPLAY_NAMES[metric],
            DISPLAY_NAMES[metric],
            float(row["midrank_percentile"]),
            discrete=discrete,
        )
    fig.suptitle(title, fontsize=16, fontweight="bold")
    fig.text(
        0.5,
        0.01,
        "Percentiles are empirical positions within the sampled post-burn-in ensemble, not classical p-values.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.96))
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_single_headline_histograms(
    pooled: pd.DataFrame,
    enacted: pd.Series,
    summary: pd.DataFrame,
    figure_dir: Path,
    name: str,
    state_name: str,
    election_label: str,
) -> None:
    for metric, discrete in (("dem_seats", True), ("efficiency_gap", False)):
        row = metric_row(summary, metric)
        fig, ax = plt.subplots(figsize=(10, 6))
        add_histogram(
            ax,
            pooled[metric],
            float(enacted[metric]),
            f"{state_name}: enacted plan vs. sampled alternatives",
            DISPLAY_NAMES[metric],
            float(row["midrank_percentile"]),
            discrete=discrete,
        )
        ax.text(
            0.99,
            0.97,
            f"Election: {election_label}\nPost-burn-in plans: {len(pooled):,}",
            transform=ax.transAxes,
            ha="right",
            va="top",
            bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.9},
        )
        fig.tight_layout()
        fig.savefig(
            figure_dir / f"{name}_{metric}_outlier.png",
            dpi=240,
            bbox_inches="tight",
        )
        plt.close(fig)


def make_sorted_district_plot(
    summary: pd.DataFrame,
    output_path: Path,
    state_name: str,
    election_label: str,
) -> None:
    x = summary["rank"].to_numpy(dtype=int)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.fill_between(x, summary["q05"], summary["q95"], alpha=0.18, label="Ensemble 5–95%")
    ax.fill_between(x, summary["q25"], summary["q75"], alpha=0.32, label="Ensemble 25–75%")
    ax.plot(x, summary["median"], linewidth=2, label="Ensemble median")
    ax.scatter(
        x,
        summary["enacted_dem_share"],
        s=42,
        zorder=4,
        label="Enacted districts",
    )
    ax.axhline(0.5, linestyle="--", linewidth=1.2, label="50% vote threshold")
    ax.set_title(
        f"{state_name} sorted-district comparison ({election_label})",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_xlabel("District rank (1 = most Democratic)")
    ax.set_ylabel("Democratic two-party vote share")
    ax.set_xticks(x)
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(alpha=0.22)
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def report_text(
    name: str,
    state_name: str,
    election_label: str,
    burn_in: int,
    chain_count: int,
    pooled: pd.DataFrame,
    outliers: pd.DataFrame,
    sorted_summary: pd.DataFrame,
) -> str:
    seats = metric_row(outliers, "dem_seats")
    gap = metric_row(outliers, "efficiency_gap")
    mm = metric_row(outliers, "mean_median")
    cut = metric_row(outliers, "cut_edges")

    largest = sorted_summary.reindex(
        sorted_summary["enacted_minus_ensemble_median"].abs().sort_values(ascending=False).index
    ).head(4)
    rank_lines = "\n".join(
        f"- Rank {int(row['rank'])}: enacted minus ensemble median = "
        f"{100 * row['enacted_minus_ensemble_median']:+.2f} percentage points"
        for _, row in largest.iterrows()
    )

    return f"""# Week 5 outlier analysis — {state_name}

## Analysis design

- Election data: {election_label}
- Independent chains: {chain_count}
- Burn-in removed from each chain: {burn_in:,} steps
- Post-burn-in sampled plans pooled: {len(pooled):,}
- The enacted plan is step 0 and is not included in the ensemble distribution.

## Enacted plan's empirical position

| Metric | Enacted | Ensemble mean | Ensemble median | Midrank percentile |
|---|---:|---:|---:|---:|
| Democratic seats | {seats['enacted_value']:.0f} | {seats['ensemble_mean']:.3f} | {seats['ensemble_median']:.3f} | {seats['midrank_percentile']:.2f}% |
| Efficiency gap | {gap['enacted_value']:.5f} | {gap['ensemble_mean']:.5f} | {gap['ensemble_median']:.5f} | {gap['midrank_percentile']:.2f}% |
| Mean–median | {mm['enacted_value']:.5f} | {mm['ensemble_mean']:.5f} | {mm['ensemble_median']:.5f} | {mm['midrank_percentile']:.2f}% |
| Cut edges | {cut['enacted_value']:.0f} | {cut['ensemble_mean']:.2f} | {cut['ensemble_median']:.2f} | {cut['midrank_percentile']:.2f}% |

## Sorted-district structure

Largest enacted-versus-ensemble median differences:

{rank_lines}

## Inference statement

The enacted plan's percentile describes where it falls among maps sampled by this exact ReCom procedure after the stated burn-in, population tolerance, contiguity convention, and other modeling choices. An extreme percentile supports the claim that the enacted plan is unusual relative to this sampled comparison set. It is not automatically a classical hypothesis-test p-value, does not prove that the chain sampled uniformly from all valid maps, and does not by itself establish partisan intent, legal liability, or illegality.

## Interpretation guardrails

1. Adjacent MCMC samples are correlated, so the number of rows exceeds the effective number of independent observations.
2. The ensemble depends on the proposal, population tolerance, artificial water/island bridges, and omitted constraints such as county splits and communities of interest.
3. Presidential vote data are a counterfactual election layer, not congressional candidate behavior.
4. The same conclusions must be checked using another election and altered constraints before being described as robust.

Generated by `scripts/run_week5_outlier_analysis.py` with output name `{name}`.
"""


def main() -> None:
    args = parse_args()
    paths = resolve_paths(args)
    plan_frames, district_frames, pooled_plans, pooled_districts = load_chain_tables(
        paths, burn_in=args.burn_in
    )

    # Keep committed tables portable: store project-relative paths rather than
    # machine-specific absolute paths such as /Users/name/Goodproject.
    def portable_path(value: str) -> str:
        path = Path(value).resolve()
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)

    for frame in plan_frames.values():
        frame["plan_csv"] = frame["plan_csv"].map(portable_path)
    for frame in district_frames.values():
        frame["district_csv"] = frame["district_csv"].map(portable_path)
    pooled_plans["plan_csv"] = pooled_plans["plan_csv"].map(portable_path)
    pooled_districts["district_csv"] = pooled_districts["district_csv"].map(portable_path)

    enacted = enacted_row(plan_frames)
    first_chain = str(enacted["chain"])
    enacted_districts = district_frames[first_chain].loc[
        district_frames[first_chain]["step"] == 0
    ].copy()

    outliers = summarize_enacted_outliers(pooled_plans, enacted)
    sorted_summary, enacted_ranked = rank_district_shares(
        pooled_districts, enacted_districts
    )
    selected = select_representative_plans(pooled_plans, enacted)

    table_dir = PROJECT_ROOT / "outputs" / "tables" / "week5"
    figure_dir = PROJECT_ROOT / "outputs" / "figures" / "week5"
    report_dir = PROJECT_ROOT / "outputs" / "reports" / "week5"
    for directory in (table_dir, figure_dir, report_dir):
        directory.mkdir(parents=True, exist_ok=True)

    outlier_path = table_dir / f"{args.name}_outlier_percentiles.csv"
    sorted_path = table_dir / f"{args.name}_sorted_district_summary.csv"
    enacted_path = table_dir / f"{args.name}_enacted_ranked_districts.csv"
    selected_path = table_dir / f"{args.name}_selected_plans.csv"
    targets_path = table_dir / f"{args.name}_recovery_targets.json"

    outliers.to_csv(outlier_path, index=False)
    sorted_summary.to_csv(sorted_path, index=False)
    enacted_ranked.to_csv(enacted_path, index=False)
    selected.to_csv(selected_path, index=False)
    targets_path.write_text(
        json.dumps(selected.to_dict(orient="records"), indent=2, allow_nan=True),
        encoding="utf-8",
    )

    make_signature_panel(
        pooled_plans,
        enacted,
        outliers,
        figure_dir / f"{args.name}_signature_outlier_panel.png",
        f"{args.state_name} enacted plan in the ReCom ensemble ({args.election_label})",
    )
    make_single_headline_histograms(
        pooled_plans,
        enacted,
        outliers,
        figure_dir,
        args.name,
        args.state_name,
        args.election_label,
    )
    make_sorted_district_plot(
        sorted_summary,
        figure_dir / f"{args.name}_sorted_districts.png",
        args.state_name,
        args.election_label,
    )

    report_path = report_dir / f"{args.name}_outlier_summary.md"
    report_path.write_text(
        report_text(
            args.name,
            args.state_name,
            args.election_label,
            args.burn_in,
            len(plan_frames),
            pooled_plans,
            outliers,
            sorted_summary,
        ),
        encoding="utf-8",
    )

    print(f"Loaded {len(plan_frames)} chains and {len(pooled_plans):,} post-burn-in plans.")
    print("\nEnacted-plan empirical positions:")
    print(
        outliers[
            [
                "metric",
                "enacted_value",
                "ensemble_mean",
                "ensemble_median",
                "midrank_percentile",
                "two_sided_extremeness_percent",
            ]
        ].to_string(index=False)
    )
    print("\nSelected plans for the comparison-map recovery step:")
    print(selected.to_string(index=False))
    print("\nSaved:")
    for path in (
        outlier_path,
        sorted_path,
        enacted_path,
        selected_path,
        targets_path,
        report_path,
        figure_dir / f"{args.name}_signature_outlier_panel.png",
        figure_dir / f"{args.name}_dem_seats_outlier.png",
        figure_dir / f"{args.name}_efficiency_gap_outlier.png",
        figure_dir / f"{args.name}_sorted_districts.png",
    ):
        print(f"  {path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
