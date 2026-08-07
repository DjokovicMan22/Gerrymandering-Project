"""Pure analysis helpers for Week 6 constraint and geography stress tests."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .outliers import empirical_position

PLAN_METRICS = (
    "dem_seats",
    "efficiency_gap",
    "mean_median",
    "cut_edges",
    "max_population_deviation",
)

REQUIRED_PLAN_COLUMNS = {
    "step",
    "district_count",
    "dem_seats",
    "rep_seats",
    "tied_seats",
    "statewide_dem_share",
    "efficiency_gap",
    "mean_median",
    "cut_edges",
    "max_population_deviation",
}


def read_plan_frames(paths: Iterable[str | Path]) -> dict[str, pd.DataFrame]:
    """Load and validate plan-level chain CSVs.

    Every chain must contain a unique step 0, a constant district count, and a
    constant statewide vote share. The returned dictionary preserves one frame
    per input path.
    """
    frames: dict[str, pd.DataFrame] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        missing = REQUIRED_PLAN_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
        if frame.empty:
            raise ValueError(f"Empty chain file: {path}")
        if frame["step"].duplicated().any():
            raise ValueError(f"Duplicate steps in {path}")
        if (frame["step"] == 0).sum() != 1:
            raise ValueError(f"{path} must contain exactly one enacted step 0")
        if frame["district_count"].nunique() != 1:
            raise ValueError(f"District count changes within {path}")
        statewide_range = (
            frame["statewide_dem_share"].max()
            - frame["statewide_dem_share"].min()
        )
        if not np.isfinite(statewide_range) or statewide_range > 1e-12:
            raise ValueError(f"Statewide vote share changes within {path}")
        key = path.stem.replace("_plan_metrics", "")
        if key in frames:
            raise ValueError(f"Duplicate chain key: {key}")
        frame = frame.sort_values("step").reset_index(drop=True)
        frame["chain"] = key
        frame["plan_csv"] = str(path)
        frames[key] = frame
    if not frames:
        raise ValueError("No chain files supplied.")
    return frames


def common_enacted_row(
    frames: dict[str, pd.DataFrame], tolerance: float = 1e-10
) -> pd.Series:
    """Return the common enacted row after checking all chains agree."""
    rows = [frame.loc[frame["step"] == 0].iloc[0] for frame in frames.values()]
    reference = rows[0]
    for row in rows[1:]:
        for column in REQUIRED_PLAN_COLUMNS - {"step"}:
            a = float(reference[column])
            b = float(row[column])
            if not np.isclose(a, b, rtol=0.0, atol=tolerance, equal_nan=True):
                raise ValueError(
                    f"Enacted plans disagree at {column}: {a} versus {b}"
                )
    return reference.copy()


def pool_after_burn_in(
    frames: dict[str, pd.DataFrame], burn_in: int
) -> pd.DataFrame:
    """Pool post-burn-in rows from every chain."""
    if burn_in < 0:
        raise ValueError("burn_in cannot be negative")
    pooled_parts: list[pd.DataFrame] = []
    for name, frame in frames.items():
        kept = frame.loc[frame["step"] >= burn_in].copy()
        if kept.empty:
            raise ValueError(f"Burn-in {burn_in} removes every row from {name}")
        pooled_parts.append(kept)
    return pd.concat(pooled_parts, ignore_index=True)


def validate_population_tolerance(
    frame: pd.DataFrame, epsilon: float, numerical_tolerance: float = 1e-9
) -> None:
    """Raise if any sampled plan violates its declared population tolerance."""
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must lie between 0 and 1")
    maximum = float(frame["max_population_deviation"].max())
    if maximum > epsilon + numerical_tolerance:
        raise ValueError(
            f"Population tolerance violated: maximum {maximum:.8f} exceeds "
            f"epsilon {epsilon:.8f}"
        )


def summarize_constraint_ensemble(
    pooled: pd.DataFrame,
    enacted: pd.Series,
    label: str,
    epsilon: float,
    metrics: Iterable[str] = PLAN_METRICS,
) -> pd.DataFrame:
    """Summarize metric distributions and enacted-plan positions."""
    rows: list[dict] = []
    for metric in metrics:
        if metric not in pooled.columns or metric not in enacted.index:
            continue
        values = pooled[metric].dropna().to_numpy(dtype=float)
        position = empirical_position(values, float(enacted[metric]))
        rows.append(
            {
                "constraint_label": label,
                "epsilon": float(epsilon),
                "metric": metric,
                "enacted_value": float(enacted[metric]),
                "q05": float(np.quantile(values, 0.05)),
                "q25": float(np.quantile(values, 0.25)),
                "q75": float(np.quantile(values, 0.75)),
                "q95": float(np.quantile(values, 0.95)),
                **position,
            }
        )
    return pd.DataFrame(rows)


def validate_enacted_across_ensembles(
    enacted_rows: Iterable[pd.Series], tolerance: float = 1e-10
) -> pd.Series:
    """Check that constraint groups use the same enacted plan and election."""
    rows = list(enacted_rows)
    if not rows:
        raise ValueError("No enacted rows supplied")
    reference = rows[0]
    for row in rows[1:]:
        for column in (
            "district_count",
            "dem_seats",
            "rep_seats",
            "tied_seats",
            "statewide_dem_share",
            "efficiency_gap",
            "mean_median",
            "cut_edges",
            "max_population_deviation",
        ):
            if not np.isclose(
                float(reference[column]),
                float(row[column]),
                rtol=0.0,
                atol=tolerance,
                equal_nan=True,
            ):
                raise ValueError(
                    f"Constraint groups use different enacted values at {column}"
                )
    return reference.copy()


def geography_baseline_summary(
    pooled: pd.DataFrame, enacted: pd.Series
) -> pd.DataFrame:
    """Compare neutral-ensemble seats with a proportional seat benchmark."""
    district_count = int(enacted["district_count"])
    statewide_share = float(enacted["statewide_dem_share"])
    proportional_seats = statewide_share * district_count
    values = pooled["dem_seats"].dropna().to_numpy(dtype=float)
    majority_threshold = district_count // 2 + 1

    row = {
        "district_count": district_count,
        "statewide_dem_share": statewide_share,
        "proportional_dem_seats": proportional_seats,
        "enacted_dem_seats": float(enacted["dem_seats"]),
        "ensemble_mean_dem_seats": float(np.mean(values)),
        "ensemble_median_dem_seats": float(np.median(values)),
        "ensemble_q05_dem_seats": float(np.quantile(values, 0.05)),
        "ensemble_q95_dem_seats": float(np.quantile(values, 0.95)),
        "geographic_gap_mean_minus_proportional": float(
            np.mean(values) - proportional_seats
        ),
        "enacted_minus_proportional": float(
            float(enacted["dem_seats"]) - proportional_seats
        ),
        "enacted_minus_ensemble_mean": float(
            float(enacted["dem_seats"]) - np.mean(values)
        ),
        "democratic_majority_threshold": majority_threshold,
        "ensemble_dem_majority_probability": float(
            np.mean(values >= majority_threshold)
        ),
        "sample_count": int(len(values)),
    }
    return pd.DataFrame([row])


def seat_frequency_table(pooled: pd.DataFrame) -> pd.DataFrame:
    """Return counts and probabilities for each Democratic seat outcome."""
    counts = pooled["dem_seats"].value_counts().sort_index()
    result = counts.rename_axis("dem_seats").reset_index(name="count")
    result["probability"] = result["count"] / result["count"].sum()
    return result


def percentile_range_table(summary: pd.DataFrame) -> pd.DataFrame:
    """Quantify how far enacted percentiles move across constraint choices."""
    required = {"metric", "midrank_percentile"}
    if required - set(summary.columns):
        raise ValueError("Summary lacks metric or midrank_percentile")
    return (
        summary.groupby("metric")["midrank_percentile"]
        .agg(
            minimum_percentile="min",
            maximum_percentile="max",
            percentile_range=lambda x: float(x.max() - x.min()),
        )
        .reset_index()
    )
