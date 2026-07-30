from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "week3"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week3"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports" / "week3"

DISTRICT_COLUMN = "CD"

STATES = {
    "mi": "Michigan",
    "mo": "Missouri",
}

ELECTION_CANDIDATES = [
    ("2020 Presidential", "PRE20D", "PRE20R"),
    ("2016 Presidential", "PRE16D", "PRE16R"),
    ("2024 Presidential", "PRE24D", "PRE24R"),
    ("2020 Presidential", "G20PREDBID", "G20PRERTRU"),
    ("2016 Presidential", "G16PREDCLI", "G16PRERTRU"),
    ("2024 Presidential", "G24PREDHAR", "G24PRERTRU"),
]

COLORS = {
    "paper": "#F6F8FC",
    "white": "#FFFFFF",
    "ink": "#172033",
    "muted": "#667085",
    "grid": "#D9E0EA",
    "dem": "#2F6FED",
    "rep": "#D94B45",
    "purple": "#7A5AF8",
    "teal": "#159D7E",
    "gold": "#D89B00",
}


@dataclass(frozen=True)
class ElectionSpec:
    name: str
    dem_column: str
    rep_column: str


def set_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titlesize": 17,
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
                    f"{current} exists as a file, but this project needs a folder there.\n"
                    f"Rename it with:\n"
                    f"mv '{current}' '{current}_old_file'"
                )
        folder.mkdir(parents=True, exist_ok=True)


def find_shapefile(state_code: str) -> Path:
    folder = RAW_DIR / state_code
    if not folder.exists():
        raise FileNotFoundError(f"Missing state folder: {folder}")

    shapefiles = list(folder.rglob("*.shp"))
    if not shapefiles:
        raise FileNotFoundError(f"No shapefile found under: {folder}")

    exact_matches = [
        path for path in shapefiles
        if path.stem.lower() == state_code.lower()
    ]

    selected = exact_matches[0] if exact_matches else shapefiles[0]
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


def detect_elections(columns: Iterable[str]) -> list[ElectionSpec]:
    available = set(columns)
    detected: list[ElectionSpec] = []
    seen: set[tuple[str, str]] = set()

    for name, dem_column, rep_column in ELECTION_CANDIDATES:
        pair = (dem_column, rep_column)
        if pair in seen:
            continue
        if dem_column in available and rep_column in available:
            detected.append(ElectionSpec(name, dem_column, rep_column))
            seen.add(pair)

    return detected


def load_state_data(
    state_code: str,
    state_name: str,
) -> tuple[gpd.GeoDataFrame, list[ElectionSpec]]:
    path = find_shapefile(state_code)
    gdf = gpd.read_file(path)

    if DISTRICT_COLUMN not in gdf.columns:
        raise KeyError(
            f"{state_name} is missing district column '{DISTRICT_COLUMN}'.\n"
            f"Available columns: {gdf.columns.tolist()}"
        )

    elections = detect_elections(gdf.columns)
    if not elections:
        raise KeyError(
            f"No recognized Democratic/Republican election column pair was found for {state_name}.\n"
            f"Available columns: {gdf.columns.tolist()}"
        )

    gdf = gdf.copy()
    gdf[DISTRICT_COLUMN] = clean_district_ids(gdf[DISTRICT_COLUMN])

    invalid_ids = {"", "nan", "None", "null", "0"}
    gdf = gdf[~gdf[DISTRICT_COLUMN].isin(invalid_ids)].copy()

    for election in elections:
        gdf[election.dem_column] = pd.to_numeric(
            gdf[election.dem_column], errors="coerce"
        ).fillna(0)
        gdf[election.rep_column] = pd.to_numeric(
            gdf[election.rep_column], errors="coerce"
        ).fillna(0)

    print(
        f"Loaded {len(gdf):,} precinct rows, "
        f"{gdf[DISTRICT_COLUMN].nunique()} districts, and "
        f"{len(elections)} election dataset(s) for {state_name}.",
        flush=True,
    )
    return gdf, elections


def winning_threshold(total_votes: float) -> int:
    return math.floor(total_votes / 2) + 1


def wasted_votes_for_district(
    dem_votes: float,
    rep_votes: float,
) -> tuple[float, float, str]:
    total = dem_votes + rep_votes
    if total <= 0:
        return 0.0, 0.0, "No votes"

    threshold = winning_threshold(total)

    if dem_votes > rep_votes:
        return max(0.0, dem_votes - threshold), rep_votes, "Democratic"
    if rep_votes > dem_votes:
        return dem_votes, max(0.0, rep_votes - threshold), "Republican"

    return dem_votes, rep_votes, "Tie"


def efficiency_gap_from_wasted_votes(
    total_dem_wasted: float,
    total_rep_wasted: float,
    total_votes: float,
) -> float:
    if total_votes <= 0:
        return np.nan
    return (total_rep_wasted - total_dem_wasted) / total_votes


def efficiency_gap_shortcut(
    dem_seat_share: float,
    dem_vote_share: float,
) -> float:
    return dem_seat_share - 2 * dem_vote_share + 0.5


def mean_median_difference(district_dem_shares: pd.Series) -> float:
    clean = district_dem_shares.dropna()
    if clean.empty:
        return np.nan
    return float(clean.median() - clean.mean())


def aggregate_district_results(
    gdf: gpd.GeoDataFrame,
    election: ElectionSpec,
) -> pd.DataFrame:
    district_results = (
        gdf.groupby(DISTRICT_COLUMN, as_index=False)
        .agg(
            dem_votes=(election.dem_column, "sum"),
            rep_votes=(election.rep_column, "sum"),
            precinct_count=(DISTRICT_COLUMN, "size"),
        )
    )

    district_results["two_party_votes"] = (
        district_results["dem_votes"] + district_results["rep_votes"]
    )
    district_results["dem_share"] = (
        district_results["dem_votes"]
        / district_results["two_party_votes"].where(
            district_results["two_party_votes"] > 0
        )
    )
    district_results["rep_share"] = 1 - district_results["dem_share"]

    wasted_results = district_results.apply(
        lambda row: wasted_votes_for_district(
            float(row["dem_votes"]), float(row["rep_votes"])
        ),
        axis=1,
        result_type="expand",
    )
    wasted_results.columns = [
        "dem_wasted_votes",
        "rep_wasted_votes",
        "winner",
    ]

    district_results = pd.concat([district_results, wasted_results], axis=1)
    district_results["dem_margin_pp"] = (
        district_results["dem_share"] - 0.5
    ) * 100

    ordered_districts = sorted(
        district_results[DISTRICT_COLUMN].tolist(),
        key=district_sort_key,
    )
    order_lookup = {
        district: index
        for index, district in enumerate(ordered_districts)
    }
    district_results["_sort"] = district_results[DISTRICT_COLUMN].map(order_lookup)

    return (
        district_results
        .sort_values("_sort")
        .drop(columns="_sort")
        .reset_index(drop=True)
    )


def calculate_state_metrics(
    state_code: str,
    state_name: str,
    election: ElectionSpec,
    district_results: pd.DataFrame,
) -> pd.DataFrame:
    total_dem_votes = float(district_results["dem_votes"].sum())
    total_rep_votes = float(district_results["rep_votes"].sum())
    total_votes = total_dem_votes + total_rep_votes

    if total_votes <= 0:
        raise ValueError(
            f"{state_name} has no valid two-party votes for {election.name}."
        )

    total_districts = len(district_results)
    dem_seats = int((district_results["winner"] == "Democratic").sum())
    rep_seats = int((district_results["winner"] == "Republican").sum())
    ties = int((district_results["winner"] == "Tie").sum())

    dem_vote_share = total_dem_votes / total_votes
    dem_seat_share = dem_seats / total_districts

    total_dem_wasted = float(district_results["dem_wasted_votes"].sum())
    total_rep_wasted = float(district_results["rep_wasted_votes"].sum())

    exact_eg = efficiency_gap_from_wasted_votes(
        total_dem_wasted,
        total_rep_wasted,
        total_votes,
    )
    shortcut_eg = efficiency_gap_shortcut(
        dem_seat_share,
        dem_vote_share,
    )
    mean_median = mean_median_difference(district_results["dem_share"])

    turnout_mean = float(district_results["two_party_votes"].mean())
    turnout_cv = (
        float(district_results["two_party_votes"].std(ddof=0)) / turnout_mean
        if turnout_mean > 0
        else np.nan
    )

    return pd.DataFrame(
        [
            {
                "state_code": state_code.upper(),
                "state": state_name,
                "election": election.name,
                "dem_column": election.dem_column,
                "rep_column": election.rep_column,
                "total_dem_votes": int(total_dem_votes),
                "total_rep_votes": int(total_rep_votes),
                "total_two_party_votes": int(total_votes),
                "dem_vote_share_pct": dem_vote_share * 100,
                "rep_vote_share_pct": (1 - dem_vote_share) * 100,
                "dem_seats": dem_seats,
                "rep_seats": rep_seats,
                "tied_districts": ties,
                "total_districts": total_districts,
                "dem_seat_share_pct": dem_seat_share * 100,
                "rep_seat_share_pct": (rep_seats / total_districts) * 100,
                "dem_wasted_votes": int(total_dem_wasted),
                "rep_wasted_votes": int(total_rep_wasted),
                "efficiency_gap_exact_pct": exact_eg * 100,
                "efficiency_gap_shortcut_pct": shortcut_eg * 100,
                "shortcut_minus_exact_pp": (shortcut_eg - exact_eg) * 100,
                "mean_median_difference_pp": mean_median * 100,
                "district_turnout_mean": turnout_mean,
                "district_turnout_cv": turnout_cv,
            }
        ]
    )


def synthetic_district_table(
    name: str,
    dem_shares: list[float],
    turnouts: list[int] | None = None,
) -> pd.DataFrame:
    if turnouts is None:
        turnouts = [1000] * len(dem_shares)

    rows = []
    for district_number, (dem_share, turnout) in enumerate(
        zip(dem_shares, turnouts),
        start=1,
    ):
        dem_votes = round(dem_share * turnout)
        rep_votes = turnout - dem_votes
        rows.append(
            {
                "scenario": name,
                DISTRICT_COLUMN: str(district_number),
                "dem_votes": dem_votes,
                "rep_votes": rep_votes,
                "precinct_count": 1,
                "two_party_votes": turnout,
            }
        )

    df = pd.DataFrame(rows)
    df["dem_share"] = df["dem_votes"] / df["two_party_votes"]
    df["rep_share"] = 1 - df["dem_share"]

    wasted = df.apply(
        lambda row: wasted_votes_for_district(
            float(row["dem_votes"]), float(row["rep_votes"])
        ),
        axis=1,
        result_type="expand",
    )
    wasted.columns = [
        "dem_wasted_votes",
        "rep_wasted_votes",
        "winner",
    ]
    return pd.concat([df, wasted], axis=1)


def build_synthetic_scenarios() -> dict[str, pd.DataFrame]:
    return {
        "Concentrated minority geography": synthetic_district_table(
            "Concentrated minority geography",
            [0.35, 0.35, 0.35, 0.35, 0.35],
        ),
        "Distributed competitive support": synthetic_district_table(
            "Distributed competitive support",
            [0.52, 0.52, 0.52, 0.10, 0.09],
        ),
        "Unequal-turnout distortion": synthetic_district_table(
            "Unequal-turnout distortion",
            [0.70, 0.70, 0.49, 0.49, 0.49],
            [400, 450, 1800, 1900, 2000],
        ),
        "Packing and cracking pattern": synthetic_district_table(
            "Packing and cracking pattern",
            [0.90, 0.53, 0.47, 0.46, 0.45],
        ),
    }


def summarize_synthetic_scenario(
    name: str,
    district_results: pd.DataFrame,
) -> dict:
    total_dem = float(district_results["dem_votes"].sum())
    total_rep = float(district_results["rep_votes"].sum())
    total_votes = total_dem + total_rep

    dem_seats = int((district_results["winner"] == "Democratic").sum())
    total_districts = len(district_results)

    dem_vote_share = total_dem / total_votes
    dem_seat_share = dem_seats / total_districts

    exact_eg = efficiency_gap_from_wasted_votes(
        float(district_results["dem_wasted_votes"].sum()),
        float(district_results["rep_wasted_votes"].sum()),
        total_votes,
    )
    shortcut_eg = efficiency_gap_shortcut(
        dem_seat_share,
        dem_vote_share,
    )
    mean_median = mean_median_difference(district_results["dem_share"])

    return {
        "scenario": name,
        "dem_vote_share_pct": dem_vote_share * 100,
        "dem_seats": dem_seats,
        "total_districts": total_districts,
        "dem_seat_share_pct": dem_seat_share * 100,
        "efficiency_gap_exact_pct": exact_eg * 100,
        "efficiency_gap_shortcut_pct": shortcut_eg * 100,
        "shortcut_minus_exact_pp": (shortcut_eg - exact_eg) * 100,
        "mean_median_difference_pp": mean_median * 100,
    }



def build_seats_votes_table(
    state_metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Create an explicit party-level seats–votes summary table."""
    row = state_metrics.iloc[0]
    total_districts = int(row["total_districts"])

    return pd.DataFrame(
        [
            {
                "party": "Democratic",
                "statewide_vote_share_pct": float(row["dem_vote_share_pct"]),
                "seats_won": int(row["dem_seats"]),
                "total_districts": total_districts,
                "seat_share_pct": float(row["dem_seat_share_pct"]),
                "seat_minus_vote_gap_pp": (
                    float(row["dem_seat_share_pct"])
                    - float(row["dem_vote_share_pct"])
                ),
            },
            {
                "party": "Republican",
                "statewide_vote_share_pct": float(row["rep_vote_share_pct"]),
                "seats_won": int(row["rep_seats"]),
                "total_districts": total_districts,
                "seat_share_pct": float(row["rep_seat_share_pct"]),
                "seat_minus_vote_gap_pp": (
                    float(row["rep_seat_share_pct"])
                    - float(row["rep_vote_share_pct"])
                ),
            },
        ]
    )


def plot_seats_votes_summary(
    state_metrics: pd.DataFrame,
    state_code: str,
    state_name: str,
    election_name: str,
) -> Path:
    """Plot the explicit seats–votes summary required for Week 3."""
    slug = election_name.lower().replace(" ", "_").replace("/", "_")
    output = FIGURE_DIR / f"{state_code}_{slug}_seats_votes_summary.png"

    summary = build_seats_votes_table(state_metrics)

    fig = plt.figure(figsize=(14, 6.8), facecolor=COLORS["paper"])

    fig.text(
        0.055,
        0.93,
        f"{state_name} seats–votes summary",
        fontsize=24,
        fontweight="bold",
        color=COLORS["ink"],
    )
    fig.text(
        0.055,
        0.885,
        (
            f"{election_name} statewide two-party vote share compared with "
            "districts won under the same election"
        ),
        fontsize=10.5,
        color=COLORS["muted"],
    )

    # Left panel: vote share versus seat share for both parties.
    left_ax = fig.add_axes([0.07, 0.17, 0.42, 0.60])
    party_y = np.array([1, 0])
    party_names = summary["party"].tolist()
    vote_values = summary["statewide_vote_share_pct"].to_numpy()
    seat_values = summary["seat_share_pct"].to_numpy()
    party_colors = [COLORS["dem"], COLORS["rep"]]

    for y_value, party, vote, seat, color in zip(
        party_y,
        party_names,
        vote_values,
        seat_values,
        party_colors,
    ):
        left_ax.plot(
            [vote, seat],
            [y_value, y_value],
            color=COLORS["grid"],
            linewidth=9,
            solid_capstyle="round",
            zorder=1,
        )
        left_ax.scatter(
            vote,
            y_value,
            s=190,
            facecolor=COLORS["white"],
            edgecolor=color,
            linewidth=3,
            zorder=3,
        )
        left_ax.scatter(
            seat,
            y_value,
            s=195,
            facecolor=color,
            edgecolor=COLORS["white"],
            linewidth=1.5,
            zorder=4,
        )

        gap = seat - vote

        left_ax.text(
            vote,
            y_value + 0.17,
            f"Vote {vote:.1f}%",
            ha="center",
            fontsize=10,
            color=COLORS["muted"],
        )
        left_ax.text(
            seat,
            y_value - 0.20,
            f"Seats {seat:.1f}%",
            ha="center",
            fontsize=10,
            fontweight="bold",
            color=color,
        )
        left_ax.text(
            (vote + seat) / 2,
            y_value + 0.01,
            f"{gap:+.1f} pp",
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=COLORS["ink"],
            bbox={
                "boxstyle": "round,pad=0.24",
                "facecolor": COLORS["paper"],
                "edgecolor": "none",
            },
            zorder=5,
        )

    left_ax.axvline(
        50,
        color=COLORS["muted"],
        linewidth=1.1,
        linestyle=(0, (4, 4)),
        alpha=0.7,
    )
    left_ax.set_xlim(0, 100)
    left_ax.set_ylim(-0.55, 1.55)
    left_ax.set_yticks(party_y)
    left_ax.set_yticklabels(
        party_names,
        fontsize=11,
        fontweight="bold",
    )
    left_ax.set_xticks([0, 25, 50, 75, 100])
    left_ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    left_ax.grid(axis="x", color=COLORS["grid"], alpha=0.75)
    left_ax.spines[:].set_visible(False)
    left_ax.tick_params(length=0)
    left_ax.set_title(
        "Statewide vote share and seat share",
        loc="left",
        fontsize=15,
        pad=12,
    )

    # Right panel: classical seats–votes point plot.
    right_ax = fig.add_axes([0.60, 0.17, 0.33, 0.60])

    right_ax.plot(
        [0, 100],
        [0, 100],
        color=COLORS["muted"],
        linewidth=1.2,
        linestyle=(0, (5, 5)),
        alpha=0.75,
        label="Proportional reference",
    )

    for _, party_row in summary.iterrows():
        color = (
            COLORS["dem"]
            if party_row["party"] == "Democratic"
            else COLORS["rep"]
        )
        marker = "o" if party_row["party"] == "Democratic" else "s"

        right_ax.scatter(
            party_row["statewide_vote_share_pct"],
            party_row["seat_share_pct"],
            s=180,
            marker=marker,
            color=color,
            edgecolor=COLORS["white"],
            linewidth=1.5,
            zorder=3,
        )
        right_ax.annotate(
            (
                f"{party_row['party']}\n"
                f"{int(party_row['seats_won'])}/"
                f"{int(party_row['total_districts'])} seats"
            ),
            (
                party_row["statewide_vote_share_pct"],
                party_row["seat_share_pct"],
            ),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=9.5,
            fontweight="bold",
            color=color,
        )

    right_ax.set_xlim(0, 100)
    right_ax.set_ylim(0, 100)
    right_ax.set_aspect("equal", adjustable="box")
    right_ax.set_xlabel("Statewide two-party vote share")
    right_ax.set_ylabel("Share of districts won")
    right_ax.set_xticks([0, 25, 50, 75, 100])
    right_ax.set_yticks([0, 25, 50, 75, 100])
    right_ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    right_ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    right_ax.grid(color=COLORS["grid"], alpha=0.70)
    right_ax.spines[:].set_visible(False)
    right_ax.tick_params(length=0)
    right_ax.set_title(
        "Seats–votes plane",
        loc="left",
        fontsize=15,
        pad=12,
    )

    fig.text(
        0.055,
        0.075,
        (
            "Open marker = statewide vote share; filled marker = seat share. "
            "The dashed diagonal represents proportional conversion of votes into seats. "
            "Distance from that line is descriptive, not proof of gerrymandering."
        ),
        fontsize=9,
        color=COLORS["muted"],
    )

    fig.savefig(
        output,
        dpi=310,
        bbox_inches="tight",
        facecolor=COLORS["paper"],
    )
    plt.close(fig)
    return output


def save_seats_votes_summary(
    state_metrics: pd.DataFrame,
    state_code: str,
    election_name: str,
) -> Path:
    """Save the explicit seats–votes summary as a standalone CSV."""
    slug = election_name.lower().replace(" ", "_").replace("/", "_")
    output = TABLE_DIR / f"{state_code}_{slug}_seats_votes_summary.csv"
    build_seats_votes_table(state_metrics).to_csv(output, index=False)
    return output

def plot_metric_dashboard(
    state_metrics: pd.DataFrame,
    district_results: pd.DataFrame,
    state_code: str,
    state_name: str,
    election_name: str,
) -> Path:
    safe_election = election_name.lower().replace(" ", "_").replace("/", "_")
    output = FIGURE_DIR / f"{state_code}_{safe_election}_partisan_metrics_dashboard.png"

    row = state_metrics.iloc[0]
    fig = plt.figure(figsize=(15, 9), facecolor=COLORS["paper"])

    fig.text(
        0.055,
        0.94,
        f"{state_name} partisan metrics",
        fontsize=25,
        fontweight="bold",
    )
    fig.text(
        0.055,
        0.902,
        f"{election_name} • district-level vote aggregated from precinct returns",
        fontsize=11,
        color=COLORS["muted"],
    )

    cards = [
        (
            "DEMOCRATIC VOTE",
            f"{row['dem_vote_share_pct']:.1f}%",
            "Statewide two-party share",
            COLORS["dem"],
        ),
        (
            "DEMOCRATIC SEATS",
            f"{int(row['dem_seats'])}/{int(row['total_districts'])}",
            "Districts won under this election",
            COLORS["dem"],
        ),
        (
            "EFFICIENCY GAP",
            f"{row['efficiency_gap_exact_pct']:+.1f}%",
            "Positive = Democratic advantage",
            COLORS["purple"],
        ),
        (
            "MEAN–MEDIAN",
            f"{row['mean_median_difference_pp']:+.1f} pp",
            "Median D share minus mean D share",
            COLORS["teal"],
        ),
    ]

    from matplotlib.patches import FancyBboxPatch

    card_y = 0.755
    card_height = 0.115
    card_width = 0.205
    card_gap = 0.018

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
            fontsize=8.7,
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

    distribution_ax = fig.add_axes([0.065, 0.14, 0.49, 0.52])
    sorted_results = district_results.sort_values("dem_share").reset_index(drop=True)
    y = np.arange(len(sorted_results))
    shares_pct = sorted_results["dem_share"] * 100
    colors = np.where(shares_pct >= 50, COLORS["dem"], COLORS["rep"])

    distribution_ax.hlines(
        y=y,
        xmin=50,
        xmax=shares_pct,
        color=colors,
        linewidth=3,
        alpha=0.72,
    )
    distribution_ax.scatter(
        shares_pct,
        y,
        c=colors,
        s=72,
        edgecolor=COLORS["white"],
        linewidth=1.2,
        zorder=3,
    )
    distribution_ax.axvline(
        50,
        color=COLORS["muted"],
        linewidth=1.2,
        linestyle=(0, (4, 4)),
    )
    distribution_ax.set_yticks(y)
    distribution_ax.set_yticklabels(
        [f"District {district}" for district in sorted_results[DISTRICT_COLUMN]]
    )
    distribution_ax.set_xlabel("Democratic two-party vote share")
    distribution_ax.set_title(
        "District vote-share distribution",
        loc="left",
        fontsize=16,
        pad=12,
    )
    distribution_ax.grid(axis="x", color=COLORS["grid"], alpha=0.7)
    distribution_ax.spines[:].set_visible(False)
    distribution_ax.tick_params(length=0)

    wasted_ax = fig.add_axes([0.625, 0.42, 0.30, 0.23])
    wasted_values = [row["dem_wasted_votes"], row["rep_wasted_votes"]]
    bars = wasted_ax.bar(
        ["Democratic", "Republican"],
        wasted_values,
        color=[COLORS["dem"], COLORS["rep"]],
        width=0.56,
    )
    for bar, value in zip(bars, wasted_values):
        wasted_ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{int(value):,}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
    wasted_ax.set_title("Wasted votes", loc="left", fontsize=15, pad=10)
    wasted_ax.set_ylabel("Votes")
    wasted_ax.grid(axis="y", color=COLORS["grid"], alpha=0.7)
    wasted_ax.spines[:].set_visible(False)
    wasted_ax.tick_params(length=0)

    shortcut_ax = fig.add_axes([0.625, 0.14, 0.30, 0.18])
    labels = ["Direct wasted-vote\ncalculation", "Equal-turnout\nshortcut"]
    values = [
        row["efficiency_gap_exact_pct"],
        row["efficiency_gap_shortcut_pct"],
    ]
    bars = shortcut_ax.barh(
        labels,
        values,
        color=[COLORS["purple"], COLORS["gold"]],
        height=0.5,
    )
    shortcut_ax.axvline(0, color=COLORS["muted"], linewidth=1)
    for bar, value in zip(bars, values):
        offset = 0.35 if value >= 0 else -0.35
        shortcut_ax.text(
            value + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{value:+.1f}%",
            ha="left" if value >= 0 else "right",
            va="center",
            fontweight="bold",
            fontsize=9,
        )
    limit = max(5, max(abs(float(value)) for value in values) + 4)
    shortcut_ax.set_xlim(-limit, limit)
    shortcut_ax.set_title(
        "Efficiency-gap shortcut check",
        loc="left",
        fontsize=15,
        pad=10,
    )
    shortcut_ax.set_xlabel(
        "Efficiency gap (positive = Democratic advantage)"
    )
    shortcut_ax.grid(axis="x", color=COLORS["grid"], alpha=0.7)
    shortcut_ax.spines[:].set_visible(False)
    shortcut_ax.tick_params(length=0)

    fig.savefig(
        output,
        dpi=310,
        bbox_inches="tight",
        facecolor=COLORS["paper"],
    )
    plt.close(fig)
    return output


def plot_synthetic_counterexamples(
    scenario_tables: dict[str, pd.DataFrame],
    scenario_summary: pd.DataFrame,
) -> Path:
    output = FIGURE_DIR / "synthetic_metric_counterexamples.png"

    fig, axes = plt.subplots(2, 2, figsize=(15, 10.5))
    fig.patch.set_facecolor(COLORS["paper"])
    axes = axes.flatten()

    for ax, scenario_name in zip(axes, scenario_tables.keys()):
        df = scenario_tables[scenario_name]
        shares_pct = df["dem_share"] * 100
        x = np.arange(1, len(df) + 1)
        colors = np.where(shares_pct >= 50, COLORS["dem"], COLORS["rep"])

        ax.bar(x, shares_pct, color=colors, width=0.68)
        ax.axhline(
            50,
            color=COLORS["muted"],
            linewidth=1.2,
            linestyle=(0, (4, 4)),
        )

        summary_row = scenario_summary[
            scenario_summary["scenario"] == scenario_name
        ].iloc[0]

        ax.set_title(scenario_name, loc="left", fontsize=14, pad=10)
        ax.text(
            0.02,
            0.96,
            (
                f"Statewide D vote: {summary_row['dem_vote_share_pct']:.1f}%\n"
                f"D seats: {int(summary_row['dem_seats'])}/"
                f"{int(summary_row['total_districts'])}\n"
                f"Exact EG: {summary_row['efficiency_gap_exact_pct']:+.1f}%\n"
                f"Mean–median: {summary_row['mean_median_difference_pp']:+.1f} pp"
            ),
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": COLORS["white"],
                "edgecolor": COLORS["grid"],
                "alpha": 0.96,
            },
        )
        ax.set_xticks(x)
        ax.set_xticklabels([f"D{i}" for i in x])
        ax.set_ylim(0, 100)
        ax.set_ylabel("Democratic vote share (%)")
        ax.grid(axis="y", color=COLORS["grid"], alpha=0.65)
        ax.spines[:].set_visible(False)
        ax.tick_params(length=0)

    fig.suptitle(
        "Synthetic counterexamples — every single metric can be fooled",
        fontsize=22,
        fontweight="bold",
        x=0.04,
        ha="left",
        y=0.985,
    )
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def save_state_election_outputs(
    state_code: str,
    election: ElectionSpec,
    district_results: pd.DataFrame,
    state_metrics: pd.DataFrame,
) -> list[Path]:
    slug = election.name.lower().replace(" ", "_").replace("/", "_")
    district_path = TABLE_DIR / f"{state_code}_{slug}_district_metrics.csv"
    summary_path = TABLE_DIR / f"{state_code}_{slug}_state_metrics.csv"

    district_results.to_csv(district_path, index=False)
    state_metrics.to_csv(summary_path, index=False)
    return [district_path, summary_path]


def write_report(
    all_metrics: pd.DataFrame,
    scenario_summary: pd.DataFrame,
) -> Path:
    output = REPORT_DIR / "week3_partisan_metrics_summary.md"

    lines = [
        "# Week 3 — Partisan metrics",
        "",
        "## Metrics implemented from scratch",
        "",
        "- **Efficiency gap:** Republican wasted votes minus Democratic wasted votes, divided by all two-party votes. Positive values use the convention of Democratic advantage.",
        "- **Equal-turnout shortcut:** `EG = S - 2V + 0.5`, where `S` is Democratic seat share and `V` is Democratic statewide vote share.",
        "- **Mean–median difference:** median Democratic district vote share minus mean Democratic district vote share.",
        "- **Seats–votes summary:** districts won under the selected election compared with statewide two-party vote share.",
        "",
        "## State results",
        "",
        "| State | Election | D vote | D seats | Exact EG | Shortcut EG | Mean–median | Turnout CV |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for _, row in all_metrics.iterrows():
        lines.append(
            "| "
            f"{row['state']} | "
            f"{row['election']} | "
            f"{row['dem_vote_share_pct']:.1f}% | "
            f"{int(row['dem_seats'])}/{int(row['total_districts'])} | "
            f"{row['efficiency_gap_exact_pct']:+.1f}% | "
            f"{row['efficiency_gap_shortcut_pct']:+.1f}% | "
            f"{row['mean_median_difference_pp']:+.1f} pp | "
            f"{row['district_turnout_cv']:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Synthetic counterexamples",
            "",
            "| Scenario | D vote | D seats | Exact EG | Shortcut error | Mean–median |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for _, row in scenario_summary.iterrows():
        lines.append(
            "| "
            f"{row['scenario']} | "
            f"{row['dem_vote_share_pct']:.1f}% | "
            f"{int(row['dem_seats'])}/{int(row['total_districts'])} | "
            f"{row['efficiency_gap_exact_pct']:+.1f}% | "
            f"{row['shortcut_minus_exact_pp']:+.1f} pp | "
            f"{row['mean_median_difference_pp']:+.1f} pp |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "No single metric establishes that a district map is fair or unfair. Efficiency gap depends on turnout and statewide vote balance. Mean–median can miss some forms of packing and cracking. Seats–votes outcomes can reflect residential geography as well as district boundaries. The Week 4 ensemble provides the state-specific baseline.",
            "",
            "## Election sensitivity",
            "",
            "This script analyzes every recognized Democratic/Republican election pair present in the source shapefile. If only `PRE20D` and `PRE20R` are present, add a second election dataset before claiming a multi-election sensitivity result.",
            "",
        ]
    )

    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    set_style()
    ensure_directories()

    generated: list[Path] = []
    metric_frames: list[pd.DataFrame] = []

    for state_code, state_name in STATES.items():
        print("\n" + "=" * 72)
        print(f"PROCESSING {state_name.upper()}")
        print("=" * 72)

        gdf, elections = load_state_data(state_code, state_name)

        for election in elections:
            district_results = aggregate_district_results(gdf, election)
            state_metrics = calculate_state_metrics(
                state_code,
                state_name,
                election,
                district_results,
            )
            metric_frames.append(state_metrics)

            generated.extend(
                save_state_election_outputs(
                    state_code,
                    election,
                    district_results,
                    state_metrics,
                )
            )
            generated.append(
                plot_metric_dashboard(
                    state_metrics,
                    district_results,
                    state_code,
                    state_name,
                    election.name,
                )
            )
            generated.append(
                save_seats_votes_summary(
                    state_metrics,
                    state_code,
                    election.name,
                )
            )
            generated.append(
                plot_seats_votes_summary(
                    state_metrics,
                    state_code,
                    state_name,
                    election.name,
                )
            )

    if not metric_frames:
        raise RuntimeError("No state-election metrics were generated.")

    all_metrics = pd.concat(metric_frames, ignore_index=True)
    sensitivity_path = TABLE_DIR / "mi_mo_election_sensitivity.csv"
    all_metrics.to_csv(sensitivity_path, index=False)
    generated.append(sensitivity_path)

    scenario_tables = build_synthetic_scenarios()
    scenario_summary = pd.DataFrame(
        [
            summarize_synthetic_scenario(name, table)
            for name, table in scenario_tables.items()
        ]
    )

    scenario_summary_path = TABLE_DIR / "synthetic_counterexample_summary.csv"
    scenario_summary.to_csv(scenario_summary_path, index=False)
    generated.append(scenario_summary_path)

    for scenario_name, table in scenario_tables.items():
        slug = scenario_name.lower().replace(" ", "_").replace("/", "_")
        path = TABLE_DIR / f"synthetic_{slug}_districts.csv"
        table.to_csv(path, index=False)
        generated.append(path)

    generated.append(
        plot_synthetic_counterexamples(
            scenario_tables,
            scenario_summary,
        )
    )
    generated.append(
        write_report(
            all_metrics,
            scenario_summary,
        )
    )

    print("\n" + "=" * 72)
    print("GENERATED OUTPUTS")
    print("=" * 72)

    for path in generated:
        print(path.relative_to(PROJECT_ROOT))

    print("\nWEEK 3 PARTISAN METRICS COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"\nFAILED: {type(error).__name__}: {error}",
            file=sys.stderr,
            flush=True,
        )
        raise
