#!/usr/bin/env python3
"""Compare Week 5 enacted-plan results across two or more elections."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables", nargs="+", type=Path)
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Display label for each table; defaults to each filename stem.",
    )
    parser.add_argument("--name", default="mi_election_robustness")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.tables) < 2:
        raise SystemExit("Provide at least two Week 5 percentile tables.")
    if args.labels and len(args.labels) != len(args.tables):
        raise SystemExit("--labels count must match table count.")

    labels = args.labels or [path.stem for path in args.tables]
    frames = []
    for path, label in zip(args.tables, labels, strict=True):
        full = path if path.is_absolute() else PROJECT_ROOT / path
        frame = pd.read_csv(full)
        needed = {"metric", "enacted_value", "midrank_percentile", "ensemble_mean"}
        missing = needed - set(frame.columns)
        if missing:
            raise ValueError(f"{full} missing columns: {sorted(missing)}")
        frame = frame.copy()
        frame.insert(0, "election", label)
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    table_dir = PROJECT_ROOT / "outputs" / "tables" / "week5"
    figure_dir = PROJECT_ROOT / "outputs" / "figures" / "week5"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    table_path = table_dir / f"{args.name}.csv"
    combined.to_csv(table_path, index=False)

    metrics = [
        metric
        for metric in ("dem_seats", "efficiency_gap", "mean_median")
        if metric in set(combined["metric"])
    ]
    pivot = combined.loc[combined["metric"].isin(metrics)].pivot(
        index="metric", columns="election", values="midrank_percentile"
    )
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.axhline(50, linewidth=1, linestyle="--")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Enacted-plan midrank percentile")
    ax.set_xlabel("")
    ax.set_title("Election-data sensitivity of enacted-plan percentiles")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Election")
    fig = ax.get_figure()
    fig.tight_layout()
    figure_path = figure_dir / f"{args.name}.png"
    fig.savefig(figure_path, dpi=240, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved {table_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved {figure_path.relative_to(PROJECT_ROOT)}")
    print(combined[["election", "metric", "enacted_value", "ensemble_mean", "midrank_percentile"]].to_string(index=False))


if __name__ == "__main__":
    main()
