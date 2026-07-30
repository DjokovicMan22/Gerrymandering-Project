from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Point, Polygon, box


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "week2"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week2"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports" / "week2"

DISTRICT_COLUMN = "CD"
DEM_COLUMN = "PRE20D"
REP_COLUMN = "PRE20R"

STATES = {
    "mi": "Michigan",
    "mo": "Missouri",
}

COLORS = {
    "paper": "#F7F9FC",
    "white": "#FFFFFF",
    "ink": "#1F2A44",
    "muted": "#667085",
    "grid": "#D7DEE8",
    "blue": "#2F6FED",
    "blue_light": "#DCE8FF",
    "red": "#D94B45",
    "red_light": "#FBE1DF",
    "purple": "#7A5AF8",
    "gold": "#EAAA08",
    "teal": "#12B76A",
}


# -------------------------------------------------------------------
# Utility / setup
# -------------------------------------------------------------------

def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.facecolor": COLORS["white"],
            "figure.facecolor": COLORS["paper"],
            "savefig.facecolor": COLORS["paper"],
            "axes.edgecolor": COLORS["grid"],
            "xtick.color": COLORS["muted"],
            "ytick.color": COLORS["muted"],
            "text.color": COLORS["ink"],
        }
    )


def ensure_directories() -> None:
    for folder in (FIGURE_DIR, TABLE_DIR, REPORT_DIR):
        current = PROJECT_ROOT
        for part in folder.relative_to(PROJECT_ROOT).parts:
            current = current / part
            if current.exists() and not current.is_dir():
                raise NotADirectoryError(
                    f"{current} exists as a file, but needs to be a folder.\n"
                    f"Fix with:\n"
                    f"mv '{current}' '{current}_old_file'"
                )
        folder.mkdir(parents=True, exist_ok=True)


def find_shapefile(state_code: str) -> Path:
    folder = RAW_DIR / state_code
    if not folder.exists():
        raise FileNotFoundError(f"Missing raw folder: {folder}")

    shapefiles = list(folder.rglob("*.shp"))
    if not shapefiles:
        raise FileNotFoundError(f"No shapefile found under: {folder}")

    exact = [p for p in shapefiles if p.stem.lower() == state_code.lower()]
    selected = exact[0] if exact else shapefiles[0]
    print(f"Found {state_code.upper()} shapefile: {selected}", flush=True)
    return selected


def clean_district_ids(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def district_sort_key(value: str) -> tuple[int, str]:
    try:
        return int(value), value
    except ValueError:
        return 10**9, value


# -------------------------------------------------------------------
# Load district geometry from precinct file
# -------------------------------------------------------------------

def load_precinct_data(state_code: str, state_name: str) -> gpd.GeoDataFrame:
    path = find_shapefile(state_code)
    gdf = gpd.read_file(path)

    required = {DISTRICT_COLUMN, "geometry"}
    missing = sorted(required - set(gdf.columns))
    if missing:
        raise KeyError(
            f"{state_name} is missing required columns: {missing}\n"
            f"Available columns: {gdf.columns.tolist()}"
        )

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf[DISTRICT_COLUMN] = clean_district_ids(gdf[DISTRICT_COLUMN])

    invalid_ids = {"", "nan", "None", "null", "0"}
    gdf = gdf[~gdf[DISTRICT_COLUMN].isin(invalid_ids)].copy()
    gdf = gdf.reset_index(drop=True)

    if gdf.crs is None:
        raise ValueError(f"{state_name} shapefile has no CRS.")

    if gdf.crs.is_geographic:
        projected = gdf.estimate_utm_crs()
        if projected is None:
            raise ValueError(f"Could not estimate projected CRS for {state_name}.")
        gdf = gdf.to_crs(projected)

    return gdf


def build_district_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    districts = (
        gdf[[DISTRICT_COLUMN, "geometry"]]
        .dissolve(by=DISTRICT_COLUMN)
        .reset_index()
    )

    order = sorted(districts[DISTRICT_COLUMN].tolist(), key=district_sort_key)
    order_lookup = {district: i for i, district in enumerate(order)}
    districts["_sort"] = districts[DISTRICT_COLUMN].map(order_lookup)
    districts = districts.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)
    return districts


# -------------------------------------------------------------------
# Smallest enclosing circle (from scratch)
# Based on the classic randomized incremental algorithm.
# -------------------------------------------------------------------

def dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def is_in_circle(point: tuple[float, float], circle: tuple[float, float, float] | None) -> bool:
    if circle is None:
        return False
    x, y, r = circle
    return dist(point, (x, y)) <= r + 1e-9


def circle_from_two_points(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float, float]:
    cx = (a[0] + b[0]) / 2.0
    cy = (a[1] + b[1]) / 2.0
    r = dist(a, b) / 2.0
    return (cx, cy, r)


def circle_from_three_points(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
) -> tuple[float, float, float] | None:
    ax, ay = a
    bx, by = b
    cx, cy = c

    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None

    ux = (
        (ax * ax + ay * ay) * (by - cy)
        + (bx * bx + by * by) * (cy - ay)
        + (cx * cx + cy * cy) * (ay - by)
    ) / d

    uy = (
        (ax * ax + ay * ay) * (cx - bx)
        + (bx * bx + by * by) * (ax - cx)
        + (cx * cx + cy * cy) * (bx - ax)
    ) / d

    r = dist((ux, uy), a)
    return (ux, uy, r)


def make_circle(points: list[tuple[float, float]]) -> tuple[float, float, float] | None:
    shuffled = points[:]
    random.shuffle(shuffled)

    circle = None
    for i, p in enumerate(shuffled):
        if circle is None or not is_in_circle(p, circle):
            circle = (p[0], p[1], 0.0)
            for j, q in enumerate(shuffled[:i]):
                if not is_in_circle(q, circle):
                    circle = circle_from_two_points(p, q)
                    for r in shuffled[:j]:
                        if not is_in_circle(r, circle):
                            c = circle_from_three_points(p, q, r)
                            if c is None:
                                candidates = [
                                    circle_from_two_points(p, q),
                                    circle_from_two_points(p, r),
                                    circle_from_two_points(q, r),
                                ]
                                valid = [
                                    cand for cand in candidates
                                    if all(is_in_circle(pt, cand) for pt in (p, q, r))
                                ]
                                if valid:
                                    circle = min(valid, key=lambda z: z[2])
                            else:
                                circle = c
    return circle


# -------------------------------------------------------------------
# Geometry helpers for metrics
# -------------------------------------------------------------------

def iter_polygons(geom) -> list[Polygon]:
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    raise TypeError(f"Unsupported geometry type: {geom.geom_type}")


def boundary_points(geom) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for poly in iter_polygons(geom):
        points.extend(list(poly.exterior.coords))
        for interior in poly.interiors:
            points.extend(list(interior.coords))

    deduped = []
    seen = set()
    for x, y in points:
        key = (round(x, 9), round(y, 9))
        if key not in seen:
            seen.add(key)
            deduped.append((float(x), float(y)))
    return deduped


def polsby_popper(area: float, perimeter: float) -> float:
    if perimeter <= 0:
        return np.nan
    return (4 * math.pi * area) / (perimeter ** 2)


def convex_hull_ratio(area: float, hull_area: float) -> float:
    if hull_area <= 0:
        return np.nan
    return area / hull_area


def reock_score(area: float, points: list[tuple[float, float]]) -> float:
    circle = make_circle(points)
    if circle is None:
        return np.nan

    _, _, radius = circle
    circle_area = math.pi * radius * radius
    if circle_area <= 0:
        return np.nan
    return area / circle_area


def compute_metrics_for_geometry(geom) -> dict[str, float]:
    area = geom.area
    perimeter = geom.length
    hull = geom.convex_hull
    hull_area = hull.area
    points = boundary_points(geom)

    pp = polsby_popper(area, perimeter)
    ch = convex_hull_ratio(area, hull_area)
    reock = reock_score(area, points)

    return {
        "area": area,
        "perimeter": perimeter,
        "convex_hull_area": hull_area,
        "polsby_popper": pp,
        "reock": reock,
        "convex_hull_ratio": ch,
    }


def metric_rank_columns(df: pd.DataFrame) -> pd.DataFrame:
    for metric in ["polsby_popper", "reock", "convex_hull_ratio"]:
        df[f"{metric}_rank"] = df[metric].rank(ascending=False, method="min").astype(int)
    return df


# -------------------------------------------------------------------
# State analysis
# -------------------------------------------------------------------

def analyze_state(state_code: str, state_name: str) -> gpd.GeoDataFrame:
    precincts = load_precinct_data(state_code, state_name)
    districts = build_district_geometries(precincts)

    metric_rows = []
    for _, row in districts.iterrows():
        metrics = compute_metrics_for_geometry(row.geometry)
        metric_rows.append(metrics)

    metrics_df = pd.DataFrame(metric_rows)
    result = districts.join(metrics_df)
    result["state_code"] = state_code.upper()
    result["state"] = state_name
    result = metric_rank_columns(result)

    return result


# -------------------------------------------------------------------
# Plots
# -------------------------------------------------------------------

def add_horizontal_colorbar(fig, cmap, norm, left, bottom, width, height, label):
    cax = fig.add_axes([left, bottom, width, height])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=8, colors=COLORS["muted"])
    cb.set_label(label, fontsize=9, color=COLORS["muted"])
    return cb


def plot_metric_gallery(state_df: gpd.GeoDataFrame, state_code: str, state_name: str) -> Path:
    output = FIGURE_DIR / f"{state_code}_compactness_gallery.png"

    n = len(state_df)
    cols = 4
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(16, 4.3 * rows))
    fig.patch.set_facecolor(COLORS["paper"])

    if rows == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    cmap = plt.cm.Blues
    norm = Normalize(
        vmin=float(state_df["polsby_popper"].min()),
        vmax=float(state_df["polsby_popper"].max()),
    )

    for ax, (_, row) in zip(axes, state_df.iterrows()):
        gpd.GeoSeries([row.geometry], crs=state_df.crs).plot(
            ax=ax,
            color=cmap(norm(row["polsby_popper"])),
            edgecolor=COLORS["ink"],
            linewidth=1.2,
        )

        ax.set_title(
            f"District {row[DISTRICT_COLUMN]}",
            fontsize=13,
            pad=8,
            loc="left",
        )

        text = (
            f"Polsby–Popper: {row['polsby_popper']:.3f}\n"
            f"Reock: {row['reock']:.3f}\n"
            f"Convex-hull ratio: {row['convex_hull_ratio']:.3f}"
        )

        ax.text(
            0.02,
            0.02,
            text,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9,
            color=COLORS["ink"],
            bbox={
                "boxstyle": "round,pad=0.30",
                "facecolor": COLORS["white"],
                "edgecolor": COLORS["grid"],
                "linewidth": 0.8,
                "alpha": 0.95,
            },
        )

        ax.set_axis_off()
        ax.set_aspect("equal", adjustable="box")

    for ax in axes[n:]:
        ax.axis("off")

    fig.suptitle(
        f"{state_name} enacted districts — compactness gallery",
        fontsize=22,
        fontweight="bold",
        x=0.05,
        ha="left",
        y=0.985,
    )

    fig.text(
        0.05,
        0.95,
        "Each district is annotated with three shape metrics computed from its enacted geometry.",
        fontsize=10,
        color=COLORS["muted"],
    )

    add_horizontal_colorbar(
        fig,
        cmap=cmap,
        norm=norm,
        left=0.32,
        bottom=0.03,
        width=0.36,
        height=0.018,
        label="Polsby–Popper score",
    )

    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_metric_bars(state_df: gpd.GeoDataFrame, state_code: str, state_name: str) -> Path:
    output = FIGURE_DIR / f"{state_code}_compactness_bar_comparison.png"

    ordered = state_df.copy()
    ordered["district_label"] = "D" + ordered[DISTRICT_COLUMN].astype(str)

    x = np.arange(len(ordered))
    width = 0.24

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(COLORS["paper"])
    ax.set_facecolor(COLORS["white"])

    ax.bar(
        x - width,
        ordered["polsby_popper"],
        width=width,
        label="Polsby–Popper",
        edgecolor=COLORS["blue"],
        linewidth=1.3,
        color=COLORS["blue_light"],
    )
    ax.bar(
        x,
        ordered["reock"],
        width=width,
        label="Reock",
        edgecolor=COLORS["purple"],
        linewidth=1.3,
        color="#EEE7FF",
    )
    ax.bar(
        x + width,
        ordered["convex_hull_ratio"],
        width=width,
        label="Convex-hull ratio",
        edgecolor=COLORS["teal"],
        linewidth=1.3,
        color="#DFF7EB",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(ordered["district_label"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title(
        f"{state_name} compactness metric comparison",
        loc="left",
        fontsize=20,
        pad=18,
    )
    ax.text(
        0,
        1.01,
        "Different compactness metrics can rank the same districts differently.",
        transform=ax.transAxes,
        fontsize=10,
        color=COLORS["muted"],
    )

    ax.grid(axis="y", color=COLORS["grid"], linewidth=0.9, alpha=0.75)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(frameon=False, ncol=3, loc="upper right")

    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


# -------------------------------------------------------------------
# Stress tests
# -------------------------------------------------------------------

def jagged_rectangle(width=12.0, height=4.0, teeth=24, amplitude=0.55) -> Polygon:
    coords = [(0, 0), (width, 0)]
    step = height / teeth
    y = 0.0
    for i in range(teeth):
        y_next = min(height, y + step)
        x = width + (amplitude if i % 2 == 0 else 0.0)
        coords.append((x, y))
        coords.append((width, y_next))
        y = y_next
    coords.extend([(0, height), (0, 0)])
    return Polygon(coords).buffer(0)


def coastline_hugger(width=13.0, height=3.2, wiggles=40, amplitude=0.45) -> Polygon:
    top = []
    for i in range(wiggles + 1):
        x = width * i / wiggles
        y = height + amplitude * math.sin(i * 0.6) + 0.12 * math.sin(i * 2.3)
        top.append((x, y))
    coords = [(0, 0), (width, 0)] + list(reversed(top)) + [(0, 0)]
    return Polygon(coords).buffer(0)


def long_thin_rectangle() -> Polygon:
    return box(0, 0, 18, 1.6)


def smooth_square() -> Polygon:
    return box(0, 0, 8, 8)


def make_stress_test_geometries() -> list[tuple[str, Polygon, str]]:
    coast = coastline_hugger()
    coast_jagged = jagged_rectangle(width=12.5, height=3.0, teeth=28, amplitude=0.55)
    coast_jagged = translate(coast_jagged, xoff=0.0, yoff=0.0)

    return [
        (
            "Long thin rectangle",
            long_thin_rectangle(),
            "Hull ratio stays high, but Polsby–Popper and Reock punish elongation.",
        ),
        (
            "Smooth coastline-hugger",
            coast,
            "Follows a wavy edge; perimeter grows while hull remains similar.",
        ),
        (
            "Jagged coastline / fractal-ish boundary",
            coast_jagged,
            "Polsby–Popper drops sharply because perimeter explodes.",
        ),
        (
            "Simple square",
            smooth_square(),
            "Reference shape: compact under all three metrics.",
        ),
    ]


def analyze_stress_tests() -> gpd.GeoDataFrame:
    rows = []
    geoms = []

    for name, geom, note in make_stress_test_geometries():
        metrics = compute_metrics_for_geometry(geom)
        rows.append(
            {
                "shape": name,
                "note": note,
                "polsby_popper": metrics["polsby_popper"],
                "reock": metrics["reock"],
                "convex_hull_ratio": metrics["convex_hull_ratio"],
            }
        )
        geoms.append(geom)

    gdf = gpd.GeoDataFrame(rows, geometry=geoms, crs="EPSG:3857")
    return gdf


def plot_stress_tests(stress_gdf: gpd.GeoDataFrame) -> Path:
    output = FIGURE_DIR / "compactness_stress_tests.png"

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.patch.set_facecolor(COLORS["paper"])
    axes = axes.flatten()

    for ax, (_, row) in zip(axes, stress_gdf.iterrows()):
        gpd.GeoSeries([row.geometry], crs=stress_gdf.crs).plot(
            ax=ax,
            color=COLORS["blue_light"],
            edgecolor=COLORS["ink"],
            linewidth=1.4,
        )
        ax.set_title(row["shape"], loc="left", fontsize=14, pad=10)

        text = (
            f"PP = {row['polsby_popper']:.3f}\n"
            f"Reock = {row['reock']:.3f}\n"
            f"Hull = {row['convex_hull_ratio']:.3f}\n\n"
            f"{row['note']}"
        )
        ax.text(
            0.02,
            0.02,
            text,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.30",
                "facecolor": COLORS["white"],
                "edgecolor": COLORS["grid"],
                "alpha": 0.96,
            },
        )

        ax.set_axis_off()
        ax.set_aspect("equal", adjustable="box")

    fig.suptitle(
        "Week 2 stress tests — when compactness metrics disagree",
        fontsize=22,
        fontweight="bold",
        x=0.05,
        ha="left",
        y=0.98,
    )
    fig.text(
        0.05,
        0.945,
        "This illustrates why compactness is useful vocabulary but not a complete fairness standard.",
        fontsize=10,
        color=COLORS["muted"],
    )

    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


# -------------------------------------------------------------------
# Save tables / report
# -------------------------------------------------------------------

def save_state_tables(state_df: gpd.GeoDataFrame, state_code: str) -> list[Path]:
    metric_cols = [
        DISTRICT_COLUMN,
        "state_code",
        "state",
        "area",
        "perimeter",
        "convex_hull_area",
        "polsby_popper",
        "reock",
        "convex_hull_ratio",
        "polsby_popper_rank",
        "reock_rank",
        "convex_hull_ratio_rank",
    ]

    csv_path = TABLE_DIR / f"{state_code}_compactness_metrics.csv"
    state_df[metric_cols].to_csv(csv_path, index=False)

    geojson_path = TABLE_DIR / f"{state_code}_compactness_metrics.geojson"
    state_df[metric_cols + ["geometry"]].to_file(geojson_path, driver="GeoJSON")

    return [csv_path, geojson_path]


def rank_summary_lines(state_df: pd.DataFrame, state_name: str) -> list[str]:
    lines = [f"## {state_name}", ""]
    for metric, label in [
        ("polsby_popper", "Polsby–Popper"),
        ("reock", "Reock"),
        ("convex_hull_ratio", "Convex-hull ratio"),
    ]:
        best = state_df.loc[state_df[metric].idxmax()]
        worst = state_df.loc[state_df[metric].idxmin()]
        lines.append(
            f"- **{label}**: highest = District {best[DISTRICT_COLUMN]} "
            f"({best[metric]:.3f}); lowest = District {worst[DISTRICT_COLUMN]} "
            f"({worst[metric]:.3f})"
        )
    lines.append("")
    return lines


def write_report(state_frames: dict[str, gpd.GeoDataFrame], stress_gdf: gpd.GeoDataFrame) -> Path:
    output = REPORT_DIR / "week2_compactness_summary.md"

    lines = [
        "# Week 2 — The geometry of compactness",
        "",
        "## Metrics implemented",
        "",
        "- **Polsby–Popper** = 4πA / P²",
        "- **Reock** = area / area of smallest enclosing circle",
        "- **Convex-hull ratio** = area / area of convex hull",
        "",
        "## Core lesson",
        "",
        "Compactness metrics do not measure the same geometric defect. "
        "Polsby–Popper is extremely sensitive to perimeter inflation, Reock punishes "
        "elongated districts because the enclosing circle grows, and convex-hull ratio "
        "mostly punishes concavity while ignoring some boundary wiggles.",
        "",
    ]

    for code in ["mi", "mo"]:
        lines.extend(rank_summary_lines(state_frames[code], STATES[code]))

    lines.extend(
        [
            "## Stress test interpretation",
            "",
        ]
    )

    for _, row in stress_gdf.iterrows():
        lines.append(
            f"- **{row['shape']}** → PP = {row['polsby_popper']:.3f}, "
            f"Reock = {row['reock']:.3f}, hull ratio = {row['convex_hull_ratio']:.3f}. "
            f"{row['note']}"
        )

    lines.extend(
        [
            "",
            "## Resolution / coastline paradox note",
            "",
            "The jagged coastline example shows why Polsby–Popper is resolution-dependent: "
            "adding more boundary detail increases perimeter without necessarily changing area very much. "
            "That can sharply lower Polsby–Popper even when the overall district footprint looks similar.",
            "",
            "## Validation note",
            "",
            "If you later pull published values from Dave’s Redistricting App for the same districts, "
            "you can compare them directly against the CSV outputs generated here.",
            "",
        ]
    )

    output.write_text("\n".join(lines), encoding="utf-8")
    return output


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:
    set_style()
    ensure_directories()

    generated: list[Path] = []
    state_frames: dict[str, gpd.GeoDataFrame] = {}

    for state_code, state_name in STATES.items():
        print("\n" + "=" * 72)
        print(f"PROCESSING {state_name.upper()}")
        print("=" * 72)

        state_df = analyze_state(state_code, state_name)
        state_frames[state_code] = state_df

        generated.extend(save_state_tables(state_df, state_code))
        generated.append(plot_metric_gallery(state_df, state_code, state_name))
        generated.append(plot_metric_bars(state_df, state_code, state_name))

    combined = pd.concat(
        [
            state_frames["mi"].drop(columns="geometry"),
            state_frames["mo"].drop(columns="geometry"),
        ],
        ignore_index=True,
    )
    combined_csv = TABLE_DIR / "mi_mo_compactness_metrics.csv"
    combined.to_csv(combined_csv, index=False)
    generated.append(combined_csv)

    stress_gdf = analyze_stress_tests()
    stress_csv = TABLE_DIR / "compactness_stress_tests.csv"
    stress_gdf.drop(columns="geometry").to_csv(stress_csv, index=False)
    generated.append(stress_csv)
    generated.append(plot_stress_tests(stress_gdf))

    report = write_report(state_frames, stress_gdf)
    generated.append(report)

    print("\n" + "=" * 72)
    print("GENERATED OUTPUTS")
    print("=" * 72)
    for path in generated:
        print(path.relative_to(PROJECT_ROOT))

    print("\nWEEK 2 COMPACTNESS ANALYSIS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nFAILED: {type(error).__name__}: {error}", file=sys.stderr)
        raise