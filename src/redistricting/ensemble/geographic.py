"""Exploratory geographic-fragmentation metrics and optional hard caps.

These precinct-level grouping proxies are NOT Michigan's legal redistricting
rules. In particular, COUNTYFIPS+MCDFIPS is only a source-data subdivision key,
not an independently verified municipality boundary or community of interest.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def _nx(graph: Any) -> Any:
    return graph.get_nx_graph() if hasattr(graph, "get_nx_graph") else graph


def _groups(graph: Any, fields: tuple[str, ...]) -> dict[tuple[str, ...], tuple[Any, ...]]:
    result: dict[tuple[str, ...], list[Any]] = defaultdict(list)
    for node, data in _nx(graph).nodes(data=True):
        key = []
        for field in fields:
            value = data.get(field)
            if value is None or str(value).strip().lower() in ("", "nan", "none"):
                raise ValueError(f"Missing or invalid {field} at node {node!r}; geographic cap cannot be audited")
            key.append(str(value).strip())
        result[tuple(key)].append(node)
    if not result:
        raise ValueError("Empty graph is not a valid geographic baseline")
    return {key: tuple(nodes) for key, nodes in result.items()}


def count_split_groups(assignment: Mapping, groups: Mapping) -> int:
    """Count source groups whose precincts have more than one district label."""
    return sum(len({assignment[node] for node in nodes}) > 1
               for nodes in groups.values())


@dataclass(frozen=True)
class GeographicCaps:
    """Optional structural guardrails; none of these imply legal compliance."""
    max_cut_edges: int | None = None
    max_split_counties: int | None = None
    max_split_county_mcd: int | None = None

    def __post_init__(self) -> None:
        for key in ("max_cut_edges", "max_split_counties", "max_split_county_mcd"):
            value = getattr(self, key)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{key} must be a nonnegative integer or None")

    @property
    def active(self) -> bool:
        return any(getattr(self, key) is not None for key in
                   ("max_cut_edges", "max_split_counties", "max_split_county_mcd"))


class GeographicEvaluator:
    """Precompute static precinct groups, then score changing district labels.

    Repeated assignments are expected in a constrained Markov chain. This is a
    descriptive score and exact hard-cap filter, not a likelihood or legal test.
    """

    def __init__(self, graph: Any, caps: GeographicCaps) -> None:
        self.caps = caps
        self.counties = (_groups(graph, ("COUNTYFIPS",))
                         if caps.max_split_counties is not None else None)
        self.county_mcd = (_groups(graph, ("COUNTYFIPS", "MCDFIPS"))
                           if caps.max_split_county_mcd is not None else None)

    def score(self, partition: Any) -> dict[str, int]:
        assignment = partition.assignment
        data = {"cut_edges": len(partition["cut_edges"])}
        if self.counties is not None:
            data["split_counties"] = count_split_groups(assignment, self.counties)
        if self.county_mcd is not None:
            data["split_county_mcd"] = count_split_groups(assignment, self.county_mcd)
        return data

    def __call__(self, partition: Any) -> bool:
        data = self.score(partition)
        caps = self.caps
        return all((
            caps.max_cut_edges is None or data["cut_edges"] <= caps.max_cut_edges,
            caps.max_split_counties is None or data["split_counties"] <= caps.max_split_counties,
            caps.max_split_county_mcd is None or data["split_county_mcd"] <= caps.max_split_county_mcd,
        ))

    def validate_reference(self, partition: Any) -> dict[str, int]:
        """Refuse an impossible experiment before constructing a Markov chain."""
        score = self.score(partition)
        if not self(partition):
            raise ValueError(f"Starting map exceeds requested geographic caps: {score}, {self.caps}")
        return score
