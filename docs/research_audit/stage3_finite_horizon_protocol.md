# Stage 3 methodological reset: precisely defined finite-horizon perturbation benchmark

**Recorded before interpreting the 64-endpoint results (18 October 2026).**
**Implementation:** `scripts/research_audit/finite_horizon_endpoints.py` and `analyze_finite_horizon.py`.
**Production workflow:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39179579464

## Why the original scientific Stage 3 could not pass

The historic ReCom models changed plan geography using five district-label-selected artificial edges, many tens to hundreds of kilometers apart, with no physical geometry validation. Enacted-anchored geographically capped samples also failed prespecified rank R-hat and effective-sample-size tests even after 32,008 serially correlated observations. A separately constructed local reversible Metropolis–Hastings sampler established conditional detailed balance but mixed worse. GerryChain 1.0 ReCom variant R, which targets a known spanning-tree-weighted law, produced **zero state changes in 200 proposed steps in each of two pilot conditions** using the strict constraints. That is an empirical bottleneck, not a solution.

We **withdraw any assertion that these histories are a converged statewide null ensemble or imply a statistically significant Michigan gerrymander.** Do not claim legal neutrality, uniformly sampled plans, gerrymandering intent or a statewide p-value.

## Repaired and independently examined graph topology

The original 4,756-precinct source graph (`mi.json` pinned Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`) and separately distributed original precinct polygon ZIP (`mi.zip` pinned Git blob `07bce18dabbcca9d549e28995a8156fd6978d7db`) were checked byte-for-byte and paired by 100% agreement of population, enacted congressional district and county attributes at each of 4,756 node indices.

The five historical artificial edges were between polygons approximately 42, 117, 134, 170 and 280 kilometers apart. A district-blind minimum-spanning-tree repair totaling just 19.6 km also **failed** the 13-district enacted baseline: four precincts of District 6 were isolated. We did not fix this by selecting edges with the enacted district label.

Instead we tested K=1,3,10,25,50 nearest external precinct polygons **per original disconnected component**, using no district labels or election results in selecting edges. K=1 did not preserve full statewide/reference connectivity; K=3 first made the graph and all 13 enacted districts connected with **13 new spatial-neighbor edges** (max polygon separation **17,768 m**). K larger created successively more artificial edges and arbitrary potential contiguity. K=3 is therefore a **researcher-selected sensitivity modeling convention after examining baseline connectivity**; it is not an independently identified legal or physical island rule.

This source-matched spatial proxy is **NOT legally certified**; polygon distance does not prove water crossing, access, island-county contiguity, VRA compliance, compactness, communities of interest, or Michigan redistricting eligibility. The KNN3 baseline cut-edge statistic is **682** versus 681 in the original 12,378-edge graph; comparators must never interchange these cut-edge definitions. All geometry-bearing input remains third-party, CC BY-NC and Redistricting Data Hub terms; we do not redistribute it in CI artifacts.

## New estimand: finite-horizon, independently seeded changes to the enacted map

We define two finite-time **algorithmic perturbation distributions**, not stationary distributions of legally valid maps.

A run begins at the **same enacted reference**, with the **same KNN3 model graph**, population tolerance ±0.5%, and a GerryChain v1.0.0 ordinary ReCom proposal seeded through its **chain-owned RNG** (`rng=seed`, not just global `random.seed`). It records **801 states including step zero** and retains ONLY the single final assignment from step 800. Invalid exploratory geographic-constraint proposals follow the recorded legacy holding/constraint handling: the number of underlying proposal calls, including hidden retries when applicable, is saved per replicate. This finite 801-recorded-state law is therefore fully specified by implementation, code version, and random seed—not assumed to equal a stationary legal-plan distribution.

Geography treatment:
- **Closer condition:** max 760 model-graph boundary cuts, max 18 split source county groups and 20 split county+MCD groups.
- **Relaxed condition:** corresponding caps 850, 24, and 49.

Both are **exploratory researcher-selected caps**, not the state's legal admissibility rules. No VRA/COI/official municipality compliance claim is permissible.

**Independent replicate design:** 32 separately seeded complete trajectories per condition; RNG seeds 10001–10032 reused as paired *experiment labels* in the two conditions. Every replicate reconstructs the same geographic input and reference plan, then executes its own seeded Markov history. We do **not** pool the 801 correlated intermediate states; the only unit counted for an uncertainty estimate is the **single terminal map from each independently seeded run**. A second-process exact replay of seed 10001 is required in each condition.

**Validation:** For all 64 final assignments, independently recompute all 4,756 node assignments, augmented-graph district contiguity, population deviation, 2020 counterfactual Democratic seats, efficiency gap, split county and county+MCD counts and model-graph boundary cuts. Refuse any mismatch with the simulation's terminal metrics. Verify source hashes, derived model-graph SHA, all seed IDs, actual step budget and all cap limits. Never upload third-party full precinct assignment maps; only source hashes and derived endpoint metrics.

## Predefined uncertainty reporting

For each condition calculate means and standard deviations of Democratic seats, efficiency gap, boundary-cut edges, split groups and exact label-invariant precinct disagreement from the enacted reference. Report percentile bootstrap **95% Monte Carlo intervals for the finite-horizon algorithm-specific mean**, using a deterministic resampling seed and 10,000 bootstrap replicates. Also report a Wilson **95% binomial interval** for the fraction of terminal simulated efficiency gaps at or above the enacted reference. These intervals quantify Monte Carlo variation *conditional on the chosen finite-time procedure*, subject to approximate independence of separately seeded streams.

Neither endpoint fraction nor its Wilson interval is a statistical p-value of the enacted map. The enacted reference is the common algorithmic starting state; the null distribution is explicitly reference-conditioned and chosen post-hoc based on methodological investigations. The result cannot directly measure whether Michigan's enacted map is a partisan outlier among neutral/legal maps.

## Exit criteria

The **software and narrowly defined finite-horizon experiment** can be certified complete only if all eight cohorts finish; all 64 independently scored endpoints and both seed-10001 replays match; no ungrounded claims of stationarity, neutral legal maps or partisan significance are made; uncertainty is correctly labeled **conditional Monte Carlo uncertainty**; graph model and limits are explicitly disclosed.

Even if those gates pass, **Stage 3 original statewide neutral-ensemble scientific claim remains rejected**. Stage 4 may use the new bounded algorithmic perturbation results for a *methodological sensitivity and robustness paper*, but may not present them as a corrected proof of gerrymandering or a converged neutral map ensemble.
