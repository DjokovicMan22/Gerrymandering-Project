"""Proposal construction for redistricting ensembles."""
from __future__ import annotations

from functools import partial
from typing import Callable

from gerrychain.proposals import recom


def make_recom_proposal(
    ideal_population: float,
    epsilon: float,
    population_column: str = "TOTPOP",
    node_repeats: int = 2,
) -> Callable:
    """Return a configured ReCom proposal function."""
    if ideal_population <= 0:
        raise ValueError("ideal_population must be positive.")
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must be between 0 and 1.")
    if node_repeats < 1:
        raise ValueError("node_repeats must be at least 1.")

    return partial(
        recom,
        pop_col=population_column,
        pop_target=ideal_population,
        epsilon=epsilon,
        node_repeats=node_repeats,
    )
