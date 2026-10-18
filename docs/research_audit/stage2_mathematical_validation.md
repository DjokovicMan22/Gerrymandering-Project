# Stage 2 — Mathematical validation and statistical reliability audit

**Project:** Gerrymandering research, Michigan 13-district counterfactual (2016/2020 presidential vote layers)  
**Review date:** 17–18 October 2026  
**Inputs:** `Gerrymandering-Project-main.zip`, including `strong_paper_review_packet.zip` extracted to `gerry_audit/packet`, with Week 4 and Week 6 plan-metric histories.  
**Readiness decision:** **Mathematical definitions verified at the plan-summary level; substantive legal-comparability and Monte Carlo convergence concerns remain unresolved.** This is a *completed analysis of available saved output*, not a reconstructed census-precinct ensemble or a certified mathematical proof of stationary mixing.

## Executive summary

The implementation's definitions of Democratic seats, the exact wasted-vote efficiency gap, mean–median district vote share, cut edges, and maximum population deviation are mathematically coherent under their stated sign conventions. The saved reference values and ensemble ranks reproduce exactly from archived chain tables. Three 2020 chains contribute 18,900 post-burn-in **observations**, but estimated effective sample sizes are only about 135–222 for key metrics. Rank-normalized R-hat values near 1.02–1.03, chain-to-chain variability, and substantial early-to-late drift do **not** establish adequate mixing. A block-bootstrap exercise suggests non-negligible Monte Carlo uncertainty, but its intervals are provisional and depend on approximate within-chain stationarity.

**Most consequential new validation result:** none of the 18,900 baseline ±2% samples meets Michigan's published ±0.5% *congressional mapping population target*, even though the reference map's reported maximum population deviation is ~0.402%. The ±1% stress test contains only 4 of 8,100 recorded observations within ±0.5%; the ±3% stress test contains none. Thus the existing comparison ensemble cannot directly answer a claim about maps drawn under that stricter target. Beyond population, the chain omits Michigan's other constitutional criteria.

**Interpretation:** This work currently supports *descriptive conditional statements about the archived simplified ReCom ensemble*, not an inference about the legal distribution of maps, an unbiased sample from all valid districtings, a probability that a fair commission would produce the reference map, or proof of intentional gerrymandering.

## 1. Mathematical definitions reviewed

Let district \(j\) have Democratic votes \(D_j\), Republican votes \(R_j\), two-party total \(T_j=D_j+R_j\), and Democratic two-party share \(d_j=D_j/T_j\) for \(T_j>0\). For \(K=13\) districts:

### 1.1 Democratic seat count

\[S_D=\sum_{j=1}^{K}\mathbf{1}\{d_j>1/2\}.\]

The implementation correctly excludes exact ties from either party's seats, and records tied seats separately. The script checks \(S_D+S_R+S_{tie}=13\) on every archived observation.

### 1.2 Wasted-vote efficiency gap

\[\mathrm{EG}=\frac{W_R-W_D}{\sum_{j=1}^{K}T_j},\]

with losing-party votes fully wasted and winner excess votes above the minimum winning threshold wasted. For integer counts, the code uses \(\lfloor T_j/2\rfloor+1\) as that threshold. This is internally consistent for the integer-valued election counts anticipated in the underlying dataset. **Positive EG** under this convention signifies more Republican wasted votes and thus a relative advantage for Democrats. This orientation must be stated everywhere; published sources sometimes reverse it. The shortcut \(S_D/K-2V_D+1/2\) assumes turnout conditions and is not interchangeable with the exact computation under arbitrary district-turnout imbalance. VEST presidential precinct counts are the correct *kind* of input for this metric, but the original graph vote entries have not been individually revalidated here.

Potential defect: the input loader checks required attributes but does not fully rule out negative/NaN/Inf election counts. Add strict numeric checks before treating aggregated wasted-vote calculations as independently validated. A zero-total district is currently omitted from the mean–median calculation, while its seat is counted as neither Democratic nor Republican; the input should fail loudly if any district has zero two-party votes.

### 1.3 Mean–median difference

\[\mathrm{MM}=\operatorname{median}(d_1,\ldots,d_K)-K^{-1}\sum_{j=1}^{K}d_j.\]

This definition and sign match the code; it is distinct from the convention **mean minus median**. The metric weights each district equally rather than by turnout and is not a definitive fairness or legal test.

### 1.4 Maximum population deviation

\[\Delta_{\max}=\max_j\left|\frac{P_j}{P_\star}-1\right|,\qquad P_\star=\frac{\sum_j P_j}{13}.\]

The code enforces \(\Delta_{\max}\leq\varepsilon\) in the specified ReCom runs, and the archived plan-level values do not exceed their declared limits. This checks the **recorded scalar metric** only; the underlying district-population sums cannot be separately verified without district-level output and source graph data.

### 1.5 Graph cut edges

\[C(\pi)=\left|\{(u,v)\in E:A_\pi(u)\ne A_\pi(v)\}\right|.\]

The code returns the number of precinct-graph adjacencies crossing district boundaries. That is a valid structural proxy but **not equivalent to the Polsby–Popper or Reock compactness measures**. It depends strongly on the source graph's precinct resolution and artificial bridge edges, so it is not a geography-independent compactness score.

## 2. Reproduced main 2020 results

Three 7,000-step chains (seeds 101, 202, 303) were trimmed from step 700 inclusive through 6999, yielding \(3\times6300=18{,}900\) observations. Step 0 is the same reference plan across chains.

| Statistic | Reference | Sample mean | Reference midrank percentile | Inclusive upper-tail percentage |
|---|---:|---:|---:|---:|
| Democratic seats | 7 | 5.714921 | 92.5185 | 13.9312 |
| Efficiency gap | +0.0033332 | −0.0999194 | 96.0741 | 3.9259 |
| Mean–median | −0.0140197 | −0.0304035 | 93.3280 | 6.6720 |
| Cut edges | 681 | 845.0066 | 0.03175 | 99.9683 |
| Max. population deviation | 0.0040193 | 0.0186543 | 0 | 100 |

**Seat count tie correction:** 16,267 observations have fewer than 7 Democratic seats, 2,438 have exactly 7, and 195 have more than 7. The midrank formula gives 92.5185%, but the inclusive upper tail is \((2438+195)/18900=13.9312\%\). A paper must not treat \(100-92.5185=7.48\%\) as the inclusive probability of 7 or more seats.

**EG upper tail:** 742/18,900 observations exceed the reference. This empirical proportion is not a sampling-design-free frequentist p-value. It has Monte Carlo error, is conditional on the sampler and geographic constraints, and is subject to post-hoc metric selection if emphasized after seeing multiple outcomes.

## 3. Autocorrelation, effective sample size, and chain mixing

Analyzed 3 equal-length post-burn-in scalar chains using `arviz.ess(method='bulk')` and `arviz.rhat(method='rank')`.

| Metric | Total observations | Approx. bulk ESS | Rank-normalized R-hat |
|---|---:|---:|---:|
| Democratic seats | 18,900 | 221.53 | 1.01825 |
| Efficiency gap | 18,900 | 185.27 | 1.01964 |
| Mean–median | 18,900 | 197.51 | 1.01926 |
| Cut edges | 18,900 | 134.77 | 1.03012 |
| Max. population deviation | 18,900 | 1464.91 | 1.00185 |

Here ESS refers to information content for the *specific scalar estimand* and is not a literal number of unique districting plans or a guaranteed accurate tail-ESS. In particular, estimating small tail proportions is harder than estimating a mean. An ESS of 185 for EG does not certify a reliable 3.93% tail estimate.

**Early-vs-late drift.** Divide each retained chain into first 3,150 and last 3,150 observations:

| Retained half | Mean D seats | Fraction with ≥7 D seats | Mean EG |
|---|---:|---:|---:|
| Early | 5.80815 | 17.9894% | −0.09253 |
| Late | 5.62169 | 9.8730% | −0.10731 |

This sizable internal difference is a concrete reason not to pronounce convergence merely because R-hat is comparatively close to one. The difference may reflect finite-chain fluctuation, long autocorrelation, incomplete mixing, or other nonstationary behavior; the saved scalar histories cannot distinguish these causes.

**Burn-in sensitivity** (all three 2020 chains pooled):

| Exclude steps earlier than | Observations | Mean D seats | Fraction ≥7 D seats |
|---|---:|---:|---:|
| 0 | 21,000 | 5.72671 | 14.2238% |
| 300 | 20,100 | 5.71652 | 13.8209% |
| 700 | 18,900 | 5.71492 | 13.9312% |
| 1500 | 16,500 | 5.69261 | 13.2727% |
| 3000 | 12,000 | 5.70817 | 13.5417% |
| 4000 | 9,000 | 5.61611 | 10.0333% |

### Exploratory block-bootstrap uncertainty

I also resampled **contiguous blocks within each chain**, concatenating the three separately resampled chains and recomputing statistics. For each block size (100, 300, 600), 850 circular-block bootstrap replicates were generated with fixed seeds. This is a *Monte Carlo stability diagnostic*, conditional on approximate stationarity and on the choice of block size; it is not a credible interval for an unobserved uniform distribution of legal plans.

For 300-step blocks, approximate 2.5–97.5 percentile intervals are:

| Quantity | Observed from saved traces | Exploratory interval |
|---|---:|---:|
| Mean Democratic seats | 5.7149 | [5.6392, 5.7960] |
| Fraction with ≥7 D seats | 13.93% | [11.30%, 16.79%] |
| Mean efficiency gap | −0.09992 | [−0.10592, −0.09366] |
| Fraction with EG ≥ enacted EG | 3.93% | [2.78%, 5.26%] |

Block-length variants give similar but not identical intervals (see CSV). Because stationarity is in doubt, these intervals should not be the final paper's sole uncertainty statement. Three independent **starts** (not just seeds from the same initial plan), longer chains, and monitored stability across windows are needed.

## 4. Primary model validity defect: population target mismatch

Michigan's commission mapping-process document lists a ±0.5% congressional population-deviation target and the state constitution ranks equal population/VRA, contiguity, communities of interest, partisan fairness, nonincumbency, political subdivisions, and reasonable compactness as plan criteria. A ±0.5% target should be understood as **the commission's published operating target**, not a complete sufficient proof of constitutionality. Source: [MICRC Mapping Process and Procedures](https://www.michigan.gov/-/media/Project/Websites/MiCRC/Procedure/MICRC_DRAFT_v1104_Mapping_Process_and_Procedures_with_Edits_Accepted.pdf?rev=232bdae8a1004b5995e61d8055536f2c), [Michigan Constitution Art. IV §6](https://legislature.mi.gov/Laws/MCL?highlight=re%2Cdrawing&objectName=mcl-Article-IV-6).

The saved step-0 reference \(\Delta_{\max}=0.0040193\approx0.402\%\) meets this target. By direct inspection of archived sampled `max_population_deviation`:

| Ensemble epsilon | Retained observations | Observations with Δmax ≤ 0.005 | Minimum recorded sample Δmax |
|---|---:|---:|---:|
| 0.01 | 8,100 | **4** | 0.0049262 |
| 0.02 | 18,900 | **0** | 0.0085434 |
| 0.03 | 8,100 | **0** | 0.0169913 |

This is not an academic quibble. The baseline reference is evaluated against an ensemble drawn from a broader and non-comparable population-feasible set. Reweighting the existing ±2% histories will **not** produce a ±0.5% sample: no retained plans meet that threshold. ReCom must be rerun with explicit \(\varepsilon=0.005\), ideally with an evaluation of whether finer-than-precinct units are needed for feasibility and adequate movement. That result must then be assessed for geography and legal constraints, not automatically declared legally valid.

## 5. Compactness and feasible-set mismatch

The reference has 681 cut edges; 18,900 sample observations average 845.0. Just **6 observations** have ≤681 cut edges (~0.0317%), **603 observations** have ≤750 (~3.19%), and 3,921 have ≤800 (~20.7%). Because the reference is almost outside the support of the sampled cut-edge proxy, a naïve conditional estimate of its partisan percentile *among maps as geographically compact as the reference* would be statistically unsupported. Simply filtering to six observations is not an adequate matching method. A new geography-sensitive proposal or explicit compactness constraints, and independent county/municipality-split diagnostics, are necessary.

Cut edges can be affected by arbitrary artificial bridge connections and precinct tessellation. They should be accompanied by more interpretable geographic measures, preferably scored on the same source representation for reference and sampled maps.

## 6. Sensitivity to population tolerance

The saved independent runs under ±1%, ±2%, and ±3% report:

| Population epsilon | Mean D seats | Fraction ≥7 D seats | Mean EG | Fraction EG ≥ reference |
|---|---:|---:|---:|---:|
| 0.01 | 5.71630 | 13.6173% | −0.09954 | 4.7407% |
| 0.02 | 5.71492 | 13.9312% | −0.09992 | 3.9259% |
| 0.03 | 5.92568 | 24.0247% | −0.08410 | 7.7284% |

This is **real parameter sensitivity in the archived experiments**, not a controlled demonstration that epsilon alone causes those shifts. They differ in chain lengths, retained observations, and potentially transient sampling behavior. The ±3% outcome illustrates that conclusions are conditional on modeling assumptions. The appropriate scientific response is not to cherry-pick the most extreme configuration, but to specify a principled legal/structural baseline before inspecting partisan outcomes.

## 7. Election-layer pairing, not independent geography replications

For seeds 101/202/303, 2016 and 2020 histories match **exactly** step-by-step in `cut_edges` and `max_population_deviation`, confirming the same recorded geographic-structure trajectories under both sets of vote fields. This is appropriate for *paired* election-layer sensitivity: differences in voting outcomes are assessed while holding the geographic sequence fixed. It is improper to count the 2016 and 2020 files as six independent geographic chains or 37,800 independent maps.

Under the saved histories, 2016 reference has 6 D seats against mean ~4.673 sampled; 2020 reference has 7 against ~5.715 sampled. The comparison is a **counterfactual scoring of the 2021 adopted/2022-cycle districts using past presidential election returns**, not an analysis of 2016 or 2020 congressional election seat outcomes under those 13 districts. The source project's metadata associates the `CD` attribute with the 2021 adopted map. Source: [Veomett Michigan source-data repository](https://github.com/eveomett-states/Michigan).

## 8. Markov stationary-distribution limitation

The implementation combines GerryChain's ordinary `recom(...)` proposal with `accept.always_accept`. The code defines **no explicit desired stationary distribution with a proved invariant/reversibility correction**. Therefore these empirical ranks cannot be described as arising from a uniform draw across all valid maps. Cannon, Duchin, Randall and Rule's *Spanning Tree Methods for Sampling Graph Partitions* specifically notes that ordinary multi-district ReCom does not have a known closed-form stationary distribution and introduces reversible ReCom with a specified spanning-tree-weighted target. Sources: [GerryChain API](https://gerrychain.readthedocs.io/en/v1.0.0/api/proposals_constraints/), [Cannon et al.](https://arxiv.org/abs/2210.01401).

Do **not** replace the sampler blindly with `RevReCom` and then assert uniformity: the reported RevReCom target is related to spanning-tree counts and also isn't uniformly weighted by map. Documenting the actual sampling process and comparing appropriate variants is part of Stage 3.

## 9. Code correctness and data safeguards

**Verified from source:** ReCom constraints enforce contiguity and a maximum population tolerance; the code records per-plan metrics under fixed vote fields; seed configuration is explicit; output metadata records relevant arguments; rank summaries implement ties correctly. This review independently re-ran `PYTHONPATH=src python -m pytest -q --ignore=tests/test_week4_chain_metrics.py`, giving **25 passed**. The GerryChain-dependent module remains unexecuted here because the dependency and underlying source geography are absent.

**Missing/weak integration checks:**

1. Assert every source precinct has finite nonnegative population and finite nonnegative two-party vote counts; reject missing IDs, duplicate graph nodes, failed joins and zero-total vote districts.
2. Independently verify that the `CD` labels represent the intended adopted districting plan, and that each initial and sampled district is contiguous under the documented land/water bridge policy.
3. Validate census total and election totals against upstream checksums and authoritative aggregate sums; do not silently coerce invalid election numbers to zero.
4. Pin Python and GerryChain versions and dependencies for exact reproducibility.
5. Record individual district statistics and selected assignments or snapshots during all future experiments; do not rely on a nested review ZIP as the sole route to saved chains.
6. Use dispersive initial maps, modern convergence diagnostics, and Monte Carlo error checks designed for rare-tail events.

### Source provenance recovery

The originally used graph and shapefile are absent **from the uploaded ZIP**, but an upstream public research repository has been identified: [eveomett-states/Michigan](https://github.com/eveomett-states/Michigan). Its README identifies the processed 2020 precinct graph/shapefile, 2020 census population, 2021 enacted Congressional `CD` assignment, and 2016/2020 VEST returns, and documents modifications to very short rook adjacencies. The license includes Creative Commons BY-NC 4.0 and compliance with Redistricting Data Hub terms. The upstream file has **not been downloaded, hashed, or matched byte-for-byte** to the local original input in this audit. Treat it as a credible candidate for Stage 3 data restoration, not already-verified provenance.

## 10. Prioritized corrections for Stage 3

| Priority | Task | Acceptance criterion |
|---|---|---|
| P0 | Restore and checksum exact graph and precinct shapefile | Logged URLs, metadata, release/version hashes, schema check, totals and map IDs |
| P0 | Run first feasible ±0.5% Michigan congressional ReCom chain | Saved full assignments, population + contiguity validation, chain trace and documented failures |
| P0 | Distinguish simplified vs legally informed model | Model constraints precisely specified; no map called legal merely because connected/equipopulous |
| P0 | Extend and diversify chains until diagnostics stabilize | Multiple initial configurations; rank-Rhat, ESS (bulk and tail), rolling metrics, MC error by chain |
| P1 | Add geographic comparator constraints | County/municipal splits, bridge audit, cut edges or compactness measures; support overlap documented |
| P1 | Independently recheck vote totals and exact EG | Preserved precinct-to-district aggregations and example hand-checks |
| P1 | Repeat sensitivity with same chain budgets and paired elections | Predeclared tolerances and consistent computational budgets |
| P2 | Expand to Missouri, if genuine two-state inference is desired | Same data/provenance/constraint gate across states |
| P2 | Improve testing and documentation | `pytest` includes actual synthetic GerryChain integration and output invariant tests |

## 11. Research writing gate

**Mathematical validation of archived scalar results: complete, with qualifications.**  
**Independent reconstruction of upstream geographic simulations: not completed.**  
**Correction of legality, representativeness, and mixing weaknesses: requires new computations in Stage 3.**

A defensible current finding: *Under the saved, partially constrained 2020 Michigan ReCom procedure, the reference plan scores above the modeled ensemble center on several Democratic-advantage metrics, but this empirical position varies with the population-tolerance parameter and is not directly transferable to a stricter, legally informed comparison space.*

Not defensible: *The observed map is objectively or illegally gerrymandered because it is at the 96th percentile of 18,900 independent, equally likely, legally valid plans.*

## Reproducibility files

- `stage2_reanalysis.py` — deterministic recalculation of each listed CSV from recovered Week 4/Week 6 plan-metric histories. Requires Python, NumPy, pandas, ArviZ and matplotlib; set `GERRY_PACKET_CHAINS` and `GERRY_STAGE2_OUTPUTS` environment variables to override defaults.
- `stage2_outputs/main2020_metrics_uncertainty.csv` — metric diagnostics, counts, approximate block-bootstrap intervals.
- `stage2_outputs/population_tolerance_comparison.csv`, `stage2_outputs/population_overlap_with_0p5pct.csv`, `stage2_outputs/burnin_sensitivity.csv`, `stage2_outputs/cut_edge_overlap.csv`, `stage2_outputs/paired_2016_2020_geography_check.csv` — independent numerical checks.
- `stage2_outputs/chain_rolling_means.png` — visual trace-drift diagnostic.

The original user ZIP was not modified. This is a new audit package with reproducibility code and derived artifacts.