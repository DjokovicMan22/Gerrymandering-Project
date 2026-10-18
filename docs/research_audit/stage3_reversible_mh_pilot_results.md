# Stage 3 reversible-boundary-MH empirical feasibility: Michigan

**Executed:** October 18, 2026.  
**Authoritative workflow (four independent jobs, all successful):** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39172395140  
**Proof, assumptions and exact proposal formulas:** [stage3_reversible_kernel_method.md](stage3_reversible_kernel_method.md)  
**Research disposition:** operational and detailed-balance tests **PASS**; practical stationary sampling, legal geography, and enactment-tail inferences **NOT CERTIFIED**.

## Research motivation

Prior ReCom simulations on the same Michigan precinct dataset reported high convergence statistics and very low ESS; their implemented transition distribution and its intended stationary target were not validated. Merely lengthening an uncharacterized chain cannot fix this. We introduced a distinct proposal family whose Metropolis–Hastings probabilities can be determined *exactly*, and then measured whether this mathematically interpretable alternative moves enough to be practically useful.

### The new stationary-law claim (narrow and exact)

Within each connected communicating component of the explicitly proxy-constrained **labeled** district-assignment space, the local edge-based MH transition kernel satisfies detailed balance relative to the **uniform distribution on that component**. This does **not** establish irreducibility across the full feasible set, convergence in a finite number of steps, uniformity among *unlabeled* plans, an accepted legal-map distribution, political significance or Michigan constitutional compliance. The source graph includes five unverified artificial bridges; split counties and MCD groupings are proxies; VRA and communities of interest are not enforced.

The kernel chooses uniformly among boundary edges, uses a fixed 50/50 mixture of oriented one-node flips and adjacent two-node district-label swaps, and accepts valid changes with the correct forward/reverse proposal-probability ratio. **Every rejected candidate is a recorded holding self-loop**. This removes the unknown ReCom proposal-law issue for this specific, separately defined model.

### Test strategy

- Exhaustive small-graph check: enumerate the feasible two-district labeled assignments on a six-precinct cycle, independently count all oriented boundary-edge proposals, and confirm `q(x,y)alpha(x,y)=q(y,x)alpha(y,x)` for every valid pair. Test deterministic seeded trajectories and rejection counters.
- Real graph: exact publicly pinned Michigan input with 4,756 nodes, 13 labels, expected statewide population and SHA. All four runs start from **distinct, independently seeded, hash-verified** warmup assignments under the specified geographic regime. They use separate MH sampling seeds.
- Each simulation records **2,001 states, 2,000 attempted MH moves**, saves a full assignment every 100 states, and checks **21 full maps** independently for assignment coverage, augmented-graph contiguity, ±0.5% population deviation, county/MCD grouping proxy limits, and presidential-vote scoring metrics. **84 archived full assignments** verified across four chains, with original per-chain score CSVs reconciled.
- The two geographic conditions are intentionally exploratory, **not formal Michigan legal constraints**:
  - **Closer:** maximum 760 cut edges, 18 split county source groups and 20 split county+MCD source groups.
  - **Relaxed:** maxima 850, 24 and 49.

## Actual numeric results

| Geographic regime | Warm seed | MH seed | Attempted | Accepted | Acceptance rate | Accepted flips | Accepted swaps | Population rejections | Contiguity rejections | Geography rejections | MH correction rejections | Fraction of precincts changed versus warm start at final state |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Closer | 101 | 7101 | 2,000 | **184** | **9.20%** | 140 | 44 | 635 | 602 | 547 | 32 | **1.787%** |
| Closer | 202 | 7202 | 2,000 | **185** | **9.25%** | 128 | 57 | 729 | 542 | 512 | 32 | **1.745%** |
| Relaxed | 101 | 7101 | 2,000 | **307** | **15.35%** | 188 | 119 | 709 | 540 | 385 | 59 | **3.659%** |
| Relaxed | 202 | 7202 | 2,000 | **319** | **15.95%** | 212 | 107 | 682 | 509 | 437 | 53 | **3.343%** |

All rejection and acceptance categories sum to precisely **2,000 attempted transitions per chain**. Total **8,000 attempted** transitions and **995 accepted** (12.44% overall); each sampled state was counted irrespective of acceptance.

The independent snapshot validator passed **21/21 maps** in each job and reconciled archived efficiency gap, Democratic seats, graph cut edges, split county groups, split county+MCD groups and maximum population deviation against the original chain CSV.

## Interpretation

This is the first sampler in the research branch whose **specified transition operator has a mathematically demonstrable uniform stationary law on each reachable feasible labeled-map component**, rather than relying on ReCom's uncharacterized selection probabilities. It produces nonzero valid movement on real Michigan precinct data, but **moving ~1.7–3.7% of precincts after 2,000 proposals is far too limited to justify a claim of broad spatial exploration or convergence**. The strict case accepts fewer than one in ten attempted moves; the relaxed case accepts about one in six.

We have **not** computed reliable R-hat/ESS from this four-job two-seed pilot, nor should it be described as stationary. The uniform feasible labeled-map distribution is a **methodological target choice**, not a legal doctrine or the asserted neutral comparison population. Local flips/swaps may be unable to connect all feasible maps (unknown irreducibility), and any hard geographic cap introduces important selection effects. The accepted counterfactual presidential-vote layer must not be confused with a real congressional election under the enacted lines.

## Next research priority

One must distinguish two separate remaining failures:

1. **Statistical accessibility/mixing:** The uniform-on-component claim is a stationarity statement, **not evidence that the component was sampled adequately**. Use longer independent seeded chains with ESS/R-hat, autocorrelation and exact spatial checkpoint comparisons. Consider more efficient *provably reversible* compound moves if simple local flips/swaps barely traverse geography.
2. **Substantive feasibility:** The geography/source grouping proxies, artificial island connections, Michigan constitutional priorities and VRA requirements remain independently unverified. A uniform distribution over the accessible proxy-maps need not resemble a uniform distribution over legally permissible map configurations.

There is still **no publication-ready gerrymandering significance claim**. This work completes a distinct, auditable transition-kernel research component while leaving Stage 3 scientific validation open.

**Provenance:** `src/redistricting/ensemble/reversible.py`, `scripts/research_audit/run_reversible_pilot.py`, `tests/test_reversible_kernel.py`, and `.github/workflows/stage3-reversible-pilot.yml`. The original `main` branch remains unchanged.
