from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
from gerrychain import Graph


def build_precinct_dual_graph(gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, Graph]:
    """Build a rook-adjacency dual graph from precinct geometry."""
    if gdf.empty:
        raise ValueError("GeoDataFrame is empty.")

    if gdf.crs is None:
        raise ValueError("GeoDataFrame has no CRS.")

    gdf = gdf.reset_index(drop=True).copy()

    # For centroid/geometry work, use a projected CRS if currently geographic.
    if gdf.crs.is_geographic:
        projected_crs = gdf.estimate_utm_crs()
        if projected_crs is not None:
            gdf = gdf.to_crs(projected_crs)

    graph = Graph.from_geodataframe(gdf, adjacency="rook")
    return gdf, graph


def plot_precinct_dual_graph(
    gdf: gpd.GeoDataFrame,
    graph: nx.Graph,
    title: str,
    output_path: str | Path,
) -> None:
    """Plot precinct polygons + dual graph edges + centroid nodes."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # representative_point() is often better than centroid for weird polygons
    points = gdf.geometry.representative_point()
    positions = {idx: (pt.x, pt.y) for idx, pt in points.items()}

    fig, ax = plt.subplots(figsize=(10, 10))

    # Base precinct polygons
    gdf.plot(
        ax=ax,
        color="#d9d9d9",
        edgecolor="white",
        linewidth=0.12,
    )

    # Graph edges
    nx.draw_networkx_edges(
        graph,
        pos=positions,
        ax=ax,
        edge_color="#4c63d9",
        width=0.18,
        alpha=0.35,
    )

    # Graph nodes
    nx.draw_networkx_nodes(
        graph,
        pos=positions,
        ax=ax,
        node_size=5,
        node_color="#e53935",
        linewidths=0,
        alpha=0.9,
    )

    # Optional: highlight isolates in black if any exist
    isolates = list(nx.isolates(graph))
    if isolates:
        nx.draw_networkx_nodes(
            graph,
            pos=positions,
            nodelist=isolates,
            ax=ax,
            node_size=12,
            node_color="black",
            linewidths=0,
        )

    ax.set_title(title, fontsize=16)
    ax.set_axis_off()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)