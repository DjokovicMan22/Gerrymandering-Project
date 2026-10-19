"""Construction and validation of GerryChain partitions."""
from __future__ import annotations

from pathlib import Path
import math
from typing import Iterable

import networkx as nx
from gerrychain import Graph, Partition, updaters


REQUIRED_NODE_FIELDS = ("CD", "TOTPOP", "PRE20D", "PRE20R")


def _connect_components_within_district(graph: Graph, district_field: str = "CD") -> list[tuple]:
    """
    Add deterministic artificial bridge edges between disconnected geographic
    components that belong to the same enacted district.

    These edges represent water/island connectivity needed by the graph model.
    They must be documented as modeling edges, not literal shared borders.
    """
    added_edges: list[tuple] = []
    # GerryChain 0.3+ wraps NetworkX; Graph.nodes is no longer an NX NodeView.
    # Mutate the NetworkX backing graph while constructing the bridge convention.
    nx_graph = graph.get_nx_graph()

    while not nx.is_connected(nx_graph):
        components = sorted(nx.connected_components(nx_graph), key=len, reverse=True)
        main_component = components[0]
        connected_one = False

        main_nodes_by_district: dict[str, list] = {}
        for node in main_component:
            district = str(nx_graph.nodes[node].get(district_field))
            main_nodes_by_district.setdefault(district, []).append(node)

        for component in components[1:]:
            component_nodes_by_district: dict[str, list] = {}
            for node in component:
                district = str(nx_graph.nodes[node].get(district_field))
                component_nodes_by_district.setdefault(district, []).append(node)

            shared_districts = sorted(
                set(main_nodes_by_district) & set(component_nodes_by_district)
            )

            if not shared_districts:
                continue

            district = shared_districts[0]
            source = min(component_nodes_by_district[district])
            target = min(main_nodes_by_district[district])

            nx_graph.add_edge(
                source,
                target,
                artificial_bridge=True,
                bridge_reason="disconnected component within enacted district",
                shared_perim=0.0,
            )
            added_edges.append((source, target, district))
            connected_one = True
            break

        if not connected_one:
            component_sizes = sorted(
                (len(c) for c in nx.connected_components(nx_graph)),
                reverse=True,
            )
            raise ValueError(
                "Could not connect graph components without crossing enacted "
                f"districts. Component sizes: {component_sizes}"
            )

    return added_edges


def load_graph(path: str | Path) -> Graph:
    """Load a GerryChain JSON graph and repair documented island components."""
    graph_path = Path(path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file does not exist: {graph_path}")

    graph = Graph.from_json(str(graph_path))

    if len(graph) == 0:
        raise ValueError("Graph contains no nodes.")

    nx_graph = graph.get_nx_graph()
    if not nx.is_connected(nx_graph):
        component_sizes_before = sorted(
            (len(c) for c in nx.connected_components(nx_graph)),
            reverse=True,
        )

        added_edges = _connect_components_within_district(graph)

        print(
            "Connected disconnected geographic components using "
            f"{len(added_edges)} documented artificial bridge edges."
        )
        print(f"Original component sizes: {component_sizes_before}")

        for source, target, district in added_edges:
            print(
                f"  bridge: node {source} <-> node {target} "
                f"within enacted district {district}"
            )

    if not nx.is_connected(nx_graph):
        raise ValueError("Graph remains disconnected after bridge repair.")

    return graph


def validate_node_fields(graph: Graph, required: Iterable[str] = REQUIRED_NODE_FIELDS) -> None:
    """Reject missing, nonnumeric, nonfinite or negative population/election inputs.

    A zero-population precinct is allowed (water/islands may be unpopulated).
    Each election-scored district must nevertheless have strictly positive
    total two-party votes. This is input integrity, not a certified VEST join.
    """
    required = tuple(required)
    missing_by_field: dict[str, int] = {field: 0 for field in required}
    invalid_by_field: dict[str, int] = {field: 0 for field in required
                                      if field == "TOTPOP" or field.startswith("PRE")}
    district_vote_totals: dict[str, float] = {}

    for node in graph:
        attrs = graph.node_data(node)
        for field in required:
            if field not in attrs or attrs[field] is None:
                missing_by_field[field] += 1
                continue
            if field == "TOTPOP" or field.startswith("PRE"):
                try:
                    value = float(attrs[field])
                except (TypeError, ValueError, OverflowError):
                    invalid_by_field[field] += 1
                    continue
                if not math.isfinite(value) or value < 0:
                    invalid_by_field[field] += 1
        if "CD" in attrs and attrs["CD"] is not None:
            vote_fields = [f for f in required if f.startswith("PRE")]
            if len(vote_fields) == 2 and all(
                f in attrs and attrs[f] is not None for f in vote_fields
            ):
                try:
                    votes = [float(attrs[f]) for f in vote_fields]
                except (TypeError, ValueError, OverflowError):
                    continue
                if all(math.isfinite(v) and v >= 0 for v in votes):
                    label = str(attrs["CD"])
                    district_vote_totals[label] = district_vote_totals.get(label, 0.0) + sum(votes)

    missing = {k: v for k, v in missing_by_field.items() if v}
    invalid = {k: v for k, v in invalid_by_field.items() if v}
    if missing:
        raise KeyError(f"Missing required node attributes: {missing}")
    if invalid:
        raise ValueError(f"Invalid negative, nonnumeric or nonfinite node values: {invalid}")
    if any(f.startswith("PRE") for f in required):
        # A zero-total district produces undefined partisan vote shares and EG.
        zero = sorted(label for label, value in district_vote_totals.items() if value <= 0)
        if zero:
            raise ValueError(f"Districts with zero two-party votes: {zero}")


def make_updaters(dem_column: str = "PRE20D", rep_column: str = "PRE20R") -> dict:
    """Create the updaters tracked for every plan in the chain."""
    return {
        "population": updaters.Tally("TOTPOP", alias="population"),
        "dem_votes": updaters.Tally(dem_column, alias="dem_votes"),
        "rep_votes": updaters.Tally(rep_column, alias="rep_votes"),
        "cut_edges": updaters.cut_edges,
    }


def build_initial_partition(
    graph: Graph,
    assignment_column: str = "CD",
    dem_column: str = "PRE20D",
    rep_column: str = "PRE20R",
) -> Partition:
    """Build the enacted-plan partition from node attributes."""
    validate_node_fields(graph, (assignment_column, "TOTPOP", dem_column, rep_column))
    partition = Partition(
        graph=graph,
        assignment=assignment_column,
        updaters=make_updaters(dem_column, rep_column),
    )
    if len(partition) < 2:
        raise ValueError("Initial assignment must contain at least two districts.")
    return partition


def ideal_population(partition: Partition) -> float:
    populations = partition["population"]
    return float(sum(populations.values()) / len(populations))


def max_population_deviation(partition: Partition, target: float | None = None) -> float:
    """Maximum absolute fractional deviation from ideal district population."""
    target = ideal_population(partition) if target is None else float(target)
    if target <= 0:
        raise ValueError("Ideal population must be positive.")
    return max(abs(float(pop) / target - 1.0) for pop in partition["population"].values())
