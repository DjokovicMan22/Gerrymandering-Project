from __future__ import annotations

import pandas as pd

from redistricting.reporting.week7 import (
    extract_percentile_rows,
    evidence_ledger,
    format_number,
    top_sorted_deviations,
)


def test_extract_percentile_rows_with_week5_columns():
    df = pd.DataFrame({
        "metric": ["dem_seats"],
        "enacted_value": [7],
        "midrank_percentile": [92.5],
        "ensemble_mean": [5.8],
        "sample_count": [18900],
    })
    rows = extract_percentile_rows(df)
    assert len(rows) == 1
    assert rows[0].metric == "dem_seats"
    assert rows[0].percentile == 92.5
    assert rows[0].ensemble_mean == 5.8


def test_top_sorted_deviations_calculates_absolute_deviation():
    df = pd.DataFrame({
        "rank": [1, 2, 3],
        "enacted_dem_share": [0.8, 0.6, 0.4],
        "median": [0.7, 0.61, 0.5],
    })
    out = top_sorted_deviations(df, n=2)
    assert list(out["rank"]) == [1, 3]


def test_evidence_ledger_includes_percentile_items():
    pct = pd.DataFrame({
        "metric": ["dem_seats", "efficiency_gap"],
        "enacted_value": [7, 0.02],
        "midrank_percentile": [90, 10],
    })
    ledger = evidence_ledger(pct, None, None, None, None)
    assert len(ledger) == 2
    assert "Week 5 percentile" in ledger.iloc[0]["Evidence item"]


def test_format_number_percent():
    assert format_number(0.1234, 1, percent=True) == "12.3%"
