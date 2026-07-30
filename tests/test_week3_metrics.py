from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "week3_partisan_metrics.py"
spec = importlib.util.spec_from_file_location("week3_partisan_metrics", SCRIPT)
assert spec is not None and spec.loader is not None
week3 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = week3
spec.loader.exec_module(week3)


def test_winning_threshold_even_turnout() -> None:
    assert week3.winning_threshold(100) == 51


def test_democratic_win_wasted_votes() -> None:
    dem_wasted, rep_wasted, winner = week3.wasted_votes_for_district(60, 40)
    assert winner == "Democratic"
    assert dem_wasted == 9
    assert rep_wasted == 40


def test_republican_win_wasted_votes() -> None:
    dem_wasted, rep_wasted, winner = week3.wasted_votes_for_district(45, 55)
    assert winner == "Republican"
    assert dem_wasted == 45
    assert rep_wasted == 4


def test_tie_is_not_silently_assigned() -> None:
    dem_wasted, rep_wasted, winner = week3.wasted_votes_for_district(50, 50)
    assert winner == "Tie"
    assert dem_wasted == 50
    assert rep_wasted == 50


def test_zero_turnout() -> None:
    assert week3.wasted_votes_for_district(0, 0) == (0.0, 0.0, "No votes")
    assert np.isnan(week3.efficiency_gap_from_wasted_votes(0, 0, 0))


def test_efficiency_gap_sign_convention() -> None:
    # Positive means Republicans wasted more votes, hence Democratic advantage.
    assert week3.efficiency_gap_from_wasted_votes(20, 30, 100) == pytest.approx(0.10)


def test_equal_turnout_shortcut() -> None:
    assert week3.efficiency_gap_shortcut(0.60, 0.55) == pytest.approx(0.0)


def test_mean_median_definition() -> None:
    import pandas as pd

    shares = pd.Series([0.40, 0.45, 0.50, 0.70, 0.75])
    expected = shares.median() - shares.mean()
    assert week3.mean_median_difference(shares) == pytest.approx(expected)
