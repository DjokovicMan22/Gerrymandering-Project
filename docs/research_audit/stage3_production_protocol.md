# Stage 3 production reproduction protocol (October 18, 2026)

**Branch:** `research/stages-1-3-validation`. **Production-launch commit:** `63b575a4b5fde2836b0110236bda1a794c94232b`. The original `main` branch is unchanged.

## Experimental setup

- Graph: `eveomett-states/Michigan/mi.json`, pinned Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`, expected 4,756 precinct nodes and population 10,077,331. Record SHA-256 independently at download.
- Model: project GerryChain ReCom proposal and contiguous-district/population constraints, using five **artificial, not geographically certified** bridge edges. Each chain begins from the same 2021-adopted reference assignment. Distinct random seeds **do not imply dispersed initializations**.
- Scoring: 2020 two-party *presidential* precinct vote allocations mapped onto the adopted 2021 13-district reference; this is a counterfactual geographic calculation, **not an election under those boundaries**.
- Population-tolerance conditions: 0.005 (±0.5%) and 0.02 (±2%).
- Matched seeds per condition: 101, 202, 303, 404.
- Recorded states per chain: 8,000, including initial state at index 0. Diagnostic burn-in excludes steps 0–1,999. Retained *serially correlated* metric states per chain: 6,000; 24,000 per tolerance; 48,000 total across both conditions.
- Saved full assignments: every tenth step (0,10,...,7990), 800 per chain. Validate every saved assignment's node set, contiguity **on the augmented graph**, population deviation, cut edges, 2020 Democratic seats, and exact pipeline efficiency gap against archived CSV. Do not claim that unarchived intermediate assignments were independently checked.
- Independent chains are run in separate GitHub Actions jobs; source provenance, raw-source hash, Python dependency freeze, chain metadata, validation CSV, and scalar plan metrics are published as **derived artifacts**. Raw third-party precinct graph and full precinct assignments are not republished.

## Automatic gates

1. Exact source Git blob, expected node count and statewide population must match.
2. Each run must finish without an exception.
3. Every archived assignment must pass structural and population checks, with calculated 2020 election scores matching the saved chain history.
4. Cross-chain summaries must be computed only from four matched-budget chains per population condition.
5. Scalar diagnostics record rank/split R-hat, bulk ESS, and tail ESS for Democratic seats, efficiency gap, mean–median, graph cut edges, and population deviations. Conservative nominal threshold: R-hat <=1.01, bulk ESS >=400, tail ESS >=400. **Passing is necessary diagnostic evidence, never proof of mixing**.

## Important boundaries

The standard model does **not** enforce the full Michigan constitutional redistricting ranking; it lacks explicit county/township/community-of-interest/Voting Rights Act constraints, has artificial adjacency bridges, and its proposal distribution is not established to sample legal plans uniformly. Accept/reject frequencies and apparent outlier ranks are conditional exploratory model descriptions—not legal determinations, causal claims, uniform-map probabilities, intent tests, or verified p-values. The sample design begins all chains at the reference plan; cross-chain similarity may be misleading even if R-hat approaches 1.

## Results and status

The production job is **launched, not yet scientifically certified**. Read the actual GitHub Actions run and derived artifacts for outcomes; this protocol must not be used as evidence that 64,000 states completed or any convergence gate passed. The shorter real-data smoke experiment successfully reconciled 14 independently validated saved full assignments across two 35-state chains, but strongly failed R-hat/ESS criteria and was not used for statistical inference.

**Reproduce workflow:** `.github/workflows/stage3-production.yml`; **validation tools:** `scripts/research_audit/verify_graph.py`, `verify_snapshots.py`, `metric_reconciliation.py`, `analyze_chains.py`.

Future research prerequisites: independent dispersed initializations, longer/multiscale runs, proposal acceptance and autocorrelation studies, geographically plausible comparison constraints, and an explicit analysis of prior-geometry and island-bridge sensitivity.
