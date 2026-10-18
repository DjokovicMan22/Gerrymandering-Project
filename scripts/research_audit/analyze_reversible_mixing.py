#!/usr/bin/env python3
"""Independently aggregate verified, matched-length reversible MH chains.

This diagnoses empirical mixing under *one* proxy-constrained model. It never
asserts stationarity, component irreducibility, or Michigan legal-plan validity.
The enacted reference comes from explicit source-derived JSON—not warm step 0.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from analyze_chains import FIELDS, read_chains, summarize


def _stem(path: Path, suffix: str) -> str:
    if not path.name.endswith(suffix):
        raise ValueError(f"Expected suffix {suffix!r} in {path.name}")
    return path.name[:-len(suffix)]


def validate_mh_cohort(
    paths: list[Path], metadata_paths: list[Path], reference_paths: list[Path],
    *, condition: str, expected_states: int,
) -> tuple[pd.Series, list[dict]]:
    """Fail closed on any mix of different kernels, warmups, conditions or sources."""
    if len(paths) != 4 or len(metadata_paths) != 4 or len(reference_paths) != 4:
        raise ValueError("Require exactly four scored chains, four metadata and four references")
    csv = {_stem(x, "_plan_metrics.csv"): x for x in paths}
    metas = {_stem(x, "_metadata.json"): x for x in metadata_paths}
    refs = {_stem(x, "_reference.json"): x for x in reference_paths}
    if len(csv) != 4 or set(csv) != set(metas) or set(csv) != set(refs):
        raise ValueError("Reference/metadata/score stems missing, duplicated or mismatched")

    summaries = []
    reference = None
    for name in sorted(csv):
        meta = json.loads(metas[name].read_text(encoding="utf-8"))
        ref = json.loads(refs[name].read_text(encoding="utf-8"))
        if meta.get("kernel") != "boundary_uniform_choice_local_flip_swap_mh_v1":
            raise ValueError(f"{name}: unexpected stationary-law/proposal kernel")
        if meta.get("warmed_step0_is_reference") is not False:
            raise ValueError(f"{name}: reference improperly equated with warm step 0")
        if meta.get("states") != expected_states or meta.get("config", {}).get("epsilon") != .005:
            raise ValueError(f"{name}: mismatched simulation budget or population tolerance")
        if meta.get("config", {}).get("flip_probability") != .5:
            raise ValueError(f"{name}: mismatched MH move mixture")
        if not meta.get("warm_start_sha256") or meta.get("warm_seed") == meta.get("sample_seed"):
            raise ValueError(f"{name}: missing/distorted warm-seed provenance")
        if not meta.get("source_sha256") or meta.get("source_blob_sha1") != (
            "a4dfe70818f87b97924781216f3d86a672cfc66a"
        ):
            raise ValueError(f"{name}: missing/mismatched pinned source graph")
        if "reference_election_scores" not in meta or ref != meta["reference_election_scores"]:
            raise ValueError(f"{name}: separately rescored enacted reference mismatch")
        if not set(FIELDS).issubset(ref):
            raise ValueError(f"{name}: missing enacted reference metrics")
        if not all(math.isfinite(float(ref[k])) for k in FIELDS):
            raise ValueError(f"{name}: non-finite enacted reference")
        if reference is None:
            reference = ref
        elif ref != reference:
            raise ValueError(f"{name}: incompatible enacted reference across seeds")
        observed = pd.read_csv(csv[name])
        if len(observed) != expected_states or not np.array_equal(
            observed["step"].to_numpy(), np.arange(expected_states)
        ):
            raise ValueError(f"{name}: missing/duplicate sampled transitions")
        needed = ["mh_attempted_total", "mh_accepted_total", "state_changed_since_previous",
                  "mh_population_rejected_total", "mh_contiguity_rejected_total",
                  "mh_geography_rejected_total", "mh_ratio_rejected_total"]
        if any(key not in observed for key in needed):
            raise ValueError(f"{name}: incomplete transition accounting")
        for key in needed:
            values=observed[key].to_numpy()
            if not np.isfinite(values.astype(float)).all() or np.any(values < 0):
                raise ValueError(f"{name}: invalid counters")
        if not np.array_equal(observed["mh_attempted_total"].to_numpy(),
                              np.arange(expected_states)):
            raise ValueError(f"{name}: missing proposals, hidden retries or state indexing")
        final = observed.iloc[-1]
        categories = ("mh_accepted_total", "mh_population_rejected_total",
                      "mh_contiguity_rejected_total", "mh_geography_rejected_total",
                      "mh_ratio_rejected_total")
        if abs(sum(float(final[key]) for key in categories) - (expected_states-1)) > 0:
            raise ValueError(f"{name}: MH accept/reject accounting does not conserve proposals")
        if int(observed["state_changed_since_previous"].sum()) != int(final["mh_accepted_total"]):
            raise ValueError(f"{name}: actual state moves disagree with accepted MH transitions")
        if not (meta.get("config", {}).get("max_cut_edges") is not None and
                meta.get("config", {}).get("max_split_counties") is not None and
                meta.get("config", {}).get("max_split_county_mcd") is not None):
            raise ValueError(f"{name}: incomplete geographic caps")
        if condition == "closer":
            caps = (760, 18, 20)
        elif condition == "relaxed":
            caps = (850, 24, 49)
        else:
            raise ValueError("Unknown geographic condition")
        if tuple(meta["config"].get(k) for k in ("max_cut_edges", "max_split_counties",
                                                   "max_split_county_mcd")) != caps:
            raise ValueError(f"{name}: mixed geographic proxy conditions")
        for key, cap in zip(("cut_edges", "split_counties", "split_county_mcd"), caps):
            if key not in observed or not (observed[key] <= cap).all():
                raise ValueError(f"{name}: sampled maps exceed geographic proxy cap")
        if (observed["max_population_deviation"] > .005 + 1e-12).any():
            raise ValueError(f"{name}: invalid sampled population deviation")
        summaries.append({
            "stem": name,
            "warm_seed": meta["warm_seed"],
            "sample_seed": meta["sample_seed"],
            "warm_start_sha256": meta["warm_start_sha256"],
            "acceptance_rate": float(final["mh_accepted_total"] / (expected_states - 1)),
            "accepted_transitions": int(final["mh_accepted_total"]),
            "population_rejections": int(final["mh_population_rejected_total"]),
            "contiguity_rejections": int(final["mh_contiguity_rejected_total"]),
            "geography_rejections": int(final["mh_geography_rejected_total"]),
            "mh_ratio_rejections": int(final["mh_ratio_rejected_total"]),
            "unique_efficiency_gap_values": int(observed["efficiency_gap"].nunique()),
            "final_distance_from_warm": float(
                meta.get("final_from_warm", {}).get("fraction_different", float("nan"))
            ),
        })
    if any(len(set(item[key] for item in summaries)) != 4 for key in
           ("warm_seed", "sample_seed", "warm_start_sha256")):
        raise ValueError("Sampling chains not initialized from four distinct seeded warm maps")
    return pd.Series(reference), summaries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chains", type=Path, nargs="+", required=True)
    ap.add_argument("--metadata", type=Path, nargs="+", required=True)
    ap.add_argument("--references", type=Path, nargs="+", required=True)
    ap.add_argument("--condition", choices=("closer","relaxed"), required=True)
    ap.add_argument("--states", type=int, required=True)
    ap.add_argument("--burn-in", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args=ap.parse_args()
    if args.burn_in < 1 or args.states-args.burn_in < 100:
        ap.error("Must reserve >=100 post-burn-in correlated states")
    reference, summaries=validate_mh_cohort(
        args.chains, args.metadata, args.references,
        condition=args.condition, expected_states=args.states,
    )
    chains = read_chains(args.chains, args.burn_in)
    metrics, audit = summarize(chains, reference, epsilon=.005)
    audit["sampler"] = "reversible boundary MH local flips and swaps"
    audit["condition"] = args.condition
    audit["burn_in"] = args.burn_in
    audit["conclusion"] = (
        "Scalar R-hat/ESS GATES PASSED (not proof of spatial mixing)"
        if audit["all_scalar_diagnostic_gates_pass"]
        else "SCALAR CONVERGENCE GATES FAILED; no stationary inference"
    )
    audit["legal_map_validity"] = "NOT CERTIFIED (artificial graph bridges, proxy geography, VRA omitted)"
    audit["stationary_law"] = (
        "Uniform within each reachable feasible labeled assignment communication class. "
        "Reachability of all feasible maps is unproven."
    )
    args.out.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.out/"rhat_ess.csv", index=False)
    pd.DataFrame(summaries).to_csv(args.out/"acceptance_by_chain.csv",index=False)
    (args.out/"audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    print(metrics.to_string(index=False),flush=True)
    print(pd.DataFrame(summaries).to_string(index=False),flush=True)
    print("VERDICT:",audit["conclusion"],flush=True)
    return 0 if audit["all_scalar_diagnostic_gates_pass"] else 2


if __name__=="__main__":
    raise SystemExit(main())
