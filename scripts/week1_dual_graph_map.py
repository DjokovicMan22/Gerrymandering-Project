from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

# Save files without opening a macOS window.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
from gerrychain import Graph
from matplotlib.collections import LineCollection


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "figures" / "week1"

STATES = {
    "mi": "Michigan",
    "mo": "Missouri",
}


def find_shapefile(state_code: str) -> Path:
    """Find the state shapefile recursively inside data/raw."""
    possible_folders = [
        RAW_DIR / state_code,
        RAW_DIR / state_code.upper(),
    ]

    matches: list[Path] = []

    for folder in possible_folders:
        if folder.exists():
            matches.extend(folder.rglob("*.shp"))

    if not matches:
        matches = [
            path
            for path in RAW_DIR.rglob("*.shp")
            if state_code.lower() in str(path).lower()
        ]

    if not matches:
        raise FileNotFoundError(
            f"\nNo shapefile found for {state_code.upper()}.\n"
            f"Expected an extracted .shp file somewhere under:\n"
            f"{RAW_DIR}"
        )

    exact_matches = [
        path for path in matches if path.stem.lower() == state_code.lower()
    ]

    selected = exact_matches[0] if exact_matches else matches[0]

    print(f"Found {state_code.upper()} shapefile: {selected}", flush=True)
    return selected


def prepare_geodataframe(shapefile: Path) -> gpd.GeoDataFrame:
    """Load, validate, clean, and project precinct geometries."""
    print(f"Loading {shapefile.name}...", flush=True)

    gdf = gpd.read_file(shapefile)

    if gdf.empty:
        raise ValueError(f"The shapefile contains no rows: {shapefile}")

    if "geometry" not in gdf.columns:
        raise ValueError(f"No geometry column found in: {shapefile}")

    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    invalid_count = int((~gdf.geometry.is_valid).sum())

    if invalid_count:
        print(f"Repairing {invalid_count} invalid geometries...", flush=True)
        gdf["geometry"] = gdf.geometry.buffer(0)

    gdf = gdf.reset_index(drop=True)

    if gdf.crs is None:
        raise ValueError(f"The shapefile has no CRS information: {shapefile}")

    if gdf.crs.is_geographic:
        projected_crs = gdf.estimate_utm_crs()

        if projected_crs is None:
            raise ValueError("Could not estimate a projected CRS.")

        print(f"Projecting data to {projected_crs}...", flush=True)
        gdf = gdf.to_crs(projected_crs)

    print(f"Loaded {len(gdf):,} precinct geometries.", flush=True)
    return gdf


def build_graph(gdf: gpd.GeoDataFrame) -> Graph:
    """Build the precinct dual graph using rook adjacency."""
    print("Building rook-adjacency graph...", flush=True)

    graph = Graph.from_geodataframe(
        gdf,
        adjacency="rook",
    )

    components = list(nx.connected_components(graph))
    isolates = list(nx.isolates(graph))

    print(
        f"Graph contains {graph.number_of_nodes():,} nodes and "
        f"{graph.number_of_edges():,} edges.",
        flush=True,
    )
    print(f"Connected components: {len(components)}", flush=True)
    print(f"Isolated nodes: {len(isolates)}", flush=True)

    return graph


def plot_dual_graph(
    gdf: gpd.GeoDataFrame,
    graph: Graph,
    state_code: str,
    state_name: str,
) -> Path:
    """Create a precinct polygon and dual-graph overlay figure."""
    if OUTPUT_DIR.exists() and not OUTPUT_DIR.is_dir():
        raise NotADirectoryError(
            f"{OUTPUT_DIR} exists but is a file, not a folder."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{state_code}_precinct_dual_graph_overlay.png"

    print("Calculating node positions...", flush=True)

    points = gdf.geometry.representative_point()

    positions = {
        int(index): (float(point.x), float(point.y))
        for index, point in points.items()
        if point is not None and not point.is_empty
    }

    if not positions:
        raise RuntimeError("No valid node positions were created.")

    edge_segments: list[list[tuple[float, float]]] = []

    for node_u, node_v in graph.edges():
        if node_u in positions and node_v in positions:
            edge_segments.append(
                [
                    positions[node_u],
                    positions[node_v],
                ]
            )

    if not edge_segments:
        raise RuntimeError(
            "The graph contains edges, but none matched the geometry indices."
        )

    print(f"Valid node positions: {len(positions):,}", flush=True)
    print(f"Valid edge segments: {len(edge_segments):,}", flush=True)

    fig, ax = plt.subplots(figsize=(14, 14), facecolor="white")

    print("Drawing precinct polygons...", flush=True)

    gdf.plot(
        ax=ax,
        facecolor="#E5E7EB",
        edgecolor="#FFFFFF",
        linewidth=0.08,
        zorder=1,
    )

    print("Drawing graph edges...", flush=True)

    edge_collection = LineCollection(
        edge_segments,
        colors="#5267D8",
        linewidths=0.20,
        alpha=0.38,
        zorder=2,
    )

    ax.add_collection(edge_collection)

    print("Drawing graph nodes...", flush=True)

    node_x = [coordinate[0] for coordinate in positions.values()]
    node_y = [coordinate[1] for coordinate in positions.values()]

    ax.scatter(
        node_x,
        node_y,
        s=4,
        c="#EF233C",
        alpha=0.90,
        linewidths=0,
        zorder=3,
    )

    isolates = [
        node
        for node in nx.isolates(graph)
        if node in positions
    ]

    if isolates:
        isolate_x = [positions[node][0] for node in isolates]
        isolate_y = [positions[node][1] for node in isolates]

        ax.scatter(
            isolate_x,
            isolate_y,
            s=24,
            c="#111827",
            edgecolors="white",
            linewidths=0.5,
            zorder=4,
        )

    min_x, min_y, max_x, max_y = gdf.total_bounds

    x_padding = max((max_x - min_x) * 0.025, 1.0)
    y_padding = max((max_y - min_y) * 0.025, 1.0)

    ax.set_xlim(min_x - x_padding, max_x + x_padding)
    ax.set_ylim(min_y - y_padding, max_y + y_padding)

    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()

    ax.set_title(
        f"{state_name} Precinct Dual Graph",
        fontsize=20,
        fontweight="bold",
        pad=16,
    )

    fig.text(
        0.5,
        0.025,
        (
            f"{graph.number_of_nodes():,} precinct nodes   •   "
            f"{graph.number_of_edges():,} rook-adjacency edges   •   "
            f"{len(isolates)} isolates"
        ),
        ha="center",
        va="center",
        fontsize=10,
    )

    fig.tight_layout(rect=(0, 0.045, 1, 0.97))

    print(f"Saving PNG to {output_path}...", flush=True)

    fig.savefig(
        output_path,
        dpi=350,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    if not output_path.exists():
        raise RuntimeError(f"Figure was not created: {output_path}")

    size_mb = output_path.stat().st_size / 1_000_000

    print(f"Finished. PNG size: {size_mb:.2f} MB", flush=True)
    return output_path


def process_state(state_code: str, state_name: str) -> None:
    print("\n" + "=" * 72, flush=True)
    print(f"PROCESSING {state_name.upper()}", flush=True)
    print("=" * 72, flush=True)

    shapefile = find_shapefile(state_code)
    gdf = prepare_geodataframe(shapefile)
    graph = build_graph(gdf)

    output = plot_dual_graph(
        gdf=gdf,
        graph=graph,
        state_code=state_code,
        state_name=state_name,
    )

    print(f"Generated: {output}", flush=True)


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}", flush=True)
    print(f"Raw-data directory: {RAW_DIR}", flush=True)
    print(f"Output directory: {OUTPUT_DIR}", flush=True)

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw-data directory does not exist: {RAW_DIR}"
        )

    failures: list[str] = []

    for state_code, state_name in STATES.items():
        try:
            process_state(state_code, state_name)
        except Exception as error:
            failures.append(state_code)

            print(
                f"\nFAILED FOR {state_name}: "
                f"{type(error).__name__}: {error}",
                file=sys.stderr,
                flush=True,
            )

    print("\n" + "=" * 72, flush=True)

    if failures:
        raise RuntimeError(
            "Map generation failed for: "
            + ", ".join(code.upper() for code in failures)
        )

    print("ALL DUAL-GRAPH MAPS GENERATED SUCCESSFULLY", flush=True)
    print(f"Open this folder:\n{OUTPUT_DIR}", flush=True)


if __name__ == "__main__":
    main()