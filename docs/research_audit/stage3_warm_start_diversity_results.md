# Stage 3 Michigan map-diversity experiment — independently seeded warmups

> **REPRODUCIBILITY ERRATUM — October 18, 2026:** The historical runs described below used GerryChain 1.0.0 without explicitly passing `rng=seed` to `MarkovChain`. Their seed labels therefore **do not reproduce exact trajectories**. The archived generated maps and scalar results remain descriptive observations but should **not** be characterized as exactly seeded/replayable. See [Stage 3 RNG reproducibility erratum](stage3_rng_reproducibility_erratum.md) and the subsequently re-executed, seeded studies.\n\n
**Executed:** 18 October 2026  
**Successful CI:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734877  
**Protocol preregistered in repository:** [stage3_warm_start_diversity_protocol.md](stage3_warm_start_diversity_protocol.md)  
**Disposition:** **THE EXACT PREDECLARED 5% DISTANCE GATE PASSED BOTH CONDITIONS.** This shows *map separation* after seeded warmups, **NOT** independence from stationarity, valid legal-map sampling, or convergence.

## Experimental design

- Source: hashed noncommercial Michigan precinct graph, pinned Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a` (4,756 nodes; 13 congressional districts), after the project's five **artificial, independently unverified** connectivity bridges.
- Four random seeds **101, 202, 303, 404** for each geography condition (eight paths). Each path begins from **the exact same enacted reference map**.
- Each path records **800 states including step 0**, providing 799 geographic-proposal attempts. Total: 6,400 recorded states and 6,392 attempts; these are dependent trajectories, not 6,400 independent plans.
- Constraint set: ±0.5% population, connected districts on augmented graph, and exploratory hard caps:
  - **Closer:** max 760 boundary-cut edges, max 18 split `COUNTYFIPS` source groups, max 20 split `COUNTYFIPS+MCDFIPS` groups.
  - **Relaxed:** corresponding caps 850, 24, and 49.
- Rejected geographic proposals cause explicitly recorded **self-loops**; original GerryChain ReCom/population/contiguity constraints remain. Stationarity is not established for this kernel.
- Each endpoint was independently validated for node coverage, contiguity on augmented graph, population deviation and source grouping scores. Actual precinct assignments were not redistributed as workflow artifacts; only cryptographic hashes, distances and summaries were retained.
- Distance metric: exact fraction of 4,756 precinct nodes assigned to a different district **after optimally permuting district names** using maximum-overlap assignment dynamic programming. A renamed but identical map therefore has distance zero.

## Verified outcomes

| Condition | Distance from enacted reference (four endpoints) | Pairwise endpoint distance (six pairs) | Geographic rejection rate (four paths) | Map-change fraction per transition | Predeclared distance gate |
|---|---:|---:|---:|---:|---|
| Closer | **12.51–19.53%** | **11.56–17.47%** | **76.47–79.97%** | **17.65–22.90%** | **PASS** |
| Relaxed | **22.92–29.65%** | **21.17–31.33%** | **52.69–57.32%** | **40.93–45.18%** | **PASS** |

All ten distance comparisons per condition exceeded both 5% thresholds, including the six pairwise seed comparisons; all eight endpoints had distinct assignment SHA-256 hashes. This establishes observable separation but **does not establish** independent starts or stationarity.

### Endpoints under closer caps

| Seed | Different from reference (precinct nodes / fraction) | Final cut edges | Final split counties | Final split county+MCD groups | Geographic proposals rejected / attempted | Recorded map changes |
|---|---:|---:|---:|---:|---:|---:|
| 101 | 929 / 19.533% | 662 | 18 | 20 | 634 / 799 | 141 |
| 202 | 595 / 12.511% | 666 | 18 | 20 | 611 / 799 | 183 |
| 303 | 753 / 15.833% | 750 | 18 | 20 | 639 / 799 | 146 |
| 404 | 670 / 14.087% | 691 | 17 | 20 | 623 / 799 | 157 |

Exact pairwise node differences: (101,202)=612; (101,303)=607; (101,404)=831; (202,303)=671; (202,404)=679; (303,404)=550. The smallest difference was **550 / 4,756 = 11.56%**, above the preregistered 5%.

### Endpoints under relaxed caps

| Seed | Different from reference (precinct nodes / fraction) | Final cut edges | Final split counties | Final split county+MCD groups | Geographic proposals rejected / attempted | Recorded map changes |
|---|---:|---:|---:|---:|---:|---:|
| 101 | 1228 / 25.820% | 790 | 24 | 45 | 458 / 799 | 327 |
| 202 | 1410 / 29.647% | 672 | 24 | 47 | 439 / 799 | 346 |
| 303 | 1232 / 25.904% | 705 | 24 | 49 | 421 / 799 | 361 |
| 404 | 1090 / 22.918% | 729 | 24 | 43 | 422 / 799 | 354 |

Exact pairwise node differences: (101,202)=1345; (101,303)=1024; (101,404)=1253; (202,303)=1097; (202,404)=1490; (303,404)=1007. The smallest difference was **1007 / 4,756 = 21.17%**, above the preregistered 5%.

## Interpretation and limits

This is a concrete improvement over the old protocol in which chains were *initialized* identically and no label-invariant endpoint diversity audit was performed. In the closer condition, the 550+ distinct precinct positions between each warmup endpoint are more than trivial random-label effects; the relaxed condition generates still larger endpoint separation, but violates the enacted map's county/MCD fragmentation levels more strongly.

**There is no convergence claim.** Every chain still traces a path outward from the same enacted state, and its endpoint is not guaranteed to be a draw from the target stationary distribution. No evidence establishes that the model explores all feasible geographic configurations, that those configurations are legally compliant, that the rejection kernel has the intended stationary target, or that raw tail fractions are valid p-values. The graph uses five unverified artificial connectivity edges, and the county+MCD source keys are not independently authenticated municipality geometries. Optimized matching counts *precincts*, not a population-weighted or spatial-distance metric; this is an intentionally narrow diversity test.

**Research-stage verdict:** Stage 3 source-verified warmup diversification is *implemented, reproducible, and its predeclared metric passed*. Stage 3 **scientific validation remains incomplete**.

## Next stage

Use **these reproducible warmup procedures**, not just their hashes, to initialize new matched-budget sampling chains; run sufficiently long independent trajectories, track high-dimensional movement and ESS/R-hat on both model conditions, and compare sensitivity to different warmup budgets. Crucially audit or correct the Markov transition kernel's stationary law and geographic/legal realism before stating a probabilistic outlier finding. The original `main` branch remains unchanged.

### Code and verification

- Exact distance and warmup: `src/redistricting/ensemble/start_diversity.py`
- CLI and independent endpoint verification: `scripts/research_audit/diversified_start_pilot.py`
- 32 CI synthetic tests: https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734817
- Successful real Michigan run, with separate reports and artifacts per geographic condition: https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734877
