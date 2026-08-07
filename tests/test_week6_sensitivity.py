from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

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


def _frame(seat_values=(2, 1, 2, 3), maximum_deviation=0.01) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "step": [0, 1, 2, 3],
            "district_count": [4] * 4,
            "dem_seats": list(seat_values),
            "rep_seats": [4 - value for value in seat_values],
            "tied_seats": [0] * 4,
            "statewide_dem_share": [0.55] * 4,
            "efficiency_gap": [0.0, -0.1, 0.0, 0.1],
            "mean_median": [0.0, -0.02, 0.01, 0.02],
            "cut_edges": [10, 12, 11, 13],
            "max_population_deviation": [0.005, maximum_deviation, 0.009, 0.008],
        }
    )


def _write(tmp_path: Path, name: str, **kwargs) -> Path:
    path = tmp_path / f"{name}_plan_metrics.csv"
    _frame(**kwargs).to_csv(path, index=False)
    return path


def test_read_pool_and_common_enacted(tmp_path):
    first = _write(tmp_path, "a")
    second = _write(tmp_path, "b")
    frames = read_plan_frames([first, second])
    enacted = common_enacted_row(frames)
    pooled = pool_after_burn_in(frames, burn_in=1)
    assert enacted["dem_seats"] == 2
    assert len(pooled) == 6
    assert pooled["step"].min() == 1


def test_population_tolerance_validation(tmp_path):
    path = _write(tmp_path, "a", maximum_deviation=0.011)
    frames = read_plan_frames([path])
    pooled = pool_after_burn_in(frames, burn_in=1)
    with pytest.raises(ValueError):
        validate_population_tolerance(pooled, 0.01)
    validate_population_tolerance(pooled, 0.02)


def test_constraint_summary_and_percentile_ranges(tmp_path):
    first = _write(tmp_path, "a")
    frames = read_plan_frames([first])
    enacted = common_enacted_row(frames)
    pooled = pool_after_burn_in(frames, burn_in=1)
    one = summarize_constraint_ensemble(pooled, enacted, "1%", 0.01)
    two = summarize_constraint_ensemble(pooled, enacted, "2%", 0.02)
    combined = pd.concat([one, two], ignore_index=True)
    ranges = percentile_range_table(combined)
    assert set(one["metric"]) >= {"dem_seats", "efficiency_gap", "mean_median"}
    assert (ranges["percentile_range"] == 0).all()


def test_geography_baseline_and_seat_frequency(tmp_path):
    path = _write(tmp_path, "a")
    frames = read_plan_frames([path])
    enacted = common_enacted_row(frames)
    pooled = pool_after_burn_in(frames, burn_in=1)
    geography = geography_baseline_summary(pooled, enacted).iloc[0]
    frequencies = seat_frequency_table(pooled)
    assert geography["proportional_dem_seats"] == pytest.approx(2.2)
    assert geography["ensemble_mean_dem_seats"] == pytest.approx(2.0)
    assert frequencies["count"].sum() == 3
    assert frequencies["probability"].sum() == pytest.approx(1.0)


def test_validate_enacted_across_ensembles_rejects_mismatch(tmp_path):
    first = _write(tmp_path, "a")
    second = _write(tmp_path, "b")
    frames_a = read_plan_frames([first])
    frames_b = read_plan_frames([second])
    enacted_a = common_enacted_row(frames_a)
    enacted_b = common_enacted_row(frames_b)
    assert validate_enacted_across_ensembles([enacted_a, enacted_b])["dem_seats"] == 2
    enacted_b = enacted_b.copy()
    enacted_b["dem_seats"] = 3
    with pytest.raises(ValueError):
        validate_enacted_across_ensembles([enacted_a, enacted_b])
