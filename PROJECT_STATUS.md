# Project status

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
