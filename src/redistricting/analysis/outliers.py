"""Core Week 5 outlier-analysis calculations.

The functions in this module intentionally separate calculation from plotting so
that the statistical logic can be unit-tested.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

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

REQUIRED_DISTRICT_COLUMNS = {
    "step",
    "district",
    "dem_votes",
    "rep_votes",
    "two_party_votes",
    "dem_share",
}


def _chain_key(path: str | Path) -> str:
    name = Path(path).name
    suffix = "_plan_metrics.csv"
    if not name.endswith(suffix):
        raise ValueError(f"Plan-metrics filename must end with {suffix!r}: {path}")
    return name[: -len(suffix)]


def _district_path_for_plan(path: str | Path) -> Path:
    plan_path = Path(path)
    return plan_path.with_name(
        plan_path.name.replace("_plan_metrics.csv", "_district_metrics.csv")
    )


def load_chain_tables(
    plan_paths: Sequence[str | Path],
    burn_in: int,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame]:
    """Load, validate, label, and pool plan/district tables.

    Returns ``(plan_frames, district_frames, pooled_plans, pooled_districts)``.
    Step 0 remains in the per-chain frames for enacted-plan validation but is
    excluded from pooled tables whenever ``burn_in > 0``.
    """
    if burn_in < 0:
        raise ValueError("burn_in cannot be negative.")
    if not plan_paths:
        raise ValueError("Provide at least one plan-metrics CSV file.")

    plan_frames: dict[str, pd.DataFrame] = {}
    district_frames: dict[str, pd.DataFrame] = {}
    pooled_plan_parts: list[pd.DataFrame] = []
    pooled_district_parts: list[pd.DataFrame] = []

    expected_district_count: int | None = None

    for raw_path in plan_paths:
        plan_path = Path(raw_path)
        district_path = _district_path_for_plan(plan_path)
        if not plan_path.exists():
            raise FileNotFoundError(plan_path)
        if not district_path.exists():
            raise FileNotFoundError(district_path)

        key = _chain_key(plan_path)
        plans = pd.read_csv(plan_path)
        districts = pd.read_csv(district_path)

        missing_plan = REQUIRED_PLAN_COLUMNS - set(plans.columns)
        missing_district = REQUIRED_DISTRICT_COLUMNS - set(districts.columns)
        if missing_plan:
            raise ValueError(f"{plan_path} is missing columns: {sorted(missing_plan)}")
        if missing_district:
            raise ValueError(
                f"{district_path} is missing columns: {sorted(missing_district)}"
            )
        if plans.empty or districts.empty:
            raise ValueError(f"Empty chain output for {key}")
        if plans["step"].duplicated().any():
            raise ValueError(f"Duplicate plan steps in {plan_path}")
        if 0 not in set(plans["step"]):
            raise ValueError(f"Step 0 enacted plan missing from {plan_path}")

        district_counts = plans["district_count"].dropna().astype(int).unique()
        if len(district_counts) != 1:
            raise ValueError(f"District count changes within {plan_path}")
        district_count = int(district_counts[0])
        if expected_district_count is None:
            expected_district_count = district_count
        elif district_count != expected_district_count:
            raise ValueError("Chains use different district counts.")

        rows_per_step = districts.groupby("step").size()
        bad = rows_per_step[rows_per_step != district_count]
        if not bad.empty:
            raise ValueError(
                f"District table has incomplete steps in {district_path}: "
                f"{bad.head().to_dict()}"
            )

        plans = plans.sort_values("step").reset_index(drop=True)
        districts = districts.sort_values(["step", "district"]).reset_index(drop=True)
        plans["chain"] = key
        districts["chain"] = key
        plans["plan_csv"] = str(plan_path)
        districts["district_csv"] = str(district_path)

        plan_frames[key] = plans
        district_frames[key] = districts

        kept_plans = plans.loc[plans["step"] >= burn_in].copy()
        kept_districts = districts.loc[districts["step"] >= burn_in].copy()
        if kept_plans.empty:
            raise ValueError(
                f"Burn-in {burn_in} removes every sample from {plan_path}"
            )
        pooled_plan_parts.append(kept_plans)
        pooled_district_parts.append(kept_districts)

    pooled_plans = pd.concat(pooled_plan_parts, ignore_index=True)
    pooled_districts = pd.concat(pooled_district_parts, ignore_index=True)
    return plan_frames, district_frames, pooled_plans, pooled_districts


def enacted_row(plan_frames: dict[str, pd.DataFrame], tolerance: float = 1e-10) -> pd.Series:
    """Return the common step-0 enacted-plan row after cross-chain validation."""
    if not plan_frames:
        raise ValueError("No plan frames provided.")
    rows = [frame.loc[frame["step"] == 0].iloc[0] for frame in plan_frames.values()]
    reference = rows[0]
    numeric_columns = [
        "district_count",
        "dem_seats",
        "rep_seats",
        "tied_seats",
        "statewide_dem_share",
        "efficiency_gap",
        "mean_median",
        "cut_edges",
        "max_population_deviation",
    ]
    for index, row in enumerate(rows[1:], start=2):
        for column in numeric_columns:
            a = float(reference[column])
            b = float(row[column])
            if not np.isclose(a, b, rtol=0.0, atol=tolerance, equal_nan=True):
                raise ValueError(
                    f"Step-0 enacted plans disagree across chains at {column}: "
                    f"{a} vs {b} (chain {index})"
                )
    return reference.copy()


def empirical_position(values: Iterable[float], observed: float) -> dict[str, float | int]:
    """Describe an observed value's location in an empirical distribution.

    ``midrank_percentile`` uses half of tied observations. Inclusive lower and
    upper tails are also reported. ``two_sided_extremeness_percent`` doubles the
    smaller inclusive tail and caps the result at 100. It is an empirical
    extremeness summary, not a classical p-value.
    """
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if not np.isfinite(observed):
        raise ValueError("observed must be finite.")
    if array.size == 0:
        raise ValueError("values contains no finite observations.")

    less = int(np.sum(array < observed))
    equal = int(np.sum(array == observed))
    greater = int(np.sum(array > observed))
    n = int(array.size)
    lower_inclusive = (less + equal) / n
    upper_inclusive = (greater + equal) / n

    return {
        "sample_count": n,
        "count_below": less,
        "count_equal": equal,
        "count_above": greater,
        "midrank_percentile": 100.0 * (less + 0.5 * equal) / n,
        "lower_tail_inclusive_percent": 100.0 * lower_inclusive,
        "upper_tail_inclusive_percent": 100.0 * upper_inclusive,
        "two_sided_extremeness_percent": 100.0
        * min(1.0, 2.0 * min(lower_inclusive, upper_inclusive)),
        "ensemble_mean": float(np.mean(array)),
        "ensemble_median": float(np.median(array)),
        "ensemble_sd": float(np.std(array, ddof=1)) if n > 1 else 0.0,
        "ensemble_min": float(np.min(array)),
        "ensemble_max": float(np.max(array)),
    }


def summarize_enacted_outliers(
    pooled_plans: pd.DataFrame,
    enacted: pd.Series,
    metrics: Sequence[str] = PLAN_METRICS,
) -> pd.DataFrame:
    """Create one empirical-position row per plan-level metric."""
    rows: list[dict] = []
    for metric in metrics:
        if metric not in pooled_plans.columns or metric not in enacted.index:
            continue
        position = empirical_position(pooled_plans[metric], float(enacted[metric]))
        rows.append(
            {
                "metric": metric,
                "enacted_value": float(enacted[metric]),
                **position,
            }
        )
    return pd.DataFrame(rows)


def rank_district_shares(
    pooled_districts: pd.DataFrame,
    enacted_districts: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Summarize rank-ordered district vote shares across sampled plans.

    Rank 1 is the most Democratic district. The returned enacted table contains
    the enacted plan's rank-ordered shares for direct overlay.
    """
    required = {"chain", "step", "dem_share"}
    if required - set(pooled_districts.columns):
        raise ValueError("pooled_districts lacks chain, step, or dem_share")
    if "dem_share" not in enacted_districts.columns:
        raise ValueError("enacted_districts lacks dem_share")

    ranked_parts: list[pd.DataFrame] = []
    district_count: int | None = None
    for (chain, step), group in pooled_districts.groupby(["chain", "step"], sort=False):
        values = group["dem_share"].to_numpy(dtype=float)
        values = values[np.isfinite(values)]
        values = np.sort(values)[::-1]
        if district_count is None:
            district_count = len(values)
        elif len(values) != district_count:
            raise ValueError("Sampled plans do not all contain the same district count.")
        ranked_parts.append(
            pd.DataFrame(
                {
                    "chain": chain,
                    "step": int(step),
                    "rank": np.arange(1, len(values) + 1),
                    "dem_share": values,
                }
            )
        )

    ranked = pd.concat(ranked_parts, ignore_index=True)
    summary = (
        ranked.groupby("rank")["dem_share"]
        .agg(
            sample_count="count",
            mean="mean",
            median="median",
            q05=lambda x: x.quantile(0.05),
            q25=lambda x: x.quantile(0.25),
            q75=lambda x: x.quantile(0.75),
            q95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )

    enacted_values = np.sort(
        enacted_districts["dem_share"].dropna().to_numpy(dtype=float)
    )[::-1]
    if district_count is not None and len(enacted_values) != district_count:
        raise ValueError("Enacted and sampled plans use different district counts.")
    enacted_ranked = pd.DataFrame(
        {
            "rank": np.arange(1, len(enacted_values) + 1),
            "enacted_dem_share": enacted_values,
        }
    )
    summary = summary.merge(enacted_ranked, on="rank", how="left")
    summary["enacted_minus_ensemble_median"] = (
        summary["enacted_dem_share"] - summary["median"]
    )
    return summary, enacted_ranked


def _robust_scale(series: pd.Series) -> float:
    values = series.to_numpy(dtype=float)
    median = np.nanmedian(values)
    mad = np.nanmedian(np.abs(values - median))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 0:
        scale = float(np.nanstd(values, ddof=1))
    return scale if np.isfinite(scale) and scale > 0 else 1.0


def select_representative_plans(
    pooled_plans: pd.DataFrame,
    enacted: pd.Series,
    direction_metric: str = "efficiency_gap",
) -> pd.DataFrame:
    """Select enacted, robustly typical, and directional extreme plans.

    The typical plan minimizes robust standardized distance from pooled medians
    over seats, efficiency gap, mean-median, and cut edges. Directional extremes
    are the minimum and maximum values of ``direction_metric``.
    """
    needed = {"chain", "step", "plan_csv", direction_metric}
    missing = needed - set(pooled_plans.columns)
    if missing:
        raise ValueError(f"pooled_plans missing columns: {sorted(missing)}")

    typical_metrics = [
        column
        for column in ("dem_seats", "efficiency_gap", "mean_median", "cut_edges")
        if column in pooled_plans.columns
    ]
    work = pooled_plans.copy()
    distance = np.zeros(len(work), dtype=float)
    for metric in typical_metrics:
        center = float(work[metric].median())
        scale = _robust_scale(work[metric])
        distance += ((work[metric].to_numpy(dtype=float) - center) / scale) ** 2
    work["typical_distance"] = np.sqrt(distance)

    typical = work.loc[work["typical_distance"].idxmin()]
    minimum = work.loc[work[direction_metric].idxmin()]
    maximum = work.loc[work[direction_metric].idxmax()]

    enacted_record = {
        "selection": "enacted",
        "chain": str(enacted["chain"]),
        "step": int(enacted["step"]),
        "plan_csv": str(enacted["plan_csv"]),
        "typical_distance": np.nan,
    }
    for metric in PLAN_METRICS:
        if metric in enacted.index:
            enacted_record[metric] = float(enacted[metric])

    rows = [enacted_record]
    for label, row in (
        ("typical", typical),
        (f"minimum_{direction_metric}", minimum),
        (f"maximum_{direction_metric}", maximum),
    ):
        record = {
            "selection": label,
            "chain": str(row["chain"]),
            "step": int(row["step"]),
            "plan_csv": str(row["plan_csv"]),
            "typical_distance": float(row.get("typical_distance", np.nan)),
        }
        for metric in PLAN_METRICS:
            if metric in row.index:
                record[metric] = float(row[metric])
        rows.append(record)
    return pd.DataFrame(rows)
