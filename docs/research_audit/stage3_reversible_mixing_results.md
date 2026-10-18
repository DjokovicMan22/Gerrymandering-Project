# Stage 3 reversible-MH multi-chain convergence experiment — executed, failed

**Date:** 18 October 2026  
**Authoritative full experimental run:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39173401095  
**All eight production and independent snapshot-verification jobs:** operationally successful.  
**Cross-chain aggregation:** operationally successful.  
**Scientific status:** **FAIL — neither model passed scalar convergence tests.**

## Purpose

Assess whether a locally reversible, explicitly specified boundary-edge Metropolis–Hastings map sampler addresses the failed statistical mixing of the earlier custom ReCom chain. The new MH transition kernel has an analytically verified detailed-balance relationship with the uniform distribution **on each communicating component** of the *proxy-constrained labeled map state space*. That statement alone is not a finite-time convergence guarantee, does not establish irreducibility across the set, and does not justify treating these maps as legal Michigan congressional plans.

## Executed experiment

- Source: pinned public 4,756-node Michigan graph, upstream Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`.
- Two **exploratory** geographic-proxy regimes:
  - Closer: max 760 cut edges, 18 split `COUNTYFIPS` groups, 20 split `COUNTYFIPS+MCDFIPS` source groups.
  - Relaxed: 850, 24, 49.
- Population tolerance: ±0.5% per district.
- Four distinct starting maps per condition, reproduced exactly by 800-state GerryChain warmups with explicit independent chain RNG seeds 101,202,303,404 and SHA-256 endpoint gates. Eight independent MH sampling RNG seeds 7101,7202,7303,7404 (used once per condition).
- Eight MH chains × 4,001 states (including warmed step 0), giving **32,008 recorded correlated states** and 32,000 attempted transitions.
- Burn-in: 1,000 states per chain. **12,004** post-burn-in correlated observations per condition, four chains.
- Saved full maps at every 50th sampling state: **81 per chain, 648 total**. All independently passed node-set, contiguity **on the augmented graph**, population, geographic-proxy, efficiency-gap, seat-count and original-CSV score reconciliation checks.
- Five exact, relabel-invariant precinct-assignment-distance checkpoints per chain.
- Predeclared gates **R-hat <= 1.01**, bulk ESS >=400, tail ESS >=400 for **every scalar metric**.

## Cross-chain diagnostics — reproducible findings

| Scalar outcome | Enacted reference | Closer mean | Closer R-hat | Closer bulk ESS | Relaxed mean | Relaxed R-hat | Relaxed bulk ESS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Democratic seats under 2020 presidential-vote scoring | 7 | 7.3052 | **2.7773** | **4.68** | 6.7638 | **3.9532** | **4.30** |
| Efficiency gap (project convention) | +0.003333 | +0.02652 | **1.5681** | **7.11** | −0.01316 | **2.5881** | **4.75** |
| Median-minus-mean | −0.014020 | −0.014233 | **2.5118** | **4.87** | −0.013572 | **2.7226** | **4.70** |
| Graph boundary cut edges | 681 | 758.89 | **1.0213** | **337.47** | 848.65 | **1.0102** | **411.87** |
| Max population deviation | 0.004019 | 0.004653 | **1.0706** | **55.39** | 0.004633 | **1.0790** | **151.38** |

All ten model-by-metric scalar gates **FAIL**. Democratic-seat and efficiency-gap effective sample sizes are exceptionally low despite more than 12,000 recorded observations per condition. The apparent raw percentile of the enacted outcome **cannot** be interpreted as a valid inferential p-value.

### Geographic fragmentation tends to saturate the allowable caps

The closer ensemble averages **758.9 cut edges** against its cap of **760**; the relaxed ensemble averages **848.6** against its cap of **850**. The enacted reference has only **681**. This is evidence that the chosen *uniform-on-accessible-labeled-map* target itself tends to emphasize boundary-rich configurations under these proxy caps. Detailed balance is a formal property, not validation that such a target is geographically appropriate.

## Actual local-MH transition and spatial movement

| Condition | Warm seed | Sampling seed | Accepted of 4,000 | Acceptance rate | Final node disagreement from warmed start |
|---|---:|---:|---:|---:|---:|
| Closer | 101 | 7101 | 383 | 9.575% | 2.586% |
| Closer | 202 | 7202 | 328 | 8.200% | 2.208% |
| Closer | 303 | 7303 | 453 | 11.325% | 2.313% |
| Closer | 404 | 7404 | 350 | 8.750% | 2.418% |
| Relaxed | 101 | 7101 | 594 | 14.850% | 4.289% |
| Relaxed | 202 | 7202 | 565 | 14.125% | 4.205% |
| Relaxed | 303 | 7303 | 670 | 16.750% | 4.205% |
| Relaxed | 404 | 7404 | 577 | 14.425% | 3.574% |

Spatial checkpoint aggregation:
- **Closer:** final mean node disagreement from initial warm map ~**2.38%**, minimum ~2.21%. Four distinct assignment digests.
- **Relaxed:** final mean node disagreement ~**4.07%**, minimum ~3.57%. Four distinct digests.

Thus some actual map changes occur, but the local kernel moves too slowly across the geographically constrained state space. The checks only quantify within-chain distance from warmup/enacted reference, not contemporaneous pairwise inter-chain mixing.

**Scientific assessment:** The reversible local flip/swap proposal did **not** solve the original mixing problem. Additional transitions without a substantive proposal redesign or target justification cannot be assumed to fix it.

## Geographic source audit: a separate failure of the existing model's assumptions

Official Michigan constitutional criteria have ordered priorities including federal law and VRA, geographic contiguity with special island treatment, communities of interest, partisan fairness, candidate/incumbency treatment, county/city/township boundaries and reasonable compactness (Mich. Const. art. IV, §6(13): https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6). Official commission mapping data: https://www.michigan.gov/micrc/mapping-process/mapping-data.

The **separate, source-pinned bridge audit** in GitHub Actions https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39173742278 established that the raw input graph has **six disconnected connected components**, of sizes **4,521, 227, 4, 2, 1 and 1**. The current pipeline makes this connected with five *synthetically chosen* precinct edges between locations sharing an enacted district label.

**All five synthetic graph connections join precincts with different county FIPS labels.** The original components' same-county overlap graph is itself disconnected into two groups, so connecting every source component by same-county labels alone would not solve connectivity. **Different counties do NOT in themselves imply an illegal or invalid geographic connection**—legitimate land adjacency, bridges, or road connections may cross county lines. The precise failure is that no external geometric/water/island evidence was used to justify these five particular simulated edges. The algorithm's district-label match does not certify physical or statutory contiguity.

The source-attribute audit is **not a GIS validation**. Obtaining and reconciling authoritative county, township, island, shoreline and precinct polygons is still necessary before treating these augmented-graph outcomes as eligible geographic comparisons.

## Final Stage 3 readiness determination

**Validated successfully:** pinned source integrity, seeded computation, independent sample-map rescoring, small-graph detailed balance of a new kernel, reproducible diversified starts, and measured movement/rejection/convergence failures.

**Not validated:** fast/enough exploration, global chain irreducibility, an appropriate stationary target for substantive legal comparison, geographic contiguity of five synthetic bridge edges, full Michigan statutory/constitutional priority criteria, communities of interest, VRA opportunity requirements, and adequate outlier inference.

**Verdict:** **Stage 3 scientific validation remains FAILED/OPEN. Stage 4 should not be represented as built on validated statistical gerrymandering findings.** A future Stage 4 could proceed *only as explicitly exploratory work*, not based on a claim that Stage 3 has passed.

Next work should be bounded by an explicit exit gate:
1. Independently certify geography and island connectivity against official GIS and legal criteria, replacing arbitrary bridges.
2. Choose and justify an appropriate legal/geographic comparison target (not just a uniform distribution that saturates boundary caps).
3. Design more effective transitions with an auditable invariant distribution and test component accessibility.
4. Run several dispersed chains and require **every** prespecified R-hat/ESS metric and spatial-mixing checks to pass.
5. If any condition fails, publish a negative/limited-methods result rather than manufacturing partisan significance.

The original `main` branch remains unchanged.
