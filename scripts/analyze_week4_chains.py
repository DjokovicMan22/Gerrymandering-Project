#!/usr/bin/env python3
"""Compare two or more Week 4 chain runs from their plan-metric CSV files."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from redistricting.diagnostics import (
    TRACKED_STATISTICS,
    make_multichain_distribution_plot,
    summarize_multiple_chains,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument("--burn-in", type=int, default=0)
    parser.add_argument("--name", default="week4_multichain")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if len(args.csv_files) < 2:
        raise SystemExit("Provide at least two plan-metrics CSV files.")

    frames = {}
    for path in args.csv_files:
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        if "step" not in frame.columns:
            raise ValueError(f"Missing step column in {path}")
        frames[path.stem] = frame

    table_dir = PROJECT_ROOT / "outputs" / "tables" / "week4"
    figure_dir = PROJECT_ROOT / "outputs" / "figures" / "week4"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    summary = summarize_multiple_chains(frames, burn_in=args.burn_in)
    summary_path = table_dir / f"{args.name}_diagnostics.csv"
    summary.to_csv(summary_path, index=False)

    for statistic in TRACKED_STATISTICS:
        if all(statistic in frame.columns for frame in frames.values()):
            make_multichain_distribution_plot(
                frames,
                statistic,
                figure_dir / f"{args.name}_{statistic}.png",
                burn_in=args.burn_in,
            )

    print(f"Saved {summary_path.relative_to(PROJECT_ROOT)}")
    print(summary.to_string(index=False))
    print("\nInterpret split-Rhat as a warning signal only; it is not proof of mixing.")


if __name__ == "__main__":
    main()
