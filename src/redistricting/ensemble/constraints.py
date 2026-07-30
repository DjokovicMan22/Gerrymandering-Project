"""Constraint helpers for GerryChain ensembles."""
from __future__ import annotations

from gerrychain import constraints
from gerrychain.partition import Partition


def build_constraints(initial_partition: Partition, epsilon: float) -> list:
    """Require contiguity and population balance at every chain step."""
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must be between 0 and 1.")
    population_constraint = constraints.within_percent_of_ideal_population(
        initial_partition,
        epsilon,
    )
    return [constraints.contiguous, population_constraint]
