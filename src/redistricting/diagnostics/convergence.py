"""Practical trace and multi-chain diagnostics for Week 4."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

TRACKED_STATISTICS = (
    "dem_seats",
    "efficiency_gap",
    "mean_median",
    "cut_edges",
    "max_population_deviation",
)


def split_rhat(chains: Iterable[np.ndarray]) -> float:
    """Compute a basic split-Rhat diagnostic for equal-length scalar chains.

    This is a practical diagnostic, not proof that a redistricting chain has mixed.
    """
    arrays = [np.asarray(chain, dtype=float) for chain in chains]
    arrays = [arr[np.isfinite(arr)] for arr in arrays]
    if len(arrays) < 2:
        return np.nan
    length = min(len(arr) for arr in arrays)
    half = length // 2
    if half < 2:
        return np.nan

    split = []
    for arr in arrays:
        trimmed = arr[: 2 * half]
        split.extend([trimmed[:half], trimmed[half:]])
    matrix = np.vstack(split)
    n = matrix.shape[1]
    within = float(np.mean(np.var(matrix, axis=1, ddof=1)))
    between = float(n * np.var(np.mean(matrix, axis=1), ddof=1))
    if within == 0:
        return 1.0 if between == 0 else np.inf
    variance_hat = ((n - 1) / n) * within + between / n
    return float(np.sqrt(variance_hat / within))


def make_trace_plots(
    frame: pd.DataFrame,
    output_path: str | Path,
    title: str,
    statistics: Iterable[str] = TRACKED_STATISTICS,
) -> None:
    statistics = [column for column in statistics if column in frame.columns]
    if not statistics:
        raise ValueError("No requested statistics exist in the input table.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(len(statistics), 1, figsize=(11, 2.7 * len(statistics)), sharex=True)
    axes = np.atleast_1d(axes)
    for axis, column in zip(axes, statistics, strict=True):
        axis.plot(frame["step"], frame[column], linewidth=0.7)
        axis.set_ylabel(column.replace("_", " "))
        axis.grid(alpha=0.25)
    axes[-1].set_xlabel("Chain step")
    fig.suptitle(title, fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def summarize_multiple_chains(frames: dict[str, pd.DataFrame], burn_in: int = 0) -> pd.DataFrame:
    rows = []
    for statistic in TRACKED_STATISTICS:
        values = {
            name: frame.loc[frame["step"] >= burn_in, statistic].to_numpy(dtype=float)
            for name, frame in frames.items()
            if statistic in frame.columns
        }
        if not values:
            continue
        pooled = np.concatenate(list(values.values()))
        rows.append(
            {
                "statistic": statistic,
                "chain_count": len(values),
                "burn_in": burn_in,
                "pooled_mean": float(np.nanmean(pooled)),
                "pooled_sd": float(np.nanstd(pooled, ddof=1)),
                "pooled_min": float(np.nanmin(pooled)),
                "pooled_max": float(np.nanmax(pooled)),
                "split_rhat": split_rhat(values.values()),
            }
        )
    return pd.DataFrame(rows)


def make_multichain_distribution_plot(
    frames: dict[str, pd.DataFrame],
    statistic: str,
    output_path: str | Path,
    burn_in: int = 0,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for name, frame in frames.items():
        values = frame.loc[frame["step"] >= burn_in, statistic].dropna()
        ax.hist(values, bins=30, density=True, histtype="step", linewidth=1.4, label=name)
    ax.set_title(f"Multi-chain comparison: {statistic.replace('_', ' ')}")
    ax.set_xlabel(statistic.replace("_", " "))
    ax.set_ylabel("Density")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
