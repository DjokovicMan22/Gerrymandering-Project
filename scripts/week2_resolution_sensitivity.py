from __future__ import annotations

import importlib.util
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables" / "week2"
FIGURE_DIR = PROJECT_ROOT / "outputs" / "figures" / "week2"


def load_week2_module():
    path = PROJECT_ROOT / "scripts" / "week2_compactness_analysis.py"
    spec = importlib.util.spec_from_file_location("week2_compactness_analysis", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def find_shapefile(code: str) -> Path:
    matches = list((RAW_DIR / code).rglob("*.shp"))
    if not matches:
        raise FileNotFoundError(f"No shapefile below {RAW_DIR / code}")
    exact = [p for p in matches if p.stem.lower() == code]
    return exact[0] if exact else matches[0]


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    week2 = load_week2_module()
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    records = []
    tolerances_m = [0, 100, 250, 500, 1000, 2500]
    state_names = {"mi": "Michigan", "mo": "Missouri"}

    for code, state_name in state_names.items():
        precincts = gpd.read_file(find_shapefile(code))
        precincts["CD"] = precincts["CD"].astype(str).str.replace(r"\.0$", "", regex=True)
        districts = precincts[["CD", "geometry"]].dissolve(by="CD").reset_index()
        if districts.crs is None:
            raise ValueError(f"{state_name} has no CRS")
        if districts.crs.is_geographic:
            districts = districts.to_crs(districts.estimate_utm_crs())

        for _, row in districts.iterrows():
            original = row.geometry
            for tolerance in tolerances_m:
                geom = original if tolerance == 0 else original.simplify(tolerance, preserve_topology=True)
                metrics = week2.compute_metrics_for_geometry(geom)
                records.append(
                    {
                        "state": state_name,
                        "district": row["CD"],
                        "simplification_tolerance_m": tolerance,
                        **metrics,
                    }
                )

    frame = pd.DataFrame(records)
    frame.to_csv(TABLE_DIR / "boundary_resolution_sensitivity.csv", index=False)

    summary = (
        frame.groupby(["state", "simplification_tolerance_m"], as_index=False)
        .agg(
            mean_polsby_popper=("polsby_popper", "mean"),
            mean_reock=("reock", "mean"),
            mean_convex_hull_ratio=("convex_hull_ratio", "mean"),
        )
    )
    summary.to_csv(TABLE_DIR / "boundary_resolution_sensitivity_summary.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for state, group in summary.groupby("state"):
        ax.plot(
            group["simplification_tolerance_m"],
            group["mean_polsby_popper"],
            marker="o",
            label=state,
        )
    ax.set_title("Boundary resolution changes mean Polsby–Popper")
    ax.set_xlabel("Topology-preserving simplification tolerance (meters)")
    ax.set_ylabel("Mean district Polsby–Popper")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "boundary_resolution_sensitivity.png", dpi=220)
    plt.close(fig)

    print("Wrote Week 2 boundary-resolution sensitivity outputs.")


if __name__ == "__main__":
    main()
