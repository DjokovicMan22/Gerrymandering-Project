# When a Random Map Is Not a Neutral Map: Geographic Adjacency, Convergence, and the Limits of Michigan Redistricting Ensembles

**A source-audited computational sensitivity study**

*Research manuscript — Version 1.0, 18 October 2026*  
*Status: Complete first scholarly draft; not yet externally peer reviewed.*  
*Data and code: [Gerrymandering-Project, research validation branch](https://github.com/DjokovicMan22/Gerrymandering-Project/tree/research/stages-1-3-validation).*

## Abstract

Computer-generated redistricting plans are frequently used to evaluate whether an enacted electoral map is unusual relative to alternative geographic arrangements. Yet the evidentiary force of such comparisons depends on choices that may appear merely technical: what qualifies as adjacent geography, which maps are considered feasible, how transitions are proposed, and whether a simulation reaches its intended distribution. This study examines those dependencies using the 13-district Michigan congressional reference, a 4,756-precinct graph, and counterfactual 2016 and 2020 presidential-vote allocations. Auditing an earlier simulation revealed five artificially inserted graph edges linking precinct polygons roughly 42–280 kilometers apart; the edges were selected because their endpoints shared an enacted district label. Replacing them with a district-label-independent polygon-proximity construction produced a connected, reference-compatible graph with 13 added edges, although legal island and water contiguity remained unverified. Previously generated ReCom chains failed prespecified convergence diagnostics. An independently implemented reversible local Metropolis–Hastings sampler had a mathematically characterized conditional target but also failed to mix adequately; an additional published reversible recombination configuration produced no accepted moves in a limited feasibility pilot. Rather than interpret these outputs as samples of legally valid maps, we define a narrower estimand: the final plan produced by 800 recorded transitions from the enacted reference. Sixty-four independently seeded trajectories—32 under each of two exploratory fragmentation regimes—yielded mean Democratic seat counts of 7.219 and 6.813, and mean efficiency gaps of +0.0201 and −0.0127. These are reproducible, model-conditional algorithmic outcomes, not neutral-map probabilities. The central finding is methodological: an apparently large ensemble can support weak substantive inference when geographic representation, admissibility and mixing are unresolved. A credible redistricting benchmark requires independent validation of each layer.

**Keywords:** redistricting; gerrymandering; Markov chain Monte Carlo; ReCom; graph topology; computational reproducibility; sampling convergence; geographic sensitivity; Michigan.

---

## 1. Introduction

A map can appear biased without being an unusual product of the rules governing its construction. Conversely, a district plan that looks geographically unremarkable can allocate political representation in ways rarely observed among plausible alternatives. Computational ensemble analysis offers a response to this ambiguity: generate alternative districting plans subject to explicit criteria, evaluate each using the same election data, and compare the enacted map with the resulting distribution. The approach is attractive precisely because it promises to replace aesthetic judgment with a reproducible counterfactual. But an ensemble is not self-validating. The adjective *neutral* describes a defensible relation between an algorithm, a feasible state space and a research question; it does not follow merely because the program contains no variable labeled “partisanship.”

There are at least four logically distinct claims in the phrase “the enacted plan is an outlier among neutral alternatives.” First, the geographic representation must correspond sufficiently well to the land, islands and legally relevant relationships being modeled. Second, the state space must embody applicable population, contiguity, community, administrative and federal voting-rights constraints. Third, the sampling procedure must have an appropriate, known or justified target distribution. Fourth, the observed chains must explore that target adequately for summary statistics to be interpretable. Reproducing a script and its output verifies none of these propositions by itself.

This distinction has become especially important as redistricting simulations have moved beyond demonstrations into empirical and legal argument. DeFord, Duchin and Solomon (2021) describe recombination algorithms for exploring graph partitions. Chikina, Frieze and Pegden (2017) examine how significance may be assessed in some Markov-chain settings without a full mixing result, but their methods require particular theoretical conditions rather than granting every finite Markov chain an automatic inferential interpretation. Cannon et al. (2026) rigorously develop a reversible recombination approach with a characterized spanning-tree-weighted stationary law. Meanwhile, Kenny et al. (2023) demonstrate how carefully constructed simulated plans can distinguish the contributions of geography, formal constraints and line-drawing decisions. Taken together, these works establish the promise of computation while making the definition and verification of its comparison distribution an essential research problem.

This paper investigates a concrete failure mode within that broader problem. Starting with a Michigan precinct-level redistricting project, we initially attempted to characterize the partisan position of the enacted congressional map through ReCom chains. Independent audits exposed shortcomings in both graph topology and stochastic sampling. Rather than hide the failed tests or interpret tens of thousands of correlated observations as independent legal alternatives, we separated the analysis into three empirically answerable questions:

1. **Graph construction:** How much does a superficially minor, unverified rule for joining disconnected precinct components change the validity of a map model?
2. **Sampling:** What can be inferred when a chain is reproducible but its stationary target, convergence or mobility is inadequate?
3. **Conditional sensitivity:** Given an explicitly defined, reference-anchored *finite-time* algorithm, how do alternative fragmentation caps affect the distribution of terminal partisan scores and spatial changes?

The contribution is not a verdict on the legality or intent of Michigan's district lines. It is an audit-backed account of why technically successful redistricting computations may fail to justify the statistical claims attached to them, together with a reproducible replacement experiment whose inferential scope is deliberately narrower. Michigan is useful not as an exemplar of presumed wrongdoing, but as a data-rich case in which source geometry, graph construction, historic output archives and multiple stochastic proposal mechanisms can be directly compared.

## 2. Research context: what would count as a neutral comparison?

### 2.1 The state space is part of the hypothesis

Represent a precinct-level state as an undirected graph `G=(V,E)`. Each vertex `v` is a geographic unit with population `p_v` and election attributes; an edge asserts adjacency under a defined geographic rule. A congressional map is an assignment `x:V→{1,…,K}`, where here `K=13`. For each district label `d`, the induced subgraph `G[x^{-1}(d)]` should be connected *under the chosen adjacency definition*. Population equality can be imposed by

```text
|P_d(x) / P* − 1| ≤ ε,      P* = (Σ_v p_v) / K,
```

where `P_d(x)` is district population, `P*` is the equal-population ideal and `ε` is the tolerance applied by the particular experiment.

This formalization immediately exposes a substantive problem: graph connectivity is not identical to legally acceptable contiguity. Michigan's Constitution, article IV, section 6(13), explicitly addresses geographic contiguity and treats islands as contiguous by land to the county of which they are part. It also establishes a ranked set of considerations that includes federal law and the Voting Rights Act, communities of interest, partisan fairness, consideration of county/city/township boundaries, and reasonable compactness. A model in which a precinct becomes “adjacent” because it is the nearest polygon across water need not satisfy those rules. Nor do generic cut-edge or county-split penalties encode them exactly. A computational state space is therefore a proposed *model of admissibility*, not a legal determination.

### 2.2 The target law is not determined by the proposal name

Even after selecting a graph and feasible set `S`, an ensemble needs a probability law `π` over maps. Uniformity over labeled maps, uniformity over unlabeled district partitions and a spanning-tree-weighted distribution are different constructions. They need not agree on the frequency of a particular partisan score. A transition kernel `P(x,y)` should be assessed relative to that intended law: stationarity requires `πP=π`, while detailed balance is the stronger sufficient condition `π(x)P(x,y)=π(y)P(y,x)`. An irreducibility and practical-mixing argument is still needed to say that finite runs approach the intended law from their starting states.

Ordinary ReCom proposes a new pair of districts by merging adjacent districts, constructing a spanning tree and splitting it into population-balanced connected parts (DeFord et al. 2021). Its strong spatial movement can be useful, but the name “ReCom” alone does not identify a universal stationary distribution, especially when custom hard rejections alter the implementation. In contrast, Cannon et al. (2026) describe a reversible recombination kernel targeting a distribution weighted by district spanning-tree counts. That theorem applies under its specified kernel and state-space assumptions; simply invoking a library routine, adding undocumented geographic restrictions, or running it for a small number of steps does not establish mixing on the present Michigan model.

The distinction between *a mathematically known invariant law* and *empirical exploration of it* underlies this paper. A theoretically reversible chain can be immobile. An active chain can have an unknown target. Neither output should automatically be treated as a sample of legal maps.

### 2.3 Partisan scores are descriptions, not self-interpreting tests

We use Democratic seats under a fixed two-party presidential vote overlay and the efficiency gap. Following Stephanopoulos and McGhee (2015), the efficiency gap is the difference between wasted Republican and Democratic votes, divided by total two-party votes. In the project's sign convention,

```text
EG(x) = [W_R(x) − W_D(x)] / [V_R(x) + V_D(x)].
```

A positive value indicates more Republican than Democratic wasted votes under this convention; a negative value indicates the reverse. Wasted votes consist of votes for the losing party and votes for the winning party beyond its defined winning threshold. The implemented threshold is `floor(total_two_party_votes/2)+1`. Because 2016 precinct allocations contain fractional votes, that floor operation makes individual district wasted-vote totals slightly sensitive to floating summation order. The source audit identified and bounded a one-vote-level difference in the archived 2016 reference efficiency gap; the discrepancy is numerically small but should not be concealed as exact agreement.

An efficiency gap or seat count is not, on its own, evidence of intent, legal invalidity or discriminatory effect. Even a perfectly computed score remains conditional on the overlay election, turnout distribution, districting graph, and law assigned to the alternative maps. In this study the 2016 and 2020 *presidential* vote fields are applied counterfactually to the congressional plan adopted in 2021; they are not observed congressional-election outcomes under that plan.

## 3. Data and reproducibility

### 3.1 Provenance and processed precinct graph

The principal Michigan source is the processed election/population/precinct dataset published by Ellen Veomett and collaborators Arbie Hsu and Alusi, using Redistricting Data Hub inputs and the `maup` geographic-processing library. Their data documentation identifies the 2020 Census population layer, VEST 2016/2020 presidential vote allocations and 2021 adopted congressional district field. The original published JSON graph is pinned by Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`; the matching original precinct polygon ZIP by `07bce18dabbcca9d549e28995a8156fd6978d7db`. The source files are governed by the authors' CC BY-NC 4.0 terms together with the applicable Redistricting Data Hub terms.

The original processed Michigan graph has **4,756 vertices, 12,378 edges, six connected components and 13 enacted congressional labels**. Summed precinct population is **10,077,331**, giving an ideal of **775,179.31** persons per district. The reference's maximum district deviation from that ideal is approximately **0.4019%**. Independently inspecting the published shapefile confirms its coordinate system as **EPSG:32616**. All 4,756 graph nodes were reconciled with polygon records on population, enacted label and county identifiers. This establishes processed-input matching, not a new recreation of the full upstream Census/VEST block-to-precinct data join or agreement with official election canvasses.

Under the processed 2020 presidential fields, statewide two-party totals are **2,804,046 Democratic** and **2,649,864 Republican** votes. The enacted reference gives **seven Democratic seats** and efficiency gap **+0.0033332** under the project's arithmetic. The processed 2016 presidential layer yields **six Democratic seats** and efficiency gap approximately **−0.0387493**, subject to the tiny rounding issue noted above. These reference calculations were independently reproduced by summing graph-node vote fields and reconciled against six saved initial-chain rows and 26 district-level election rows.

### 3.2 Independent computational checks

Reproducibility was assessed at different levels rather than reduced to a single “tests passed” declaration. Source identities were checked against exact published byte hashes. Original archived scalar histories were reanalyzed directly from the checked-in research ZIP rather than trusting their saved summary tables. Polsby–Popper, convex-hull ratio and Reock compactness scores were independently recalculated for all 13 reference districts from source-matched polygons; the Reock check used GEOS/Shapely's minimum-bounding-radius routine rather than the project's earlier randomized enclosing-circle implementation. At the code level, new adversarial tests reject malformed step indices, impossible seat counts, invalid population deviations, nonfinite precinct vote counts and other corrupt inputs.

These checks support the numerical and engineering claims made in subsequent sections. They cannot recover the full precinct assignments of historical chains that saved only scalar time series. They also do not verify the upstream raw Census/VEST joins or the legal admissibility of any sampled map. These omissions are treated as limits of the evidence, not as features that can be inferred from the consistency of derived tables.

## 4. Geographic topology: a five-edge decision that changed the model

### 4.1 The hidden role of artificial adjacency

The published Michigan graph contains six disconnected components, a common difficulty for land-based precinct graphs with island, shoreline or water-separated pieces. The original project made the graph connected by repeatedly identifying a disconnected component and a vertex in the principal component that shared an enacted congressional district label. It then added an artificial edge between arbitrarily selected vertices of that common label. The logic was convenient: it made the reference districts connected without explicitly changing their precinct assignments. But it encoded the enacted map into the connectivity repair itself.

When the original published precinct polygons were consulted, the five artificial edges proved to span roughly **42, 117, 134, 170 and 280 kilometers** between their endpoint polygons. They were not chosen to represent contact, geographic proximity, county-island rules or a documented transport corridor. An algorithm that subsequently assesses “contiguity” on the augmented graph inherits these unsupported connections. The fact that a reference map passes contiguity in such a graph therefore offers little independent evidence that the model reproduces physical or legal geography.

This is not merely a cartographic imperfection. The graph `E` determines which precinct reassignment moves are feasible, which districts count as contiguous and how many cut edges a plan has. Artificial edges can also change proposal probabilities for boundary-driven Markov chains. In addition, conditioning the construction of `E` on the enacted label `CD` undermines a comparison intended to treat the enacted map as an external object evaluated against alternatives.

### 4.2 Geometric repair, reference compatibility and selection bias

The first replacement joined original graph components using a minimum-spanning tree based on measured polygon-to-polygon distance, without consulting district labels when proposing edges. Its total proposed connection length fell to approximately **19.6 kilometers**. However, the resulting graph still left a four-precinct piece of the enacted sixth district disconnected. Rather than repair the failure by adding another enacted-label-conditioned connection, we examined a predeclared sensitivity grid of *K* nearest external polygon contacts per original disconnected component, with *K* taking values 1, 3, 10, 25 and 50.

The smallest **tested** neighborhood level that simultaneously connected the statewide graph and allowed all 13 enacted reference districts to be represented as connected was **K=3**, yielding **13 distinct inserted edges**. The longest candidate polygon separation was approximately **17.8 kilometers**. Under this model graph, the enacted reference has **682 graph cut edges**, versus **681** on the untouched published source graph. Source graph and generated-graph hashes were checked in independent workflow runs.

This construction avoids *directly* using partisan returns or enacted labels to select individual edges. Yet the choice of K=3 was made *after* testing whether the reference itself remained representable. The overall modeling decision is thus still partly reference-conditioned. More importantly, geographic nearness alone does not certify Michigan's statutory island/county contiguity: some candidate connections span nonzero gaps between polygons and may cross water. The resulting KNN3 graph is therefore best described as an **explicit proximity-based sensitivity topology**. It is not a legal replacement for an authoritative adjacency model.

A general principle follows: selecting boundary conventions by how well they preserve the benchmark plan can introduce a subtle baseline-selection mechanism even when a local edge-selection routine never reads election data. An analytically legitimate neutral benchmark would require an adjacency convention grounded independently in geography and applicable law *before* assessing the enacted plan.

## 5. Sampling experiments: motion is not convergence

### 5.1 Original archived ReCom histories

The earlier Michigan experiment produced long ReCom traces and summary percentiles. Subsequent audits recovered the original checked-in research ZIP and independently recomputed **12 complete scalar-metric histories**: six 7,000-state runs under 2016 or 2020 presidential overlays with nominal ±2% population tolerance, and six 3,000-state runs under ±1% or ±3% tolerances. After the archived burn-in convention, the 2020 ±2% case contained **18,900 correlated recorded states**, with mean Democratic seats **5.7149** and mean efficiency gap **−0.0999**. The enacted reference's inclusive Democratic seat-count upper-tail frequency was **2,633/18,900 (13.93%)**, while a midrank percentile counted tied values differently. Such differences are not statistical-significance estimates: the observations are serially correlated, the target distribution was not shown to be the legally relevant one, and the original RNG settings did not make those historic trajectories replayable from their nominal seed numbers.

The original ±2% chains also do not satisfy the later, stricter ±0.5% population modeling assumption. Among the 18,900 post-burn-in states in that historical condition, **zero** met the ±0.5% tolerance. A sample cannot be retroactively relabeled as drawn from a more restrictive feasible space merely because its partisan metrics were calculated correctly.

### 5.2 Explicit-seed ReCom and diagnostic failure

After correcting GerryChain 1.0's independent random-number generator initialization, a separate experiment used four dispersed warm starts under each of two exploratory geographic-constraint regimes. Eight explicitly seeded ReCom chains, each with **4,001 recorded states**, produced **32,008 serially correlated observations** and 648 independently verified saved assignments. For the efficiency gap, the closer condition yielded rank-normalized **R-hat 1.733** and bulk effective sample size **9.4**; the relaxed condition yielded **R-hat 1.139** and bulk ESS **20.4**. Both violated the study's prespecified scalar diagnostics of R-hat no greater than **1.01** and ESS at least **400**.

R-hat and ESS are diagnostics, not proofs of equilibrium; nevertheless, values this far outside prespecified acceptance criteria are affirmative grounds **not** to interpret pooled values as stationary estimates. As emphasized by Vehtari et al. (2021), convergence analysis must attend to inter-chain behavior and autocorrelation rather than the sheer volume of saved draws. Here, chains often moved noticeably through geographic space, yet movement did not produce satisfactory mixing on partisan outcomes.

### 5.3 Reversibility without usable exploration

We next implemented a local boundary-edge Metropolis–Hastings kernel with a known acceptance correction. The algorithm chooses a boundary edge, proposes either a one-precinct district flip or a two-precinct label swap, rejects invalid configurations, and applies `min(1,q(y,x)/q(x,y))` to enforce detailed balance between feasible neighboring states. Exact enumeration on a small graph verified detailed balance in the implemented finite setting. The resulting uniform invariant law applies **within a reachable communicating component of labeled, proxy-feasible maps**; irreducibility across the full feasible space was not established.

Theory did not resolve the empirical obstacle. A real-data pilot obtained acceptance rates around **9–16%** but changed only **1.7–3.7%** of precinct assignments from warm starts after 2,000 attempts. In later eight-chain testing, efficiency-gap R-hat and bulk ESS remained unacceptable: for the closer condition **1.568 and 7.1**, respectively; for the relaxed condition **2.588 and 4.8**. Under the project's hard caps and small feasible boundary moves, the method did not explore useful portions of the space in the allotted computational budget.

We also tested a GerryChain implementation of the published reversible ReCom variant. Under the specific strict parameter settings tried, neither of two **200-proposal** pilots produced a changed map. This is a negative *pilot configuration* result, not a general refutation of reversible recombination or of the proven spanning-tree target developed by Cannon et al. (2026).

Together, the experiments reveal an operational distinction that should appear in redistricting research reports: **a chain with strong local movement is not necessarily a valid stationary sampler, and a sampler with a derivable stationary law is not necessarily computationally effective under the proposed constraints**.

## 6. A narrower, identifiable estimand: finite-horizon perturbation

### 6.1 What is being sampled?

Because the neutral stationary target was not verified, the final experiment deliberately changed the research question. Let `x_0` be the enacted reference assignment and `P_c` the implemented stochastic transition procedure under geographic condition `c`. Rather than assert that `x_T` approximates a uniform or spanning-tree-weighted legal map, define the **finite-horizon outcome law**

```text
Q_c,T(A) = Pr{x_T ∈ A | x_0 = enacted reference, graph = KNN3,
                       fixed transition implementation and caps c}.
```

Here `T=800` recorded transitions after step zero. The estimand `E_{Q_c,T}[f(x_T)]` is meaningful by construction: it describes what this particular algorithm produces after a fixed computational horizon starting from a particular map. It does **not** imply a unique stationary target, unbiased representation of legal maps, or independence of the final state from the enacted reference. This weaker estimand is the subject of our finite-horizon comparison.

### 6.2 Experiment protocol

We used the source-reconciled KNN3 model graph, an ideal-population deviation tolerance of **±0.5%**, and GerryChain 1.0 ReCom transitions with an explicitly initialized, chain-owned RNG. Each run recorded **801 states including the initial enacted plan**. Only its *terminal* state was retained as a Monte Carlo observation.

Two geographically constrained regimes were examined. The **closer** regime permitted at most **760 cut edges**, **18 split source county groups**, and **20 split source county-plus-MCD groups**. The **relaxed** regime increased these thresholds to **850**, **24**, and **49**, respectively. The counts are exploratory proxies, not Michigan statutory compliance determinations. They were selected in a broader development process involving source and pilot inspection; the final 64-run protocol fixed them before the final independent-endpoint results were aggregated, but this is **not an untouched confirmatory preregistration**.

For each condition, independently initialized RNG seeds **10001–10032** generated **32 trajectories**, producing **64 terminal maps** in total. The same seed labels were used across conditions for bookkeeping; they do not make the alternative Markov kernels identical. Seed 10001 was replayed in a separate process in both regimes, reproducing terminal assignment hashes and complete reported metrics. Each terminal assignment was independently rescored for 2020 presidential seat counts and efficiency gap, population equality, proxy fragmentation, source-graph contiguity and its SHA-256. Both regimes had **32 distinct final assignment hashes**.

Sampling *one terminal map per independently seeded run*, rather than all **51,264** correlated recorded states, makes the Monte Carlo unit explicit. It does not remove every concern about pseudorandomness or parameter choice, and 32 terminal maps per condition remain a modest sample. But it avoids mistaking closely related successive MCMC states for independent observations when estimating uncertainty about the **finite-time algorithmic mean**.

### 6.3 Uncertainty calculations

For a statistic `f`, the mean of 32 independent-seed endpoints estimates `E_{Q_c,T}[f]` under the generator and its fixed starting map. We used 10,000 nonparametric, deterministic-seed bootstrap resamples of the **32 endpoints**, taking the 2.5th and 97.5th percentiles to form approximate **95% Monte Carlo intervals for that conditional mean**. These intervals represent variability among independent runs of this algorithm, not uncertainty about a legally neutral map distribution or a claim of generalizing to other election years.

For the descriptive indicator that an endpoint's efficiency gap is at least the enacted reference efficiency gap, we computed the observed proportion and Wilson 95% binomial interval. Since the enacted map is also the deterministic starting state, and the model and caps are researcher-designed, the resulting fraction **must not** be described as an enacted-map randomization p-value.

## 7. Results

### 7.1 Terminal partisan scores and geographic movement

**Table 1. Independent finite-horizon terminal map outcomes, by geographic-cap condition.** Entries are mean [approximate 95% bootstrap interval] across **32 separately seeded terminal maps**, *not* 801 sequential observations per run. 2020 presidential vote fields are applied counterfactually to the adopted congressional assignment.

| Outcome | Closer constraints | Relaxed constraints |
|---|---:|---:|
| Democratic seats | **7.219 [7.000, 7.438]** | **6.813 [6.594, 7.031]** |
| Efficiency gap (project sign) | **+0.02010 [+0.00300, +0.03722]** | **−0.01268 [−0.03036, +0.00458]** |
| Cut edges in KNN3 model graph | **695.09 [686.00, 703.75]** | **758.84 [746.66, 771.16]** |
| Split source county groups | **17.97 [17.91, 18.00]** | **23.81 [23.63, 23.97]** |
| Split county-plus-MCD groups | **19.94 [19.84, 20.00]** | **47.94 [47.50, 48.34]** |
| Precincts reassigned after optimal district-label matching | **13.40% [12.05%, 14.81%]** | **29.00% [27.75%, 30.29%]** |

### Figures: exact, independently checked endpoint data

The following figures were generated **directly from the 64 independently verified terminal assignment metrics** in the archived successful Stage 3 workflow. The data were retrieved in a separate, read-only GitHub Actions job; the plotting script refuses a wrong graph hash, a missing seed, duplicate endpoint map hashes, unreconciled source summary means, or incorrectly asserted legality/stationarity. Each figure depicts the *fixed-horizon algorithmic law*, not a neutral legal-map sample.

![Figure 1: Empirical cumulative distributions of endpoint efficiency gaps for both constraint regimes, with enacted reference shown by dotted vertical line.](figures/figure1_terminal_EG_ECDF.svg)

**Figure 1.** Empirical cumulative distributions of terminal efficiency gaps in the two researcher-defined regimes (32 independent seeded endpoints per regime). The dotted reference line marks the enacted map's counterfactual 2020 presidential efficiency gap. This is *not* a legal-map outlier test.

![Figure 2: Matched RNG-seed labels' terminal efficiency gaps under tighter versus relaxed caps.](figures/figure2_paired_seed_EG.svg)

**Figure 2.** The 32 pairs of terminal efficiency-gap scores indexed by a common RNG seed label across the two cap conditions. The dashed diagonal indicates equal partisan scores. Common seed identifiers do *not* mean that matched trajectories use identical proposal sequences or produce comparable individual districts.

![Figure 3: Endpoint efficiency gap against fraction of precincts reassigned from the enacted map.](figures/figure3_spatial_change_vs_EG.svg)

**Figure 3.** Assignment movement from the reference after optimal relabeling versus terminal efficiency gap. The between-regime separation in mobility illustrates the algorithm's sensitivity to exploratory geographic caps. These geographic nodes are not necessarily legally valid districts.

The exact source-scored CSV, original aggregate JSON, graph fingerprint, generated SVG and PNG images, and bootstrap comparison manifest are preserved in the [Stage 4 evidence-figure run](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39203488689). The deterministic figure generator is `scripts/research_audit/stage4_make_figures.py`.

The tighter model produces terminal plans closer to the original geography by every reported fragmentation measure and yields modestly higher Democratic seat scores under the selected election layer. Mean efficiency gaps differ by about **0.0328** (3.28 percentage points of the efficiency-gap scale) between regimes, while mean Democratic seats differ by about **0.406** seats. These are differences between **specified finite-time algorithmic procedures**, not a causal estimate of how legally valid district maps would respond to relaxing real Michigan law.

The geometry contrast is particularly strong. Under the closer regime, an endpoint differs from the enacted assignment at approximately **13.4%** of precinct nodes after optimal district-label matching; under the relaxed regime, **29.0%**. The chains also reject a large share of attempted geographic proposals: on average **79.22%** under closer caps and **52.83%** under relaxed caps. Lower geometric movement under tighter caps is consistent with more severe constraints on feasible proposals. However, the rejected-proposal rate is an implementation diagnostic and does not prove any particular legal or political mechanism.

The closer condition concentrates near its caps on county and county-plus-MCD splits (means **17.97 of 18** and **19.94 of 20**). The relaxed condition approaches its much larger bounds (means **23.81 of 24** and **47.94 of 49**). Because the baseline itself has only **14 split source county groups** and **9 split county-plus-MCD groups**, both models can diverge materially from the reference's administrative fragmentation. A headline suggesting “maps just like the enacted one except for partisan choices” would therefore misdescribe the sample-generating assumptions.

### 7.2 Why the enacted-reference frequency is not a p-value

The 2020-reference efficiency gap is about **+0.00333**. In the closer regime, **16 of 32** terminal simulated gaps were at least that value (50.0%; Wilson 95% interval approximately **33.6–66.4%**). In the relaxed regime, **13 of 32** met the same criterion (40.6%; Wilson interval approximately **25.5–57.7%**). Neither fraction provides a legal-map null probability. The generator is initialized *at* the enacted reference, the model topology is a geometry-proximity approximation, and the two cap regimes are researcher-selected. Consequently, no inference about intent, statutory validity or statewide partisan extremeness follows from these percentages.

The findings support a different, narrower statement: **within 800 recorded ReCom transitions from the same reference and on the same experimental proximity graph, choices about fragmentation caps were associated with materially different geographic movement and distributions of partisan scores**. The experiment makes that conditional relationship observable and reproducible. It does not identify which cap choice is socially, legally or scientifically neutral.

### 7.3 Paired-seed sensitivity as a secondary, model-conditional check

Because each cap regime was run under the same 32 nominal pseudorandom seeds, one can report differences between the corresponding terminal outcomes indexed by seed, rather than relying solely on two separate sets of condition means. We retained the paired indexing of the original fixed-horizon experiment and drew **20,000 bootstrap resamples of entire seed-indexed endpoint pairs**, not individual correlated chain steps. A deterministic resampling seed (20261018) makes the interval calculation reproducible.

**Table 2. Secondary paired-seed model contrasts.** Positive values mean the **tighter minus relaxed** finite-horizon procedure has a larger mean statistic. These intervals describe conditional simulation-procedure differences, not legal-plan probabilities or the causal effect of one isolated geographic rule.

| Endpoint statistic | Mean (tighter − relaxed) | Paired bootstrap 95% interval |
|---|---:|---:|
| Democratic seats (2020 presidential overlay) | **+0.406** seats | **[+0.124, +0.719]** |
| Efficiency gap (project sign convention) | **+0.03278** | **[+0.00975, +0.05631]** |
| KNN3 graph cut edges | **−63.75** | **[−80.06, −46.91]** |
| Reassigned precinct nodes from enacted reference | **−15.61 percentage points** | **[−17.79, −13.50]** |

The paired bootstrap uses the joint seed-indexed output of the two programs. Its precision is conditional on the fixed, researcher-selected comparison and approximate independence across the 32 separate RNG seed labels. It does **not** imply identical stochastic proposals within a pair, actual matched districts, or isolation of any one cap, because the cut-edge, county-split and MCD-split caps changed simultaneously. The results nonetheless sharpen the descriptive finding: the two finite-horizon procedures have distinguishable outcomes in this executed computational experiment. They supply **no additional evidence that either procedure samples neutral, legally valid Michigan plans**.

## 8. Discussion

### 8.1 Reproducibility is necessary but not inferential validity

The most important negative finding is a failure of implication. The source-matched graph, deterministic seeds, complete terminal assignment hashes, independent metric rescoring and 80 passing synthetic/adversarial tests demonstrate increasingly strong *computational reproducibility*. The historical archive's original metrics can also be recovered and checked. Yet a fully replicable output may be generated from an arbitrary spatial model or a nonconverged sampler. Reproducibility answers “can the claimed computation be recreated?” The inferential question is “does that computation estimate the quantity required by the scientific claim?” The first is a prerequisite for, not a substitute for, the second.

This distinction also explains why the failed chains are useful evidence rather than wasted research. Comparing the ordinary ReCom proposal with an analytically reversible local kernel revealed a practical tradeoff: far-moving updates need not come with a known neutral target, while a well-defined local target may be effectively inaccessible under restrictive constraints. The published reversible spanning-tree method provides a theoretically grounded alternative, but the zero-move local pilot showed that parameter feasibility matters independently of asymptotic theory. A serious analysis should report proposal attempts, invalid moves, self-loop rates, cross-chain diagnostics, spatial diversity, and validation of the state space—not simply the total number of maps output by the program.

### 8.2 Geographic choices are substantive research decisions

The five long, district-conditioned artificial edges were originally an engineering expedient. Auditing their physical lengths revealed how an ostensibly small data-preparation decision can encode the object under study into the space of alternatives. Even the repaired KNN3 model exposes an unresolved tension: geographic proximity is measurable, but constitutional island and community rules are not reducible to arbitrary nearest-neighbor links. A source-complete redistricting benchmark would need to verify county-based island contiguity and municipal/administrative boundaries from authoritative GIS, implement VRA opportunity constraints and communities of interest with appropriate domain review, and document how each criterion affects feasibility.

The Michigan Constitution is especially revealing here. Its ordered criteria include both geographic contiguity and avoiding disproportionate partisan advantage. These are not interchangeable with a single cut-edge cap or a generic measure of graph compactness. Nor can two population-balanced and connected synthetic plans be presumed *equally legally plausible*. Careful source work and explicit modeling assumptions should precede probabilistic conclusions, not merely accompany them in an appendix.

### 8.3 What the finite-horizon experiment does and does not rescue

It is tempting to conclude that replacing a stationary-ensemble claim with an endpoint experiment makes the substantive redistricting question disappear. That would be too strong. The endpoint experiment still illuminates *algorithmic sensitivity*: conditional on an explicit map and graph, relaxing the exploratory caps alters how far the chain moves and where its partisan-score distribution lies. The result could inform methodological design, benchmark stress testing and selection of more realistic constraints for a later study.

But it should not be misused as a backdoor outlier test. The reference is not drawn from the endpoint law, nor is the endpoint law justified as a neutral distribution over legal maps. Moreover, the eight hundred-step horizon is itself an experimental parameter; the results could change with the horizon. The models were selected after an exploratory process that considered whether the enacted map remained representable. The reported confidence intervals quantify uncertainty among seeded runs **conditional on all those choices**, not uncertainty about a universal redistricting truth.

### 8.4 A sequence of conditions for future substantive inference

To advance from this methods study to a genuine Michigan neutral-map analysis, four tasks are indispensable. First, reconstruct and independently certify legal contiguity, islands, communities and relevant boundaries from authoritative sources. Second, define feasible plans in a way that meaningfully reflects the ordered state and federal criteria, rather than relying on an unexplained combination of proxy thresholds. Third, choose an explicit target law over the feasible set and a kernel for which stationarity and accessibility are defensible. Fourth, demonstrate adequate exploration from appropriately diverse initial maps, with scalar and geographic diagnostics and sufficient replicated computation. Only then would an enacted-map percentile be plausibly interpretable as an inferential comparison rather than a descriptive property of software output.

## 9. Limitations

The first and largest limitation is **legal and geographic**. The repaired KNN3 graph is an experimentally chosen proximity approximation, not a certified Michigan island, shoreline, municipal, Voting Rights Act or communities-of-interest model. The absence of detailed VRA and community constraints precludes legal plan probability claims. In addition, the source polygons and election allocations are processed public derivatives; the original raw Census/VEST joining pipeline and agreement with official election canvasses have not been fully rebuilt.

Second, the election overlays are historically displaced: 2016 and 2020 presidential returns are allocated to a plan adopted in 2021. They do not account for candidate-specific congressional voting, later shifts in turnout, incumbency or strategic responses to new district lines. Third, efficiency gap and seat count summarize only selected aspects of representation; their interpretation depends on turnout, geography, competitiveness and the aggregation rule.

Fourth, the historic simulation archives do not preserve every precinct assignment or the correctly initialized chain RNG stream; their original transitions cannot be independently reconstructed from saved scalar scores alone. While new tests verify all finite-horizon terminal maps, the 64-run experiment was not designed to establish stationary convergence. The two geographic conditions differ in several cap thresholds simultaneously, so their score difference cannot be attributed to a single administrative constraint. The sample size of 32 endpoints per condition permits only modest-precision conditional Monte Carlo summaries. Finally, KNN3 and the constraint regimes emerged through exploratory development, and the final finite-horizon protocol was fixed only after that preliminary search; the analysis should not be presented as an externally preregistered confirmatory test.

These limitations do not contradict the empirical findings. They determine the scale of claims those findings can support.

## 10. Conclusion

A map ensemble acquires scientific meaning through the distribution it represents, not through the number of files produced. In this Michigan case, independent source audits exposed geographic repairs conditioned on the enacted map; convergence diagnostics rejected the inference that pooled ReCom traces represented stationary alternatives; and a reversible sampler with an interpretable conditional target proved too immobile under the chosen proxy constraints. The methodological response was to abandon the unsupported statewide null claim and specify a finite-horizon algorithmic estimand.

The resulting 64 independently verified endpoint maps show substantial sensitivity to geographic-cap choices: under otherwise fixed, source-reconciled modeling inputs, tighter constraints produced less precinct reassignment and different mean partisan scores than relaxed constraints. The result is directly reproducible, but it concerns **what the algorithm did after a chosen number of transitions**, not the frequency of partisan outcomes among all legally valid Michigan districts. It cannot establish that the enacted map was extreme, intentionally manipulated or unlawful.

That boundary between computation and inference is the paper's central claim. Redistricting algorithms can render assumptions transparent and generate informative counterfactuals. Their authority depends on whether geography, legal admissibility, transition law and convergence have each been independently justified. When those conditions are unverified, acknowledging failure is not a retreat from quantitative research; it is a more accurate account of what the numbers know.

---

## References

Cannon, Sarah, Moon Duchin, Dana Randall, and Parker Rule. 2026. “Spanning Trees and Redistricting: New Methods for Sampling and Validation.” *SIAM Review* 68 (2): 349–381. https://doi.org/10.1137/24M166944X.

Chikina, Maria, Alan Frieze, and Wesley Pegden. 2017. “Assessing Significance in a Markov Chain without Mixing.” *Proceedings of the National Academy of Sciences* 114 (11): 2860–2864. https://doi.org/10.1073/pnas.1617540114.

DeFord, Daryl, Moon Duchin, and Justin Solomon. 2021. “Recombination: A Family of Markov Chains for Redistricting.” *Harvard Data Science Review* 3 (1). https://doi.org/10.1162/99608f92.eb30390f.

Kenny, Christopher T., Cory McCartan, Tyler Simko, Shiro Kuriwaki, and Kosuke Imai. 2023. “Widespread Partisan Gerrymandering Mostly Cancels Nationally, but Reduces Electoral Competition.” *Proceedings of the National Academy of Sciences* 120 (25): e2217322120. https://doi.org/10.1073/pnas.2217322120.

McCartan, Cory, Christopher T. Kenny, Tyler Simko, George Garcia III, Kevin Wang, Melissa Wu, Shiro Kuriwaki, and Kosuke Imai. 2022. “Simulated Redistricting Plans for the Analysis and Evaluation of Redistricting in the United States.” *Scientific Data* 9. https://doi.org/10.1038/s41597-022-01808-2.

Michigan Constitution of 1963, art. IV, § 6(13). Michigan Legislature. https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6.

Stephanopoulos, Nicholas O., and Eric M. McGhee. 2015. “Partisan Gerrymandering and the Efficiency Gap.” *University of Chicago Law Review* 82 (2): 831–900. https://chicagounbound.uchicago.edu/uclrev/vol82/iss2/4/.

Vehtari, Aki, Andrew Gelman, Daniel Simpson, Bob Carpenter, and Paul-Christian Bürkner. 2021. “Rank-Normalization, Folding, and Localization: An Improved R-hat for Assessing Convergence of MCMC.” *Bayesian Analysis* 16 (2): 667–718. https://doi.org/10.1214/20-BA1221.

Veomett, Ellen, with Arbie Hsu and Alusi. “Michigan JSON and Shapefile” (processed precinct GIS, election and population data; source README and notebook). Source materials obtained from the Redistricting Data Hub, June 2024. https://github.com/eveomett-states/Michigan. CC BY-NC 4.0 and applicable Redistricting Data Hub conditions.

---

## Reproducibility and evidence appendix

**A. Processed input fingerprints.** Michigan original graph Git blob SHA-1: `a4dfe70818f87b97924781216f3d86a672cfc66a`. Original polygon ZIP Git blob SHA-1: `07bce18dabbcca9d549e28995a8156fd6978d7db`. Derived KNN3 graph SHA-256: `14355742f58291f4c26267982de07a21037c347f7598a68f032e0d68ea1d542c`. Historical archive ZIP SHA-256: `0f52e51f8b64d1f2bc93b2e4fc206f824d777d494a90ae8a278461bac48736d4`.

**B. Exact computational environment.** The main experimental dependency is `gerrychain==1.0.0` with Python 3.11, networkx, numpy, pandas and geopandas/shapely. CI captures dependency versions. Both condition cohorts used deterministic `PYTHONHASHSEED=0`, independently seeded chain RNG streams and per-run assignment/graph hashes.

**C. Audited original source, geometry and mathematics.** [Stage 1–2 verification report](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/research_audit/STAGE12_FINAL_VERIFICATION.md); [successful independent source, history and compactness CI](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183949679); [source provenance record](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/data_provenance.md).

**D. Nonconvergence and model construction.** [Original diversified ReCom diagnostics](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/research_audit/stage3_diversified_sampling_results.md); [reversible local-chain diagnostics](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/research_audit/stage3_reversible_mixing_results.md); [geographic bridge analysis and finite-horizon protocol](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/research_audit/stage3_finite_horizon_protocol.md).

**E. Independently seeded endpoint experiment.** [Successful 64-run GitHub Actions workflow, derived CSV endpoints, JSON summary and seed replay evidence](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152601); [Stage 3 final empirical report](https://github.com/DjokovicMan22/Gerrymandering-Project/blob/research/stages-1-3-validation/docs/research_audit/STAGE3_FINAL_REPORT.md). The published workflow artifact contains model-specific derived scores but excludes redistributed third-party source graphs and full precinct assignment maps.

**F. Plotting and paired contrasts.** [Stage 4 original-data graphics and paired Monte Carlo computation](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39203488689); production code in `scripts/research_audit/stage4_make_figures.py`. Input is the original Stage 3 aggregate artifact, strictly checked by SHA and seed identities. Contrasts concern the researcher-defined finite-horizon procedures only.

**G. Status and interpretation.** This is a **methods and conditional-sensitivity manuscript**; numerical computations and scoped reproducibility checks passed, while legal-plan stationarity, authoritative geographic admissibility and an enacted-map outlier hypothesis were **not established**. This manuscript should undergo external methodological review before submission. The reported conditional bootstrap intervals and endpoint frequencies are **not** gerrymandering significance tests.
