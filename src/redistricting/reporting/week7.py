from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd


@dataclass(frozen=True)
class ResultSnippet:
    metric: str
    enacted_value: float
    percentile: float
    ensemble_mean: float | None = None
    ensemble_median: float | None = None
    sample_count: int | None = None
    lower_tail: float | None = None
    upper_tail: float | None = None


def read_csv_if_exists(path: str | Path) -> pd.DataFrame | None:
    p = Path(path)
    if not p.exists():
        return None
    return pd.read_csv(p)


def require_file(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required file missing: {p}")
    return p


def write_text(path: str | Path, text: str) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def first_matching_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    colset = set(columns)
    for c in candidates:
        if c in colset:
            return c
    return None


def format_number(value, digits: int = 3, percent: bool = False, signed: bool = False) -> str:
    if value is None:
        return "not available"
    try:
        v = float(value)
    except Exception:
        return str(value)
    sign = "+" if signed else ""
    if percent:
        return f"{v:{sign}.{digits}%}"
    if abs(v) >= 1000:
        return f"{v:{sign},.0f}"
    if abs(v) >= 100:
        return f"{v:{sign},.0f}"
    if abs(v) >= 10:
        return f"{v:{sign}.{max(1, digits-1)}f}"
    if float(v).is_integer() and abs(v) < 20 and not signed:
        return f"{int(v)}"
    return f"{v:{sign}.{digits}f}"


def clean_metric_name(name: str) -> str:
    mapping = {
        "dem_seats": "Democratic seats",
        "efficiency_gap": "efficiency gap",
        "mean_median": "mean-median difference",
        "cut_edges": "cut edges",
        "max_population_deviation": "maximum population deviation",
        "statewide_dem_share": "statewide Democratic vote share",
    }
    return mapping.get(str(name), str(name).replace("_", " "))


def markdown_table(df: pd.DataFrame | None, max_rows: int | None = None, digits: int = 4) -> str:
    if df is None:
        return "_Table not found._"
    if df.empty:
        return "_Table is empty._"
    out = df.copy()
    if max_rows is not None:
        out = out.head(max_rows)
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda x: f"{x:.{digits}f}" if pd.notna(x) else "")
    try:
        return out.to_markdown(index=False)
    except Exception:
        return out.to_csv(index=False)


def compact_table_text(df: pd.DataFrame | None, columns: Sequence[str] | None = None, max_rows: int = 12, digits: int = 4) -> str:
    if df is None:
        return "_Table not found._"
    out = df.copy()
    if columns:
        cols = [c for c in columns if c in out.columns]
        if cols:
            out = out[cols]
    return markdown_table(out, max_rows=max_rows, digits=digits)


def read_text_if_exists(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def image_markdown(path: str | Path, caption: str) -> str:
    p = Path(path)
    if p.exists():
        return f"\n![{caption}]({p.as_posix()})\n\n**Figure. {caption}**\n"
    return f"\n_[Missing figure: `{p.as_posix()}`. Generate this output before final submission.]_\n"


def extract_percentile_rows(percentiles: pd.DataFrame | None) -> list[ResultSnippet]:
    if percentiles is None or percentiles.empty:
        return []
    metric_col = first_matching_column(percentiles.columns, ["metric", "statistic", "quantity"])
    value_col = first_matching_column(percentiles.columns, ["enacted_value", "enacted", "value"])
    pct_col = first_matching_column(percentiles.columns, ["midrank_percentile", "percentile", "enacted_percentile", "empirical_percentile"])
    mean_col = first_matching_column(percentiles.columns, ["ensemble_mean", "pooled_mean", "mean"])
    med_col = first_matching_column(percentiles.columns, ["ensemble_median", "pooled_median", "median"])
    n_col = first_matching_column(percentiles.columns, ["sample_count", "n", "count"])
    lower_col = first_matching_column(percentiles.columns, ["lower_tail_inclusive_percent", "lower_tail", "left_tail"])
    upper_col = first_matching_column(percentiles.columns, ["upper_tail_inclusive_percent", "upper_tail", "right_tail"])
    if not metric_col or not value_col or not pct_col:
        return []
    rows = []
    for _, row in percentiles.iterrows():
        try:
            rows.append(ResultSnippet(
                metric=str(row[metric_col]),
                enacted_value=float(row[value_col]),
                percentile=float(row[pct_col]),
                ensemble_mean=float(row[mean_col]) if mean_col and pd.notna(row[mean_col]) else None,
                ensemble_median=float(row[med_col]) if med_col and pd.notna(row[med_col]) else None,
                sample_count=int(row[n_col]) if n_col and pd.notna(row[n_col]) else None,
                lower_tail=float(row[lower_col]) if lower_col and pd.notna(row[lower_col]) else None,
                upper_tail=float(row[upper_col]) if upper_col and pd.notna(row[upper_col]) else None,
            ))
        except Exception:
            continue
    return rows


def get_metric_row(percentiles: pd.DataFrame | None, metric_substring: str) -> ResultSnippet | None:
    target = metric_substring.lower()
    for row in extract_percentile_rows(percentiles):
        if target in row.metric.lower():
            return row
    return None


def summarize_percentiles(percentiles: pd.DataFrame | None) -> str:
    rows = extract_percentile_rows(percentiles)
    if not rows:
        return "Percentile table was found, but column names were not recognized. Inspect the CSV manually."
    lines = []
    for r in rows:
        comparison = ""
        if r.ensemble_mean is not None:
            comparison += f", ensemble mean {format_number(r.ensemble_mean, 3)}"
        if r.ensemble_median is not None:
            comparison += f", ensemble median {format_number(r.ensemble_median, 3)}"
        tails = ""
        if r.lower_tail is not None and r.upper_tail is not None:
            tails = f"; inclusive lower tail {format_number(r.lower_tail, 2)}%, upper tail {format_number(r.upper_tail, 2)}%"
        lines.append(f"- **{clean_metric_name(r.metric)}**: enacted {format_number(r.enacted_value, 3)}{comparison}; empirical midrank percentile **{format_number(r.percentile, 2)}%**{tails}.")
    return "\n".join(lines)


def metric_sentence(percentiles: pd.DataFrame | None, metric: str, label: str) -> str:
    row = get_metric_row(percentiles, metric)
    if row is None:
        return f"The {label} percentile was not available in the generated table."
    extra = ""
    if row.ensemble_mean is not None:
        extra = f" The ensemble mean is {format_number(row.ensemble_mean, 3)}."
    return f"For {label}, the enacted value is **{format_number(row.enacted_value, 3)}** and its empirical midrank percentile is **{format_number(row.percentile, 2)}%**.{extra}"


def infer_sample_count(paths: Sequence[Path], burn_in: int) -> int:
    total = 0
    for p in paths:
        try:
            total += max(len(pd.read_csv(p)) - burn_in, 0)
        except Exception:
            pass
    return total


def top_sorted_deviations(sorted_summary: pd.DataFrame | None, n: int = 5) -> pd.DataFrame | None:
    if sorted_summary is None or sorted_summary.empty:
        return None
    df = sorted_summary.copy()
    if "enacted_minus_ensemble_median" not in df.columns:
        if {"enacted_dem_share", "median"}.issubset(df.columns):
            df["enacted_minus_ensemble_median"] = df["enacted_dem_share"] - df["median"]
        else:
            return None
    df["absolute_deviation"] = df["enacted_minus_ensemble_median"].abs()
    return df.sort_values("absolute_deviation", ascending=False).head(n)


def describe_extremeness(row: ResultSnippet | None, high_label: str, low_label: str) -> str:
    if row is None:
        return "not available"
    if row.percentile >= 90:
        return high_label
    if row.percentile <= 10:
        return low_label
    if 40 <= row.percentile <= 60:
        return "near the middle of the sampled distribution"
    if row.percentile > 60:
        return "above the ensemble center but not in the extreme tail"
    return "below the ensemble center but not in the extreme tail"


def evidence_ledger(percentiles: pd.DataFrame | None, diagnostics: pd.DataFrame | None, constraint: pd.DataFrame | None, geography: pd.DataFrame | None, percentile_ranges: pd.DataFrame | None) -> pd.DataFrame:
    rows: list[dict] = []
    for r in extract_percentile_rows(percentiles):
        rows.append({
            "Evidence item": f"Week 5 percentile: {clean_metric_name(r.metric)}",
            "What it shows": f"Enacted value {format_number(r.enacted_value, 3)} lies at {format_number(r.percentile, 2)}% of the sampled ensemble.",
            "How it supports or limits the claim": "Supports an outlier claim only relative to the specific ensemble and scoring election.",
        })
    if diagnostics is not None and not diagnostics.empty:
        if "split_rhat" in diagnostics.columns:
            max_rhat = diagnostics["split_rhat"].max()
            rows.append({
                "Evidence item": "Week 4 multi-chain diagnostics",
                "What it shows": f"Maximum split-Rhat across tracked scalar statistics is {format_number(max_rhat, 3)}.",
                "How it supports or limits the claim": "Chains look practically comparable on tracked summaries, but this is not a proof of full state-space mixing.",
            })
        if "pooled_min" in diagnostics.columns and "pooled_max" in diagnostics.columns and "statistic" in diagnostics.columns:
            seats = diagnostics.loc[diagnostics["statistic"] == "dem_seats"]
            if not seats.empty:
                rows.append({
                    "Evidence item": "Seat exploration",
                    "What it shows": f"Post-burn-in chains explored Democratic seat counts from {format_number(seats.iloc[0]['pooled_min'], 0)} to {format_number(seats.iloc[0]['pooled_max'], 0)}.",
                    "How it supports or limits the claim": "The chain is not frozen at the enacted plan; it traverses materially different outcomes.",
                })
    if constraint is not None and not constraint.empty:
        rows.append({
            "Evidence item": "Week 6 population-tolerance sensitivity",
            "What it shows": "The same outlier quantities are recomputed under alternate population tolerances.",
            "How it supports or limits the claim": "If percentiles remain similar, the conclusion is less likely to be an artifact of a single tolerance choice; if they move, the paper reports that sensitivity.",
        })
    if percentile_ranges is not None and not percentile_ranges.empty:
        largest = percentile_ranges.sort_values("percentile_range", ascending=False).head(1)
        if not largest.empty:
            row = largest.iloc[0]
            rows.append({
                "Evidence item": "Largest percentile movement across constraints",
                "What it shows": f"{clean_metric_name(row['metric'])} moves by {format_number(row['percentile_range'], 2)} percentile points across tested tolerances.",
                "How it supports or limits the claim": "Quantifies robustness instead of merely asserting it.",
            })
    if geography is not None and not geography.empty:
        row = geography.iloc[0]
        if {"proportional_dem_seats", "ensemble_mean_dem_seats", "enacted_dem_seats"}.issubset(geography.columns):
            rows.append({
                "Evidence item": "Geographic baseline",
                "What it shows": f"Proportional benchmark {format_number(row['proportional_dem_seats'], 2)} seats, ensemble mean {format_number(row['ensemble_mean_dem_seats'], 2)} seats, enacted {format_number(row['enacted_dem_seats'], 0)} seats.",
                "How it supports or limits the claim": "Separates disproportionality caused by district geography from proportional representation as a purely arithmetic benchmark.",
            })
    return pd.DataFrame(rows)
