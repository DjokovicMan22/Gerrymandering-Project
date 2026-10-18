#!/usr/bin/env python3
"""Compare matched-budget sampling chains begun at differently warmed maps.

IMPORTANT: Enacted-reference scores must come from explicitly stored reference
JSON, NEVER from any sampling chain's distinct step-0 warmup partition.
Scalar R-hat/ESS is diagnostic only, not proof of high-dimensional mixing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_chains import FIELDS, read_chains, summarize


def check_cohort(
    chain_files: list[Path], metadata_files: list[Path], reference_files: list[Path],
    condition: str,
) -> tuple[pd.Series, list[dict]]:
    if len(chain_files) != len(metadata_files) or len(chain_files) != len(reference_files):
        raise ValueError("Each chain must have a matching metadata and enacted-reference file")
    if len(chain_files) != 4:
        raise ValueError(f"Expected four independently warmed chains, got {len(chain_files)}")

    def stem(path: Path, suffix: str) -> str:
        if not path.name.endswith(suffix):
            raise ValueError(f"Unexpected filename: {path.name}")
        return path.name[:-len(suffix)]

    metrics_by_stem = {stem(p, "_plan_metrics.csv"):p for p in chain_files}
    meta_by_stem = {stem(p, "_metadata.json"):p for p in metadata_files}
    ref_by_stem = {stem(p, "_reference.json"):p for p in reference_files}
    if (len(metrics_by_stem) != 4 or set(metrics_by_stem) != set(meta_by_stem) or
            set(metrics_by_stem) != set(ref_by_stem)):
        raise ValueError("Input chain/metadata/reference stem mismatch")

    metas = []
    references = []
    for key in sorted(metrics_by_stem):
        meta = json.loads(meta_by_stem[key].read_text(encoding="utf-8"))
        original = json.loads(ref_by_stem[key].read_text(encoding="utf-8"))
        if meta.get("condition") != condition or meta.get("warmed_step0_is_reference") is not False:
            raise ValueError(f"{key}: wrong condition or accidentally started at enacted map")
        warm_meta = meta.get("warmup_metadata", {})
        if warm_meta.get("final_assignment_sha256") is None:
            raise ValueError(f"{key}: missing warm-start assignment identity")
        if (meta.get("reference_election_scores") != original or
                not set(FIELDS).issubset(original)):
            raise ValueError(f"{key}: enacted reference disagreement/missing fields")
        if not np.all(np.isfinite([original[field] for field in FIELDS])):
            raise ValueError(f"{key}: reference metrics include nonfinite values")
        if not all(meta.get("geographic_proxy_caps", {}).get(f) is not None for f in
                   ("max_cut_edges", "max_split_counties", "max_split_county_mcd")):
            raise ValueError(f"{key}: missing geographic proxy guardrails")
        refs_for_election = [meta.get("source_sha256"), meta.get("source_git_blob")]
        if not all(refs_for_election):
            raise ValueError(f"{key}: source provenance missing")
        metas.append(meta)
        references.append(original)
    if any(other != references[0] for other in references[1:]):
        raise ValueError("Not all chains use the same independently scored enacted reference")

    def distinct(key) -> bool:
        return len({value for value in key}) == len(metas)

    if not distinct(m["warmup_metadata"]["seed"] for m in metas):
        raise ValueError("Warmup seeds are not unique")
    if not distinct(m["sample_seed"] for m in metas):
        raise ValueError("Sampling seeds are not unique")
    if not distinct(m["warmup_metadata"]["final_assignment_sha256"] for m in metas):
        raise ValueError("Warmup maps are identical")
    if not all(m["warmup_distance_from_enacted"]["fraction_different"] >= .05 for m in metas):
        raise ValueError("At least one warm start fails the 5% enacted-reference gate")
    if len({m["source_sha256"] for m in metas}) != 1:
        raise ValueError("Inconsistent original source bytes")
    if len({json.dumps(m["geographic_proxy_caps"], sort_keys=True) for m in metas}) != 1:
        raise ValueError("Inconsistent geographic constraints")
    if len({m["sample_steps_including_warm_start"] for m in metas}) != 1:
        raise ValueError("Sample budgets differ")
    if len({m["warmup_metadata"]["warmup_states_including_reference"] for m in metas}) != 1:
        raise ValueError("Warmup budgets differ")
    return pd.Series(references[0]), metas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chains", type=Path, nargs="+", required=True)
    parser.add_argument("--metadata", type=Path, nargs="+", required=True)
    parser.add_argument("--references", type=Path, nargs="+", required=True)
    parser.add_argument("--condition", choices=("closer", "relaxed"), required=True)
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument("--epsilon", type=float, default=0.005)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.burn_in < 1 or not 0 < args.epsilon < 1:
        parser.error("Burn-in must be >=1 and epsilon must be between 0 and 1")
    enacted, metas = check_cohort(args.chains, args.metadata, args.references,
                                  args.condition)
    chains = read_chains(args.chains, args.burn_in)
    scores, result = summarize(chains, enacted, epsilon=args.epsilon)
    if not np.all(np.isfinite(scores["pooled_mean"])):
        raise ValueError("Nonfinite pooled metrics")
    result["condition"] = args.condition
    result["all_chains_started_from_reference"] = False
    result["common_warmup_ancestor_is_enacted"] = True
    result["enacted_reference_source"] = "four matching verified independent reference JSON files"
    result["reference_metrics"] = {k:float(enacted[k]) for k in FIELDS}
    result["warmup_hashes"] = [m["warmup_metadata"]["final_assignment_sha256"] for m in metas]
    result["warmup_endpoint_distances_from_enacted"] = [
        m["warmup_distance_from_enacted"]["fraction_different"] for m in metas
    ]
    result["sample_endpoint_distances_from_warmup"] = [
        m["final_sample_distance_from_warm_start"]["fraction_different"] for m in metas
    ]
    result["mean_sample_end_distance_from_warmup"] = float(np.mean(
        result["sample_endpoint_distances_from_warmup"]
    ))
    result["model_limitations"] = [
        "Warm-started chains have distinct maps but a shared enacted ancestor.",
        "Geographic split proxies are not Michigan's legally operative redistricting constraints.",
        "Artificial graph bridges are not independently verified physical contiguity.",
        "This ReCom/rejection kernel has no validated stationary distribution.",
        "Rank R-hat and ESS do not certify spatial mixing, stationarity, or legal probabilities.",
    ]
    result["research_readiness"] = "NOT CERTIFIED: stationary target and legal geography unverified"
    args.out.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.out / "scalar_diagnostics.csv", index=False)
    (args.out / "cohort_audit.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(scores.to_string(index=False))
    print("MODEL DISCLAIMER:", result["research_readiness"])
    print("SCALAR_GATE_PASS", result["all_scalar_diagnostic_gates_pass"])
    return 0 if result["all_scalar_diagnostic_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
