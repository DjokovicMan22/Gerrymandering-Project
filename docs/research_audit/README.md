**Stages 1–2 follow-up is complete within the original processed-source and archived-metric scope:** [STAGE12_FINAL_VERIFICATION.md](STAGE12_FINAL_VERIFICATION.md). Includes 13 independently reconciled district compactness scores, 12 archived chain histories, six independently rescored original references, 26 Week 3 district vote rows, input corruption tests, and a documented 2016 one-vote floating threshold difference. **Original stochastic trajectory replay, legal geography and raw source joins remain unverified.** [Successful reproducibility workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183710341).\n\n# Stage 3 completed methods-result handoff (current)

**Final status:** **CLOSED as a reproducible, explicitly limited finite-horizon research experiment**, with 64 independently checked endpoint maps, conditional bootstrap uncertainty, a source-matched district-blind proximity graph, and documented negative convergence results. **NOT closed as a validated neutral ensemble of legally permissible Michigan congressional maps.** For authoritative figures, methods, provenance, limits and permissible Stage 4 paper scope, read [**STAGE3_FINAL_REPORT.md**](STAGE3_FINAL_REPORT.md). [Experiment: all eight batches and aggregation PASS](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152601).

**Interpret old audit sections below as historical unsuccessful candidate designs**, not the current final experiment. Geographic KNN3 proximity links are still unverified under Michigan's physical/island-contiguity and legal constraints; do not claim a statewide gerrymandering significance result.

## Current Stage 3 scientific gate — failed (October 18, 2026)

**Do not mark Stage 3 as scientifically validated and do not treat Stage 4 as a confirmed outlier analysis yet.** The latest *eight-chain reversible Metropolis–Hastings experiment* completed **32,008 recorded sample states**, all 648 saved maps passed independent reconciliation, and the exact proposal kernel passed synthetic detailed-balance tests. Nevertheless, **neither proxy-geographic condition meets the R-hat/ESS gates**: efficiency-gap R-hat **1.568** (closer) and **2.588** (relaxed), and bulk ESS **7.1** and **4.8** versus required R-hat ≤1.01 and ESS ≥400. Means lie near the hard boundary-cut caps, which raises a separate target-distribution issue.

**New official-source geographical evidence:** The raw graph has six disconnected pieces and all five artificial bridge edges chosen to join them cross county identifiers. These facts do **not** establish illegality—real contiguity can cross counties—but **the particular constructed links have no independent GIS/topological validation**. Simple same-county links cannot fully connect the original graph either. Full Michigan constitutional requirements (VRA, communities, contiguity, partisan fairness, boundaries, compactness) are not implemented.

- [Executed MH R-hat/ESS results and final Stage 3 blocker ledger](stage3_reversible_mixing_results.md).
- [Complete successful eight-chain pipeline plus failed convergence findings](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39173401095).
- [Source-pinned Michigan graph bridge audit](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39173742278).
- Official constitutional text: https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6
- Official commission mapping data: https://www.michigan.gov/micrc/mapping-process/mapping-data

The next finite research gate is: replace/certify artificial contiguity with authoritative GIS; justify the constrained comparison distribution; develop demonstrably mixing transitions and pass prespecified diagnostics. If these fail, Stage 3 should publish a transparent negative methods result rather than claim a valid gerrymandering probability.

# Stages 1–3: reproducible research-development branch

**Branch:** `research/stages-1-3-validation` (separate development branch, **not a GitHub fork**).  
**Original main branch:** unchanged.  
**Scope:** Michigan 13-district 2021-adopted congressional map; 2016 and 2020 presidential voting layers are **counterfactual scores**, not results of elections under that map.  
**Scientific disposition:** Stage 1 reviewed; Stage 2 mathematically audited; Stage 3 exploratory feasibility demonstrated in a prior separate execution, **not publication-ready**.

## Reversible local sampler: specified stationary target and Michigan feasibility pilot

**New Stage 3 method:** A separately defined boundary-edge Metropolis–Hastings sampler whose proposal probabilities and detailed-balance correction are explicit. Enumerative toy-map tests verify each nontrivial pair's detailed balance. The stationary measure is **uniform over each communicating component of proxy-constrained labeled assignments**—not a proven single law over all legally acceptable Michigan plans. Irreducibility, mixing time, adequate sample size, physical island geography, VRA rules, communities of interest and legal-plan uniformity are **unverified**.

**Real pilot: completed successfully:** Four 2,001-state Michigan runs (2 warm seeds × 2 geographic regimes), 8,000 proposed MH transitions, **995 accepted**, **84 independently verified full assignments**. Acceptance ranged **9.20–9.25%** under closer caps and **15.35–15.95%** under relaxed caps. Despite this, exact final assignments differed from their warmup maps on only **1.7–3.7%** of precinct nodes. This is reproducible algorithmic progress, **not convergence certification or a gerrymandering p-value**.

- [Proof, assumptions, transition formulas and limits](stage3_reversible_kernel_method.md).
- [Actual pilot outcomes and rejection reasons](stage3_reversible_mh_pilot_results.md).
- [All four successful source/seed-validated MH jobs](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39172395140).
- Code `src/redistricting/ensemble/reversible.py`, executable `scripts/research_audit/run_reversible_pilot.py`, exact balance tests `tests/test_reversible_kernel.py`.

## Latest Stage 3 diversified-start full sampling (October 18, 2026)

**Executed and independently checked:** eight **explicitly seeded GerryChain 1.0** Michigan sampling chains starting from eight cryptographically verified different warm-start maps, **32,008 recorded sample states** and **648 validated archived full assignments**. The fixed enacted reference is separately scored for comparison; the warmed sample step 0 is NOT the enacted plan. Five exact relabel-invariant spatial probes per chain show nonzero map movement.

**Scientific result:** BOTH geographic models **fail every scalar R-hat/ESS convergence gate**. Under closer caps, efficiency-gap rank R-hat ~**1.733** and bulk ESS **9.4**; under relaxed caps, R-hat ~**1.139** and bulk ESS **20.4**, versus gate R-hat <=1.01 and ESS >=400. Do **not** infer a legal-plan p-value or stationary outlier probability. Physical island adjacency, municipality polygons, Michigan legal constraints, and the transition kernel's intended stationary law remain unverified.

- [Authoritative report and explicit nonconvergence verdict](stage3_diversified_sampling_results.md)
- [Production run: 8/8 sampling and validation jobs + four-chain scalar aggregation passed operational checks](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162686274)
- [Independent spatial movement analysis](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39163062277)
- [Preregistered experimental parameters](stage3_diversified_sampling_protocol.md), [corrected seed-diversity study](stage3_seeded_diversity_results.md), and [historic RNG erratum](stage3_rng_reproducibility_erratum.md)

## Critical reproducibility correction and current Stage 3 experiments

**Corrected GerryChain 1.0 seeded RNG:** Previous production/geo pilot/warmup files tagged with a `seed` were not deterministic because `random.seed` was used without `MarkovChain(rng=seed)`. Read [the documented erratum](stage3_rng_reproducibility_erratum.md) before interpreting historical results. The branch now uses `MarkovChain(rng=seed)`, pins `gerrychain==1.0.0`, and has [passed two separate-process replay smoke tests](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162110048).

**Corrected warmups:** [Eight independently seeded starting-map results](stage3_seeded_diversity_results.md) passed exact, label-invariant 5% distance gates in both geographic proxy conditions; these maps share the same enacted ancestor and are NOT stationary draws. [Verified warmup CI](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162240056).

**Current sampling experiment:** [Predeclared diversified-start protocol](stage3_diversified_sampling_protocol.md); [eight-chain production run](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162686274). The sampling step-0 maps are warmed, **not the enacted reference**, and the aggregation script must use matching, separately scored enacted JSON references. Execution/CI completion does not imply stationary sampling or valid gerrymandering probabilities.

## Stage 3 seeded warm-start diversity — October 18, 2026

**Executed:** Eight separately seeded Michigan ReCom warmup paths, each 800 recorded states, starting from the same enacted plan. All eight final plans passed independent structural/geographic/population checks. Exact **label-invariant** node-assignment differences passed the predeclared 5% minimum both relative to enacted and across all pairs: **closer** pairwise 11.56–17.47%; **relaxed** pairwise 21.17–31.33%. Geographic proposal rejection remains high (closer 76–80%; relaxed 53–57%). **This is measured diversification, not stationarity or legally representative sampling.**

- [Executed results](stage3_warm_start_diversity_results.md) and [predeclared protocol](stage3_warm_start_diversity_protocol.md).
- [Successful two-condition GitHub Actions run](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734877).
- [32 passing automated tests](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734817).
- Reproduction entrypoint: `scripts/research_audit/diversified_start_pilot.py`; package: `src/redistricting/ensemble/start_diversity.py`.
- **Stage 3 scientific validation remains open:** all chains share an enacted ancestor, geographic/legal model conditions are limited, and no stationary-law or mixing certification exists.

## Geographic comparability extension — completed short pilot

The October 18 **holding-kernel** geographic sensitivity pilot executed four real Michigan chains (600 recorded states each; 240 independently validated archived assignments). Enforced caps were (cut edges, split counties, split county+MCD source groups): closer (760, 18, 20) and relaxed (850, 24, 49). Rejected geographic proposals create recorded self-loops rather than invisible retries.

- **Results:** [stage3_geographic_pilot_results.md](stage3_geographic_pilot_results.md).
- **Successful GitHub Actions pilot:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39123162067
- **Scientific disposition:** closer caps rejected 71–83% of geographic proposals; both models remained fragmented relative to the enacted county/MCD split counts. **Not converged, not legally certified, not suitable for a gerrymandering p-value.** Do not pool earlier retry-kernel pilot traces with the holding-kernel traces.
- **Model implementation:** `src/redistricting/ensemble/geographic.py`, updated `constraints.py`, `chain.py`, and `scripts/run_baseline.py`.
- **Regression tests:** `tests/test_geographic_constraints.py` including an actual RustworkX-backed GerryChain Partition.

## Updated empirical execution status — October 18, 2026

The historical completion ledger below predates the latest full production execution. **Eight 8,000-state GerryChain jobs completed and passed per-chain verification (64,000 recorded states; 6,400 checked saved full assignments).** The separately executed cross-chain postprocessor succeeded, but **both ±0.5% and ±2% models fail the conservative R-hat/ESS convergence requirements**. Comparison maps are also much more fragmented than the enacted reference (about 916–919 versus 681 graph cut edges), so the research is **not scientifically certified** and cannot support claims of legality or map-intent probability.

- Executed findings: [stage3_executed_empirical_results.md](stage3_executed_empirical_results.md)
- Production CI: https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39120743275
- Successful independent diagnostics CI: https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39121398554
- The original production CI includes a **failed legacy aggregation job** caused by an artifact path mismatch. All eight simulation/verification jobs succeeded; the independent aggregation CI succeeded, and the production workflow's path was corrected for subsequent runs.
- A **new production run must be explicitly triggered** by changing `docs/research_audit/trigger_stage3_production.txt` on this branch; editing other research files does not inadvertently restart 64,000 expensive chain states.

## Evidence provenance

- `docs/research_audit/stage1_repository_audit.md`: previously completed code/data/reproducibility audit. Static audit + 25 helper-function tests, **not** complete live rerun.
- `docs/research_audit/stage2_mathematical_validation.md`: previously independently recalculated saved scalar histories; 18,900 serially dependent post-burn-in observations, with low ESS and model limitations.
- `docs/research_audit/stage3_prior_empirical_report.md`: archived account of 13 earlier short real-graph chains, 7,300 proposals and 560 retained correlated observations across four model conditions. The original complete runtime outputs/assignments were **not imported** into this branch. A report is not a reproduced experiment.
- `scripts/research_audit/*`: new reproducibility and audit tools implemented on this branch.
- `tests/test_research_audit.py`: synthetic tests of data/chain input-gating.

## Source input (do not commit third-party data)

Public source: https://github.com/eveomett-states/Michigan  
File: `mi.json`, pinned Git blob SHA-1: `a4dfe70818f87b97924781216f3d86a672cfc66a`.  
Expected properties from the previously archived Stage 3 report: 4,756 nodes; 12,378 original edges; population 10,077,331; 13 reference districts; approximately 0.4019% maximum reference population deviation.  
**Licensing:** CC BY-NC 4.0 and Redistricting Data Hub use/attribution conditions; comply with the upstream terms. Source owner disclaims legal correctness.

**Directly verified on this branch:** `docs/research_audit/source_graph_verified.json` records an independent read of the immutable upstream Git blob: 4,756 nodes, 12,378 edges, zero duplicate precinct IDs, zero adjacency asymmetries, 10,077,331 census population, 13 reference districts, 681 original graph cut edges, and 14 split county / 9 split county-MCD groups. The original graph has disconnected pieces; artificial bridges have not been geographically certified.

### Step A — install dependencies and obtain verified source

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install arviz
python scripts/research_audit/download_source.py --acknowledge-source-terms
python scripts/research_audit/verify_graph.py \\
  --graph data/raw/mi/mi/mi.json \\
  --expected-git-blob a4dfe70818f87b97924781216f3d86a672cfc66a \\
  --expected-nodes 4756 --expected-population 10077331 \\
  --output outputs/research_audit/source_manifest.json
```

A graph-byte hash match establishes only matching **processed-source bytes**; it does not independently establish precise geographic adjacencies, vote allocation, physical island bridges, or Voting Rights Act compliance.

### Step B — matched-budget runs, never pretend they have run

```bash
python scripts/research_audit/run_experiment_matrix.py
# Inspect the printed commands before opting in.
python scripts/research_audit/run_experiment_matrix.py --execute
```

The matrix plans **4 seeds × 2 population tolerances × 8,000 steps**, 2,000 step burn-in, assignment snapshots every 10 steps. The driver calls the original GerryChain `run_baseline.py`, validates snapshots with `verify_snapshots.py`, and summarizes saved plan traces with `analyze_chains.py`. Data-sensitive executable work needs an environment with GerryChain and the verified original graph. The pipeline uses the **existing artificial graph bridges**; it logs neither physically verified island adjacency nor county-/municipality-split constraints, so outputs remain research models, not legally eligible plans.

The runner refuses to overwrite existing chain outputs unless explicitly invoked with `--overwrite`, and returns exit status 2 if diagnostic thresholds fail (while retaining those diagnostics).\n\nSaved assignments are only a **subsample**. Passing snapshot checks does not validate each unrecorded transition. Retain complete assignments or implement per-step invariant checks before a journal-quality release.

### Step C — investigate and report diagnostics

Each experiment condition produces:

- Original per-chain metrics, district rows, seed/epsilon metadata, and assignment snapshots under `outputs/chains/week4/`.
- Independent snapshot-validation paired election scores under `outputs/research_audit/epsilon_*/validated_snapshots.csv`. Each saved snapshot's Democratic-seat count, efficiency gap, cut edges, and population deviation are reconciled with its original plan-metrics CSV. Any mismatch aborts the matrix.
- Rank R-hat, bulk ESS, tail ESS, inclusive upper tails, and ±0.5% overlap under `outputs/research_audit/epsilon_*/diagnostics.csv` and `audit.json`.

`analyze_chains.py` uses an intentionally conservative **diagnostic gate** (R-hat <= 1.01 and bulk/tail ESS >= 400). Passing these scalar checks would be **necessary evidence, not proof** that the sampled high-dimensional map distribution is stationary, representative, or uniform. The driver marks inadequate mixing with an exit code but retains outputs.

## Completion ledger

| Gate | Status on this branch | Remaining |
| --- | --- | --- |
| Stage 1 repository audit | Archived, complete within its limited static scope | Restore original inputs/independent geographic source checks |
| Stage 2 numeric validation | Archived results and independent CSV analyzer added | Reproduce original archived histories from recovered nested ZIP and compare artifact hashes |
| Stage 3 source acquisition | Pinned and validated source-fetch **code** added | Actually download and hash on execution machine |
| Stage 3 feasible tighter model | Previous report documents short exploratory runs | Reproduce with original full-precision per-step data; validate transitions |
| Stage 3 standardized experiment | Matched-budget *runner* added | Execute runs; archive complete outputs and diagnostics |
| Stage 3 geography | Existing bridge handling reviewed; geographic proxy mismatch previously documented | Audit bridges against real map; add county/municipal, compactness, VRA/COI-aware comparisons |
| Stage 3 mixing and sensitivity | Methods/rejection conditions documented | Independent starts, mixing, stable ESS/tails, comparable models and uncertainty |
| Final paper | **Not certified** | Correct claims, cite original sources, bounded inference |

## Nonnegotiable interpretation

Do **not** say that 18,900 sequential samples are 18,900 independent maps; do **not** report raw upper-tail fractions as exact p-values; do **not** call a sample legal simply because it is contiguous and population balanced; do **not** assert uniform sampling from ReCom; do **not** infer intent or illegality from a partisan score. The already observed county-split discrepancy is central, not a cosmetic concern.

## Tests

```bash
PYTHONPATH=src python -m pytest tests/test_research_audit.py -q
```

These are synthetic validations, not an assertion that the live Michigan graph run passed. Before use in a submission, add real-data integration tests that cover every accepted step and independently reconstruct source election joins.
