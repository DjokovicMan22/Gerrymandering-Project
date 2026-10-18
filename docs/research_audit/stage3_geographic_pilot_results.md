# Stage 3 geographic-constraint pilot — executed and independently validated

> **REPRODUCIBILITY ERRATUM — October 18, 2026:** The historical runs described below used GerryChain 1.0.0 without explicitly passing `rng=seed` to `MarkovChain`. Their seed labels therefore **do not reproduce exact trajectories**. The archived generated maps and scalar results remain descriptive observations but should **not** be characterized as exactly seeded/replayable. See [Stage 3 RNG reproducibility erratum](stage3_rng_reproducibility_erratum.md) and the subsequently re-executed, seeded studies.\n\n
**Executed:** 18 October 2026  
**Development branch:** `research/stages-1-3-validation`  
**Authoritative holding-kernel run:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39123162067  
**Four jobs:** **ALL PASSED**. **Status:** exploratory sensitivity investigation, **NOT CONVERGED**, not a legally valid plan ensemble.

## Scientific question and input

Can constraints on graph boundary cuts, county splits, and county+MCD source groups reduce the structural mismatch identified in the 64,000-state baseline? We test two deliberately exploratory sets of hard proxy caps, keeping the same pinned 4,756-node Michigan source graph, source 13-district 2021-adopted reference, ±0.5% population tolerance, 2020 counterfactual presidential scoring layer, and five **unverified** artificial connectivity bridges.

The enacted reference has **681 cut edges**, **14 split COUNTYFIPS groups**, **9 split (COUNTYFIPS, MCDFIPS) groups**, and scores **7 Democratic seats** under fixed 2020 two-party presidential allocations.

**Model conditions:**

| Condition | Max cut edges | Max split counties | Max split county+MCD groups |
|---|---:|---:|---:|
| Closer geographic proxies | 760 | 18 | 20 |
| Relaxed geographic proxies | 850 | 24 | 49 |

Neither condition includes all legal requirements. County+MCD keys are processed source labels, not independently validated municipal polygons. There is no VRA opportunity-district rule, communities-of-interest model, county nesting priority, compactness geometry guarantee, or water/island physical contiguity certification.

## Crucial Markov kernel distinction

The first pilot iteration (`39122790378`, source code before the holding-kernel fix) used GerryChain's built-in constraint retry semantics, which **skipped** invalid proposed states. Four jobs ultimately finished, but the resulting valid-transition-indexed histories must **not** be pooled with this experiment.

The authoritative experiment (`39123162067`) instead wraps the ReCom proposal in `GeographicHoldingProposal`. It draws **one** candidate per proposed transition. If that candidate violates a geographic cap, it retains the previous plan and records the geographic rejection. Its built-in population and contiguity guards remain present. Thus 600 recorded states per chain (including step 0) correspond to **599 geographic proposal attempts**, modulo separately enforced built-in conditions. This proposal kernel is different from the earlier conditional-retry kernel; its stationary law has not been established.

## Executed holding-kernel pilot results

All four jobs recorded **600 states** each, dropped the first **100** for descriptive means (500 retained highly dependent states per chain), and saved one full assignment every 10 steps. **All 240 archived full assignments** passed independent node-set, population, augmented-graph contiguity, geographic-cap, seat-score, efficiency-gap, and cut-edge checks. These checks do not validate physically legitimate island bridges or all unarchived states.

| Condition | Seed | Mean D seats | Mean EG | Mean cut edges | Mean split counties | Mean split county+MCD | Geographic proposals rejected | Fraction of recorded steps changing assignment |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Closer | 101 | 8.000 | +0.081884 | 686.358 | 17.642 | 19.726 | 427/599 (71.3%) | 24.8% |
| Closer | 202 | 6.956 | −0.002297 | 742.314 | 17.830 | 19.760 | 499/599 (83.3%) | 15.8% |
| Relaxed | 101 | 6.230 | −0.061500 | 807.124 | 23.620 | 48.272 | 315/599 (52.6%) | 44.2% |
| Relaxed | 202 | 6.520 | −0.036227 | 793.124 | 23.648 | 48.168 | 322/599 (53.8%) | 40.6% |

Here EG is the project's floor-half-plus-one wasted-vote convention, `(Republican wasted − Democratic wasted) / two-party votes`. A positive score corresponds to a relative Democratic advantage. **None of these means is presented as a converged distribution expectation or p-value.**

The county and MCD limits are nearly saturated in every condition, remaining above the reference counts of 14 and 9. These model ensembles are *closer* on graph cut edges than the baseline (~916–919) but **are not equivalent** in geography. Particularly in the closer condition, the two seeds disagree substantially in mean D seats and efficiency gap. The large fraction of self-loops, tiny number of independent starts, and short run length invalidate an inference of stationary mixing. Both chains began from the exact same reference assignment.

### Verification and provenance

- Source: immutable Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`; exact source graph checked per job.
- Executable: `src/redistricting/ensemble/geographic.py`, `chain.py`, `constraints.py`, `scripts/run_baseline.py`.
- GitHub workflow: `.github/workflows/stage3-geographic-pilot.yml`.
- Saved plan snapshots independently rescored by `scripts/research_audit/verify_snapshots.py`; score reconciliation checked by `metric_reconciliation.py`.
- Regression coverage includes actual RustworkX-backed GerryChain partitions, county/MCD group definition, strict missing-field failure, self-loop rejection, and accepted proposals.
- Four CI artifacts named `stage3-geographic-{closer,relaxed}-{101,202}` contain derived summaries, metadata, and reconciled snapshots (not original third-party precinct graph bytes).
- No independent physical geography, original election allocation, Markov stationary distribution, or legal-plan validity audit is claimed.

## Implications for next research work

1. **Do not infer gerrymandering intent, illegality or tail probability** from this preliminary, constraint-conditional pilot.
2. Audit the five artificial bridges against authoritative water/island geography; a purely numerical node connection is not a topological certification.
3. Develop a geographically credible, externally justified constraint hierarchy rather than selecting numerical caps solely to resemble the enacted plan; otherwise there is reference-map selection bias.
4. Generate genuinely dispersed permissible initial maps and use sufficiently long runs with rejection rates and independently assessed autocorrelation/mixing; expect strict caps to impede movement.
5. Confirm split-count categories against official county and municipal GIS geometries, including ambiguous or missing MCD codes, and add explicit legal requirements only after verifying authoritative data.
6. Compare sensitivity across multiple plausible *independently justified* legal/geographic conditions. The existing pilot demonstrates feasibility of auditable hard constraints, not that a publication-ready comparison ensemble has been generated.

**Conclusion:** The new geographically constrained model runs on verified source data with valid snapshot checks, but the strict model's 71–83% proposal rejection and strong inter-chain differences reinforce the need for better proposal design, dispersed starting plans, and independent geographic evidence before Stage 3 can be scientifically closed.
