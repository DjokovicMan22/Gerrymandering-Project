# Project status

## Stage 4 — The Phantom Baseline, successfully compiled and visually inspected

- [x] **Rewritten manuscript**: [The Phantom Baseline: Geographic Assumptions, Mixing Failures, and Constraint Sensitivity in Computational Redistricting](outputs/reports/stage4/when_a_random_map_is_not_a_neutral_map.md). The argument is a **three-axis forensic diagnostic** with executable reliability gates, not an original-project bug diary.
- [x] **Authoritative reading PDF:** [16-page STIX/XeLaTeX PDF](outputs/reports/stage4/phantom_baseline.pdf). [Editable source](outputs/reports/stage4/phantom_baseline.tex).
- [x] **Four evidence-linked vector figures:** one exact-GIS reconstructed map of the five synthetic edges (measured 42.26–280.19 km), plus three graphics derived from the archived, individually validated 64-map experiment.
- [x] **Three journal-formatted `booktabs` tables**, four numbered display equations, searchable text, figure manifests, rendered page previews, and source/paper hashes.
- [x] **Signed 32-pair bootstrap stress test:** tighter-minus-relaxed efficiency gap **+0.03278**, paired 95% interval **[+0.00975, +0.05631]**. Relaxed caps *decrease* mean Democratic seats by **0.406** and increase precinct reassignment by **15.61 percentage points**.
- [x] **All latest checks successful:** [journal PDF workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39359458520), [research audit](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39359458615), and [Michigan empirical smoke test](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39359458586).
- [ ] **External methodological peer review** and target-journal style submission. Geographic/statistical legality of an enacted-map neutral outlier test has not been established, nor was a second-state replication performed.

Only the `research/stages-1-3-validation` development branch was modified. Original `main` remains unchanged.

## Stage 3 final decision — CLOSED, SCOPED RESEARCH RESULT

- [x] Source-pinned Michigan graph and original precinct polygon ZIP aligned for all 4,756 nodes.
- [x] Reject original 5 district-conditioned artificial bridges after independently measuring distances of ~42–280 km.
- [x] Propose district-blind source-polygon KNN3 proximity graph; independently confirm enacted plan remains connected (13 synthetic edges). **Model geography remains exploratory, NOT legally certified.**
- [x] Explicitly seed GerryChain 1.0 RNGs, verify replay and independently rescore saved maps.
- [x] Test both ReCom and reversible local MH multi-chain performance; document formal R-hat/ESS **FAILURES**.
- [x] Execute 64 separate, independently validated 801-state runs, using **one endpoint per seed** across two geographic-cap regimes; all 64 accepted in reproducible finite-horizon model.
- [x] Quantify algorithm-conditional Monte Carlo means/uncertainty; forbid neutral-legal-map p-value interpretation.
- [x] Publish a final Stage 3 evidence report with explicit positive, negative and unresolved claims: [STAGE3_FINAL_REPORT.md](docs/research_audit/STAGE3_FINAL_REPORT.md).
- [ ] **NOT PASSED:** adequate stationary mixing on a validated legal-plan state space; Michigan official contiguity, water/islands, VRA and communities-of-interest validation. This stronger research question is **closed as unsupported**, not quietly declared successful.

**Stage 4 can begin as a bounded methodology and sensitivity manuscript based on the finished finite-horizon result. It cannot represent Stage 3 as proof of Michigan gerrymandering.** Prior week-based checklist below is a historical activity ledger, not the current Stage 3 exit gate.


## Week 1 — Data and graph

- [x] Load Michigan and Missouri precinct shapefiles
- [x] Plot precinct two-party vote share
- [x] Build and visualize dual graphs
- [x] Plot enacted districts
- [x] Produce descriptive vote–seat summaries
- [x] Validate enacted district populations and contiguity
- [x] Enumerate equal-size contiguous 4×4 grid splits by code
- [ ] Independently verify the 4×4 result by hand or a second method
- [x] Document state selection and adjacency conventions
- [ ] Add final source URLs and retrieval dates to data provenance

## Week 2 — Compactness

- [x] Implement Polsby–Popper
- [x] Implement Reock
- [x] Implement convex-hull ratio
- [x] Create district galleries and synthetic stress tests
- [x] Add boundary-resolution sensitivity experiment
- [x] Write isoperimetric explanation and projection limitations
- [ ] Cross-check selected district values against an independent tool
- [ ] Add formal citations to the final paper bibliography

## Week 3 — Partisan metrics

- [x] Implement exact wasted-vote efficiency gap
- [x] Implement equal-turnout shortcut
- [x] Implement mean–median difference
- [x] Implement seats–votes summaries
- [x] Compare 2016 and 2020 presidential elections
- [x] Create synthetic counterexamples
- [x] Write shortcut derivation and assumptions
- [x] Add unit tests for metric edge cases
- [ ] Cross-check selected results against an independent source
- [ ] Decide whether to add congressional-election data and document its limitations

## Weeks 4–7

- [ ] Build first valid Michigan ReCom chain
- [ ] Run and save a 1,000-step debugging chain
- [ ] Run at least 20,000 production samples
- [ ] Add trace plots and multi-chain diagnostics
- [ ] Produce enacted-map percentile and sorted-district plots
- [ ] Run robustness investigations
- [ ] Complete paper, repository cleanup, and talk
