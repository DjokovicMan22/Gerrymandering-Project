from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from redistricting.analysis.outliers import (
    empirical_position,
    enacted_row,
    load_chain_tables,
    rank_district_shares,
    select_representative_plans,
    summarize_enacted_outliers,
)


def test_empirical_position_handles_ties_with_midrank():
    result = empirical_position([1, 2, 2, 4], 2)
    assert result["sample_count"] == 4
    assert result["count_below"] == 1
    assert result["count_equal"] == 2
    assert result["count_above"] == 1
    assert result["midrank_percentile"] == pytest.approx(50.0)
    assert result["lower_tail_inclusive_percent"] == pytest.approx(75.0)
    assert result["upper_tail_inclusive_percent"] == pytest.approx(75.0)


def _plan_frame(offset: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "step": [0, 1, 2],
            "district_count": [2, 2, 2],
            "dem_seats": [1, 0, 2],
            "rep_seats": [1, 2, 0],
            "tied_seats": [0, 0, 0],
            "statewide_dem_share": [0.5, 0.5, 0.5],
            "efficiency_gap": [0.0, -0.1 + offset, 0.1 + offset],
            "mean_median": [0.0, -0.02, 0.02],
            "cut_edges": [10, 12, 14],
            "max_population_deviation": [0.01, 0.015, 0.018],
        }
    )


def _district_frame() -> pd.DataFrame:
    rows = []
    shares_by_step = {
        0: [0.6, 0.4],
        1: [0.55, 0.45],
        2: [0.7, 0.3],
    }
    for step, shares in shares_by_step.items():
        for district, share in enumerate(shares, start=1):
            total = 100.0
            rows.append(
                {
                    "step": step,
                    "district": str(district),
                    "dem_votes": share * total,
                    "rep_votes": (1 - share) * total,
                    "two_party_votes": total,
                    "dem_share": share,
                }
            )
    return pd.DataFrame(rows)


def _write_chain(tmp_path: Path, name: str, offset: float = 0.0) -> Path:
    plan_path = tmp_path / f"{name}_plan_metrics.csv"
    district_path = tmp_path / f"{name}_district_metrics.csv"
    _plan_frame(offset).to_csv(plan_path, index=False)
    _district_frame().to_csv(district_path, index=False)
    return plan_path


def test_load_chain_tables_applies_burn_in(tmp_path):
    first = _write_chain(tmp_path, "chain_a")
    second = _write_chain(tmp_path, "chain_b")
    plan_frames, district_frames, pooled_plans, pooled_districts = load_chain_tables(
        [first, second], burn_in=1
    )
    assert len(plan_frames) == 2
    assert len(district_frames) == 2
    assert len(pooled_plans) == 4
    assert len(pooled_districts) == 8
    assert pooled_plans["step"].min() == 1


def test_enacted_row_requires_matching_step_zero(tmp_path):
    first = _write_chain(tmp_path, "chain_a")
    second = _write_chain(tmp_path, "chain_b", offset=0.01)
    frames, _, _, _ = load_chain_tables([first, second], burn_in=1)
    # Offset changes only post-burn-in rows; enacted step 0 still matches.
    assert enacted_row(frames)["dem_seats"] == 1

    bad = pd.read_csv(second)
    bad.loc[0, "efficiency_gap"] = 0.5
    bad.to_csv(second, index=False)
    frames, _, _, _ = load_chain_tables([first, second], burn_in=1)
    with pytest.raises(ValueError):
        enacted_row(frames)


def test_rank_district_shares_most_democratic_is_rank_one(tmp_path):
    first = _write_chain(tmp_path, "chain_a")
    plans, districts, _, pooled_districts = load_chain_tables([first], burn_in=1)
    enacted_districts = districts["chain_a"].query("step == 0")
    summary, enacted = rank_district_shares(pooled_districts, enacted_districts)
    assert enacted.loc[enacted["rank"] == 1, "enacted_dem_share"].iloc[0] == pytest.approx(0.6)
    assert summary.loc[summary["rank"] == 1, "median"].iloc[0] == pytest.approx(0.625)
    assert summary.loc[summary["rank"] == 2, "median"].iloc[0] == pytest.approx(0.375)


def test_summary_and_representative_plan_selection(tmp_path):
    first = _write_chain(tmp_path, "chain_a")
    second = _write_chain(tmp_path, "chain_b")
    frames, _, pooled, _ = load_chain_tables([first, second], burn_in=1)
    enacted = enacted_row(frames)
    summary = summarize_enacted_outliers(pooled, enacted)
    assert set(summary["metric"]) >= {"dem_seats", "efficiency_gap", "mean_median"}

    selected = select_representative_plans(pooled, enacted)
    assert set(selected["selection"]) == {
        "enacted",
        "typical",
        "minimum_efficiency_gap",
        "maximum_efficiency_gap",
    }
    minimum = selected.query("selection == 'minimum_efficiency_gap'").iloc[0]
    maximum = selected.query("selection == 'maximum_efficiency_gap'").iloc[0]
    assert minimum["efficiency_gap"] == pytest.approx(-0.1)
    assert maximum["efficiency_gap"] == pytest.approx(0.1)
