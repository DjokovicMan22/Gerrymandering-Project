# Stage 3 verified explicit-RNG diversified-start Michigan sampling — executed results

**Executed:** October 18, 2026  
**Production CI (8/8 sampled-chain + independent snapshot verification jobs PASSED; aggregation PASSED):** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162686274  
**Separate exact spatial checkpoint postprocessing (PASSED):** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39163062277  
**Predeclared protocol:** [stage3_diversified_sampling_protocol.md](stage3_diversified_sampling_protocol.md)  
**Historical seed reproducibility erratum:** [stage3_rng_reproducibility_erratum.md](stage3_rng_reproducibility_erratum.md)

## Abstract and disposition

We executed **eight** deterministic-trajectory Michigan ReCom chains, **four** under closer geographic caps and **four** under relaxed caps, initialized from separately seeded, cryptographically checked, structurally validated warmup assignments. Each chain recorded **4,001 sampled states including its unique warmed step zero**, for **32,008 recorded sample states** in total. The separately generated warmups comprised an additional **6,400 states**, not combined with the analysis sample.

All eight simulations and their per-chain validation jobs passed. **81 complete sampled assignments per chain**, **648 in total**, were independently recalculated for population, augmented-graph contiguity, geography proxies, Democratic seats, cut edges and the efficiency gap, then reconciled against the saved history. The aggregation job checked all four seeds/condition, source and references, matched budgets and distinct initial warm hashes. The enacted reference is **separately scored from the precinct graph, not taken from the different step-zero maps**.

**BOTH CONDITIONS FAIL EVERY TRACKED SCALAR R-HAT/ESS GATE.** Stationary sampling, legal-map geography, and probabilistic outlier claims remain **NOT CERTIFIED**.

## Methods

- Same immutable processed Michigan public precinct file (Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`, 4,756 precinct graph nodes, 13 reference districts); fixed artificial within-district bridges remain unverified as physical/geographic connections.
- GerryChain pinned at **1.0.0** with chain-owned seeded `MarkovChain(rng=...)`. Warm seeds 101, 202, 303, 404, and independent sample seeds 1101, 1202, 1303, 1404. Exact warmup map SHA-256 values required to match the [corrected seed-verified diversity study](stage3_seeded_diversity_results.md).
- Two exploratory proxy constraint regimes: closer (cut-edge cap 760, split COUNTYFIPS cap 18, split COUNTYFIPS+MCDFIPS cap 20) and relaxed (850, 24, 49), both max district population deviation ±0.5%. **These are not independently certified Michigan legal criteria or valid municipality polygons.**
- For each of eight sampling chains: 4,001 recorded states including warm step zero and 4,000 proposed transitions; 1,000 starting **sample** states discarded for descriptive summaries and scalar diagnostics, leaving **3,001 highly correlated states per chain**, or **12,004 per condition**.
- Geographic-invalid proposed maps are counted as holding self-loops; when feasible the Markov chain changes state. The full stationary distribution/reversibility of this specific kernel is not known.
- Saved complete map at sampling steps 0,50,...,4000 (81/chain) independently checked by `verify_snapshots.py`; reported sampling metrics reconciled with `metric_reconciliation.py`.
- Five exact label-invariant spatial checkpoint comparisons per chain (steps 0,1000,2000,3000,4000). Each checkpoint records precinct fraction differing from enacted reference and from its own warmup map after **optimal district relabeling**. No full precinct-level assignments redistributed.
- Reference map baseline, using the fixed 2020 two-party presidential-vote scoring convention: **7 Democratic seats, efficiency gap +0.003333, 681 graph cut edges**. The 2020 vote allocation is counterfactual on the adopted 2021 13-seat map, not an actual congressional election with those boundaries.
- Preregistered scalar gates: rank-normalized R-hat <=1.01; bulk ESS >=400; tail ESS >=400 **for every tracked metric**. The gates diagnose scalar sampling behavior; passing them would still not prove spatial mixing or an appropriate legal-plan target.

## Actual four-chain diagnostics (post-burn-in 12,004 observations per regime)

| Metric | Reference | Closer pooled mean | Closer rank R-hat | Closer bulk ESS | Closer tail ESS | Relaxed pooled mean | Relaxed rank R-hat | Relaxed bulk ESS | Relaxed tail ESS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Democratic seats | 7 | 7.553232 | **1.814835** | **5.82** | **5.36** | 6.321976 | **1.203982** | **14.67** | **31.65** |
| Efficiency gap | +0.003333 | +0.047586 | **1.733426** | **9.44** | **30.32** | −0.052158 | **1.139005** | **20.45** | **63.04** |
| Median minus mean | −0.014020 | −0.012573 | **1.125335** | **31.61** | **62.05** | −0.020685 | **1.178245** | **15.92** | **44.71** |
| Graph boundary cuts | 681 | 684.459847 | **1.262680** | **12.25** | **27.37** | 740.773159 | **1.219696** | **13.36** | **66.91** |
| Maximum district population deviation | 0.004019 | 0.004466 | **1.056506** | **83.44** | **96.71** | 0.004575 | **1.016286** | **336.90** | **210.46** |

**All ten condition-by-metric combinations fail the predeclared thresholds.** Many apparent thousands of stored states provide only single-digit to low-double-digit effective information on the primary seat/gap outcomes. Do not compute inferential p-values from raw score tail counts or present the enacted reference's rank as a validated legal-plan outlier probability.

### Independently inspected chain-level heterogeneity

All values below are **post-burn-in descriptive means from 3,001 dependent states per chain**.

| Condition | Warm seed | Sample seed | Mean D seats | Mean efficiency gap | Mean graph cuts | Fraction geographic proposals rejected | Fraction sampled transitions changing map |
|---|---:|---:|---:|---:|---:|---:|---:|
| Closer | 101 | 1101 | 8.000 | +0.08137 | 694.59 | 76.60% | 21.20% |
| Closer | 202 | 1202 | 7.944 | +0.07653 | 695.49 | 80.55% | 17.15% |
| Closer | 303 | 1303 | 7.269 | +0.02621 | 681.99 | 82.20% | 15.93% |
| Closer | 404 | 1404 | 7.000 | +0.00622 | 665.77 | 79.05% | 17.73% |
| Relaxed | 101 | 1101 | 5.829 | −0.08886 | 743.35 | 53.78% | 44.63% |
| Relaxed | 202 | 1202 | 6.566 | −0.03362 | 739.21 | 60.85% | 37.63% |
| Relaxed | 303 | 1303 | 6.180 | −0.06039 | 724.75 | 58.55% | 39.50% |
| Relaxed | 404 | 1404 | 6.713 | −0.02577 | 755.79 | 53.40% | 44.70% |

The seeds have **different warmed starting maps and separately controlled RNG streams**. Differences across their means are diagnostic evidence against trusting a pooled stationary estimate, especially in the closer model, not legitimate random-sample error bars.

## Explicit spatial-movement diagnostics

All five checkpoints were measured for all eight chains using exact maximum-overlap matching of the 13 district labels. After 4,000 recorded transitions:

| Condition | Mean precinct fraction different from own warm start | Minimum across four chains | Mean precinct fraction different from enacted reference | Unique endpoint SHA-256 hashes |
|---|---:|---:|---:|---:|
| Closer | **13.11%** | 10.26% | 18.28% | 4/4 |
| Relaxed | **30.94%** | 18.82% | 33.49% | 4/4 |

Mean fraction different from own warm map at checkpoints 1000,2000,3000,4000:
- **Closer:** 8.00%, 12.08%, 14.07%, **13.11%**.
- **Relaxed:** 26.38%, 29.27%, 26.79%, **30.94%**.

**Interpretation:** chains are not literally frozen in their initial configurations. Yet large-scale map movement does not establish rapid exploration of all feasible plan regions or mixing between chains. Spatial reports contain each chain's distance to the enacted/warm map, NOT exact contemporaneous *pairwise inter-chain* distances; these cannot be reconstructed from their saved hashes and scalar distances alone.

## Substantive geographic caution

The closer condition better matches the reference's **graph boundary cut count** (pooled ~684 versus enacted 681) than the old unconstrained model (~916–919). But it still permits approximately 18 county source groups split instead of reference 14, and approximately 20 COUNTYFIPS+MCDFIPS groups split instead of reference 9. The relaxed model is markedly more fragmented in all geographic proxies (~741 graph cuts, ~24 split county groups and ~48 split MCD source groups). The caps were chosen as exploratory research conditions, **not scientifically or legally justified admissibility rules**; comparison with the enacted map remains structurally conditional and potentially biased by constraint selection.

## Reproducibility and scientific standing

- Original `main` unchanged.
- Artifacts: production job yields per-chain plan CSV, source hashes, dependency freeze (GerryChain 1.0.0), warmed assignment SHA and distinct sample RNG, separately scored reference JSON, per-chain post-burn-in summary, five exact spatial probes and independently recomputed snapshot summary. Original graph and saved full precinct assignment maps were excluded from public artifacts.
- Aggregated R-hat, ESS and audited common reference metadata: [production workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162686274).
- Cross-chain exact spatial checkpoint descriptive reports: [independent spatial workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39163062277).
- Independent two-process smoke replay before production: https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162110048.
- 5% corrected warm-map distance checks (preregistered and passed): https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162240056.
- Analytical scripts: `run_diversified_chains.py`, `analyze_diversified_chains.py`, `analyze_diversified_spatial.py`, `verify_snapshots.py`.

**Scientific verdict: Stage 3 execution and end-to-end reproducibility checks PASS; sampling adequacy FAILS, and legal/geographic/stationary-target validity is UNVERIFIED.** No probabilistic gerrymandering claim is warranted from these ensembles.

## Recommended next research step

Prioritize **proposal mechanism and stationary-target validity** rather than merely collecting more correlated ReCom states. Assess valid moves versus self-loops and chain autocorrelation under each geographic regime, choose a defensible constraint system from independently verified Michigan county/municipal/water geography, and evaluate an explicitly justified transition kernel (including whether reversibility/detailed balance can be proved for the intended target). Only after validating proposal-law and comparing multiple dispersed starts should much longer runs with multiscale spatial diagnostics be interpreted probabilistically.
