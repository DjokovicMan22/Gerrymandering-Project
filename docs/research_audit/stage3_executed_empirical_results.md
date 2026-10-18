# Stage 3 completed execution: Michigan ReCom matched-budget experiment

**Executed:** October 18, 2026  
**Production run:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39120743275  
**Successful independent aggregation:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39121398554  
**Disposition:** **64,000 recorded model states executed and 6,400 saved full assignments verified. BOTH CONDITIONS FAIL PREDECLARED SCALAR CONVERGENCE GATES. NOT PUBLICATION-READY.**

## Input and modeling assumptions

Processed Michigan public source Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a` (4,756 graph nodes; 13 reference congressional districts, 10,077,331 people), downloaded with exact-byte hash gate. Sampling uses the project's GerryChain ReCom proposal, starting from the same 2021-adopted reference map for every chain, with deterministic artificial island bridges. Those bridges have not been independently verified as geographic contiguity.

The fixed scoring layer is 2020 precinct-allocated presidential two-party votes, not an actual congressional election under these districts. No VRA, community-of-interest, county-split, municipal-split or full state constitutional constraint set is enforced.

## Actual execution and independent checks

Eight successfully completed CI chain jobs: four seeds (101, 202, 303, 404) at each of two population deviations (±0.5%, ±2%). Each job recorded 8,000 chain states inclusive of the reference step 0, and independently verified 800 saved full assignment snapshots (every 10th state). The complete execution produced 64,000 plan-metric rows and 6,400 validated full snapshots. Each observed population was recalculated on the same augmented graph; saved seat scores, efficiency gaps, cut edges, and maximum population deviations matched independent rescoring. These checks are for the *saved snapshots*; unarchived intermediate assignments are not independently rescored.

Each condition has four post-burn-in chains of 6,000 **serially dependent** metric states (24,000 per condition); 2,000 initial states per chain were discarded for diagnostics. Real inputs are not redistributed; derived CSV diagnostics and metadata are accessible as GitHub Actions artifacts.

## Completed diagnostics

The baseline reference scores **7 Democratic seats** under the 2020 presidential two-party vote layer, and the pipeline's floor-half-plus-one winning-threshold efficiency gap **+0.003333** (positive means relative Democratic advantage). The graph reference has **681 cut edges**.

| Metric | Reference | ±0.5% pooled mean | ±0.5% R-hat | ±0.5% bulk ESS | ±2% pooled mean | ±2% R-hat | ±2% bulk ESS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Democratic seats | 7 | 5.679792 | 1.008784 | 284.57 | 5.777292 | 1.009747 | 338.42 |
| Efficiency gap | +0.003333 | -0.102155 | 1.010327 | 275.90 | -0.095080 | 1.009743 | 364.08 |
| Median minus mean district vote share | -0.014020 | -0.030330 | 1.006926 | 345.07 | -0.029347 | 1.008440 | 330.17 |
| Graph cut edges | 681 | 919.378583 | 1.008178 | 277.57 | 915.716708 | 1.027196 | 235.09 |
| Maximum population deviation | 0.004019 | 0.004609 | 1.005223 | 1606.43 | 0.018649 | 1.003885 | 1789.05 |

The efficiency-gap reference score is at approximately the 95.06th sample midrank percentile under ±0.5% and 93.58th under ±2%. The raw fractions of scored observations with gap >= reference are respectively 0.049417 and 0.064208. **These fractions are not converged posterior probabilities, uniformly sampled map probabilities, or valid independent-observation p-values.** All 24,000 recorded states per condition met their specified population deviation; this is a metric audit and is not an independent per-step full assignment check.

The predeclared diagnostic requirements are rank R-hat <= 1.01 and bulk/tail effective sample size >= 400 for every tracked metric. Both conditions **fail**: gap bulk ESS is 276 at ±0.5% and 364 at ±2%; Democratic-seat ESS 285 and 338; cut-edge ESS 278 and 235. Additionally, efficiency-gap R-hat is 1.010327 under ±0.5%, and cut-edge R-hat is 1.027196 under ±2%. Even passing these scalar metrics would not prove adequate high-dimensional mixing.

## Central substantive limitation: comparison maps are too fragmented

The reference has 681 graph cut edges, whereas both produced ensembles average **approximately 916–919**. None of the 24,000 recorded states in either condition had a cut-edge statistic at or below the reference, so the comparison set is strongly mismatched to the reference map in this structural proxy. Without binding county/municipality splits and realistic additional geographic/legal restrictions, a purported partisan-outlier conclusion from these samples would overstate the validity of the baseline.

**Do not claim:** proof of gerrymandering, partisan intent, map illegality, valid legal-map sampling, reliable probabilities of observing an enacted map, convergence, stationarity, or a uniformly sampled set of maps.

## Required next scientific stage

1. Establish physically justifiable island/water adjacency and document verified geography.
2. Add constraint-matched comparisons for municipal and county splits and other relevant ranked legal criteria; document omissions (including VRA and communities of interest) explicitly.
3. Initialize independent chains from genuinely separated valid starting assignments, not only varying the seed from the same enacted map.
4. Extend/replicate runs and demonstrate stable ESS/R-hat, reproducible conditional tail behavior and autocorrelation diagnostics; inspect high-dimensional map-mixing proxies.
5. Add sensitivity to alternative sampling proposals and uncertainty bounds for correlated observations.
6. Reassess outlier claims only after both statistical and geographic comparability checks.

The original `main` branch was not modified. This report documents an **executed but scientifically uncertified** baseline extension, not a completed final Stage 3 claim.
