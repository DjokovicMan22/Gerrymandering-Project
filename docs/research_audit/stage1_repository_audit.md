# Stage 1 — Deep Repository Audit

**Audit date:** 2026-10-17/18  
**Input:** `Gerrymandering-Project-main.zip` (archive snapshot dated 2026-08-07; embedded commit prefix `f34c3c5668785c26eb619812c3dce1e87b44be47`)  
**Disposition:** **Conditional research prototype — not yet publication-ready or end-to-end independently reproducible.**  
**Important scope limitation:** This was a static source-code review, executable unit-test run, and independent analysis of the *saved* plan-level time series. It was **not** a fresh precinct-level simulation, full graph-validation run, or legal validity certification. The source precinct data are absent.

## Executive findings

The repository contains implemented descriptive and geometric metrics for Michigan and Missouri; a GerryChain/ReCom implementation; three saved Michigan 2020 and three 2016 chain histories; Michigan population-tolerance stress-test histories; plotted analyses; and a long Week 7 manuscript. The saved numeric outputs are internally consistent. However, essential source data, geography snapshots, full individual district-output tables, and complete input provenance are missing. Some advertised longer-term features remain empty placeholders.

The top concerns are **(1)** an underconstrained comparison ensemble, **(2)** serious dependence among sequential MCMC observations, **(3)** missing data provenance and exact reproduction inputs, **(4)** interpretation of the partisan conclusions, and **(5)** incomplete independent geography validation. A technically substantial research project exists, but the present evidence supports a narrower claim than a formal determination of legally valid alternative plans or definitive partisan manipulation.

## Evidence hierarchy

- **Verified from source:** Functions, defaults, declarations, code architecture, missing/present files.
- **Independently calculated from archived CSVs:** Chain lengths, empirical percentiles, means, cross-election geographic trace parity, approximate MCMC diagnostics.
- **Partly checked:** Geometry and election statistics published in Week 1–3 tables, output figures, and map-recovery claims; original inputs unavailable.
- **Not verified:** Running GerryChain on original precinct graph, actual plan legality, each intermediate plan's full contiguity, provenance matching the enacted plan, and full reconstruction of geographic comparison figures.

## 1. Inventory and research coverage

| Area | Source evidence | Assessment |
|---|---|---|
| Descriptive two-state analysis | `scripts/week1_*`, `outputs/tables/week1` | Substantive implementation and tables for MI/MO |
| Geometric compactness | `scripts/week2_compactness_analysis.py`, `scripts/week2_resolution_sensitivity.py` | Polsby–Popper, Reock, convex-hull ratio, resolution tests |
| Partisan metrics | `scripts/week3_partisan_metrics.py` | Exact wasted-vote gap, shortcut, mean–median, counterexamples; unit-tested |
| ReCom generator | `src/redistricting/ensemble/{partition,chain,proposals,constraints}.py`, `scripts/run_baseline.py` | Core pipeline implemented; must be re-executed against original graph |
| Ensemble diagnostics | `src/redistricting/diagnostics/convergence.py`, `scripts/analyze_week4_chains.py` | Split-Rhat and plots; effective sample size not in original pipeline |
| Plan outlier analysis | `src/redistricting/analysis/outliers.py`, `scripts/run_week5_outlier_analysis.py` | Quantiles and ranked districts implemented |
| Sensitivity | `src/redistricting/analysis/sensitivity.py`, Week 6 scripts | MI ε=1%, 2%, 3% implemented; only population-balance sensitivity |
| Map recovery | `scripts/recover_week5_map_examples.py` | Deterministic replay with metric comparison; replay cannot be repeated without missing inputs |
| Research manuscript | `outputs/reports/week7/mi_2020_final_paper.md` | Extensive draft, not independently validated for final publication |
| Optimization, surrogate ML, several notebooks and configs | `src/redistricting/optimization/*`, `surrogate/*`, empty `notebooks/`, empty YAML configs | Placeholders, not implemented analyses |
| Missouri ReCom experiment | Baseline runner is parameterized for `mo`, but no saved Missouri chain histories found | **Not yet demonstrated** |

### Repository packaging concerns

1. `data/raw/` is absent. The baseline runner expects `data/raw/mi/mi/mi.json` (or Missouri counterpart). No complete original shapefile/graph package accompanies the research.
2. Ordinary `outputs/chains/week4` and `outputs/chains/week6` directories are absent from the extracted root. The original plan-level CSVs and metadata are recoverable by separately extracting **`strong_paper_review_packet.zip`**, an embedded archive. This recovery step is undocumented in the normal reproduction commands.
3. The nested review packet contains plan-level histories, **not** corresponding district-level 13-rows-per-plan CSVs or assignment histories. Consequently, Week 5 ranked-district calculations cannot be independently reproduced from the provided packet alone.
4. `docs/data_provenance.md` still contains source organization, source URL, retrieval date, map vintage, and preprocessing placeholders for both states. `docs/data_sources.md` and several other documentation stubs are empty.
5. Versions are declared as minimum bounds in `pyproject.toml`, not pinned. This matters particularly for stochastic map replay.
6. README/`PROJECT_STATUS.md` are stale: Weeks 4–7 are unchecked despite extensive existing outputs. The Week 7 repo checklist is unchecked.
7. Source code and output figures are present; this is a saved August snapshot, not proof of current October development status.

## 2. Independently recomputed 2020 Michigan results

**Source:** nested packet, three `mi_2020_chain*_7000steps_seed*_plan_metrics.csv` tables. All three have exactly 7,000 rows indexed `step=0...6999`. With `step >= 700`, there are 6,300 retained rows per chain; **18,900 sequential observations total**. Step 0 is the common reference plan, deliberately excluded from the post-burn-in distribution.

| Statistic | Reference-plan value | Pooled mean | Reference midrank percentile | Independent verification |
|---|---:|---:|---:|---|
| Democratic seats | 7 | 5.714921 | 92.5185% | Matches saved table |
| Efficiency gap (R wasted − D wasted) / two-party votes | +0.0033332 | −0.0999194 | 96.0741% | Matches |
| Mean–median (median − mean Democratic district share) | −0.0140197 | −0.0304035 | 93.3280% | Matches |
| Cut edges | 681 | 845.0066 | 0.03175% | Matches |
| Maximum population deviation | 0.40193% | 1.86543% | 0% | Matches |

The saved histories contain **no missing plan-level metric values**. Maximum recorded population deviation per 2% run is approximately 1.9999%, consistent with the configured bound. These checks establish **arithmetic consistency of recorded data**, not end-to-end correctness of the original geography or Markov transitions.

### Why seat-count percentiles need careful interpretation

For enacted 7 Democratic seats, of 18,900 observations **16,267 have fewer than 7**, **2,438 have exactly 7**, and **195 have more than 7**. Thus the midrank is 92.52%, but **13.93% of sampled outcomes have at least 7 seats** (the inclusive upper tail). It would be misleading to state that the seat-count result has an upper-tail probability of 7.48% just by subtracting midrank from 100. This is a discrete/tied statistic.

For the efficiency gap, 742/18,900 sampled values are above the reference (3.93% empirical upper tail), but this proportion is **not** an off-the-shelf independent-sample p-value and must not be treated as a formal proof of improper design. Also note multiple-metric selection if emphasizing whichever statistic is most extreme.

### Election-layer design

A cross-election audit found that **all three matched-seed 2016 and 2020 chain pairs have exactly identical cut-edge and population-deviation time series**, despite different partisan scores. This strongly supports that the same geographic proposal histories were rescored under the two elections. This is valuable as a *paired election-layer comparison*, but the two election ensembles should **not** be described as independent geographic samples of 18,900 each.

The 2016 file reports 6 reference Democratic seats versus 4.67265 average sampled Democratic seats, whereas the 2020 file reports 7 versus 5.71492. In both scoring elections the enacted reference is more Democratic-favorable than the unconstrained-compactness baseline in seat count. That is a conditional finding about a 13-district counterfactual map, **not** the result of either historical presidential or House election held under those 13 districts.

## 3. MCMC dependence and convergence

Using a rank-normalized diagnostic on three post-burn-in chains (3×6300 rows; `arviz.ess(..., method='bulk')` and `arviz.rhat(..., method='rank')`):

| Scalar metric | Bulk ESS, approximate | Rank R-hat |
|---|---:|---:|
| Democratic seats | 221.5 | 1.01825 |
| Efficiency gap | 185.3 | 1.01964 |
| Mean–median difference | 197.5 | 1.01926 |
| Cut edges | 134.8 | 1.03012 |
| Maximum population deviation | 1,464.9 | 1.00185 |

These diagnostics depend on the scalar being measured and on the ESS estimator. They are **not counts of distinct plans**. The 2020 seat and efficiency-gap lag-one autocorrelations were approximately 0.93. Chain-specific 2020 post-burn-in mean seat counts range from **5.617** to **5.829**, and chain-specific mean cut edges from **832.77** to **859.35**. Accordingly:

- 18,900 post-burn-in **observations** is accurate; 18,900 independent maps is not.
- Close-but-not-perfect R-hat values are an incomplete convergence check; scalar similarity does not prove mixing over district assignments.
- Confidence/uncertainty intervals for means and percentiles require methods respecting serial dependence (e.g., replicate-chain comparisons, appropriately selected block bootstrap, or careful Monte Carlo standard errors).
- Three chains with a common enacted starting state do not test convergence from dispersed starting plans.
- Burn-in of 700, and of 300 for shorter tolerance runs, is a design choice. There is no reported systematic burn-in sensitivity or convergence proof.

## 4. Constraint model versus legally realistic alternatives — **HIGH PRIORITY**

At `src/redistricting/ensemble/constraints.py:9-16`, the enforced conditions are **only contiguity and within-percent population**. At `src/redistricting/ensemble/chain.py:124-142`, proposals use ReCom with `always_accept` for candidates satisfying those conditions. At `scripts/run_baseline.py:31-35` the default population tolerance is ±2%.

Michigan's constitutional map criteria additionally include equal population and compliance with federal voting-rights requirements, geographically appropriate island connections, communities of interest, avoiding disproportionate partisan advantage, subdivision-boundary consideration, and reasonable compactness. Its published mapping procedure specified a ±0.5% congressional tolerance target. Sources: [Michigan Constitution art. IV §6](https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6); [MICRC mapping procedure](https://www.michigan.gov/micrc/-/media/Project/Websites/MiCRC/Procedure/MICRC_DRAFT_v1104_Mapping_Process_and_Procedures_with_Edits_Redlined.pdf).

**Consequence:** The sampled plans are graph-contiguous, population-tolerant configurations under a simplified model, **not certified legally valid Michigan congressional maps**. A 1%/2%/3% variation may be a useful methodological sensitivity, but is insufficient for a legal or fully realistic null ensemble. The reference max population deviation is 0.402%, while the 2% pooled mean is 1.865%; reference is structurally different in population balance from typical sampled plans. Similarly, reference cut edges 681 versus ensemble average 845 are an important indication of model/shape mismatch and cannot be assigned to partisan mechanisms in isolation.

ReCom's `always_accept` implementation does not sample plans uniformly from all admissible configurations and does not enforce partisan neutrality as a theorem. An algorithm without an explicit party objective does not automatically define the appropriate nonpartisan reference distribution. GerryChain's documentation distinguishes ReCom variants by pair-selection and spanning-tree mechanisms: [GerryChain proposal documentation](https://gerrychain.readthedocs.io/en/v1.0.0/api/proposals_constraints/). Record the actual installed version and specify the exact proposal variant.

**Required follow-up:** run more appropriate constraints, including ±0.5% or stricter if feasible, legally motivated boundary criteria, and VRA checks with appropriate demographic data. Compare results by constraint set. This is additional experimentation, **not a Stage 1 verification already completed**.

## 5. Geography representation and input provenance — **HIGH PRIORITY**

`src/redistricting/ensemble/partition.py:14-72` connects disconnected graph components by adding artificial edges **between arbitrary minimum-numbered nodes of a common initial district**, without using actual proximity, water routes, or county island membership as the selection rule. This maintains graph reachability but may distort district contiguity and the number/location of cut edges. Every artificial edge must be logged and justified against actual geography.

The Week 1 dissolve component report (`outputs/tables/week1/mi_district_population_validation.csv`) flags **7 of 13 Michigan districts** as multi-component polygons; some report hundreds of pieces. That is a GIS diagnostic, **not proof of illegal district discontinuity**: Michigan has islands and fragmented geometries, and graph-level adjacency conventions differ from polygon-component tests. With no original shapefile or graph available, this discrepancy cannot be resolved now.

The project describes Michigan's map simply as the "enacted" plan. Michigan's present 13-district congressional cycle was adopted in 2021 for 2022 onward (the commission's Chestnut map), while the voting layers are 2016 and 2020 *historical presidential returns*. It is valid to use old votes counterfactually on a newer map, but the exact map vintage and precinct-to-map assignment provenance need explicit verification and accurate text. Official references: [MICRC 2021 commission report](https://www.michigan.gov/micrc/-/media/Project/Websites/MiCRC/MISC8/Commission-Report.pdf?rev=b81719cd008241af8c4ce2b8691365ce); [Michigan mapping data](https://www.michigan.gov/micrc/mapping-process/mapping-data).

**Required input audit:** obtain each original source file with upstream URLs and retrieval dates, map identifier, population vintage, election-field descriptions, how 2016/2020 votes were assigned to the chosen precinct geography, CRS, feature count, null/duplicate node check, island/bridge adjacency convention, checksum, and explicit proof that map and election tables join without gaps or duplicates.

## 6. Mathematical implementation and test quality

### Positive findings

- `scripts/week3_partisan_metrics.py` implements exact wasted votes and clearly labels its sign convention. The `src/redistricting/ensemble/chain.py:42-66` formula agrees with saved Week 3 reference metrics to the available precision.
- The nonuniform-turnout distinction from the seats/votes shortcut is understood and documented.
- Polsby–Popper, convex-hull ratio, and a smallest enclosing circle implementation for Reock are present. Unit tests exercise elementary geometry and simple bounds.
- Step 0 is appropriately excluded from the post-burn-in empirical sample.
- `empirical_position()` correctly implements discrete midranks and inclusive tails; numerical output matches independent recomputation.
- Selected-plan replay verifies tracked scalar metrics before accepting recovered assignments (`scripts/recover_week5_map_examples.py:74-148`), a good integrity precaution.
- Original manuscript qualifies its claims about legal conclusions and full MCMC mixing; this is a worthwhile safeguard.

### Defects and test gaps

- Unit tests cover simple metric examples, CSV transformations, and helper functions, **not** an actual precinct-level chain reproduction with independent baseline checking.
- Graph node validation checks field presence and negative population but does **not** comprehensively verify election vote data are nonnegative and finite, population values finite, joins complete, IDs stable, or all initial districts graph-contiguous. Graph-level validation is otherwise delegated to GerryChain.
- The bridge-repair routine is not independently tested in the included suite.
- Week 1 `contiguous_by_polygon_components` is a different notion of contiguity from graph connectivity. It should not be interpreted as authoritative legal contiguity without island treatment.
- The compactness scripts calculate shape metrics but the ensemble only tracks cut edges; these are not interchangeable. Boundary cut edges depend on precinct resolution.
- The traditional split-Rhat implementation can return values slightly below one in finite samples. It is a useful internal check but should be supplemented by modern rank diagnostics, ESS, and multiple starts.
- Research literature and references are preliminary: existing citations to Guest et al. 2019 and Kenny et al. 2023 were verified externally, but the manuscript still requires source-by-source citation checking and methodological literature on the actual ReCom sampler.
- `run_baseline.py` imports GerryChain and assumes its graph-path convention; the provided snapshot does not contain input data or a lockfile sufficient to reproduce historical stochastic transitions byte-for-byte.
- `scripts/run_optimization.py`, `run_sensitivity.py`, `train_surrogate.py`, and several `src/redistricting` modules are **empty stubs**, so don't describe them as implemented contributions.

### Executed tests

Command: `PYTHONPATH=src python -m pytest -q --ignore=tests/test_week4_chain_metrics.py`  
**Result: 25 passed.**

The full suite cannot currently be collected in this isolated environment because `gerrychain` is not installed and container package download failed owing to unavailable network/package access. The six Week 4 tests therefore remain **unexecuted here**, not failed. The 25 passing tests establish bounded helper-function correctness, not full pipeline validity.

## 7. Robustness work actually completed

For 2020 Michigan, independent recomputation confirms the saved summaries of 8,100 post-burn-in observations for each ±1% and ±3% configuration; the ±2% baseline has 18,900. Mean Democratic seats are 5.7163 (±1%), 5.7149 (±2%), and 5.9257 (±3%). Efficiency-gap ensemble means are −0.09954, −0.09992, and −0.08410. Both alternative chains start from the same step-0 reference plan.

This is meaningful *population-tolerance* sensitivity. It does **not** cover county or municipal splits, compactness-preserving transitions, VRA opportunity districts, alternative graph adjacency/bridge rules, independent map-generation algorithms, or starting states. Robustness is therefore **partially studied, not established globally**.

The 2016/2020 comparison is also useful but paired by geographic chain, as explained above. The proposal mechanism was not audited at runtime.

## 8. Priority-ranked issue ledger

| ID | Severity | Issue | Consequence | First corrective action |
|---|---|---|---|---|
| P0-01 | Critical | `data/raw` missing and provenance blank | Not end-to-end reproducible | Restore hashed data + metadata and map identifiers |
| P0-02 | Critical | Only contiguity and loose population rules | Comparison set unlike legally realistic alternatives | Design legally motivated constrained sampler, stricter census equality |
| P0-03 | High | 18,900 observations highly correlated | False precision and inference risk | Add robust ESS/rank-Rhat, Monte Carlo uncertainty, longer/dispersed chains |
| P0-04 | High | Graph bridge choices arbitrary | Potentially alters geography and cut edges | Audit every bridge against county/water geography |
| P1-05 | High | Missing archived district histories and assignments | Cannot reproduce sorted ranks or map examples directly | Archive district metrics and selected/full assignment snapshots |
| P1-06 | High | "Enacted" map and election source lineage unspecified | Possible historical/mapping mislabel | Confirm exact 2021/22 map and provenance of 2016/20 assignment |
| P1-07 | High | Actual cut-edge distribution structurally different from reference | Confounding in interpretation | Add matched compactness/county split sensitivity |
| P1-08 | Medium | No Missouri ReCom replication results | Two-state generalization unsupported | Reproduce same ensemble/diagnostics in Missouri |
| P1-09 | Medium | Discrete seat-count midrank easily misread | Overstates apparent outlier status | Always show `P(S>=7)=13.93%` alongside 92.52% midrank |
| P1-10 | Medium | Sparse integration tests, no version lock | Reliability and replay risk | Add synthetic graph integration test and frozen environment |
| P2-11 | Low | README/status/checklist stale, empty placeholders | Confusion about actual completeness | Update documentation and remove/prominently label stubs |
| P2-12 | Medium | Manuscript still oversells "valid maps", lacks data citation | Submission credibility gap | Rewrite claims once experiments validated |

## 9. Defensible claims today vs. not defensible today

### Supported by the saved data (with stated caveats)

1. A substantial Michigan 13-district counterfactual evaluation exists, using fixed 2016/2020 presidential vote layers and a three-chain ReCom pipeline.
2. Under the specific 2020, ±2%, contiguity-based sampling procedure, the recorded enacted reference has 7 Democratic seats versus 5.715 average sampled seats, and the reported empirical positions are arithmetically correct.
3. The 2016 and 2020 scoring comparisons use matching geographic chain histories for each seed and permit paired descriptive comparisons.
4. Varying population tolerance from ±1% to ±3% changes some statistics; the magnitude is explicitly measurable.
5. These results constitute a computational case study **conditional on the supplied code and archived outputs**.

### Not yet supported

1. "This map is an illegal or intentionally partisan gerrymander."
2. "The simulation uniformly samples all legally valid congressional maps."
3. "The enacted map is statistically proven extreme with sample size 18,900 independent maps."
4. "All 13 districts and all simulated maps meet every legally relevant condition."
5. "The findings replicate in Missouri with ReCom."
6. "The project derives a new fairness theorem or a novel mathematically validated algorithm."
7. "A third party can regenerate all figures from the public repository with no additional input files."

## 10. Gate for beginning Stage 2

Stage 1 has completed source inspection, available tests, saved-output recalculation, scope checks, and external cross-checks for major legal/procedural context. The next stage is not paper drafting. It should be **mathematical validation and empirical repair**, in this order:

1. Supply original raw precinct shapefiles and GerryChain graph or verifiable URLs/checksums; reconcile the 2021 Chestnut plan with the `CD` field.
2. Inspect water/island bridges and initial/sampled district contiguity on the exact original graph.
3. Specify a legally credible constraint set and run the first short **≤0.5% population** chain; debug feasibility.
4. Verify a short deterministic chain end to end with pinned GerryChain version and archived plan/district snapshots.
5. Add ESS, chain variability, and MC uncertainty to outlier and sensitivity estimates.
6. Redesign the paper's contribution around explicit **sensitivity to constraints and election layers**, rather than a general claim that the enacted map is a partisan gerrymander.
7. Replicate in Missouri if the manuscript's comparative claims need two states.

**Audit conclusion:** Promising, real computational work; internal arithmetic generally consistent. The principal publication obstacles are not prose quality but **data lineage, legally meaningful ensemble construction, Monte Carlo uncertainty, and independently reproducing the geographic experiment**. The paper should not be finalized until these are addressed or expressly bounded.