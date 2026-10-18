"""Constraint helpers for GerryChain ensembles."""
from __future__ import annotations

from gerrychain import constraints
from gerrychain.partition import Partition

from .geographic import GeographicEvaluator


def build_constraints(initial_partition: Partition, epsilon: float,
                      geography: GeographicEvaluator | None = None) -> list:
    """Require contiguity and population balance at every chain step."""
    if not 0 < epsilon < 1:
        raise ValueError("epsilon must be between 0 and 1.")
    population_constraint = constraints.within_percent_of_ideal_population(
        initial_partition,
        epsilon,
    )
    checks = [constraints.contiguous, population_constraint]
    if geography is not None:
        geography.validate_reference(initial_partition)
        checks.append(geography)
    return checks
