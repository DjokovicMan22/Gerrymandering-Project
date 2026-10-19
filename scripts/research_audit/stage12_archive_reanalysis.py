#!/usr/bin/env python3
"""Fail-closed, independent Stage 2 recomputation directly from the original packet ZIP.

Only archived plan-level metric histories are reproduced. No original MCMC
transition paths, legal geography, or independent district assignments are
present in the ZIP; none is claimed as validated here.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd

FIELDS = ("dem_seats", "efficiency_gap", "mean_median",
          "cut_edges", "max_population_deviation")
SEEDS = (101, 202, 303)
REFERENCE = {
    "2020": {"dem_seats": 7, "efficiency_gap": 0.003333204985047425,
             "cut_edges": 681, "max_population_deviation": 0.0040193182103474},
    "2016": {"dem_seats": 6, "efficiency_gap": -0.038749278029653667,
             "cut_edges": 681, "max_population_deviation": 0.0040193182103474},
}


def expected_paths() -> dict[str, tuple[int, int, int, str]]:
    paths = {}
    for year in ("2016", "2020"):
        for idx, seed in enumerate(SEEDS, start=1):
            name = f"outputs/chains/week4/mi_{year}_chain{idx}_7000steps_seed{seed}_plan_metrics.csv"
            paths[name] = (7000, 700, 0, year)
    for pct in (1, 3):
        for idx, seed in enumerate(SEEDS, start=1):
            name = f"outputs/chains/week6/mi_2020_eps{pct}pct_chain{idx}_3000steps_seed{seed}_plan_metrics.csv"
            paths[name] = (3000, 300, pct, "2020")
    return paths


def load_csv_bytes(content: bytes, *, name: str, steps: int, tolerance: float) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(content))
    missing = set(FIELDS + ("step",)) - set(df.columns)
    if missing:
        raise ValueError(f"{name}: missing fields {sorted(missing)}")
    if len(df) != steps or df["step"].isna().any() or df["step"].duplicated().any():
        raise ValueError(f"{name}: expected exactly {steps} distinct recorded steps")
    if not np.array_equal(df["step"].to_numpy(), np.arange(steps)):
        raise ValueError(f"{name}: nonsequential step identifiers")
    metrics = df[list(FIELDS)].to_numpy(dtype=float)
    if not np.isfinite(metrics).all():
        raise ValueError(f"{name}: nonfinite archived statistics")
    if ((df["dem_seats"] < 0) | (df["dem_seats"] > 13) |
        (df["dem_seats"] % 1 != 0)).any():
        raise ValueError(f"{name}: invalid Democratic seat count")
    if ((df["cut_edges"] < 0) | (df["cut_edges"] % 1 != 0)).any():
        raise ValueError(f"{name}: invalid boundary-edge count")
    if ((df["max_population_deviation"] < 0) |
        (df["max_population_deviation"] > tolerance + 1e-9)).any():
        raise ValueError(f"{name}: violated original declared population tolerance")
    return df


def check_reference(df: pd.DataFrame, year: str, name: str) -> None:
    for metric, value in REFERENCE[year].items():
        if not math.isclose(float(df.iloc[0][metric]), value, rel_tol=1e-6, abs_tol=2e-6):
            raise ValueError(f"{name}: archived step-0 {metric} disagrees with source reference")


def summarize_frames(frames: list[pd.DataFrame], burn: int, reference: pd.Series) -> dict:
    retained = pd.concat([df.iloc[burn:] for df in frames], ignore_index=True)
    if len(retained) != len(frames) * (len(frames[0]) - burn):
        raise ValueError("Incorrect pooled post-burn-in row count")
    summary = {"retained_correlated_observations": len(retained),
               "retained_per_chain": len(frames[0]) - burn,
               "burn_in": burn}
    for metric in FIELDS:
        vals = retained[metric].to_numpy(dtype=float)
        ref = float(reference[metric])
        summary[metric] = {
            "mean": float(vals.mean()),
            "reference": ref,
            "midrank_percentile": float(100 * ((vals < ref).sum() + 0.5 * (vals == ref).sum()) / len(vals)),
            "inclusive_upper_tail_count": int((vals >= ref).sum()),
            "inclusive_upper_tail_fraction": float((vals >= ref).mean()),
        }
    pop = retained["max_population_deviation"].to_numpy(dtype=float)
    summary["count_within_0p5pct_population_tolerance"] = int((pop <= .005 + 1e-12).sum())
    summary["fraction_within_0p5pct_population_tolerance"] = float((pop <= .005 + 1e-12).mean())
    return summary


def reanalyze(packet: Path) -> dict:
    if not packet.is_file():
        raise FileNotFoundError(packet)
    manifest = {
        "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
        "packet_size_bytes": packet.stat().st_size,
        "original_packet_path": str(packet),
        "source_type": "archived_plan_level_metric_histories_only",
        "independently_replayed_original_MCMC_transitions": False,
        "original_precinct_assignments_available_in_packet": False,
        "legal_map_ensemble_certified": False,
        "archived_chain_metrics": {},
    }
    frames = {}
    paths = expected_paths()
    with ZipFile(packet) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("ZIP contains duplicate member names")
        for name, (steps, burn, pct, year) in paths.items():
            if name not in names:
                raise ValueError(f"Required archived chain absent: {name}")
            raw = z.read(name)
            tolerance = {0: .02, 1: .01, 3: .03}[pct]
            df = load_csv_bytes(raw, name=name, steps=steps, tolerance=tolerance)
            check_reference(df, year, name)
            frames[name] = df
            manifest["archived_chain_metrics"][name] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "rows": len(df),
                "step0_reference_verified": True,
            }
    results = {"source_integrity": manifest, "conditions": {},
               "paired_geographic_trajectories_match": {},
               "claims": ["Archived scalar outputs independently recomputed from original packet ZIP.",
                          "All archived histories are serially correlated MCMC observations.",
                          "Original transitions cannot be reconstructed byte-for-byte from saved scalar histories.",
                          "Archived percentiles are not legal-map p-values."]}
    for year in ("2016", "2020"):
        selected = [frames[f"outputs/chains/week4/mi_{year}_chain{i}_7000steps_seed{seed}_plan_metrics.csv"]
                    for i, seed in enumerate(SEEDS, start=1)]
        results["conditions"][f"{year}_2pct"] = summarize_frames(selected, 700, selected[0].iloc[0])
    for pct in (1, 3):
        selected = [frames[f"outputs/chains/week6/mi_2020_eps{pct}pct_chain{i}_3000steps_seed{seed}_plan_metrics.csv"]
                    for i, seed in enumerate(SEEDS, start=1)]
        results["conditions"][f"2020_{pct}pct"] = summarize_frames(selected, 300, selected[0].iloc[0])
    for i, seed in enumerate(SEEDS, start=1):
        p16 = frames[f"outputs/chains/week4/mi_2016_chain{i}_7000steps_seed{seed}_plan_metrics.csv"]
        p20 = frames[f"outputs/chains/week4/mi_2020_chain{i}_7000steps_seed{seed}_plan_metrics.csv"]
        equal = bool(np.array_equal(p16["cut_edges"].to_numpy(), p20["cut_edges"].to_numpy()) and
                     np.array_equal(p16["max_population_deviation"].to_numpy(),
                                    p20["max_population_deviation"].to_numpy()))
        if not equal:
            raise ValueError(f"2016 and 2020 geographic traces differ for seed {seed}")
        results["paired_geographic_trajectories_match"][str(seed)] = True

    baseline = results["conditions"]["2020_2pct"]
    if baseline["retained_correlated_observations"] != 18900:
        raise ValueError("Unexpected baseline observation count")
    if baseline["count_within_0p5pct_population_tolerance"] != 0:
        raise ValueError("Baseline ±2% population overlap disagrees with independently audited archive")
    if results["conditions"]["2020_1pct"]["count_within_0p5pct_population_tolerance"] != 4:
        raise ValueError("±1% population overlap disagrees with audited archive")
    if results["conditions"]["2020_3pct"]["count_within_0p5pct_population_tolerance"] != 0:
        raise ValueError("±3% population overlap disagrees with audited archive")
    if not math.isclose(baseline["dem_seats"]["mean"], 5.714921, abs_tol=2e-6):
        raise ValueError("2020 archived Democratic-seat mean disagrees with independent baseline")
    if not math.isclose(baseline["efficiency_gap"]["mean"], -.0999194, abs_tol=2e-6):
        raise ValueError("2020 archived efficiency-gap mean disagrees with independent baseline")
    if not math.isclose(baseline["dem_seats"]["inclusive_upper_tail_fraction"],
                        2633 / 18900, abs_tol=1e-12):
        raise ValueError("Incorrect handling of tied Democratic-seat counts")
    if not math.isclose(baseline["efficiency_gap"]["inclusive_upper_tail_fraction"],
                        742 / 18900, abs_tol=1e-12):
        raise ValueError("Efficiency-gap upper tail disagrees with archived baseline")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = reanalyze(args.packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False), encoding="utf-8")
    print("STAGE2_ARCHIVE_INDEPENDENT_REANALYSIS_PASS")
    print("PACKET_SHA256", results["source_integrity"]["packet_sha256"])
    for condition, values in results["conditions"].items():
        print("CONDITION", condition, json.dumps({
            "observations": values["retained_correlated_observations"],
            "dem_seats_mean": values["dem_seats"]["mean"],
            "efficiency_gap_mean": values["efficiency_gap"]["mean"],
            "count_population_0p5pct": values["count_within_0p5pct_population_tolerance"],
        }, sort_keys=True))
    print("NOTE: source assignments and original stochastic transitions not reconstructed")


if __name__ == "__main__":
    main()
