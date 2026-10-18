"""Auditable, label-invariant map distance and seeded ReCom warm starts.

These are independent *random-seed trajectories from the same enacted map*,
NOT independent stationary draws from the legal or geographic plan space.
A diversity check measures endpoints without overstating independence.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass
from functools import lru_cache
from typing import Any, Mapping

import numpy as np
from gerrychain import MarkovChain, accept

from .constraints import build_constraints
from .geographic import GeographicCaps, GeographicEvaluator, GeographicHoldingProposal
from .partition import ideal_population, max_population_deviation
from .proposals import make_recom_proposal


def normalized_assignment(assignment: Mapping) -> dict[str, str]:
    """Normalize GerryChain node/district IDs for portable reproducibility."""
    normalized = {str(node): str(district) for node, district in assignment.items()}
    if len(normalized) != len(assignment):
        raise ValueError("Node IDs collide after conversion to strings")
    return normalized


def assignment_digest(assignment: Mapping) -> str:
    """Hash all precinct assignments without distributing precinct-level data."""
    clean = normalized_assignment(assignment)
    encoded = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def label_invariant_distance(left: Mapping, right: Mapping) -> dict[str, float | int]:
    """Exact minimum precinct mismatch after optimal one-to-one district relabeling.

    Solves a maximum-weight assignment by subset dynamic programming. For
    Michigan's 13 districts this is ~2^13 states, not 13! permutations.
    It prevents arbitrary label changes from masquerading as different maps.
    """
    a = normalized_assignment(left)
    b = normalized_assignment(right)
    if not a or set(a) != set(b):
        raise ValueError("Comparisons require the same nonempty precinct node set")
    la, lb = sorted(set(a.values())), sorted(set(b.values()))
    if len(la) != len(lb):
        raise ValueError("Comparisons require the same district count")
    k = len(la)
    if k > 18:
        raise ValueError("Exact subset matching supports at most 18 districts")
    ix_a, ix_b = {v: i for i, v in enumerate(la)}, {v: i for i, v in enumerate(lb)}
    weights = [[0] * k for _ in range(k)]
    for node in a:
        weights[ix_a[a[node]]][ix_b[b[node]]] += 1

    @lru_cache(None)
    def optimal(mask: int) -> int:
        row = mask.bit_count()
        if row == k:
            return 0
        return max(weights[row][col] + optimal(mask | (1 << col))
                   for col in range(k) if not mask & (1 << col))

    n = len(a)
    overlap = optimal(0)
    return {
        "precinct_nodes": n,
        "districts": k,
        "optimally_matched_nodes": overlap,
        "different_nodes": n - overlap,
        "fraction_different": (n - overlap) / n,
    }


@dataclass(frozen=True)
class WarmStartConfig:
    epsilon: float = 0.005
    steps_including_reference: int = 800
    node_repeats: int = 2
    max_cut_edges: int | None = 760
    max_split_counties: int | None = 18
    max_split_county_mcd: int | None = 20

    @property
    def caps(self) -> GeographicCaps:
        return GeographicCaps(
            self.max_cut_edges,
            self.max_split_counties,
            self.max_split_county_mcd,
        )

    def validate(self) -> None:
        if not 0 < self.epsilon < 1:
            raise ValueError("epsilon must be between 0 and 1")
        if self.steps_including_reference < 2:
            raise ValueError("warmup requires >=2 states, including the reference")
        if self.node_repeats < 1:
            raise ValueError("node_repeats must be positive")
        if not self.caps.active:
            raise ValueError("Require at least one explicit geographic cap for this pilot")


def warm_endpoint(reference: Any, seed: int, config: WarmStartConfig) -> tuple[dict, dict]:
    """Run one independently seeded, geographically capped ReCom warmup path.

    Output is one verified-feasibility candidate, not a stationary sample.
    GerryChain may retry built-in-invalid proposals; geographic-invalid
    proposals become explicit self-loops and are counted separately.
    """
    config.validate()
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("numpy/random seed must be an integer in [0, 2**32)")
    random.seed(seed)
    np.random.seed(seed)
    evaluator = GeographicEvaluator(reference.graph, config.caps)
    starting_geography = evaluator.validate_reference(reference)
    target = ideal_population(reference)
    proposal = GeographicHoldingProposal(
        make_recom_proposal(target, config.epsilon, node_repeats=config.node_repeats),
        evaluator,
    )
    chain = MarkovChain(
        proposal=proposal,
        constraints=build_constraints(reference, config.epsilon, geography=evaluator),
        accept=accept.always_accept,
        initial_state=reference,
        total_steps=config.steps_including_reference,
    )
    changed_steps = 0
    last_assignment: dict | None = None
    final = reference
    for _, partition in enumerate(chain):
        current = dict(partition.assignment.items())
        if last_assignment is not None and current != last_assignment:
            changed_steps += 1
        last_assignment = current
        final = partition
    assert last_assignment is not None  # Chain must yield its initial state.

    if not evaluator(final):
        raise ValueError("Final plan violated one or more geographic proxy caps")
    deviation = max_population_deviation(final, target)
    if deviation > config.epsilon + 1e-12:
        raise ValueError("Final plan violated its population tolerance")
    attempted = proposal.attempted
    if attempted != config.steps_including_reference - 1:
        raise ValueError(f"Expected one geographic proposal attempt per transition, got {attempted}")
    meta = {
        "seed": seed,
        "warmup_states_including_reference": config.steps_including_reference,
        "geographic_proposal_attempts": attempted,
        "geographic_rejections": proposal.geographic_rejected,
        "geographic_rejection_fraction": proposal.geographic_rejected / attempted,
        "changed_state_transitions": changed_steps,
        "change_fraction_per_recorded_transition": changed_steps / attempted,
        "final_max_population_deviation": deviation,
        "final_geographic_proxies": evaluator.score(final),
        "reference_geographic_proxies": starting_geography,
        "final_assignment_sha256": assignment_digest(last_assignment),
        "model_warning": (
            "Seeded warmup from the same enacted reference. Distinct endpoints "
            "are not independent stationary or uniformly sampled district plans."
        ),
    }
    return last_assignment, meta


def compare_seeded_endpoints(
    reference_assignment: Mapping,
    endpoints: Mapping[int, Mapping],
    *,
    minimum_pairwise_distance: float = 0.05,
    minimum_reference_distance: float = 0.05,
) -> tuple[list[dict], bool]:
    """Measure diversity and fail closed on non-diversified warmup endpoints."""
    if not 0 <= minimum_pairwise_distance <= 1 or not 0 <= minimum_reference_distance <= 1:
        raise ValueError("distance thresholds must be in [0,1]")
    if len(endpoints) < 2:
        raise ValueError("Need at least two separately seeded warmup endpoints")
    seeds = sorted(endpoints)
    rows = []
    viable = True
    for seed in seeds:
        delta = label_invariant_distance(reference_assignment, endpoints[seed])
        delta.update(comparison="reference_to_seed", seed_a="reference", seed_b=seed)
        rows.append(delta)
        viable &= delta["fraction_different"] >= minimum_reference_distance
    for i, first in enumerate(seeds):
        for second in seeds[i + 1:]:
            delta = label_invariant_distance(endpoints[first], endpoints[second])
            delta.update(comparison="seed_to_seed", seed_a=first, seed_b=second)
            rows.append(delta)
            viable &= delta["fraction_different"] >= minimum_pairwise_distance
    return rows, bool(viable)
