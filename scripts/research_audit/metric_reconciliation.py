"""Cross-check independently recomputed district statistics against chain archives."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

def crosscheck_metrics(verified: pd.DataFrame, metric_files: list[Path],
                       *, tolerance: float = 1e-8) -> None:
    """Require saved assignment scores to match archived chain rows.

    Comparisons use a relative and absolute tolerance because vote allocations
    can be fractional. Snapshot metrics must never be silently trusted.
    """
    if len(metric_files) != verified["chain"].nunique():
        raise ValueError("Provide exactly one metric CSV per assignment file")
    for metric_path in metric_files:
        assignment_name = metric_path.name.replace("_plan_metrics.csv", "_assignments.json")
        if assignment_name == metric_path.name:
            raise ValueError(f"Unexpected metric filename: {metric_path}")
        observed = verified.loc[verified["chain"] == assignment_name]
        if observed.empty:
            raise ValueError(f"No verified snapshots correspond to {metric_path}")
        # Independently rescored 2020 results carry an explicit election suffix.
        # The original single-election chain CSV uses unsuffixed metric names.
        observed = observed.copy()
        for field in ("dem_seats", "efficiency_gap"):
            if field not in observed.columns:
                named = f"{field}_20"
                if named not in observed.columns:
                    raise ValueError(f"Verified snapshots missing {field} / {named}")
                observed[field] = observed[named]
        archived = pd.read_csv(metric_path)
        needed = {"step", "dem_seats", "efficiency_gap", "cut_edges",
                  "max_population_deviation"}
        if not needed.issubset(archived.columns):
            raise ValueError(f"{metric_path}: missing columns {sorted(needed - set(archived.columns))}")
        if archived["step"].duplicated().any():
            raise ValueError(f"{metric_path}: duplicate step values")
        aligned = observed.merge(archived, on="step", suffixes=("_verified", "_archived"),
                                 validate="one_to_one", how="left", indicator=True)
        if not aligned["_merge"].eq("both").all():
            raise ValueError(f"{metric_path}: missing recorded steps for verified snapshots")
        for field in needed - {"step"}:
            a = aligned[f"{field}_verified"].to_numpy(dtype=float)
            b = aligned[f"{field}_archived"].to_numpy(dtype=float)
            if not all(math.isfinite(x) for x in a) or not all(math.isfinite(x) for x in b):
                raise ValueError(f"{metric_path}: nonfinite {field}")
            if not all(math.isclose(x, y, rel_tol=tolerance, abs_tol=tolerance)
                       for x, y in zip(a, b, strict=True)):
                raise ValueError(f"{metric_path}: {field} disagrees with recomputed snapshots")


