# Stage 3 — Empirical extension, robustness, and readiness audit

**Research project:** Beyond the Outlier: robustness and constraint-conditional congressional redistricting analysis  
**Study:** Michigan congressional 13-district counterfactual, with 2016 and 2020 presidential vote layers applied to 2021-adopted districts  
**Date of work:** 18 October 2026  
**Status:** **Significant executed empirical progress; NOT scientifically complete or approved for a definitive empirical paper.**

## Executive assessment

The stage 2 mathematical and source-output audit was complete but found that all 18,900 archived 2020 baseline ensemble observations were outside the Michigan commission's published approximately ±0.5% congressional mapping-population target. Stage 3 now demonstrates the **feasibility of a genuinely tighter population-constrained stochastic district recombination simulation** on the real public 4,756-node precinct graph. Thirteen short seeded chain runs, comprising 7,300 proposed transitions and 560 retained dependent observations across four model conditions, were executed on the public source graph. They show substantial sensitivity to model assumptions and a striking mismatch between sampled and reference geography.

**They do not establish a converged distribution, a sample of legally compliant plans, any proof of intent, or a defensible estimate of the probability that a commission would enact the reference map.** More independent computation and better geographic modeling are essential before framing primary results as journal-quality inference.

## 1. Exact external graph provenance and validation

Public research source: `eveomett-states/Michigan`, `mi.json`, Git blob SHA-1 `a4dfe70818f87b97924781216f3d86a672cfc66a`, 7,651,302 bytes. Repository README credits Ellen Veomett, Arbie Hsu and Alusi and Redistricting Data Hub / VEST inputs, and documents modification of very short precinct rook adjacencies. The raw data have CC BY-NC 4.0 and additional RDH restrictions. No source precinct input bytes are redistributed in this package. `src/download_source.py` enforces the exact Git blob ID and logs downloaded SHA-256 when run with local internet access.

Graph verified against the public GitHub blob through the connected GitHub interface: **4,756 nodes**, **12,378 source edges**, census population **10,077,331**, ideal population **775,179.30769**. District reference = 13 labels; max population deviation **0.00401931821** (0.4019%). The original graph contains six connected components of sizes **4,521, 227, 4, 2, 1, 1**. Five artificial bridges were introduced to connect disconnected graph pieces within the reference district, yielding **12,383 model edges**. Bridges are model artifacts, not verified physical land/water adjacencies.

Independent source integrity checks found **zero** node-index mismatches, duplicate `PRECINCTID` values, bad population/presidential-vote fields, or asymmetric adjacency relationships. The 2020 presidential two-party totals in this processed source are **2,804,046 Democratic** and **2,649,864 Republican**; 2016 values sum to about **2,268,777 Democratic** and **2,279,540 Republican**. **864 precinct records have fractional 2016 presidential values**, reflecting upstream allocation. Five precinct records have zero combined major-party 2020 votes, but the district totals used for scoring are positive. The optional `boundary_perim` field is null for many interior precincts and is **not used for a fabricated compactness calculation**. These are processed-input totals, not independently checked official statewide election totals.

The reference has **681 cut edges**, **14 counties split among two or more districts**, and **9 county-plus-township/municipality-code groups split** in the underlying precinct encoding. The public original graph and the archived baseline match on source population, reference cut edges and reference maximum deviation. This is **not** proof of byte-identical provenance for every original local file in the archived ZIP. The original ZIP was unavailable for raw-byte materialization in the current execution environment.

The 2020 reference yields **seven seats scored Democratic using the presidential two-party votes**. The continuous-half threshold wasted-vote efficiency gap, `(W_R − W_D)/two_party_total`, is approximately **+0.00333284**. Positive means a relative Democratic advantage. Our independent implementation uses continuous half-vote winner excess; the original stage 2 code used floor-half-plus-one, which produces a tiny numerical difference and should not be silently blended. The mean-minus-median difference is **mean district Democratic vote share − median**, with its sign labeled explicitly.

## 2. Method

The independently implemented sampler, `src/recom_experiment.js`, selects an edge whose endpoints are in different districts, merges those districts, independently assigns random real-valued weights to the merged induced-graph edges, builds a **randomized minimum spanning tree by Kruskal's algorithm**, selects a tree edge giving a population-feasible split, and assigns the resulting two tree components the original two labels. The algorithm tries up to 80 fresh random trees per proposed merge. If the chosen plan violates the optional cut-edge or geographic split restriction, or no qualifying tree split exists, the Markov chain retains its current state and records a rejection. Population balance and graph contiguity are checked for every *accepted* plan by the packaged runner.

This is a **ReCom-style research prototype, not the library's GerryChain ReCom**, and the i.i.d.-edge-weight random MST is **not a uniform spanning tree**. The resulting Markov stationary law is not proven uniform across maps. The transition process is explicitly defined and its inferential uncertainty is not hidden. All chains in these initial experiments start from the **same reference map**, so separate random seeds alone do not guarantee dispersed starting distributions.

County split counts and county+MCDFIPS group split counts are descriptive geographic proxies. The initial structural cap was **at most 900 graph cut edges**; the additional fourth model also imposes a limit of **24 split counties** and **49 split county+municipal-code units**. All these thresholds are research proxies, not legal Michigan compactness, county, or community-of-interest rules. The default model does **not** enforce communities of interest, incumbent neutrality, VRA opportunity districts, island county contiguity, detailed shoreline geometry, or all ranked constitutional criteria. Michigan law ranks multiple requirements beyond equal population and graph contiguity, so no model output is labeled a *legally valid plan*.

## 3. Executed experiments (short-run exploratory only)

| Model | Chains | Transitions per chain | Burn-in per chain | Retained samples total | Accepted / proposed | Mean Democratic seats (2020) | Mean EG (2020) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ±0.5%, cut-edge cap 900 | 4 | 700 | 200 | 200 | 2,709 / 2,800 | 5.695 | −0.10191 |
| ±0.5%, no cut-edge cap | 3 | 500 | 100 | 120 | 1,498 / 1,500 | 6.042 | −0.07490 |
| ±2%, cut-edge cap 900 | 3 | 500 | 100 | 120 | 1,413 / 1,500 | 5.867 | −0.08887 |
| ±0.5%, cut cap 900, ≤24 split counties, ≤49 split municipal-code units | 3 | 500 | 100 | 120 | 768 / 1,500 | 6.858 | −0.00674 |

Each chain retains one observation per 10 proposed transitions following the specified burn-in. These observations are highly correlated. Different chain lengths/burn-ins mean the table **does not support attributing differences exclusively to one changed model constraint**. It is a feasibility and sensitivity diagnostic. The source data, algorithm, seeds, burn-in and proposal budgets are declared, but the samples were computed via the connector-assisted JavaScript execution and only scalar run summaries plus one short-run metric trace were archived. The included standalone Node.js runner enables deterministic full-assignment snapshots in a subsequent local recomputation but **has not been used to recreate this exact full run from downloaded graph bytes inside the local container**. That is a reproducibility limitation.

The reference scores **seven Democratic seats, EG +0.00333**. In the first stricter capped condition, the raw fraction of 200 retained observations at least as high as the reference was **18% on Democratic seats** and **3% on EG**. These fractions must not be presented as p-values, uniform-map probabilities, or stable tail probabilities.

## 4. Geographic sensitivity and comparability

Averages by model:

| Model | Counties split | Municipal groups split | Graph cut edges |
|---|---:|---:|---:|
| Enacted reference | 14 | 9 | 681 |
| Strict, cap 900 | 33.90 | 73.87 | 829.87 |
| Strict, uncapped | 34.52 | 75.66 | 845.65 |
| Loose, cap 900 | 34.11 | 75.49 | 841.65 |
| Strict, geographic caps | 23.52 | 47.83 | 732.80 |

The difference is severe and indicates that the new ensemble fails an essential *geographic plausibility* comparison despite strictly balanced population and topological contiguity. The comparison distribution therefore cannot honestly be called legally informed on the basis of population tolerance alone. The 900-edge limit still permits substantially more geographic fragmentation than the reference. A fourth geographic-proxy model **was executed** (3 chains × 500 transitions; 120 retained, strongly dependent observations). The caps materially altered model behavior and caused frequent rejected proposals: acceptance rates were 52.2%, 54.6%, and 46.8% for seeds 101, 202 and 303, respectively. The result was strikingly chain-sensitive:

| Seed | Mean D seats | Mean EG | Tail fraction EG ≥ reference |
|---|---:|---:|---:|
| 101 | 6.400 | −0.04264 | 35% |
| 202 | 6.475 | −0.03574 | 40% |
| 303 | 7.700 | +0.05816 | 100% |

These are **not** estimates of the true probability of extreme plans. The opposite signs of chain-specific EG means and extreme tail disagreement are particularly strong warnings against treating this constrained sample as a stable stationary distribution. Constraints can induce proposal rejection and local trapping. Numeric caps are exploratory proxies, not authoritative state criteria. The narrowness of the geographic constraint is not enough to establish legal realism: the mean geographic split count remains far above the reference (23.52 vs 14 counties; 47.83 vs 9 municipal groups).

## 5. Short-run chain diagnostics

For the only condition with saved *per-observation traces* (strict ±0.5%, cut-edge cap 900; four chains, 50 retained values each), ArviZ reported:

| Metric | Rank/split R-hat (approx.) | Bulk ESS | Tail ESS |
|---|---:|---:|---:|
| Efficiency gap | **1.05** | **63** | **42** |
| Democratic seats | **1.12** | **44** | **80** |

Trace values for EG were rounded to five decimals before the diagnostic calculation. Results are approximate. Four short traces cannot rule out very slow mixing and clear **failure of a conservative R-hat ≤1.01 convergence gate**. Consequently, the simulation is not a scientifically defensible stationary ensemble. The numerical uncertainty and chain-to-chain variation make claims of exact reference-map outlier probability premature. Graph cut-edge and county-split differences compound the problem.

The figure `outputs/strict_cap900_eg_trace.png` displays chain-dependent metric variation. `outputs/geographic_mismatch.png` displays the split-county discrepancy. `src/diagnose_full.py` computes comprehensive future-run summaries from saved NDJSON output.

## 6. Prior 2016–2020 paired-year analysis (Stage 3 archive, separate from new runs)

An earlier Stage 3 analysis of the archived Week 4/6 saved chain summaries found that reference efficiency gap rose by approximately **0.04208** between presidential vote layers and the archived ensemble mean rose by approximately **0.04255**, so the reference-minus-ensemble contrast changed by about **−0.00047**. This is a useful and testable robustness *hypothesis*, not proof of stability for the stricter ensemble. Rank correlations between elections were much weaker than the similarity in sample mean differences suggested. The new runner scores both election layers for each retained map and retains selected uniform swing seat counts, making a clean paired analysis possible after full convergence work.

## 7. Delivered reproducibility tools and tests

- `src/recom_experiment.js`: seeded ReCom-style tree sampler, ± tolerance, cut and county/municipal split caps, sample-level 2016/2020 partisan/geographic metrics, full-assignment snapshots, rejection logging, per-source SHA-256 and bridge audit.
- `src/download_source.py`: exact public graph acquisition with content-addressed Git blob verification and SHA-256 provenance manifest.
- `src/verify_snapshots.py`: independent snapshot population/graph-contiguity checker.
- `src/diagnose.py`: independently analyzed the available 4 × 50 short-run traces, and produced figures/CSV.
- `src/diagnose_full.py`: full-run R-hat / ESS and reference-tail audit for newly generated NDJSON.
- `run_full_profile.sh`: predeclared matched-budget 4-condition **longer** experiment, four seeds, 8,000 transitions per chain and 2,000-step burn-in, plus snapshot checks. **Not executed** in this environment. This is a run recipe, not a claim of completed samples.
- `tests/test_engine.js`: **5 synthetic tests passed** using Node v22; tests include determinism, tight balance, contiguity, metric consistency and invalid-map rejection. Synthetic tests cannot establish full real-geography correctness.
- `outputs/experiment_summary.csv`, `outputs/group_summaries.csv`, `outputs/strict_cap900_traces.json`, `outputs/strict_cap900_diagnostics.csv`, PNG figures: research outputs. The trace file contains rounded, manually transcribed values, not original full-precision source arrays.

## 8. Readiness decision

**Stage 3 is NOT fully complete.** The following gates remain open:

1. Execute the packaged pipeline locally end to end on the verified real graph and archive complete assignments and per-step metadata.
2. Achieve satisfactory between-chain mixing, bulk and tail ESS, early/late-window agreement, stable rare-event estimates, and more dispersed initialization or explicit tempering/proposal comparisons.
3. Replace arbitrary cut and split limits with defensible county/municipal/compactness criteria, inspect the five artificial graph bridges, and analyze communities of interest / voting-rights requirements if making claims about legally plausible plans.
4. Run the **same** chain budgets across population and geographic sensitivities and directly compare paired 2016/2020 metrics on each common retained assignment.
5. Independently check geographic data joins, map labels and transformed election totals against original public source and authoritative statewide totals; retain source hashes and reproducible local manifests.
6. Reassess final research question and confine claims to what the actually sampled state space represents. Missouri must receive comparable provenance/validation if any conclusion generalizes to that second state.

A high-quality **methodological paper** about sensitivity, chain dependence, and failures of naive gerrymandering ensembles is already a plausible outcome. A definitive partisan-outlier paper based on the stricter, legally defensible distribution is **not yet** justified.

## References and source conditions

- [Michigan source repository](https://github.com/eveomett-states/Michigan) (CC BY-NC 4.0 and RDH terms).
- [Michigan Constitution Art. IV §6](https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6), ranked criteria for redistricting.
- [Michigan Independent Citizens Redistricting Commission mapping process](https://www.michigan.gov/micrc/mapping-process).
- DeFord, D., Duchin, M., and Solomon, J. *Recombination: A Family of Markov Chains for Redistricting* (2021).
- Cannon, S., Duchin, M., Randall, D., and Rule, P. *Spanning Tree Methods for Sampling Graph Partitions* (2022/2024).

**Interpretation standard:** Outlier percentages and robustness claims remain conditional on the model and its demonstrated sampling behavior. Statistical deviation from one simplified ensemble is neither a legal conclusion nor evidence of a mapmaker's intent.