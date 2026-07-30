#!/usr/bin/env python3
"""Replay selected Week 4 chains and render Week 5 comparison maps.

The production CSVs store metrics but not every full precinct assignment. This
script uses the recorded random seeds and chain settings to replay only as far as
needed, captures the four selected assignments, verifies their metrics against
the saved CSVs, and draws the enacted/typical/directional-extreme map panel.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gerrychain import MarkovChain, accept

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from redistricting.ensemble.constraints import build_constraints
from redistricting.ensemble.partition import (
    build_initial_partition,
    ideal_population,
    load_graph,
)
from redistricting.ensemble.proposals import make_recom_proposal
from redistricting.ensemble.chain import partition_statistics

VALIDATE_METRICS = (
    "dem_seats",
    "efficiency_gap",
    "mean_median",
    "cut_edges",
    "max_population_deviation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--shapefile", type=Path, required=True)
    parser.add_argument("--name", default="mi_2020")
    parser.add_argument("--state-name", default="Michigan")
    parser.add_argument("--election-label", default="2020 presidential election")
    return parser.parse_args()


def project_path(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else PROJECT_ROOT / value


def metadata_path_for_plan(plan_path: Path) -> Path:
    return plan_path.with_name(
        plan_path.name.replace("_plan_metrics.csv", "_metadata.json")
    )


def replay_chain(
    plan_path: Path,
    targets: list[dict],
) -> dict[str, dict[str, str]]:
    metadata_path = metadata_path_for_plan(plan_path)
    if not metadata_path.exists():
        raise FileNotFoundError(metadata_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    stored = pd.read_csv(plan_path).set_index("step")

    graph_path = project_path(metadata["graph_path"])
    graph = load_graph(graph_path)
    partition = build_initial_partition(
        graph,
        assignment_column=metadata["assignment_column"],
        dem_column=metadata["dem_column"],
        rep_column=metadata["rep_column"],
    )
    target_population = ideal_population(partition)
    epsilon = float(metadata["epsilon"])
    node_repeats = int(metadata["node_repeats"])
    seed = int(metadata["seed"])

    desired_steps = {int(item["step"]) for item in targets}
    maximum_step = max(desired_steps)
    labels_by_step: dict[int, list[str]] = defaultdict(list)
    for item in targets:
        labels_by_step[int(item["step"])].append(str(item["selection"]))

    random.seed(seed)
    np.random.seed(seed)
    proposal = make_recom_proposal(
        ideal_population=target_population,
        epsilon=epsilon,
        node_repeats=node_repeats,
    )
    chain = MarkovChain(
        proposal=proposal,
        constraints=build_constraints(partition, epsilon),
        accept=accept.always_accept,
        initial_state=partition,
        total_steps=maximum_step + 1,
    )

    captured: dict[str, dict[str, str]] = {}
    for step, current in enumerate(chain):
        if step not in desired_steps:
            continue

        calculated, _ = partition_statistics(current, step, target_population)
        expected = stored.loc[step]
        for metric in VALIDATE_METRICS:
            if not np.isclose(
                float(calculated[metric]),
                float(expected[metric]),
                rtol=0.0,
                atol=1e-10,
                equal_nan=True,
            ):
                raise RuntimeError(
                    f"Replay mismatch at step {step}, metric {metric}: "
                    f"calculated={calculated[metric]} stored={expected[metric]}. "
                    "Do not use the recovered map until dependency versions and "
                    "random-state behavior are reconciled."
                )

        assignment = {
            str(node): str(district)
            for node, district in current.assignment.items()
        }
        for label in labels_by_step[step]:
            captured[label] = assignment
        print(f"Recovered and verified step {step:,} from {plan_path.name}")

        if len(captured) == len(targets):
            break

    missing = {str(item["selection"]) for item in targets} - set(captured)
    if missing:
        raise RuntimeError(f"Failed to recover selections: {sorted(missing)}")
    return captured


def assignment_for_geodataframe(
    gdf: gpd.GeoDataFrame,
    assignment: dict[str, str],
) -> list[str]:
    result = []
    missing = []
    for index in gdf.index:
        key = str(index)
        if key not in assignment:
            missing.append(key)
        else:
            result.append(assignment[key])
    if missing:
        raise KeyError(
            "Shapefile row indices do not match graph node IDs. "
            f"First missing IDs: {missing[:10]}"
        )
    return result


def display_label(selection: str) -> str:
    return {
        "enacted": "Enacted plan",
        "typical": "Typical sampled plan",
        "minimum_efficiency_gap": "Most negative efficiency gap",
        "maximum_efficiency_gap": "Most positive efficiency gap",
    }.get(selection, selection.replace("_", " ").title())


def render_maps(
    targets: list[dict],
    assignments: dict[str, dict[str, str]],
    shapefile: Path,
    output_path: Path,
    state_name: str,
    election_label: str,
) -> None:
    gdf = gpd.read_file(shapefile).reset_index(drop=True)
    if gdf.empty:
        raise ValueError(f"Empty shapefile: {shapefile}")

    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    axes = axes.ravel()
    ordered = [
        "enacted",
        "typical",
        "minimum_efficiency_gap",
        "maximum_efficiency_gap",
    ]
    records = {str(item["selection"]): item for item in targets}

    for axis, selection in zip(axes, ordered, strict=True):
        if selection not in records or selection not in assignments:
            axis.set_visible(False)
            continue
        record = records[selection]
        current = gdf.copy()
        current["_district"] = assignment_for_geodataframe(
            current, assignments[selection]
        )
        districts = current.dissolve(by="_district", as_index=False)
        districts["_plot_id"] = np.arange(len(districts))
        districts.plot(
            ax=axis,
            column="_plot_id",
            categorical=True,
            cmap="tab20",
            edgecolor="black",
            linewidth=0.7,
        )
        axis.set_axis_off()
        axis.set_title(
            f"{display_label(selection)}\n"
            f"step {int(record['step']):,} | D seats {int(record['dem_seats'])} | "
            f"EG {float(record['efficiency_gap']):+.3f}\n"
            f"mean–median {float(record['mean_median']):+.3f} | "
            f"cut edges {int(record['cut_edges'])}",
            fontsize=11,
            fontweight="bold",
        )

    fig.suptitle(
        f"{state_name}: enacted and representative ReCom plans\n{election_label}",
        fontsize=17,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.015,
        "Directional extremes are selected by efficiency gap within the sampled post-burn-in ensemble.",
        ha="center",
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0.035, 1, 0.94))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    targets_path = project_path(args.targets)
    shapefile_path = project_path(args.shapefile)
    targets = json.loads(targets_path.read_text(encoding="utf-8"))
    if not isinstance(targets, list) or not targets:
        raise ValueError("Targets JSON must contain a nonempty list.")

    grouped: dict[Path, list[dict]] = defaultdict(list)
    for item in targets:
        grouped[project_path(item["plan_csv"])].append(item)

    assignments: dict[str, dict[str, str]] = {}
    for plan_path, chain_targets in grouped.items():
        assignments.update(replay_chain(plan_path, chain_targets))

    chain_dir = PROJECT_ROOT / "outputs" / "chains" / "week5"
    figure_dir = PROJECT_ROOT / "outputs" / "figures" / "week5"
    chain_dir.mkdir(parents=True, exist_ok=True)
    assignments_path = chain_dir / f"{args.name}_selected_assignments.json"
    assignments_path.write_text(
        json.dumps(assignments, separators=(",", ":")), encoding="utf-8"
    )

    figure_path = figure_dir / f"{args.name}_plan_comparison_maps.png"
    render_maps(
        targets,
        assignments,
        shapefile_path,
        figure_path,
        args.state_name,
        args.election_label,
    )

    print("Saved:")
    print(f"  {assignments_path.relative_to(PROJECT_ROOT)}")
    print(f"  {figure_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
