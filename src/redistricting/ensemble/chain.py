"""Run ReCom chains and convert partitions into analysis-ready tables."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from gerrychain import MarkovChain, accept

from .constraints import build_constraints
from .partition import ideal_population, max_population_deviation
from .proposals import make_recom_proposal


@dataclass(frozen=True)
class ChainConfig:
    total_steps: int = 1_000
    epsilon: float = 0.02
    node_repeats: int = 2
    seed: int = 2026
    snapshot_interval: int = 0

    def validate(self) -> None:
        if self.total_steps < 2:
            raise ValueError("total_steps must be at least 2 (the initial plan is step 0).")
        if not 0 < self.epsilon < 1:
            raise ValueError("epsilon must be between 0 and 1.")
        if self.node_repeats < 1:
            raise ValueError("node_repeats must be at least 1.")
        if self.snapshot_interval < 0:
            raise ValueError("snapshot_interval cannot be negative.")


def _winning_threshold(total_votes: float) -> int:
    return math.floor(total_votes / 2.0) + 1


def exact_efficiency_gap(dem_votes: list[float], rep_votes: list[float]) -> float:
    """(Republican wasted - Democratic wasted) / total two-party votes."""
    dem_wasted = 0.0
    rep_wasted = 0.0
    total_votes = 0.0

    for dem, rep in zip(dem_votes, rep_votes, strict=True):
        dem = float(dem)
        rep = float(rep)
        total = dem + rep
        if total <= 0:
            continue
        total_votes += total
        threshold = _winning_threshold(total)
        if dem > rep:
            dem_wasted += max(0.0, dem - threshold)
            rep_wasted += rep
        elif rep > dem:
            dem_wasted += dem
            rep_wasted += max(0.0, rep - threshold)
        else:
            dem_wasted += dem
            rep_wasted += rep

    return np.nan if total_votes <= 0 else (rep_wasted - dem_wasted) / total_votes


def partition_statistics(partition, step: int, target_population: float) -> tuple[dict, list[dict]]:
    """Return one plan-level row and district-level vote-share rows."""
    district_ids = sorted(partition.parts, key=lambda value: str(value))
    dem_by_district = partition["dem_votes"]
    rep_by_district = partition["rep_votes"]

    dem_votes = [float(dem_by_district[d]) for d in district_ids]
    rep_votes = [float(rep_by_district[d]) for d in district_ids]
    totals = np.asarray(dem_votes) + np.asarray(rep_votes)
    shares = np.divide(
        np.asarray(dem_votes),
        totals,
        out=np.full(len(totals), np.nan, dtype=float),
        where=totals > 0,
    )

    valid_shares = shares[~np.isnan(shares)]
    dem_seats = int(np.sum(shares > 0.5))
    tied_seats = int(np.sum(shares == 0.5))
    statewide_dem_share = float(np.sum(dem_votes) / np.sum(totals)) if np.sum(totals) > 0 else np.nan
    mean_median = (
        float(np.median(valid_shares) - np.mean(valid_shares))
        if len(valid_shares)
        else np.nan
    )

    plan_row = {
        "step": step,
        "district_count": len(district_ids),
        "dem_seats": dem_seats,
        "rep_seats": len(district_ids) - dem_seats - tied_seats,
        "tied_seats": tied_seats,
        "statewide_dem_share": statewide_dem_share,
        "efficiency_gap": exact_efficiency_gap(dem_votes, rep_votes),
        "mean_median": mean_median,
        "cut_edges": len(partition["cut_edges"]),
        "max_population_deviation": max_population_deviation(partition, target_population),
    }

    district_rows = [
        {
            "step": step,
            "district": str(district),
            "dem_votes": dem,
            "rep_votes": rep,
            "two_party_votes": dem + rep,
            "dem_share": share,
        }
        for district, dem, rep, share in zip(
            district_ids, dem_votes, rep_votes, shares.tolist(), strict=True
        )
    ]
    return plan_row, district_rows


def run_recom_chain(initial_partition, config: ChainConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[int, dict]]:
    """Run a ReCom chain and return plan metrics, district metrics, and snapshots."""
    config.validate()
    random.seed(config.seed)
    np.random.seed(config.seed)

    target_population = ideal_population(initial_partition)
    proposal = make_recom_proposal(
        ideal_population=target_population,
        epsilon=config.epsilon,
        node_repeats=config.node_repeats,
    )
    chain = MarkovChain(
        proposal=proposal,
        constraints=build_constraints(initial_partition, config.epsilon),
        accept=accept.always_accept,
        initial_state=initial_partition,
        total_steps=config.total_steps,
    )

    plan_rows: list[dict] = []
    district_rows: list[dict] = []
    snapshots: dict[int, dict] = {}

    for step, partition in enumerate(chain):
        plan_row, current_district_rows = partition_statistics(
            partition, step, target_population
        )
        plan_rows.append(plan_row)
        district_rows.extend(current_district_rows)

        if config.snapshot_interval and step % config.snapshot_interval == 0:
            snapshots[step] = {
                str(node): str(district)
                for node, district in partition.assignment.items()
            }

        if step == 0 or (step + 1) % max(1, min(100, config.total_steps // 10)) == 0:
            print(
                f"step {step + 1:,}/{config.total_steps:,} | "
                f"D seats={plan_row['dem_seats']} | "
                f"cut edges={plan_row['cut_edges']}",
                flush=True,
            )

    return pd.DataFrame(plan_rows), pd.DataFrame(district_rows), snapshots


def save_chain_outputs(
    plan_metrics: pd.DataFrame,
    district_metrics: pd.DataFrame,
    snapshots: dict[int, dict],
    output_directory: str | Path,
    run_name: str,
    metadata: dict,
) -> dict[str, Path]:
    """Save chain outputs atomically enough for ordinary local research use."""
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    paths = {
        "plan_metrics": output_directory / f"{run_name}_plan_metrics.csv",
        "district_metrics": output_directory / f"{run_name}_district_metrics.csv",
        "metadata": output_directory / f"{run_name}_metadata.json",
    }
    plan_metrics.to_csv(paths["plan_metrics"], index=False)
    district_metrics.to_csv(paths["district_metrics"], index=False)

    metadata = dict(metadata)
    metadata["rows"] = {
        "plan_metrics": len(plan_metrics),
        "district_metrics": len(district_metrics),
    }
    paths["metadata"].write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if snapshots:
        paths["snapshots"] = output_directory / f"{run_name}_assignments.json"
        paths["snapshots"].write_text(json.dumps(snapshots), encoding="utf-8")

    return paths
