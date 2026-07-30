from __future__ import annotations

import importlib.util
import sys
import math
from pathlib import Path

import pytest
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "week2_compactness_analysis.py"
spec = importlib.util.spec_from_file_location("week2_compactness_analysis", SCRIPT)
assert spec is not None and spec.loader is not None
week2 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = week2
spec.loader.exec_module(week2)


def test_square_polsby_popper() -> None:
    metrics = week2.compute_metrics_for_geometry(box(0, 0, 1, 1))
    assert metrics["polsby_popper"] == pytest.approx(math.pi / 4)
    assert metrics["convex_hull_ratio"] == pytest.approx(1.0)


def test_circle_is_near_one() -> None:
    circle = Point(0, 0).buffer(1, quad_segs=256)
    metrics = week2.compute_metrics_for_geometry(circle)
    assert metrics["polsby_popper"] > 0.999
    assert metrics["reock"] > 0.99


def test_metric_bounds() -> None:
    metrics = week2.compute_metrics_for_geometry(box(0, 0, 4, 1))
    for key in ("polsby_popper", "reock", "convex_hull_ratio"):
        assert 0 < metrics[key] <= 1
