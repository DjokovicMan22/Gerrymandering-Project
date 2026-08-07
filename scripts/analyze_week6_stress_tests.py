#!/usr/bin/env python3
"""Analyze Week 6 constraint sensitivity and the geographic seat baseline."""
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

from redistricting.analysis.sensitivity import (
    common_enacted_row,
    geography_baseline_summary,
    percentile_range_table,
    pool_after_burn_in,
    read_plan_frames,
    seat_frequency_table,
    summarize_constraint_ensemble,
    validate_enacted_across_ensembles,
    validate_population_tolerance,
)
from redistricting.diagnostics import summarize_multiple_chains

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
        "--config",
        type=Path,
        default=Path("configs/week6_mi_2020.json"),
    )
    parser.add_argument("--name", default="mi_2020")
    return parser.parse_args()


def load_config(path: Path) -> dict:
    full = path if path.is_absolute() else PROJECT_ROOT / path
    if not full.exists():
        raise FileNotFoundError(full)
    config = json.loads(full.read_text(encoding="utf-8"))
    groups = config.get("ensembles")
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError("Config must define at least two ensembles")
    if sum(bool(group.get("baseline")) for group in groups) != 1:
        raise ValueError("Exactly one ensemble must have baseline=true")
    return config


def resolve_glob(pattern: str) -> list[Path]:
    paths = sorted(PROJECT_ROOT.glob(pattern))
    if not paths:
        raise FileNotFoundError(f"No files match project-relative glob: {pattern}")
    return paths


def make_constraint_distribution_figure(
    pooled_by_label: dict[str, pd.DataFrame],
    enacted: pd.Series,
    output_path: Path,
    title: str,
) -> None:
    metrics = ("dem_seats", "efficiency_gap", "mean_median", "cut_edges")
    labels = list(pooled_by_label)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9.5))
    for axis, metric in zip(axes.flat, metrics, strict=True):
        values = [pooled_by_label[label][metric].dropna().to_numpy() for label in labels]
        axis.boxplot(values, tick_labels=labels, showfliers=False)
        axis.axhline(float(enacted[metric]), linewidth=2, linestyle="--", label="Enacted")
        axis.set_title(DISPLAY_NAMES[metric], fontweight="bold")
        axis.grid(axis="y", alpha=0.25)
        axis.tick_params(axis="x", rotation=12)
        axis.legend()
    fig.suptitle(title, fontsize=16, fontweight="bold")
    fig.text(
        0.5,
        0.01,
        "Boxes compare post-burn-in sampled distributions under different population tolerances.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.96))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_percentile_sensitivity_figure(summary: pd.DataFrame, output_path: Path) -> None:
    selected = summary.loc[
        summary["metric"].isin(("dem_seats", "efficiency_gap", "mean_median", "cut_edges"))
    ].copy()
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    for metric, group in selected.groupby("metric"):
        group = group.sort_values("epsilon")
        ax.plot(
            100 * group["epsilon"],
            group["midrank_percentile"],
            marker="o",
            linewidth=1.8,
            label=DISPLAY_NAMES.get(metric, metric),
        )
    ax.axhline(50, linestyle="--", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Allowed population deviation (%)")
    ax.set_ylabel("Enacted-plan midrank percentile")
    ax.set_title("Constraint sensitivity of enacted-plan percentiles", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def make_geography_figure(
    pooled: pd.DataFrame,
    enacted: pd.Series,
    geography: pd.DataFrame,
    output_path: Path,
    title: str,
) -> None:
    row = geography.iloc[0]
    values = pooled["dem_seats"].to_numpy(dtype=float)
    minimum = int(np.floor(values.min()))
    maximum = int(np.ceil(values.max()))
    bins = np.arange(minimum - 0.5, maximum + 1.5, 1)

    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    ax.hist(values, bins=bins, edgecolor="black")
    ax.axvline(
        float(row["proportional_dem_seats"]),
        linewidth=2,
        linestyle=":",
        label=f"Proportional benchmark = {row['proportional_dem_seats']:.2f}",
    )
    ax.axvline(
        float(row["ensemble_mean_dem_seats"]),
        linewidth=2,
        label=f"Neutral-ensemble mean = {row['ensemble_mean_dem_seats']:.2f}",
    )
    ax.axvline(
        float(enacted["dem_seats"]),
        linewidth=2.4,
        linestyle="--",
        label=f"Enacted = {int(enacted['dem_seats'])}",
    )
    ax.set_xticks(range(minimum, maximum + 1))
    ax.set_xlabel("Democratic seats")
    ax.set_ylabel("Sampled plans")
    ax.set_title(title, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def stability_word(percentile_range: float) -> str:
    if percentile_range <= 10:
        return "small"
    if percentile_range <= 25:
        return "moderate"
    return "substantial"


def build_report(
    config: dict,
    name: str,
    summary: pd.DataFrame,
    ranges: pd.DataFrame,
    diagnostics: pd.DataFrame,
    geography: pd.DataFrame,
    baseline_label: str,
    pooled_sizes: dict[str, int],
) -> str:
    state_name = config.get("state_name", "State")
    election_label = config.get("election_label", "election layer")
    group_lines = "\n".join(
        f"- {label}: {count:,} post-burn-in sampled plans"
        for label, count in pooled_sizes.items()
    )

    percentile_rows = summary.loc[
        summary["metric"].isin(("dem_seats", "efficiency_gap", "mean_median", "cut_edges"))
    ]
    percentile_table = percentile_rows[
        [
            "constraint_label",
            "metric",
            "enacted_value",
            "ensemble_mean",
            "ensemble_median",
            "midrank_percentile",
        ]
    ].to_markdown(index=False, floatfmt=".4f")

    range_lines = []
    for _, row in ranges.iterrows():
        metric = row["metric"]
        if metric not in DISPLAY_NAMES:
            continue
        width = float(row["percentile_range"])
        range_lines.append(
            f"- {DISPLAY_NAMES[metric]}: {width:.2f}-percentage-point range "
            f"({stability_word(width)} sensitivity by the declared descriptive rule)."
        )
    range_text = "\n".join(range_lines)

    diagnostic_table = diagnostics[
        [
            "constraint_label",
            "statistic",
            "chain_count",
            "burn_in",
            "pooled_mean",
            "pooled_sd",
            "split_rhat",
        ]
    ].to_markdown(index=False, floatfmt=".4f")

    geo = geography.iloc[0]
    return f"""# Week 6 stress tests — {state_name}

## Design

Election layer: {election_label}

Population-tolerance ensembles:

{group_lines}

The Week 6 investigations are:

1. **Constraint sensitivity:** whether the enacted plan's empirical position moves when the allowed district-population deviation changes.
2. **Geographic baseline:** whether the neutral ensemble itself departs from proportional seat allocation, which estimates how geography and the modeling constraints can produce disproportionality without treating proportionality as the sampling target.

## Investigation 1: population-tolerance sensitivity

{percentile_table}

Observed percentile movement across the tested tolerances:

{range_text}

These ranges are descriptive. A stable percentile across the tested values strengthens robustness only with respect to this particular constraint perturbation. It does not show robustness to every omitted rule.

## Multi-chain diagnostics

{diagnostic_table}

Split-Rhat is used as a warning diagnostic. Values near 1 support agreement among the tracked scalar distributions but do not prove that ReCom fully mixed over the space of valid maps.

## Investigation 2: geographic baseline

Baseline ensemble: **{baseline_label}**

- Statewide Democratic two-party share: {100 * geo['statewide_dem_share']:.3f}%
- Proportional Democratic-seat benchmark: {geo['proportional_dem_seats']:.3f} of {int(geo['district_count'])}
- Neutral-ensemble mean Democratic seats: {geo['ensemble_mean_dem_seats']:.3f}
- Neutral-ensemble median Democratic seats: {geo['ensemble_median_dem_seats']:.3f}
- Neutral-ensemble 5–95% range: {geo['ensemble_q05_dem_seats']:.3f} to {geo['ensemble_q95_dem_seats']:.3f}
- Geography/constraint gap, ensemble mean minus proportional benchmark: {geo['geographic_gap_mean_minus_proportional']:+.3f} seats
- Enacted minus neutral-ensemble mean: {geo['enacted_minus_ensemble_mean']:+.3f} seats
- Probability of a Democratic seat majority in the baseline ensemble: {100 * geo['ensemble_dem_majority_probability']:.2f}%

The neutral ensemble is not designed to force proportional representation. A systematic difference between its seat distribution and the proportional benchmark is evidence that residential geography and the chosen map constraints affect seat conversion. It is not proof that every part of the difference is unavoidable.

## Strongest limitations

1. **The comparison distribution is conditional on modeling choices.** ReCom, population tolerance, graph adjacency conventions, and any omitted constraints define which maps are treated as typical.
2. **No proof of uniform sampling or full mixing.** Trace plots and multi-chain agreement are practical diagnostics, not a theorem about the stationary distribution or mixing time.
3. **Important legal and political constraints are not modeled.** The baseline does not explicitly preserve Voting Rights Act opportunity districts, communities of interest, municipal boundaries, or county splits.
4. **Election-layer dependence.** Presidential votes are assigned to alternative districts as a fixed counterfactual layer; they do not model congressional candidates, incumbency, turnout changes, or voter adaptation.
5. **Artificial bridge edges.** Water-separated or disconnected precinct components were connected with documented modeling edges. These preserve graph operations but are not literal shared land borders.
6. **Correlated samples.** Consecutive MCMC plans are not independent, so row count is larger than effective sample size.
7. **Outlier status is not a legal conclusion.** The analysis can establish unusualness relative to a declared ensemble. It cannot by itself establish intent, causation, constitutional liability, or illegality.

## Strongest argument against the conclusion

The enacted plan can appear extreme because the ensemble omits real redistricting requirements or encodes an overly broad comparison class. Therefore, the correct claim is conditional: the enacted plan is or is not unusual **among maps generated under the stated proposal and constraints**. The analysis must not silently upgrade that conditional statement into a universal judgment about all legally valid maps.

Generated by `scripts/analyze_week6_stress_tests.py` using configuration for `{name}`.
"""


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    summary_parts: list[pd.DataFrame] = []
    diagnostic_parts: list[pd.DataFrame] = []
    enacted_rows: list[pd.Series] = []
    pooled_by_label: dict[str, pd.DataFrame] = {}
    pooled_sizes: dict[str, int] = {}
    baseline_label: str | None = None

    for group in config["ensembles"]:
        label = str(group["label"])
        epsilon = float(group["epsilon"])
        burn_in = int(group["burn_in"])
        paths = resolve_glob(str(group["glob"]))
        frames = read_plan_frames(paths)
        enacted = common_enacted_row(frames)
        pooled = pool_after_burn_in(frames, burn_in)
        validate_population_tolerance(pooled, epsilon)

        summary_parts.append(
            summarize_constraint_ensemble(pooled, enacted, label, epsilon)
        )
        diagnostics = summarize_multiple_chains(frames, burn_in=burn_in)
        diagnostics.insert(0, "constraint_label", label)
        diagnostics.insert(1, "epsilon", epsilon)
        diagnostic_parts.append(diagnostics)
        enacted_rows.append(enacted)
        pooled_by_label[label] = pooled
        pooled_sizes[label] = len(pooled)
        if group.get("baseline"):
            baseline_label = label

    enacted = validate_enacted_across_ensembles(enacted_rows)
    if baseline_label is None:
        raise RuntimeError("No baseline ensemble resolved")

    summary = pd.concat(summary_parts, ignore_index=True)
    diagnostics = pd.concat(diagnostic_parts, ignore_index=True)
    ranges = percentile_range_table(summary)
    baseline_pooled = pooled_by_label[baseline_label]
    geography = geography_baseline_summary(baseline_pooled, enacted)
    seat_frequency = seat_frequency_table(baseline_pooled)

    table_dir = PROJECT_ROOT / "outputs" / "tables" / "week6"
    figure_dir = PROJECT_ROOT / "outputs" / "figures" / "week6"
    report_dir = PROJECT_ROOT / "outputs" / "reports" / "week6"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    summary_path = table_dir / f"{args.name}_constraint_sensitivity.csv"
    ranges_path = table_dir / f"{args.name}_percentile_ranges.csv"
    diagnostics_path = table_dir / f"{args.name}_constraint_diagnostics.csv"
    geography_path = table_dir / f"{args.name}_geography_baseline.csv"
    seats_path = table_dir / f"{args.name}_seat_distribution.csv"
    summary.to_csv(summary_path, index=False)
    ranges.to_csv(ranges_path, index=False)
    diagnostics.to_csv(diagnostics_path, index=False)
    geography.to_csv(geography_path, index=False)
    seat_frequency.to_csv(seats_path, index=False)

    distributions_path = figure_dir / f"{args.name}_constraint_distributions.png"
    percentiles_path = figure_dir / f"{args.name}_constraint_percentiles.png"
    geography_figure_path = figure_dir / f"{args.name}_geography_baseline.png"
    make_constraint_distribution_figure(
        pooled_by_label,
        enacted,
        distributions_path,
        title=f"{config.get('state_name', 'State')}: constraint sensitivity",
    )
    make_percentile_sensitivity_figure(summary, percentiles_path)
    make_geography_figure(
        baseline_pooled,
        enacted,
        geography,
        geography_figure_path,
        title=f"{config.get('state_name', 'State')}: neutral geography vs proportionality",
    )

    report = build_report(
        config,
        args.name,
        summary,
        ranges,
        diagnostics,
        geography,
        baseline_label,
        pooled_sizes,
    )
    report_path = report_dir / f"{args.name}_stress_tests.md"
    report_path.write_text(report, encoding="utf-8")

    print("Saved:")
    for path in (
        summary_path,
        ranges_path,
        diagnostics_path,
        geography_path,
        seats_path,
        distributions_path,
        percentiles_path,
        geography_figure_path,
        report_path,
    ):
        print(f"  {path.relative_to(PROJECT_ROOT)}")
    print("\nPercentile ranges across constraints:")
    print(ranges.to_string(index=False))
    print("\nGeographic baseline:")
    print(geography.to_string(index=False))


if __name__ == "__main__":
    main()
