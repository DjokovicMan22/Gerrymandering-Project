#!/usr/bin/env python3
"""Stage 2/3: reproducible diagnostics for archived plan-level chain CSVs.

Example:
 python scripts/research_audit/analyze_chains.py \\
   --chains outputs/chains/week4/mi_2020_chain*_plan_metrics.csv \\
   --burn-in 700 --out outputs/research_audit/baseline_2020

Input files must each hold one chain, indexed by an increasing 'step' column.
All R-hat/ESS estimates are diagnostics, not proof of mixing or uniformity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ("dem_seats", "efficiency_gap", "mean_median",
          "cut_edges", "max_population_deviation")


def read_chains(paths: list[Path], burn_in: int) -> dict[str, pd.DataFrame]:
    if len(paths) < 2:
        raise ValueError("At least two independently seeded chains are required")
    results = {}
    for path in paths:
        df = pd.read_csv(path)
        missing = set(FIELDS + ("step",)) - set(df.columns)
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        if df.empty or df["step"].duplicated().any() or not df["step"].is_monotonic_increasing:
            raise ValueError(f"{path}: empty, duplicated or out-of-order steps")
        if int(df["step"].iloc[0]) != 0:
            raise ValueError(f"{path}: expected reference plan at step 0")
        if not np.isfinite(df[list(FIELDS)].to_numpy(float)).all():
            raise ValueError(f"{path}: non-finite metrics")
        retained = df.loc[df["step"] >= burn_in].reset_index(drop=True)
        if len(retained) < 8:
            raise ValueError(f"{path}: insufficient post-burn-in observations")
        if path.name in results:
            raise ValueError(f"duplicate input: {path.name}")
        results[path.name] = retained
    if len({len(df) for df in results.values()}) != 1:
        raise ValueError("Use matched post-burn-in budgets across chains")
    return results


def summarize(chains: dict[str, pd.DataFrame], reference: pd.Series,
              epsilon: float = 0.005) -> tuple[pd.DataFrame, dict]:
    try:
        import arviz as az
    except ImportError as exc:
        raise RuntimeError("Install ArviZ for rank R-hat and bulk/tail ESS: pip install arviz") from exc

    rows = []
    diagnostics_pass = True
    for metric in FIELDS:
        data = np.stack([frame[metric].to_numpy(float) for frame in chains.values()])
        ref = float(reference[metric])
        n = data.size
        # ArviZ calculations account for rank normalisation and autocorrelation.
        try:
            rh = float(az.rhat(data, method="rank"))
            bulk = float(az.ess(data, method="bulk"))
            tail = float(az.ess(data, method="tail"))
        except Exception:
            rh = bulk = tail = float("nan")
        gate = bool(np.isfinite(rh) and rh <= 1.01 and
                    np.isfinite(bulk) and bulk >= 400 and
                    np.isfinite(tail) and tail >= 400)
        diagnostics_pass &= gate
        rows.append({
            "metric": metric, "reference": ref, "pooled_mean": float(data.mean()),
            "n_chains": data.shape[0], "saved_observations": n,
            "midrank_percentile": float(100 * ((data < ref).sum() + 0.5 * (data == ref).sum()) / n),
            "inclusive_upper_tail_fraction": float((data >= ref).sum() / n),
            "rank_rhat": rh, "bulk_ess": bulk, "tail_ess": tail,
            "scalar_diagnostic_gate": gate,
        })
    population = np.concatenate([f["max_population_deviation"].to_numpy(float)
                                 for f in chains.values()])
    overlap = int(np.count_nonzero(population <= epsilon + 1e-12))
    meta = {
        "chain_files": list(chains), "chains": len(chains),
        "retained_samples_per_chain": len(next(iter(chains.values()))),
        "total_correlated_observations": len(population),
        "population_tolerance_tested": epsilon,
        "observations_within_tolerance": overlap,
        "observations_outside_tolerance": int(len(population) - overlap),
        "all_scalar_diagnostic_gates_pass": diagnostics_pass,
        "research_readiness": "NOT CERTIFIED: geographic and legal constraints not tested",
        "notes": [
            "Sequential MCMC samples are not independent uniform maps.",
            "Tail fractions are empirical conditional frequencies, not legal findings or exact p-values.",
            "Scalar diagnostics alone never prove convergence of high-dimensional maps.",
            "This script does not verify original precinct geography or reproduce transitions."
        ],
    }
    return pd.DataFrame(rows), meta


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chains", nargs="+", type=Path, required=True)
    parser.add_argument("--burn-in", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epsilon", type=float, default=0.005)
    args = parser.parse_args()
    if args.burn_in < 1 or not 0 < args.epsilon < 1:
        parser.error("burn-in must be >=1, epsilon must be within (0,1)")
    # File globbing is handled by the shell. Quotes around '*' prevent expansion.
    frames = read_chains(args.chains, args.burn_in)
    original = pd.read_csv(args.chains[0])
    reference = original.loc[original["step"] == 0].iloc[0]
    summary, metadata = summarize(frames, reference, epsilon=args.epsilon)
    metadata["burn_in"] = args.burn_in
    args.out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out / "diagnostics.csv", index=False)
    (args.out / "audit.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print("Population overlap:", metadata["observations_within_tolerance"],
          "/", metadata["total_correlated_observations"])
    return 0 if metadata["all_scalar_diagnostic_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
