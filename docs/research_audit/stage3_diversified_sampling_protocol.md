# Stage 3 preregistration — sampling chains from explicitly seeded, verified diversified maps

**Branch:** `research/stages-1-3-validation`. **Status at authoring:** software implemented; production run not yet claimed to pass.  
**Important erratum:** [GerryChain 1.0 RNG reproducibility correction](stage3_rng_reproducibility_erratum.md). The previous seed labels were not sufficient to reproduce their trajectories; all experiments below use the explicitly seeded chain-owned RNG.

## Main question

When chains are initialized at *measurably different*, reproducibly generated maps that satisfy exploratory geographic constraints, do their scalar/structural diagnostics exhibit credible agreement or continued nonconvergence? We do not hypothesize that the legally valid Michigan plan space has been identified, nor that default ReCom samples uniformly.

## Fixed design before executing the production workflow

- Input: the same public Michigan 2020 precinct-vote layer and 13-district 2021 reference, graph with 4,756 nodes, pinned upstream Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`, and five **not independently verified** artificial island connections.
- Two exploratory geographic constraints: **closer** (max 760 cut edges, 18 split county source groups and 20 split county+MCD source groups); **relaxed** (850, 24, 49).
- Population balance: max fractional deviation **0.005** (±0.5%).
- Independently seeded warmup paths: `101, 202, 303, 404`, **800 states including enacted start** each. Run the warmups independently with `MarkovChain(rng=warm_seed)` and check the exact endpoint hash against the corrected, explicitly seeded diversity pilot. Refuse mismatching hash, missing node, invalid population or source-group split counts.
- New sampling RNG seeds, separate from warmups: `1101, 1202, 1303, 1404`. Build the sampling Partition from **the actual warmup assignment**, not from the graph's enacted CD node attribute. Pin `gerrychain==1.0.0`; fix `PYTHONHASHSEED=0`; store the dependency freeze.
- Four chains per geographic condition (eight total), each exactly **4,001 recorded states including its *warmed* step 0** and **4,000 subsequent transitions**. Total production sample states = **32,008**. The initial warmup states are not pooled into the sampling statistics.
- Discard sampling steps 0–999 as diagnostic burn-in. Four *correlated* sample series per condition each retain 3,001 rows (12,004 per condition). The four chains per condition must have distinct warmup hashes and different sample seeds. Compare source SHA, source graph, constraints and sample budgets before pooling.
- Save all full precinct assignments at sampling steps 0,50,...,4000 (81 per chain, **648 independently checkable full assignments** overall). Independently recompute populations, augmented-graph contiguity, source-group cuts, 2020 election scores and graph boundary cuts from every saved map. Verify the archived sampling plan-metric CSVs match those independently recalculated values.
- Compute **five label-invariant spatial probes per chain**, at steps 0,1000,2000,3000,4000: exact precinct disagreement (after optimizing district-label matching) both from the enacted reference and the chain's warmed start. Record candidate assignment hashes; **do not redistribute full third-party precinct assignment data** via CI artifacts.
- Independently calculate the enacted reference score JSON on every worker. The enacted map is **not step 0 of the sampling chains**. Aggregation must check all reference JSON files match and use these values for reported baseline percentiles/tail frequencies. A chain's warmed step 0 is *never* used as the enacted reference.
- Summaries: Democratic seats under 2020 counterfactual precinct presidential votes, pipeline efficiency gap, median-minus-mean, cut edges, population deviation, sampled-state change fraction, geographic rejection fraction, chain endpoint spatial separation and split groups.
- Scalar gates are conservative **rank R-hat <= 1.01, bulk ESS >= 400, tail ESS >= 400** per metric in each geographic condition. Violations must result in `NOT CERTIFIED`, even if software execution passes. Examine spatial movement separately: scalar convergence is not sufficient evidence of high-dimensional mixing.

## Outlier inference restrictions

The proposed Markov kernel is not established as uniform over legal maps (or reversible with a well-defined intended target). Geographic hard caps are researcher-chosen proxies rather than audited Michigan legal priorities. There is no credible conclusion about gerrymandering intent, legal validity or a tail-event probability. **Raw fraction with EG >= enacted reference** may be described as conditional historical frequency only, not an independent-observation p-value.

The eight separate random paths begin at the same enacted ancestor **before warmup**. Having different assignments at the sampling start proves diversification, not independence from stationarity. The previous 64,000-state unseeded/retry-kernel histories must never be silently pooled with these chain-owned-RNG holding-kernel experiments.

**Advance Stage 3 only after:** seeded replay and provenance pass; all eight sampling chains independently validated; four-chain diagnostics and spatial movement quantified; physically defensible geography/legal constraints and the Markov stationary target investigated further.
