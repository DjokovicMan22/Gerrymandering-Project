from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "week1"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week1"

STATES = {
    "mi": "Michigan",
    "mo": "Missouri",
}

DISTRICT_COLUMN = "CD"
DEM_COLUMN = "PRE20D"
REP_COLUMN = "PRE20R"

REQUIRED_COLUMNS = [
    DISTRICT_COLUMN,
    DEM_COLUMN,
    REP_COLUMN,
]


def find_shapefile(state_code: str) -> Path:
    state_folder = RAW_DIR / state_code

    if not state_folder.exists():
        raise FileNotFoundError(
            f"State data folder does not exist: {state_folder}"
        )

    shapefiles = list(state_folder.rglob("*.shp"))

    if not shapefiles:
        raise FileNotFoundError(
            f"No shapefile found under: {state_folder}"
        )

    exact_matches = [
        path
        for path in shapefiles
        if path.stem.lower() == state_code.lower()
    ]

    selected = exact_matches[0] if exact_matches else shapefiles[0]

    print(f"Found {state_code.upper()} shapefile: {selected}", flush=True)
    return selected


def load_state_data(
    state_code: str,
    state_name: str,
) -> gpd.GeoDataFrame:
    shapefile = find_shapefile(state_code)

    print(f"Loading {state_name}...", flush=True)

    gdf = gpd.read_file(shapefile)

    if gdf.empty:
        raise ValueError(
            f"{state_name} shapefile contains no rows."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in gdf.columns
    ]

    if missing_columns:
        raise KeyError(
            f"{state_name} is missing columns: {missing_columns}\n"
            f"Available columns:\n{gdf.columns.tolist()}"
        )

    gdf = gdf.copy()

    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    gdf[DEM_COLUMN] = pd.to_numeric(
        gdf[DEM_COLUMN],
        errors="coerce",
    ).fillna(0)

    gdf[REP_COLUMN] = pd.to_numeric(
        gdf[REP_COLUMN],
        errors="coerce",
    ).fillna(0)

    gdf[DISTRICT_COLUMN] = (
        gdf[DISTRICT_COLUMN]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    invalid_district_values = {
        "",
        "nan",
        "None",
        "null",
        "0",
    }

    gdf = gdf[
        ~gdf[DISTRICT_COLUMN].isin(invalid_district_values)
    ].copy()

    gdf = gdf.reset_index(drop=True)

    if gdf.crs is None:
        raise ValueError(
            f"{state_name} shapefile has no CRS."
        )

    if gdf.crs.is_geographic:
        projected_crs = gdf.estimate_utm_crs()

        if projected_crs is None:
            raise ValueError(
                f"Could not determine projected CRS for {state_name}."
            )

        print(
            f"Projecting {state_name} to {projected_crs}...",
            flush=True,
        )

        gdf = gdf.to_crs(projected_crs)

    print(
        f"Loaded {len(gdf):,} precincts across "
        f"{gdf[DISTRICT_COLUMN].nunique()} congressional districts.",
        flush=True,
    )

    return gdf


def district_sort_key(value: str) -> tuple[int, str]:
    try:
        return int(value), value
    except ValueError:
        return 10**9, value


def calculate_district_results(
    gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    district_results = (
        gdf.groupby(DISTRICT_COLUMN, as_index=False)
        .agg(
            dem_votes=(DEM_COLUMN, "sum"),
            rep_votes=(REP_COLUMN, "sum"),
            precinct_count=(DISTRICT_COLUMN, "size"),
        )
    )

    district_results["two_party_votes"] = (
        district_results["dem_votes"]
        + district_results["rep_votes"]
    )

    district_results["dem_vote_share"] = (
        district_results["dem_votes"]
        / district_results["two_party_votes"].where(
            district_results["two_party_votes"] > 0
        )
    )

    district_results["rep_vote_share"] = (
        district_results["rep_votes"]
        / district_results["two_party_votes"].where(
            district_results["two_party_votes"] > 0
        )
    )

    district_results["winner"] = "Tie"

    district_results.loc[
        district_results["dem_votes"]
        > district_results["rep_votes"],
        "winner",
    ] = "Democratic"

    district_results.loc[
        district_results["rep_votes"]
        > district_results["dem_votes"],
        "winner",
    ] = "Republican"

    district_results["dem_margin_votes"] = (
        district_results["dem_votes"]
        - district_results["rep_votes"]
    )

    district_results["dem_margin_pct"] = (
        district_results["dem_vote_share"] - 0.5
    ) * 100

    ordered_districts = sorted(
        district_results[DISTRICT_COLUMN].tolist(),
        key=district_sort_key,
    )

    district_order = {
        district: index
        for index, district in enumerate(ordered_districts)
    }

    district_results["_sort_order"] = (
        district_results[DISTRICT_COLUMN]
        .map(district_order)
    )

    district_results = (
        district_results
        .sort_values("_sort_order")
        .drop(columns="_sort_order")
        .reset_index(drop=True)
    )

    return district_results


def calculate_state_summary(
    state_code: str,
    state_name: str,
    district_results: pd.DataFrame,
) -> pd.DataFrame:
    total_dem_votes = district_results["dem_votes"].sum()
    total_rep_votes = district_results["rep_votes"].sum()
    total_two_party_votes = total_dem_votes + total_rep_votes

    if total_two_party_votes <= 0:
        raise ValueError(
            f"{state_name} has no valid two-party presidential votes."
        )

    total_districts = len(district_results)

    democratic_seats = int(
        (district_results["winner"] == "Democratic").sum()
    )

    republican_seats = int(
        (district_results["winner"] == "Republican").sum()
    )

    tied_seats = int(
        (district_results["winner"] == "Tie").sum()
    )

    democratic_vote_share = total_dem_votes / total_two_party_votes
    republican_vote_share = total_rep_votes / total_two_party_votes

    democratic_seat_share = democratic_seats / total_districts
    republican_seat_share = republican_seats / total_districts

    democratic_gap = (
        democratic_seat_share
        - democratic_vote_share
    )

    republican_gap = (
        republican_seat_share
        - republican_vote_share
    )

    summary = pd.DataFrame(
        [
            {
                "state_code": state_code.upper(),
                "state": state_name,
                "election": "2020 Presidential",
                "dem_votes": int(total_dem_votes),
                "rep_votes": int(total_rep_votes),
                "two_party_votes": int(total_two_party_votes),
                "dem_vote_share": democratic_vote_share,
                "rep_vote_share": republican_vote_share,
                "total_districts": total_districts,
                "dem_seats": democratic_seats,
                "rep_seats": republican_seats,
                "tied_seats": tied_seats,
                "dem_seat_share": democratic_seat_share,
                "rep_seat_share": republican_seat_share,
                "dem_representation_gap": democratic_gap,
                "rep_representation_gap": republican_gap,
                "dem_vote_share_pct": democratic_vote_share * 100,
                "rep_vote_share_pct": republican_vote_share * 100,
                "dem_seat_share_pct": democratic_seat_share * 100,
                "rep_seat_share_pct": republican_seat_share * 100,
                "dem_representation_gap_pp": democratic_gap * 100,
                "rep_representation_gap_pp": republican_gap * 100,
            }
        ]
    )

    return summary


def build_district_geodataframe(
    gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    district_map = (
        gdf[
            [
                DISTRICT_COLUMN,
                DEM_COLUMN,
                REP_COLUMN,
                "geometry",
            ]
        ]
        .dissolve(
            by=DISTRICT_COLUMN,
            aggfunc={
                DEM_COLUMN: "sum",
                REP_COLUMN: "sum",
            },
        )
        .reset_index()
    )

    district_map["two_party_votes"] = (
        district_map[DEM_COLUMN]
        + district_map[REP_COLUMN]
    )

    district_map["dem_vote_share"] = (
        district_map[DEM_COLUMN]
        / district_map["two_party_votes"].where(
            district_map["two_party_votes"] > 0
        )
    )

    district_map["rep_vote_share"] = (
        district_map[REP_COLUMN]
        / district_map["two_party_votes"].where(
            district_map["two_party_votes"] > 0
        )
    )

    district_map["winner"] = "Tie"

    district_map.loc[
        district_map[DEM_COLUMN]
        > district_map[REP_COLUMN],
        "winner",
    ] = "Democratic"

    district_map.loc[
        district_map[REP_COLUMN]
        > district_map[DEM_COLUMN],
        "winner",
    ] = "Republican"

    return district_map


def plot_district_vote_share_map(
    district_map: gpd.GeoDataFrame,
    state_code: str,
    state_name: str,
) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        FIGURE_DIR
        / f"{state_code}_congressional_vote_share.png"
    )

    fig, ax = plt.subplots(
        figsize=(12, 12),
        facecolor="white",
    )

    district_map.plot(
        ax=ax,
        column="dem_vote_share",
        cmap="RdBu",
        vmin=0,
        vmax=1,
        edgecolor="#111827",
        linewidth=1.5,
        legend=True,
        legend_kwds={
            "label": "Democratic two-party presidential vote share",
            "shrink": 0.72,
        },
    )

    for _, row in district_map.iterrows():
        point = row.geometry.representative_point()

        district_number = str(row[DISTRICT_COLUMN])
        democratic_percentage = row["dem_vote_share"] * 100

        label = (
            f"{district_number}\n"
            f"{democratic_percentage:.1f}% D"
        )

        ax.text(
            point.x,
            point.y,
            label,
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#111827",
            zorder=5,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "edgecolor": "#4B5563",
                "linewidth": 0.6,
                "alpha": 0.88,
            },
        )

    ax.set_title(
        (
            f"{state_name} Congressional Districts\n"
            "2020 Presidential Two-Party Vote Share"
        ),
        fontsize=18,
        fontweight="bold",
        pad=18,
    )

    ax.text(
        0.5,
        0.015,
        (
            "District presidential vote totals were calculated by "
            "aggregating precinct-level PRE20D and PRE20R votes."
        ),
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=9,
    )

    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=350,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    print(f"Saved map: {output_path}", flush=True)
    return output_path


def plot_vote_seat_comparison(
    summary: pd.DataFrame,
    state_code: str,
    state_name: str,
) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = (
        FIGURE_DIR
        / f"{state_code}_vote_seat_comparison.png"
    )

    row = summary.iloc[0]

    categories = [
        "Democratic",
        "Republican",
    ]

    vote_shares = [
        row["dem_vote_share_pct"],
        row["rep_vote_share_pct"],
    ]

    seat_shares = [
        row["dem_seat_share_pct"],
        row["rep_seat_share_pct"],
    ]

    x_positions = [0, 1]
    bar_width = 0.34

    fig, ax = plt.subplots(
        figsize=(9, 7),
        facecolor="white",
    )

    vote_bars = ax.bar(
        [position - bar_width / 2 for position in x_positions],
        vote_shares,
        width=bar_width,
        label="Presidential vote share",
        edgecolor="#111827",
        linewidth=0.7,
    )

    seat_bars = ax.bar(
        [position + bar_width / 2 for position in x_positions],
        seat_shares,
        width=bar_width,
        label="Congressional seat share",
        edgecolor="#111827",
        linewidth=0.7,
    )

    for bar in list(vote_bars) + list(seat_bars):
        height = bar.get_height()

        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 1,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    ax.axhline(
        50,
        color="#6B7280",
        linewidth=1,
        linestyle="--",
        alpha=0.8,
    )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(categories)

    ax.set_ylim(
        0,
        max(max(vote_shares), max(seat_shares)) + 12,
    )

    ax.set_ylabel("Share (%)")

    ax.set_title(
        (
            f"{state_name}: Presidential Vote Share\n"
            "Compared with Congressional Seat Share"
        ),
        fontsize=16,
        fontweight="bold",
        pad=14,
    )

    ax.grid(
        axis="y",
        alpha=0.22,
        linewidth=0.8,
    )

    ax.legend(
        frameon=False,
        loc="upper center",
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    print(f"Saved comparison chart: {output_path}", flush=True)
    return output_path


def save_tables(
    state_code: str,
    district_results: pd.DataFrame,
    state_summary: pd.DataFrame,
) -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    district_path = (
        TABLE_DIR
        / f"{state_code}_district_vote_results.csv"
    )

    summary_path = (
        TABLE_DIR
        / f"{state_code}_vote_seat_comparison.csv"
    )

    district_results.to_csv(
        district_path,
        index=False,
    )

    state_summary.to_csv(
        summary_path,
        index=False,
    )

    print(f"Saved table: {district_path}", flush=True)
    print(f"Saved table: {summary_path}", flush=True)


def process_state(
    state_code: str,
    state_name: str,
) -> pd.DataFrame:
    print("\n" + "=" * 72, flush=True)
    print(f"PROCESSING {state_name.upper()}", flush=True)
    print("=" * 72, flush=True)

    gdf = load_state_data(
        state_code,
        state_name,
    )

    district_results = calculate_district_results(gdf)

    state_summary = calculate_state_summary(
        state_code,
        state_name,
        district_results,
    )

    district_map = build_district_geodataframe(gdf)

    save_tables(
        state_code,
        district_results,
        state_summary,
    )

    plot_district_vote_share_map(
        district_map,
        state_code,
        state_name,
    )

    plot_vote_seat_comparison(
        state_summary,
        state_code,
        state_name,
    )

    row = state_summary.iloc[0]

    print(
        f"\n{state_name} results:",
        flush=True,
    )

    print(
        f"Democratic presidential vote share: "
        f"{row['dem_vote_share_pct']:.2f}%",
        flush=True,
    )

    print(
        f"Republican presidential vote share: "
        f"{row['rep_vote_share_pct']:.2f}%",
        flush=True,
    )

    print(
        f"Democratic seats: "
        f"{int(row['dem_seats'])} of "
        f"{int(row['total_districts'])}",
        flush=True,
    )

    print(
        f"Republican seats: "
        f"{int(row['rep_seats'])} of "
        f"{int(row['total_districts'])}",
        flush=True,
    )

    print(
        f"Democratic representation gap: "
        f"{row['dem_representation_gap_pp']:+.2f} percentage points",
        flush=True,
    )

    print(
        f"Republican representation gap: "
        f"{row['rep_representation_gap_pp']:+.2f} percentage points",
        flush=True,
    )

    return state_summary


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}", flush=True)
    print(f"Raw-data directory: {RAW_DIR}", flush=True)
    print(f"Figure directory: {FIGURE_DIR}", flush=True)
    print(f"Table directory: {TABLE_DIR}", flush=True)

    FIGURE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TABLE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summaries: list[pd.DataFrame] = []
    failures: list[str] = []

    for state_code, state_name in STATES.items():
        try:
            summary = process_state(
                state_code,
                state_name,
            )

            summaries.append(summary)

        except Exception as error:
            failures.append(state_code)

            print(
                f"\nFAILED FOR {state_name}: "
                f"{type(error).__name__}: {error}",
                file=sys.stderr,
                flush=True,
            )

    if summaries:
        combined_summary = pd.concat(
            summaries,
            ignore_index=True,
        )

        combined_path = (
            TABLE_DIR
            / "mi_mo_vote_seat_comparison.csv"
        )

        combined_summary.to_csv(
            combined_path,
            index=False,
        )

        print(
            f"\nSaved combined table: {combined_path}",
            flush=True,
        )

        display_columns = [
            "state",
            "dem_vote_share_pct",
            "rep_vote_share_pct",
            "dem_seats",
            "rep_seats",
            "dem_seat_share_pct",
            "rep_seat_share_pct",
            "dem_representation_gap_pp",
            "rep_representation_gap_pp",
        ]

        print("\nCOMBINED RESULTS", flush=True)
        print(
            combined_summary[display_columns].to_string(
                index=False,
                float_format=lambda value: f"{value:.2f}",
            ),
            flush=True,
        )

    if failures:
        raise RuntimeError(
            "Analysis failed for: "
            + ", ".join(
                code.upper()
                for code in failures
            )
        )

    print(
        "\nVOTE-SEAT ANALYSIS COMPLETED SUCCESSFULLY",
        flush=True,
    )


if __name__ == "__main__":
    main()