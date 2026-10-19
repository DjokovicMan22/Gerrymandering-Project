# Stage 3 final report — reproducible Michigan modeling and finite-horizon robustness

**Research decision: BOUNDED STAGE 3 COMPLETE, ORIGINAL NEUTRAL-ENSEMBLE HYPOTHESIS NOT VALIDATED.**  
**Date:** 18 October 2026 (Pacific); GitHub Actions executed 19 October 2026 UTC.  
**Branch:** `research/stages-1-3-validation`; original `main` unchanged.  
**Authoritative successful experiment:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152601  
**Current reproducibility/test CI:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180311321  
**Predeclared replacement protocol:** [stage3_finite_horizon_protocol.md](stage3_finite_horizon_protocol.md)  
**Underlying complete source experiment output:** GitHub Actions artifact `stage3-finite-horizon-final-methodological-outcomes` (on the authoritative successful run).

## Executive finding

This stage began with an ambitious scientific objective: compare an enacted Michigan congressional plan against an ensemble of neutral, legally valid, sufficiently mixed alternatives and quantify its statistical extremeness. **That objective was not achieved and may not be claimed.** Detailed testing demonstrated why: (a) a historic graph-completion rule introduced arbitrary, far-separated node connections selected according to enacted districts; (b) both ordinary ReCom and an analytically reversible alternative failed prespecified mixing/convergence thresholds under stringent, incomplete geographic proxy constraints; and (c) Michigan's legally operative rules, including VRA, communities of interest and island/county geometry, have not been fully encoded or independently certified.

Instead of manufacturing an outlier p-value, we completed a **different, precisely defined and directly reproducible experiment**: how much can the enacted plan change after a fixed number of seeded, constrained ReCom transitions on an independently source-reconciled spatial-proximity graph? We independently generated and rescored **64 terminal assignments**, one per seeded 801-state run, and calculated conditional Monte Carlo uncertainty across those separate replicates. The results constitute valid observations **about that algorithm at that horizon and under its researcher-chosen constraints**. They do not represent a stationary law over Michigan's permissible plans.

## Audited inputs and reference score

| Item | Verified provenance / scope |
|---|---|
| State and reference | Michigan; 13-district adopted 2021 congressional reference |
| Original precinct graph | 4,756 vertices; source Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a` |
| Original source geometry | Archived precinct polygon ZIP; Git blob `07bce18dabbcca9d549e28995a8156fd6978d7db` |
| Polygon-to-node alignment | 4,756/4,756 row attributes reconciled on population, district label, county |
| Spatial adjacency used for **new** bounded model | Original source graph plus 13 proposed nearest-component polygon connections, selected without using the enacted districts or votes; *not legally certified* |
| Derived graph SHA-256 | `14355742f58291f4c26267982de07a21037c347f7598a68f032e0d68ea1d542c` |
| Enacted reference graph cut edges under new model | **682** (not the prior augmented graph's 681) |
| Enacted reference outcome under fixed election overlay | **7 Democratic seats**, efficiency gap **+0.0033332** (project convention) |
| Election data limitation | 2020 precinct presidential-vote allocation scored counterfactually against the adopted 2021 districts; **not** an actual congressional election under those districts |
| Population tolerance | ±0.5% of statewide ideal district population |
| Geography caps, exploratory only | Closer: ≤760 cut edges, ≤18 split source counties, ≤20 split county+MCD groups; relaxed: ≤850, ≤24, ≤49 |

The original Michigan input graph contained six disconnected components. The five older synthetic edges joined places roughly **42, 117, 134, 170, and 280 km** apart because endpoints shared an enacted district label. A minimum-distance component-spanning-tree alternative reduced total edge lengths but left part of District 6 disconnected. A source-polygon nearest-contact sensitivity study showed that **K=3** is the first tested K yielding statewide and within-enacted-plan connectivity, giving 13 extra edges (maximum proposed separation about **17.8 km**). This is a **geometry-proximity model chosen after exploring K values**, not evidence that any particular water or island edge is legally or physically appropriate. The actual Michigan legal feasible state space remains unverified.

Source geometry evidence: [polygon cross-check](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39177796795), [distance-minimum candidate model](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39177987944), [K sensitivity](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39178626625), and [source-reconciled KNN3 sampling pilot](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152649).

## Stage 3 execution and reproducibility

- Fixed finite horizon: **801 recorded states per independent trajectory**, including the enacted initial state and terminal step 800.
- **32 independently seeded trajectories per condition**, seeds 10001–10032. Only each trajectory's **one final map** enters the Monte Carlo sample, not the 800 correlated preceding states.
- Total: **64 independently seeded, independently verified terminal plans**, representing **51,264 recorded chain states**, the bulk of which are intentionally excluded from the cross-run sample.
- Source graph and original source polygon ZIP checked against independently pinned Git blob hashes before regenerating the model graph in each worker.
- Chain-owned GerryChain 1.0 RNG explicitly seeded; each sampled map has an SHA-256 assignment digest.
- The two condition cohorts contain **32 unique terminal map hashes each**. All 64 maps passed independent reassignment rescore and source-graph contiguity, population tolerance and listed geographic-cap checks.
- Seed **10001** is replayed from the same source files in a separate Python process in each condition. Full endpoint metrics and hashes match exactly.
- The aggregate refuses missing or duplicate seed IDs, mismatched graph SHA, different enacted reference scores, wrong horizon/condition, unverifiable endpoint flags and cap/population violations.
- Synthetic and adversarial audit tests pass in the development branch.

**Statistical target:** the probability distribution of the algorithm's final map after exactly 800 transitions from the enacted reference, conditional on the KNN3 model and the specified constraints. **Not** the uniform distribution of legal Michigan plans; **not** a neutral null; **not** a direct gerrymandering-significance test. Identical seed numbers across conditions provide paired deterministic experimental labels but conditions correspond to different model kernels.

### Observed independent-endpoint results

The table reports means across exactly 32 endpoint maps per condition, with **95% percentile bootstrap intervals for the conditional Monte Carlo mean** (10,000 deterministic resamples of independent endpoints, not chain observations).

| Endpoint metric | Closer geographic caps: mean [95% CI] | Relaxed geographic caps: mean [95% CI] |
|---|---:|---:|
| Democratic seats scored under 2020 presidential voting | **7.219 [7.000, 7.438]** | **6.813 [6.594, 7.031]** |
| Project efficiency gap | **+0.02010 [+0.00300, +0.03722]** | **−0.01268 [−0.03036, +0.00458]** |
| Number of graph boundary-cut edges | **695.09 [686.00, 703.75]** | **758.84 [746.66, 771.16]** |
| Number of split source county groups | **17.97 [17.91, 18.00]** | **23.81 [23.63, 23.97]** |
| Number of split source county+MCD groups | **19.94 [19.84, 20.00]** | **47.94 [47.50, 48.34]** |
| Fraction of precinct nodes reassigned after optimal label matching | **13.40% [12.05%, 14.81%]** | **29.00% [27.75%, 30.29%]** |

**Conditional empirical comparison with the enacted reference:** An endpoint's efficiency gap was at least the enacted reference's value in **16/32 (50.0%)** of closer runs and **13/32 (40.625%)** of relaxed runs. The corresponding Wilson 95% intervals for those algorithmic endpoint frequencies are [33.6%,66.4%] and [25.5%,57.7%], respectively. **Neither is a legally neutral redistricting p-value.** In particular, these intervals do not measure whether the enacted map was intentionally, illegally, or unusually gerrymandered.

The mean geographic-cap proposal rejection fraction is **79.22%** (closer) versus **52.83%** (relaxed). The chains are strongly condition-dependent. The closer condition typically uses virtually all permitted source-county and source-MCD splits, whereas the enacted reference has fewer, reinforcing the necessity of better legal-model assumptions before substantive plan comparisons.

### Historical rejected candidate designs and why they were not relabeled as success

1. **Original unseeded ReCom:** historic seed labels were not passed to GerryChain's chain-specific RNG, so those trajectories could not be replayed from those labels; [erratum](stage3_rng_reproducibility_erratum.md).
2. **Explicitly seeded custom ReCom with geographic hard caps:** 8 × 4,001 states and 648 independently verified archived maps, but efficiency-gap bulk ESS only **9.4 (closer)** and **20.4 (relaxed)**, rank R-hat **1.733** and **1.139** respectively. Failed prespecified convergence thresholds; [report](stage3_diversified_sampling_results.md).
3. **Local boundary-flip/swap Metropolis–Hastings:** the proposal has an explicit, provably reversible stationary target **within each reachable communicating class** of labeled proxy-feasible maps, but the later eight-chain 32,008-state experiment produced efficiency-gap bulk ESS just **7.1 (closer)** and **4.8 (relaxed)** with rank R-hat **1.568** and **2.588**; [report](stage3_reversible_mixing_results.md).
4. **GerryChain v1.0 published reversible ReCom R tuning:** exactly **0 changes in 200 proposals** under each tested constraint regime. Stationary-target elegance without usable movement does not validate an ensemble.
5. **Geography:** all five old bridges were selected by enacted district membership, with no independent geometry. Shortest-polygon-distance component MST left four precincts of District 6 disconnected. The KNN3 proxy fixes baseline representability but **does not establish legal topology or water/island connectivity**.

## Formal disposition, scope and Stage 4 handoff

**Stage 3 is CLOSED AS A REPRODUCIBLE, NEGATIVE-RESULTS METHODS AND FINITE-HORIZON SENSITIVITY EXPERIMENT.** The engineering and data-source audit deliverables were completed and the limited conditional Monte Carlo calculation passed its explicit 64-endpoint exit gates.

**The stronger initial goal—scientifically validated stationary sampling of legally acceptable Michigan district maps—FAILED.** It must **not** be marked passed, nor can a downstream paper claim a neutral-ensemble outlier probability, statistically significant gerrymander, or Michigan legal compliance. The new graph is a tested **proximity-based sensitivity model**, not a validated substitute for authoritative water, island, municipal, VRA or community-of-interest geography.

**Permitted Stage 4 scope:** write an academically rigorous *methods and sensitivity* paper comparing geographic assumptions, Markov proposal mechanics, convergence failures, the source-matched KNN3 construction, and finite-horizon algorithmic endpoints, with explicit negative findings and reproducible controls. Frame the research question as methodological: *how do geographic adjacency conventions and constraint severity alter redistricting simulation behavior and counterfactual partisan scores?* Clearly report that the constructed graph remains exploratory and that observed endpoints arise from an enacted-anchored perturbation, not from a neutral legal-plan ensemble. Use the completed finite-horizon protocol and all source integrity records as primary evidence.

**Out of scope without new evidence:** legal/statistical conclusions about Michigan gerrymandering or a publication-ready neutral map distribution. Such an extension would require independent authoritative GIS/legal constraints and demonstrations of adequate mixing under a justified target law.

### Source and code index

- [Finite-horizon preregistered protocol](stage3_finite_horizon_protocol.md).
- [Latest 64-endpoint successful GitHub Actions experiment](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152601).
- `scripts/research_audit/build_geometric_knn_graph.py` and `geometric_knn_sensitivity.py`: geometry-provenanced, district-blind adjacency sensitivity.
- `scripts/research_audit/finite_horizon_endpoints.py`: one exact terminal map per explicitly seeded trajectory, independently rescored.
- `scripts/research_audit/analyze_finite_horizon.py`: strict 64-map aggregation, deterministic bootstrap and Wilson conditional uncertainty.
- `tests/test_finite_horizon.py`: fail-closed cohort corruption tests.
- [Research audit ledger](README.md): original Stage 1–3 lineage, prior tests, negative convergence and topology evidence.

**No changes were made to `main`; no original third-party graph, original polygons or complete derived assignment maps were redistributed in the experimental output artifacts.**
