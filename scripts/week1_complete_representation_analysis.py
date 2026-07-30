from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "week1"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week1"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports" / "week1"

DISTRICT_COLUMN = "CD"
DEM_COLUMN = "PRE20D"
REP_COLUMN = "PRE20R"

# Actual U.S. House delegation after the 2022 election, the first election
# under the post-2020 congressional maps represented by these datasets.
STATES = {
    "mi": {
        "name": "Michigan",
        "actual_dem_seats": 7,
        "actual_rep_seats": 6,
        "actual_election": "2022 U.S. House",
    },
    "mo": {
        "name": "Missouri",
        "actual_dem_seats": 2,
        "actual_rep_seats": 6,
        "actual_election": "2022 U.S. House",
    },
}

COLORS = {
    "ink": "#172033",
    "muted": "#667085",
    "grid": "#D9E0EA",
    "paper": "#F7F9FC",
    "white": "#FFFFFF",
    "dem": "#2F6FED",
    "dem_light": "#DCE8FF",
    "rep": "#D94B45",
    "rep_light": "#FBE1DF",
    "accent": "#7A5AF8",
}

PARTY_CMAP = LinearSegmentedColormap.from_list(
    "party_balance",
    [
        (0.00, "#A50026"),
        (0.35, "#EF8A62"),
        (0.50, "#F7F7F7"),
        (0.65, "#67A9CF"),
        (1.00, "#2166AC"),
    ],
)


def ensure_output_directories() -> None:
    for folder in (FIGURE_DIR, TABLE_DIR, REPORT_DIR):
        current = PROJECT_ROOT
        for part in folder.relative_to(PROJECT_ROOT).parts:
            current = current / part
            if current.exists() and not current.is_dir():
                raise NotADirectoryError(
                    f"{current} exists as a file, but this project needs it to be a folder.\n"
                    f"Rename it with:\n"
                    f"mv '{current}' '{current}_old_file'"
                )
        folder.mkdir(parents=True, exist_ok=True)


def set_modern_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 18,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelcolor": COLORS["ink"],
            "axes.edgecolor": COLORS["grid"],
            "axes.facecolor": COLORS["white"],
            "figure.facecolor": COLORS["paper"],
            "xtick.color": COLORS["muted"],
            "ytick.color": COLORS["muted"],
            "text.color": COLORS["ink"],
            "savefig.facecolor": COLORS["paper"],
        }
    )


def find_shapefile(state_code: str) -> Path:
    state_folder = RAW_DIR / state_code
    if not state_folder.exists():
        raise FileNotFoundError(f"Missing state folder: {state_folder}")

    shapefiles = list(state_folder.rglob("*.shp"))
    if not shapefiles:
        raise FileNotFoundError(f"No shapefile found under: {state_folder}")

    exact = [path for path in shapefiles if path.stem.lower() == state_code.lower()]
    selected = exact[0] if exact else shapefiles[0]
    print(f"Found {state_code.upper()} shapefile: {selected}", flush=True)
    return selected


def clean_district_ids(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def load_state_data(state_code: str, state_name: str) -> gpd.GeoDataFrame:
    shapefile = find_shapefile(state_code)
    gdf = gpd.read_file(shapefile)

    required = {DISTRICT_COLUMN, DEM_COLUMN, REP_COLUMN, "geometry"}
    missing = sorted(required - set(gdf.columns))
    if missing:
        raise KeyError(
            f"{state_name} is missing required columns: {missing}\n"
            f"Available columns: {gdf.columns.tolist()}"
        )

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    gdf[DEM_COLUMN] = pd.to_numeric(gdf[DEM_COLUMN], errors="coerce").fillna(0)
    gdf[REP_COLUMN] = pd.to_numeric(gdf[REP_COLUMN], errors="coerce").fillna(0)
    gdf[DISTRICT_COLUMN] = clean_district_ids(gdf[DISTRICT_COLUMN])

    invalid_ids = {"", "nan", "None", "null", "0"}
    gdf = gdf[~gdf[DISTRICT_COLUMN].isin(invalid_ids)].copy().reset_index(drop=True)

    if gdf.crs is None:
        raise ValueError(f"{state_name} shapefile has no CRS.")

    if gdf.crs.is_geographic:
        projected = gdf.estimate_utm_crs()
        if projected is None:
            raise ValueError(f"Could not estimate a projected CRS for {state_name}.")
        gdf = gdf.to_crs(projected)

    total = gdf[DEM_COLUMN] + gdf[REP_COLUMN]
    gdf["dem_share"] = (gdf[DEM_COLUMN] / total.where(total > 0)).fillna(0.5)

    print(
        f"Loaded {len(gdf):,} precincts and "
        f"{gdf[DISTRICT_COLUMN].nunique()} districts for {state_name}.",
        flush=True,
    )
    return gdf


def district_sort_key(value: str) -> tuple[int, str]:
    try:
        return int(value), value
    except ValueError:
        return 10**9, value


def aggregate_districts(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    districts = (
        gdf[[DISTRICT_COLUMN, DEM_COLUMN, REP_COLUMN, "geometry"]]
        .dissolve(
            by=DISTRICT_COLUMN,
            aggfunc={DEM_COLUMN: "sum", REP_COLUMN: "sum"},
        )
        .reset_index()
    )

    districts["two_party_votes"] = districts[DEM_COLUMN] + districts[REP_COLUMN]
    districts["dem_share"] = (
        districts[DEM_COLUMN]
        / districts["two_party_votes"].where(districts["two_party_votes"] > 0)
    ).fillna(0.5)
    districts["rep_share"] = 1 - districts["dem_share"]
    districts["presidential_winner"] = np.where(
        districts["dem_share"] > 0.5,
        "Democratic",
        np.where(districts["dem_share"] < 0.5, "Republican", "Tie"),
    )
    districts["dem_margin_pp"] = (districts["dem_share"] - 0.5) * 100

    order = sorted(districts[DISTRICT_COLUMN].tolist(), key=district_sort_key)
    lookup = {district: index for index, district in enumerate(order)}
    districts["_sort"] = districts[DISTRICT_COLUMN].map(lookup)
    return districts.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)


def calculate_summary(
    state_code: str,
    config: dict,
    gdf: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
) -> pd.DataFrame:
    dem_votes = float(gdf[DEM_COLUMN].sum())
    rep_votes = float(gdf[REP_COLUMN].sum())
    two_party_votes = dem_votes + rep_votes

    if two_party_votes <= 0:
        raise ValueError(f"{config['name']} has no valid two-party votes.")

    dem_vote_share = dem_votes / two_party_votes
    rep_vote_share = rep_votes / two_party_votes

    actual_dem_seats = int(config["actual_dem_seats"])
    actual_rep_seats = int(config["actual_rep_seats"])
    total_seats = actual_dem_seats + actual_rep_seats
    actual_dem_share = actual_dem_seats / total_seats
    actual_rep_share = actual_rep_seats / total_seats

    presidential_dem_wins = int((districts["presidential_winner"] == "Democratic").sum())
    presidential_rep_wins = int((districts["presidential_winner"] == "Republican").sum())
    presidential_ties = int((districts["presidential_winner"] == "Tie").sum())

    return pd.DataFrame(
        [
            {
                "state_code": state_code.upper(),
                "state": config["name"],
                "presidential_election": "2020 Presidential",
                "house_election": config["actual_election"],
                "dem_presidential_votes": int(dem_votes),
                "rep_presidential_votes": int(rep_votes),
                "two_party_presidential_votes": int(two_party_votes),
                "dem_presidential_vote_share_pct": dem_vote_share * 100,
                "rep_presidential_vote_share_pct": rep_vote_share * 100,
                "actual_dem_house_seats": actual_dem_seats,
                "actual_rep_house_seats": actual_rep_seats,
                "actual_total_house_seats": total_seats,
                "actual_dem_house_seat_share_pct": actual_dem_share * 100,
                "actual_rep_house_seat_share_pct": actual_rep_share * 100,
                "actual_dem_representation_gap_pp": (actual_dem_share - dem_vote_share) * 100,
                "actual_rep_representation_gap_pp": (actual_rep_share - rep_vote_share) * 100,
                "presidential_dem_district_wins": presidential_dem_wins,
                "presidential_rep_district_wins": presidential_rep_wins,
                "presidential_tied_districts": presidential_ties,
                "presidential_dem_district_share_pct": presidential_dem_wins / len(districts) * 100,
                "presidential_rep_district_share_pct": presidential_rep_wins / len(districts) * 100,
            }
        ]
    )


def add_horizontal_colorbar(fig: plt.Figure) -> None:
    cax = fig.add_axes([0.26, 0.065, 0.48, 0.018])
    mapper = plt.cm.ScalarMappable(
        cmap=PARTY_CMAP,
        norm=TwoSlopeNorm(vmin=0.20, vcenter=0.50, vmax=0.80),
    )
    mapper.set_array([])
    colorbar = fig.colorbar(mapper, cax=cax, orientation="horizontal")
    colorbar.set_ticks([0.2, 0.35, 0.5, 0.65, 0.8])
    colorbar.set_ticklabels(["20% D", "35% D", "Even", "65% D", "80% D"])
    colorbar.outline.set_visible(False)
    colorbar.ax.tick_params(length=0, labelsize=9, colors=COLORS["muted"])


def plot_precinct_vote_share(gdf: gpd.GeoDataFrame, state_code: str, state_name: str) -> Path:
    output = FIGURE_DIR / f"{state_code}_precinct_presidential_vote_share.png"
    fig, ax = plt.subplots(figsize=(11, 11))

    gdf.plot(
        ax=ax,
        column="dem_share",
        cmap=PARTY_CMAP,
        norm=TwoSlopeNorm(vmin=0.20, vcenter=0.50, vmax=0.80),
        linewidth=0,
        antialiased=False,
    )

    ax.set_title(f"{state_name} precinct presidential vote share", loc="left", fontsize=20, pad=18)
    ax.text(
        0,
        1.015,
        "2020 Democratic two-party share • precinct-level geography",
        transform=ax.transAxes,
        fontsize=10,
        color=COLORS["muted"],
    )
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")
    add_horizontal_colorbar(fig)
    fig.text(
        0.5,
        0.025,
        "Two-party share = Democratic votes ÷ (Democratic + Republican votes)",
        ha="center",
        fontsize=9,
        color=COLORS["muted"],
    )
    fig.savefig(output, dpi=320, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_district_vote_share(
    districts: gpd.GeoDataFrame,
    state_code: str,
    state_name: str,
) -> Path:
    output = FIGURE_DIR / f"{state_code}_congressional_district_vote_share.png"
    fig, ax = plt.subplots(figsize=(11, 11))

    districts.plot(
        ax=ax,
        column="dem_share",
        cmap=PARTY_CMAP,
        norm=TwoSlopeNorm(vmin=0.20, vcenter=0.50, vmax=0.80),
        edgecolor=COLORS["white"],
        linewidth=2.2,
    )

    for _, row in districts.iterrows():
        point = row.geometry.representative_point()
        share = row["dem_share"] * 100
        label_color = COLORS["dem"] if share > 50 else COLORS["rep"]
        ax.text(
            point.x,
            point.y,
            f"{row[DISTRICT_COLUMN]}\n{share:.1f}% D",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=COLORS["ink"],
            bbox={
                "boxstyle": "round,pad=0.36",
                "facecolor": COLORS["white"],
                "edgecolor": label_color,
                "linewidth": 1.4,
                "alpha": 0.96,
            },
        )

    ax.set_title(f"{state_name} congressional district vote share", loc="left", fontsize=20, pad=18)
    ax.text(
        0,
        1.015,
        "2020 presidential votes aggregated into enacted congressional districts",
        transform=ax.transAxes,
        fontsize=10,
        color=COLORS["muted"],
    )
    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="box")
    add_horizontal_colorbar(fig)
    fig.savefig(output, dpi=320, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_actual_vote_vs_seats(summary: pd.DataFrame, state_code: str, state_name: str) -> Path:
    output = FIGURE_DIR / f"{state_code}_actual_vote_vs_house_seats.png"
    row = summary.iloc[0]

    parties = ["Democratic", "Republican"]
    votes = np.array(
        [row["dem_presidential_vote_share_pct"], row["rep_presidential_vote_share_pct"]]
    )
    seats = np.array(
        [row["actual_dem_house_seat_share_pct"], row["actual_rep_house_seat_share_pct"]]
    )
    y = np.array([1, 0])

    fig, ax = plt.subplots(figsize=(11, 6.7))
    ax.set_facecolor(COLORS["white"])

    for yi, vote, seat, party in zip(y, votes, seats, parties):
        color = COLORS["dem"] if party == "Democratic" else COLORS["rep"]
        ax.plot([vote, seat], [yi, yi], color=COLORS["grid"], linewidth=8, solid_capstyle="round")
        ax.scatter(vote, yi, s=160, color=COLORS["white"], edgecolor=color, linewidth=3, zorder=3)
        ax.scatter(seat, yi, s=170, color=color, edgecolor=COLORS["white"], linewidth=1.5, zorder=4)
        ax.text(vote, yi + 0.16, f"Vote {vote:.1f}%", ha="center", fontsize=10, color=COLORS["muted"])
        ax.text(seat, yi - 0.19, f"Seats {seat:.1f}%", ha="center", fontsize=10, fontweight="bold", color=color)
        gap = seat - vote
        ax.text(
            (vote + seat) / 2,
            yi + 0.02,
            f"{gap:+.1f} pp",
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=COLORS["ink"],
            bbox={"boxstyle": "round,pad=0.25", "facecolor": COLORS["paper"], "edgecolor": "none"},
        )

    ax.axvline(50, color=COLORS["muted"], linewidth=1.2, linestyle=(0, (4, 4)), alpha=0.65)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.55, 1.55)
    ax.set_yticks(y)
    ax.set_yticklabels(parties, fontsize=11, fontweight="bold")
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8, alpha=0.65)
    ax.spines[:].set_visible(False)
    ax.tick_params(axis="both", length=0)
    ax.set_title(f"{state_name}: presidential vote vs. actual House seats", loc="left", fontsize=20, pad=24)
    ax.text(
        0,
        1.01,
        "2020 presidential two-party vote share compared with the 2022 U.S. House delegation",
        transform=ax.transAxes,
        fontsize=10,
        color=COLORS["muted"],
    )
    fig.text(
        0.09,
        0.055,
        "Open marker = presidential vote share   •   Filled marker = actual House seat share",
        fontsize=9,
        color=COLORS["muted"],
    )
    fig.savefig(output, dpi=320, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_presidential_district_wins(summary: pd.DataFrame, state_code: str, state_name: str) -> Path:
    output = FIGURE_DIR / f"{state_code}_presidential_district_wins_vs_actual_seats.png"
    row = summary.iloc[0]

    labels = ["2020 presidential\nwinner by district", "Actual 2022\nHouse delegation"]
    dem_counts = [int(row["presidential_dem_district_wins"]), int(row["actual_dem_house_seats"])]
    rep_counts = [int(row["presidential_rep_district_wins"]), int(row["actual_rep_house_seats"])]
    total = int(row["actual_total_house_seats"])

    fig, ax = plt.subplots(figsize=(9.5, 6.5))
    ax.set_facecolor(COLORS["white"])
    y = np.arange(len(labels))

    ax.barh(y, dem_counts, color=COLORS["dem"], height=0.52, label="Democratic")
    ax.barh(y, rep_counts, left=dem_counts, color=COLORS["rep"], height=0.52, label="Republican")

    for yi, d_count, r_count in zip(y, dem_counts, rep_counts):
        if d_count:
            ax.text(d_count / 2, yi, f"{d_count} D", ha="center", va="center", color="white", fontweight="bold")
        if r_count:
            ax.text(d_count + r_count / 2, yi, f"{r_count} R", ha="center", va="center", color="white", fontweight="bold")

    ax.set_xlim(0, total)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xticks(range(total + 1))
    ax.set_xlabel("Congressional districts")
    ax.invert_yaxis()
    ax.spines[:].set_visible(False)
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.8, alpha=0.7)
    ax.tick_params(length=0)
    ax.set_title(f"{state_name}: presidential district wins and actual seats", loc="left", fontsize=19, pad=20)
    ax.text(
        0,
        1.01,
        "Modeled district outcomes are shown separately from actual congressional election results",
        transform=ax.transAxes,
        fontsize=10,
        color=COLORS["muted"],
    )
    ax.legend(frameon=False, ncol=2, loc="lower right")
    fig.savefig(output, dpi=320, bbox_inches="tight")
    plt.close(fig)
    return output


def add_card(
    fig: plt.Figure,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    value: str,
    subtitle: str,
    accent: str,
) -> None:
    card = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        transform=fig.transFigure,
        facecolor=COLORS["white"],
        edgecolor="#E5EAF1",
        linewidth=1,
        zorder=2,
    )
    fig.patches.append(card)
    fig.text(x + 0.025, y + height - 0.045, title, fontsize=9.5, color=COLORS["muted"])
    fig.text(x + 0.025, y + height - 0.102, value, fontsize=22, fontweight="bold", color=accent)
    fig.text(x + 0.025, y + 0.028, subtitle, fontsize=8.7, color=COLORS["muted"])


def plot_state_dashboard(
    summary: pd.DataFrame,
    districts: gpd.GeoDataFrame,
    state_code: str,
    state_name: str,
) -> Path:
    output = FIGURE_DIR / f"{state_code}_week1_summary_dashboard.png"
    row = summary.iloc[0]

    dem_vote = row["dem_presidential_vote_share_pct"]
    rep_vote = row["rep_presidential_vote_share_pct"]

    dem_seat = row["actual_dem_house_seat_share_pct"]
    rep_seat = row["actual_rep_house_seat_share_pct"]

    dem_gap = row["actual_dem_representation_gap_pp"]

    actual_dem_seats = int(row["actual_dem_house_seats"])
    actual_rep_seats = int(row["actual_rep_house_seats"])
    total_seats = int(row["actual_total_house_seats"])

    model_dem = int(row["presidential_dem_district_wins"])
    model_rep = int(row["presidential_rep_district_wins"])

    fig = plt.figure(
        figsize=(15, 9),
        facecolor=COLORS["paper"],
    )

    # ---------------------------------------------------------
    # Header
    # ---------------------------------------------------------

    fig.text(
        0.055,
        0.935,
        f"{state_name} representation snapshot",
        fontsize=25,
        fontweight="bold",
        color=COLORS["ink"],
    )

    fig.text(
        0.055,
        0.895,
        "2020 presidential vote geography compared with the 2022 U.S. House delegation",
        fontsize=11,
        color=COLORS["muted"],
    )

    # ---------------------------------------------------------
    # Summary cards
    # ---------------------------------------------------------

    card_y = 0.735
    card_height = 0.115
    card_width = 0.205
    card_gap = 0.018

    cards = [
        (
            "DEMOCRATIC VOTE",
            f"{dem_vote:.1f}%",
            "2020 two-party presidential share",
            COLORS["dem"],
        ),
        (
            "ACTUAL HOUSE SEATS",
            f"{actual_dem_seats} D · {actual_rep_seats} R",
            f"{total_seats} total districts",
            COLORS["ink"],
        ),
        (
            "DEMOCRATIC SEAT SHARE",
            f"{dem_seat:.1f}%",
            "2022 U.S. House delegation",
            COLORS["dem"],
        ),
        (
            "REPRESENTATION GAP",
            f"{dem_gap:+.1f} pp",
            "D seat share minus D vote share",
            COLORS["accent"],
        ),
    ]

    for index, (title, value, subtitle, accent) in enumerate(cards):
        x = 0.055 + index * (card_width + card_gap)

        card = FancyBboxPatch(
            (x, card_y),
            card_width,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.016",
            transform=fig.transFigure,
            facecolor=COLORS["white"],
            edgecolor="#DDE4EE",
            linewidth=1.1,
            zorder=2,
        )

        fig.patches.append(card)

        fig.text(
            x + 0.018,
            card_y + 0.082,
            title,
            fontsize=8.6,
            color=COLORS["muted"],
            fontweight="bold",
        )

        fig.text(
            x + 0.018,
            card_y + 0.039,
            value,
            fontsize=20,
            fontweight="bold",
            color=accent,
        )

        fig.text(
            x + 0.018,
            card_y + 0.013,
            subtitle,
            fontsize=8.2,
            color=COLORS["muted"],
        )

    # ---------------------------------------------------------
    # Map
    # ---------------------------------------------------------

    map_ax = fig.add_axes([0.055, 0.12, 0.49, 0.53])

    districts.plot(
        ax=map_ax,
        column="dem_share",
        cmap=PARTY_CMAP,
        norm=TwoSlopeNorm(
            vmin=0.20,
            vcenter=0.50,
            vmax=0.80,
        ),
        edgecolor=COLORS["white"],
        linewidth=2.0,
    )

    for _, district in districts.iterrows():
        point = district.geometry.representative_point()
        district_number = str(district[DISTRICT_COLUMN])
        dem_share = district["dem_share"] * 100

        label_edge = (
            COLORS["dem"]
            if dem_share >= 50
            else COLORS["rep"]
        )

        map_ax.text(
            point.x,
            point.y,
            f"{district_number}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=COLORS["ink"],
            bbox={
                "boxstyle": "circle,pad=0.27",
                "facecolor": COLORS["white"],
                "edgecolor": label_edge,
                "linewidth": 1.2,
                "alpha": 0.97,
            },
            zorder=5,
        )

    map_ax.set_title(
        "Congressional district presidential vote",
        loc="left",
        fontsize=16,
        pad=12,
    )

    map_ax.text(
        0,
        1.01,
        "Blue districts lean Democratic; red districts lean Republican",
        transform=map_ax.transAxes,
        fontsize=9,
        color=COLORS["muted"],
    )

    map_ax.set_axis_off()
    map_ax.set_aspect("equal", adjustable="box")

    # Map legend
    legend_ax = fig.add_axes([0.155, 0.085, 0.29, 0.016])

    scalar = plt.cm.ScalarMappable(
        cmap=PARTY_CMAP,
        norm=TwoSlopeNorm(
            vmin=0.20,
            vcenter=0.50,
            vmax=0.80,
        ),
    )

    scalar.set_array([])

    colorbar = fig.colorbar(
        scalar,
        cax=legend_ax,
        orientation="horizontal",
    )

    colorbar.set_ticks([0.2, 0.5, 0.8])
    colorbar.set_ticklabels(
        ["20% D", "Even", "80% D"]
    )

    colorbar.outline.set_visible(False)

    colorbar.ax.tick_params(
        length=0,
        labelsize=8,
        colors=COLORS["muted"],
    )

    # ---------------------------------------------------------
    # Vote versus seats comparison
    # ---------------------------------------------------------

    comparison_ax = fig.add_axes([0.61, 0.39, 0.33, 0.25])

    categories = ["Democratic", "Republican"]

    vote_values = [dem_vote, rep_vote]
    seat_values = [dem_seat, rep_seat]

    y_positions = np.array([1, 0])

    party_colors = [
        COLORS["dem"],
        COLORS["rep"],
    ]

    for y_value, party, vote_value, seat_value, color in zip(
        y_positions,
        categories,
        vote_values,
        seat_values,
        party_colors,
    ):
        comparison_ax.plot(
            [vote_value, seat_value],
            [y_value, y_value],
            color=COLORS["grid"],
            linewidth=7,
            solid_capstyle="round",
            zorder=1,
        )

        comparison_ax.scatter(
            vote_value,
            y_value,
            s=135,
            facecolor=COLORS["white"],
            edgecolor=color,
            linewidth=2.6,
            zorder=3,
        )

        comparison_ax.scatter(
            seat_value,
            y_value,
            s=145,
            facecolor=color,
            edgecolor=COLORS["white"],
            linewidth=1.2,
            zorder=4,
        )

        comparison_ax.text(
            vote_value,
            y_value + 0.18,
            f"Vote {vote_value:.1f}%",
            ha="center",
            fontsize=9,
            color=COLORS["muted"],
        )

        comparison_ax.text(
            seat_value,
            y_value - 0.20,
            f"Seats {seat_value:.1f}%",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=color,
        )

    comparison_ax.axvline(
        50,
        color=COLORS["muted"],
        linewidth=1,
        linestyle=(0, (4, 4)),
        alpha=0.65,
    )

    comparison_ax.set_xlim(0, 100)
    comparison_ax.set_ylim(-0.5, 1.5)

    comparison_ax.set_yticks(y_positions)
    comparison_ax.set_yticklabels(
        categories,
        fontsize=10,
        fontweight="bold",
    )

    comparison_ax.set_xticks([0, 25, 50, 75, 100])
    comparison_ax.set_xticklabels(
        ["0%", "25%", "50%", "75%", "100%"]
    )

    comparison_ax.grid(
        axis="x",
        color=COLORS["grid"],
        alpha=0.7,
    )

    comparison_ax.spines[:].set_visible(False)
    comparison_ax.tick_params(length=0)

    comparison_ax.set_title(
        "Statewide vote and seat shares",
        loc="left",
        fontsize=15,
        pad=12,
    )

    # ---------------------------------------------------------
    # District result comparison
    # ---------------------------------------------------------

    district_ax = fig.add_axes([0.61, 0.15, 0.33, 0.15])

    labels = [
        "2020 presidential\nwinner by district",
        "Actual 2022\nHouse delegation",
    ]

    dem_counts = [
        model_dem,
        actual_dem_seats,
    ]

    rep_counts = [
        model_rep,
        actual_rep_seats,
    ]

    y = np.arange(2)

    district_ax.barh(
        y,
        dem_counts,
        color=COLORS["dem"],
        height=0.48,
    )

    district_ax.barh(
        y,
        rep_counts,
        left=dem_counts,
        color=COLORS["rep"],
        height=0.48,
    )

    for yi, d_count, r_count in zip(
        y,
        dem_counts,
        rep_counts,
    ):
        if d_count:
            district_ax.text(
                d_count / 2,
                yi,
                f"{d_count} D",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                fontsize=9,
            )

        if r_count:
            district_ax.text(
                d_count + r_count / 2,
                yi,
                f"{r_count} R",
                ha="center",
                va="center",
                color="white",
                fontweight="bold",
                fontsize=9,
            )

    district_ax.set_xlim(0, total_seats)
    district_ax.set_yticks(y)
    district_ax.set_yticklabels(labels, fontsize=9)
    district_ax.set_xticks(range(total_seats + 1))
    district_ax.set_xlabel(
        "Congressional districts",
        fontsize=9,
    )

    district_ax.invert_yaxis()
    district_ax.grid(
        axis="x",
        color=COLORS["grid"],
        alpha=0.65,
    )

    district_ax.spines[:].set_visible(False)
    district_ax.tick_params(length=0)

    district_ax.set_title(
        "Modeled district outcomes vs. actual seats",
        loc="left",
        fontsize=14,
        pad=10,
    )

    # ---------------------------------------------------------
    # Footer
    # ---------------------------------------------------------

    fig.text(
        0.61,
        0.075,
        (
            "Descriptive comparison only. A vote-seat gap does not by itself "
            "establish gerrymandering; geography, turnout, candidate effects, "
            "and district boundaries all influence representation."
        ),
        fontsize=8.8,
        color=COLORS["muted"],
        wrap=True,
    )

    fig.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
        facecolor=COLORS["paper"],
    )

    plt.close(fig)

    return output


def save_state_tables(
    state_code: str,
    summary: pd.DataFrame,
    districts: gpd.GeoDataFrame,
) -> list[Path]:
    summary_path = TABLE_DIR / f"{state_code}_representation_summary.csv"
    district_path = TABLE_DIR / f"{state_code}_district_presidential_results.csv"

    summary.to_csv(summary_path, index=False)
    district_table = pd.DataFrame(
        {
            "district": districts[DISTRICT_COLUMN],
            "dem_presidential_votes": districts[DEM_COLUMN].astype(int),
            "rep_presidential_votes": districts[REP_COLUMN].astype(int),
            "two_party_votes": districts["two_party_votes"].astype(int),
            "dem_presidential_vote_share_pct": districts["dem_share"] * 100,
            "rep_presidential_vote_share_pct": districts["rep_share"] * 100,
            "presidential_winner": districts["presidential_winner"],
            "dem_margin_pp": districts["dem_margin_pp"],
        }
    )
    district_table.to_csv(district_path, index=False)
    return [summary_path, district_path]


def write_markdown_report(combined: pd.DataFrame) -> Path:
    output = REPORT_DIR / "week1_vote_seat_summary.md"
    lines = [
        "# Week 1 — Presidential Vote and U.S. House Seat Comparison",
        "",
        "## Method",
        "",
        "- Presidential vote share uses 2020 Democratic and Republican precinct votes only.",
        "- Precinct votes are aggregated statewide and by enacted congressional district.",
        "- Actual House seat shares use the 2022 U.S. House delegation, the first election under the post-2020 maps represented by these datasets.",
        "- Presidential district wins are reported separately from actual House election winners.",
        "",
        "## Results",
        "",
        "| State | D vote | R vote | Actual D seats | Actual R seats | D seat share | D representation gap | 2020 presidential district wins |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in combined.iterrows():
        lines.append(
            "| "
            f"{row['state']} | "
            f"{row['dem_presidential_vote_share_pct']:.1f}% | "
            f"{row['rep_presidential_vote_share_pct']:.1f}% | "
            f"{int(row['actual_dem_house_seats'])} | "
            f"{int(row['actual_rep_house_seats'])} | "
            f"{row['actual_dem_house_seat_share_pct']:.1f}% | "
            f"{row['actual_dem_representation_gap_pp']:+.1f} pp | "
            f"{int(row['presidential_dem_district_wins'])} D / "
            f"{int(row['presidential_rep_district_wins'])} R |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The representation gap is a descriptive difference between statewide presidential vote share and actual congressional seat share. It is not, by itself, evidence that a map is gerrymandered. Later ensemble analysis is needed to compare the enacted map with legally valid alternatives under the same geography and constraints.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def process_state(state_code: str, config: dict) -> tuple[pd.DataFrame, list[Path]]:
    state_name = config["name"]
    print("\n" + "=" * 72)
    print(f"PROCESSING {state_name.upper()}")
    print("=" * 72)

    gdf = load_state_data(state_code, state_name)
    districts = aggregate_districts(gdf)
    summary = calculate_summary(state_code, config, gdf, districts)

    outputs = save_state_tables(state_code, summary, districts)
    outputs.extend(
        [
            plot_precinct_vote_share(gdf, state_code, state_name),
            plot_district_vote_share(districts, state_code, state_name),
            plot_actual_vote_vs_seats(summary, state_code, state_name),
            plot_presidential_district_wins(summary, state_code, state_name),
            plot_state_dashboard(summary, districts, state_code, state_name),
        ]
    )

    row = summary.iloc[0]
    print(
        f"{state_name}: D vote {row['dem_presidential_vote_share_pct']:.1f}% | "
        f"Actual seats {int(row['actual_dem_house_seats'])} D, "
        f"{int(row['actual_rep_house_seats'])} R | "
        f"D gap {row['actual_dem_representation_gap_pp']:+.1f} pp"
    )
    return summary, outputs


def main() -> None:
    set_modern_style()
    ensure_output_directories()

    summaries: list[pd.DataFrame] = []
    generated: list[Path] = []
    failures: list[str] = []

    for state_code, config in STATES.items():
        try:
            summary, outputs = process_state(state_code, config)
            summaries.append(summary)
            generated.extend(outputs)
        except Exception as error:
            failures.append(state_code)
            print(
                f"\nFAILED FOR {config['name']}: "
                f"{type(error).__name__}: {error}",
                file=sys.stderr,
                flush=True,
            )

    if summaries:
        combined = pd.concat(summaries, ignore_index=True)
        combined_path = TABLE_DIR / "mi_mo_representation_comparison.csv"
        combined.to_csv(combined_path, index=False)
        generated.append(combined_path)
        generated.append(write_markdown_report(combined))

    print("\n" + "=" * 72)
    print("GENERATED OUTPUTS")
    print("=" * 72)
    for path in generated:
        print(path.relative_to(PROJECT_ROOT))

    if failures:
        raise RuntimeError(
            "Analysis failed for: " + ", ".join(code.upper() for code in failures)
        )

    print("\nWEEK 1 VOTE-SEAT ANALYSIS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
