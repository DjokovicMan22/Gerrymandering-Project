from __future__ import annotations

import itertools
from collections import deque
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week1"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports" / "week1"

STATE_NAMES = {"mi": "Michigan", "mo": "Missouri"}
DISTRICT_COLUMN = "CD"
POPULATION_COLUMN = "TOTPOP"


def find_shapefile(state_code: str) -> Path:
    matches = list((RAW_DIR / state_code).rglob("*.shp"))
    if not matches:
        raise FileNotFoundError(f"No shapefile below {RAW_DIR / state_code}")
    exact = [p for p in matches if p.stem.lower() == state_code]
    return exact[0] if exact else matches[0]


def clean_district_ids(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def validate_enacted_plan(state_code: str, state_name: str) -> pd.DataFrame:
    gdf = gpd.read_file(find_shapefile(state_code))
    required = {DISTRICT_COLUMN, POPULATION_COLUMN, "geometry"}
    missing = required - set(gdf.columns)
    if missing:
        raise KeyError(f"{state_name} missing columns: {sorted(missing)}")

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf[DISTRICT_COLUMN] = clean_district_ids(gdf[DISTRICT_COLUMN])
    gdf[POPULATION_COLUMN] = pd.to_numeric(gdf[POPULATION_COLUMN], errors="coerce").fillna(0)
    gdf = gdf[~gdf[DISTRICT_COLUMN].isin({"", "0", "nan", "None", "null"})].copy()

    district_population = gdf.groupby(DISTRICT_COLUMN)[POPULATION_COLUMN].sum().sort_index()
    ideal = float(district_population.sum() / len(district_population))

    dissolved = gdf[[DISTRICT_COLUMN, "geometry"]].dissolve(by=DISTRICT_COLUMN)
    contiguity = dissolved.geometry.apply(
        lambda geom: geom.geom_type == "Polygon" or (
            geom.geom_type == "MultiPolygon" and len(geom.geoms) == 1
        )
    )
    component_count = dissolved.geometry.apply(
        lambda geom: 1 if geom.geom_type == "Polygon" else len(geom.geoms)
    )

    result = pd.DataFrame(
        {
            "state": state_name,
            "district": district_population.index,
            "population": district_population.values,
            "ideal_population": ideal,
        }
    )
    result["absolute_deviation"] = result["population"] - ideal
    result["relative_deviation"] = result["absolute_deviation"] / ideal
    result["absolute_relative_deviation"] = result["relative_deviation"].abs()
    result["geometry_component_count"] = result["district"].map(component_count)
    result["contiguous_by_polygon_components"] = result["district"].map(contiguity)
    return result


def neighbors(cell: int, side: int = 4) -> list[int]:
    row, col = divmod(cell, side)
    candidates = []
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = row + dr, col + dc
        if 0 <= nr < side and 0 <= nc < side:
            candidates.append(nr * side + nc)
    return candidates


def is_connected(cells: set[int], side: int = 4) -> bool:
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for nxt in neighbors(current, side):
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def count_grid_partitions(side: int = 4) -> tuple[int, int]:
    total_cells = side * side
    half = total_cells // 2
    all_cells = set(range(total_cells))
    labeled_count = 0

    # Fix cell 0 in district A. This removes duplicate A/B label swaps.
    for remainder in itertools.combinations(range(1, total_cells), half - 1):
        district_a = {0, *remainder}
        district_b = all_cells - district_a
        if is_connected(district_a, side) and is_connected(district_b, side):
            labeled_count += 1

    unlabeled_count = labeled_count
    return labeled_count, unlabeled_count


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    for code, name in STATE_NAMES.items():
        frame = validate_enacted_plan(code, name)
        frame.to_csv(TABLE_DIR / f"{code}_district_population_validation.csv", index=False)
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(TABLE_DIR / "mi_mo_district_population_validation.csv", index=False)

    labeled, unlabeled = count_grid_partitions(4)
    summary_lines = [
        "# Week 1 population and counting validation",
        "",
    ]
    for name, frame in combined.groupby("state"):
        summary_lines.extend(
            [
                f"## {name}",
                "",
                f"- Districts: {len(frame)}",
                f"- Ideal population: {frame['ideal_population'].iloc[0]:,.2f}",
                f"- Maximum absolute relative deviation: {frame['absolute_relative_deviation'].max():.4%}",
                f"- District geometries with more than one polygon component: {(frame['geometry_component_count'] > 1).sum()}",
                "",
            ]
        )
    summary_lines.extend(
        [
            "## 4×4 grid experiment",
            "",
            "The grid is divided into two equal eight-cell districts. Both districts must be rook-contiguous. Cell 0 is fixed in district A so swapping district labels is not double-counted.",
            "",
            f"- Valid unlabeled partitions: **{unlabeled}**",
            "",
            "This is a small counting illustration, not an estimate of the number of real congressional plans.",
        ]
    )
    (REPORT_DIR / "week1_population_and_grid.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Wrote Week 1 validation outputs. 4×4 valid partitions: {unlabeled}")


if __name__ == "__main__":
    main()
