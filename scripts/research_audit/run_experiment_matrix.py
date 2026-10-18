#!/usr/bin/env python3
"""Run matched-budget Michigan ReCom comparisons through the original pipeline.

EXPLORATORY: the underlying ensemble enforces graph-contiguity/population only.
It does not enforce Michigan's complete legal redistricting criteria.
The command refuses to run unless --execute is provided.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "run_baseline.py"
VERIFIER = ROOT / "scripts" / "research_audit" / "verify_snapshots.py"
DIAGNOSTICS = ROOT / "scripts" / "research_audit" / "analyze_chains.py"

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--overwrite", action="store_true", help="Explicitly allow replacing existing experiment outputs")
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--burn-in", type=int, default=2000)
    ap.add_argument("--snapshot-interval", type=int, default=10)
    ap.add_argument("--seeds", type=int, nargs="+", default=[101, 202, 303, 404])
    ap.add_argument("--epsilons", type=float, nargs="+", default=[0.005, 0.02])
    args = ap.parse_args()
    if args.steps <= args.burn_in or args.burn_in < 1:
        ap.error("Need steps > burn-in >= 1")
    if not args.seeds or len(set(args.seeds)) != len(args.seeds):
        ap.error("Provide distinct random seeds")
    if args.snapshot_interval < 1 or any(not 0 < e < 1 for e in args.epsilons):
        ap.error("Invalid snapshot interval or population tolerances")
    if len(args.seeds) < 2:
        ap.error("At least two chains required for diagnostics")
    graph = ROOT / "data" / "raw" / "mi" / "mi" / "mi.json"
    if args.execute and not graph.exists():
        ap.error(f"Required local graph missing: {graph}")

    print("MODEL: GerryChain ReCom; contiguity + population only; not legally certified.")
    any_diagnostic_failure = False
    for epsilon in args.epsilons:
        names = []
        for seed in args.seeds:
            chain_id = f"stage3eps{str(epsilon).replace('.', 'p')}_chain{seed}"
            stem = f"mi_2020_{chain_id}_{args.steps}steps_seed{seed}"
            names.append(stem)
            cmd = [sys.executable, str(BASELINE), "--state", "mi",
                   "--election", "2020", "--epsilon", str(epsilon),
                   "--steps", str(args.steps), "--seed", str(seed),
                   "--chain-id", chain_id,
                   "--snapshot-interval", str(args.snapshot_interval)]
            print("+", " ".join(cmd))
            if args.execute:
                subprocess.run(cmd, check=True, cwd=ROOT)
        chain_dir = ROOT / "outputs" / "chains" / "week4"
        out = ROOT / "outputs" / "research_audit" / f"epsilon_{epsilon}"
        assignment_files = [chain_dir / (s + "_assignments.json") for s in names]
        metric_files = [chain_dir / (s + "_plan_metrics.csv") for s in names]
        if args.execute and not args.overwrite:
            existing = [p for p in assignment_files + metric_files if p.exists()]
            if existing:
                raise FileExistsError("Refusing to overwrite existing experiment artifacts. Use --overwrite after review: " + ", ".join(map(str, existing)))
        verification = [sys.executable, str(VERIFIER), "--graph", str(graph),
                        "--epsilon", str(epsilon), "--assignments",
                        *map(str, assignment_files), "--output",
                        str(out / "validated_snapshots.csv")]
        diagnostics = [sys.executable, str(DIAGNOSTICS), "--chains",
                       *map(str, metric_files), "--burn-in", str(args.burn_in),
                       "--epsilon", str(epsilon), "--out", str(out)]
        for cmd in (verification, diagnostics):
            print("+", " ".join(cmd))
            if args.execute:
                # Diagnostic exit 2 denotes inadequate mixing; save results and
                # continue to other conditions rather than hiding the failure.
                result = subprocess.run(cmd, cwd=ROOT, check=False)
                if cmd[1] == str(DIAGNOSTICS) and result.returncode == 2:
                    any_diagnostic_failure = True
                    print("NOT CERTIFIED: chain diagnostics did not pass for epsilon", epsilon, file=sys.stderr)
                if result.returncode not in (0, 2):
                    raise RuntimeError(f"Subprocess failed: {result.returncode}: {cmd}")
    if not args.execute:
        print("DRY RUN ONLY. Pass --execute to run. No simulations performed.")
    return 2 if any_diagnostic_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
