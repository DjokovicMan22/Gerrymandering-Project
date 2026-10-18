#!/usr/bin/env python3
"""Aggregate sparse exact-label-invariant checkpoint probes from diverse starts.

These are per-chain distances to a common enacted map and to each chain's own
warm starting map. Without redistributing complete assignments, pairwise
inter-chain *spatial* distances at later checkpoints cannot be reconstructed:
do not infer them from the scalar probes or from assignment hashes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


REQUIRED = {"step", "reference_fraction_different", "warm_start_fraction_different",
            "assignment_sha256"}


def analyze_spatial(paths: list[Path], expected_steps: tuple[int, ...] =
                    (0, 1000, 2000, 3000, 4000)
                    ) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if len(paths) != 4 or len({p.name for p in paths}) != 4:
        raise ValueError("Exactly four distinctly named probe CSVs required per condition")
    if len(set(expected_steps)) != len(expected_steps) or tuple(sorted(expected_steps)) != expected_steps:
        raise ValueError("Checkpoints must be ordered and distinct")
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        if not REQUIRED.issubset(df.columns):
            raise ValueError(f"{path}: missing columns {sorted(REQUIRED - set(df.columns))}")
        if tuple(int(v) for v in df["step"]) != expected_steps:
            raise ValueError(f"{path}: checkpoint indices do not match the protocol")
        for key in ("reference_fraction_different", "warm_start_fraction_different"):
            series = df[key]
            if not series.apply(lambda value: math.isfinite(float(value)) and 0 <= float(value) <= 1).all():
                raise ValueError(f"{path}: invalid finite fractional distances in {key}")
        if abs(float(df.iloc[0]["warm_start_fraction_different"])) > 1e-12:
            raise ValueError(f"{path}: checkpoint zero must be identical to the warm start")
        if not bool(df["assignment_sha256"].str.fullmatch(r"[0-9a-f]{64}").fillna(False).all()):
            raise ValueError(f"{path}: invalid assignment hash")
        df = df.assign(chain=path.name)
        frames.append(df)
    all_data = pd.concat(frames, ignore_index=True)
    if all_data.loc[all_data["step"] == 0, "assignment_sha256"].nunique() != 4:
        raise ValueError("Four warm-start assignment hashes must be distinct")
    summary = all_data.groupby("step", as_index=False).agg(
        reference_mean=("reference_fraction_different", "mean"),
        reference_min=("reference_fraction_different", "min"),
        reference_max=("reference_fraction_different", "max"),
        warm_mean=("warm_start_fraction_different", "mean"),
        warm_min=("warm_start_fraction_different", "min"),
        warm_max=("warm_start_fraction_different", "max"),
        unique_assignment_hashes=("assignment_sha256", "nunique"),
    )
    endpoint = all_data.loc[all_data["step"] == expected_steps[-1]].copy()
    context = {
        "expected_chains": 4,
        "checkpoints": list(expected_steps),
        "endpoint_min_movement_from_warmup": float(endpoint["warm_start_fraction_different"].min()),
        "endpoint_mean_movement_from_warmup": float(endpoint["warm_start_fraction_different"].mean()),
        "endpoint_unique_assignment_hashes": int(endpoint["assignment_sha256"].nunique()),
        "meaning": "Distances prove movement from warm starts, not convergence.",
        "limitation": (
            "Pairwise inter-chain map distances at the checkpoints cannot be "
            "reconstructed from individual reference/warmup distances and hashes. "
            "No direct estimate of high-dimensional spatial mixing is established."
        ),
    }
    return all_data, summary, context


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probes", nargs="+", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--condition", choices=("closer", "relaxed"), required=True)
    args = p.parse_args()
    raw, summary, result = analyze_spatial(args.probes)
    result["condition"] = args.condition
    args.out.mkdir(parents=True, exist_ok=True)
    raw.to_csv(args.out / "spatial_probes_by_chain.csv", index=False)
    summary.to_csv(args.out / "spatial_checkpoints_summary.csv", index=False)
    (args.out / "spatial_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
