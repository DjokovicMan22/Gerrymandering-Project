# Stages 1–3: reproducible research-development branch

**Branch:** `research/stages-1-3-validation` (separate development branch, **not a GitHub fork**).  
**Original main branch:** unchanged.  
**Scope:** Michigan 13-district 2021-adopted congressional map; 2016 and 2020 presidential voting layers are **counterfactual scores**, not results of elections under that map.  
**Scientific disposition:** Stage 1 reviewed; Stage 2 mathematically audited; Stage 3 exploratory feasibility demonstrated in a prior separate execution, **not publication-ready**.

## Evidence provenance

- `docs/research_audit/stage1_repository_audit.md`: previously completed code/data/reproducibility audit. Static audit + 25 helper-function tests, **not** complete live rerun.
- `docs/research_audit/stage2_mathematical_validation.md`: previously independently recalculated saved scalar histories; 18,900 serially dependent post-burn-in observations, with low ESS and model limitations.
- `docs/research_audit/stage3_prior_empirical_report.md`: archived account of 13 earlier short real-graph chains, 7,300 proposals and 560 retained correlated observations across four model conditions. The original complete runtime outputs/assignments were **not imported** into this branch. A report is not a reproduced experiment.
- `scripts/research_audit/*`: new reproducibility and audit tools implemented on this branch.
- `tests/test_research_audit.py`: synthetic tests of data/chain input-gating.

## Source input (do not commit third-party data)

Public source: https://github.com/eveomett-states/Michigan  
File: `mi.json`, pinned Git blob SHA-1: `a4dfe70818f87b97924781216f3d86a672cfc66a`.  
Expected properties from the previously archived Stage 3 report: 4,756 nodes; 12,378 original edges; population 10,077,331; 13 reference districts; approximately 0.4019% maximum reference population deviation.  
**Licensing:** CC BY-NC 4.0 and Redistricting Data Hub use/attribution conditions; comply with the upstream terms. Source owner disclaims legal correctness.

**Directly verified on this branch:** `docs/research_audit/source_graph_verified.json` records an independent read of the immutable upstream Git blob: 4,756 nodes, 12,378 edges, zero duplicate precinct IDs, zero adjacency asymmetries, 10,077,331 census population, 13 reference districts, 681 original graph cut edges, and 14 split county / 9 split county-MCD groups. The original graph has disconnected pieces; artificial bridges have not been geographically certified.

### Step A — install dependencies and obtain verified source

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pip install arviz
python scripts/research_audit/download_source.py --acknowledge-source-terms
python scripts/research_audit/verify_graph.py \\
  --graph data/raw/mi/mi/mi.json \\
  --expected-git-blob a4dfe70818f87b97924781216f3d86a672cfc66a \\
  --expected-nodes 4756 --expected-population 10077331 \\
  --output outputs/research_audit/source_manifest.json
```

A graph-byte hash match establishes only matching **processed-source bytes**; it does not independently establish precise geographic adjacencies, vote allocation, physical island bridges, or Voting Rights Act compliance.

### Step B — matched-budget runs, never pretend they have run

```bash
python scripts/research_audit/run_experiment_matrix.py
# Inspect the printed commands before opting in.
python scripts/research_audit/run_experiment_matrix.py --execute
```

The matrix plans **4 seeds × 2 population tolerances × 8,000 steps**, 2,000 step burn-in, assignment snapshots every 10 steps. The driver calls the original GerryChain `run_baseline.py`, validates snapshots with `verify_snapshots.py`, and summarizes saved plan traces with `analyze_chains.py`. Data-sensitive executable work needs an environment with GerryChain and the verified original graph. The pipeline uses the **existing artificial graph bridges**; it logs neither physically verified island adjacency nor county-/municipality-split constraints, so outputs remain research models, not legally eligible plans.

Saved assignments are only a **subsample**. Passing snapshot checks does not validate each unrecorded transition. Retain complete assignments or implement per-step invariant checks before a journal-quality release.

### Step C — investigate and report diagnostics

Each experiment condition produces:

- Original per-chain metrics, district rows, seed/epsilon metadata, and assignment snapshots under `outputs/chains/week4/`.
- Independent snapshot-validation paired election scores under `outputs/research_audit/epsilon_*/validated_snapshots.csv`.
- Rank R-hat, bulk ESS, tail ESS, inclusive upper tails, and ±0.5% overlap under `outputs/research_audit/epsilon_*/diagnostics.csv` and `audit.json`.

`analyze_chains.py` uses an intentionally conservative **diagnostic gate** (R-hat <= 1.01 and bulk/tail ESS >= 400). Passing these scalar checks would be **necessary evidence, not proof** that the sampled high-dimensional map distribution is stationary, representative, or uniform. The driver marks inadequate mixing with an exit code but retains outputs.

## Completion ledger

| Gate | Status on this branch | Remaining |
| --- | --- | --- |
| Stage 1 repository audit | Archived, complete within its limited static scope | Restore original inputs/independent geographic source checks |
| Stage 2 numeric validation | Archived results and independent CSV analyzer added | Reproduce original archived histories from recovered nested ZIP and compare artifact hashes |
| Stage 3 source acquisition | Pinned and validated source-fetch **code** added | Actually download and hash on execution machine |
| Stage 3 feasible tighter model | Previous report documents short exploratory runs | Reproduce with original full-precision per-step data; validate transitions |
| Stage 3 standardized experiment | Matched-budget *runner* added | Execute runs; archive complete outputs and diagnostics |
| Stage 3 geography | Existing bridge handling reviewed; geographic proxy mismatch previously documented | Audit bridges against real map; add county/municipal, compactness, VRA/COI-aware comparisons |
| Stage 3 mixing and sensitivity | Methods/rejection conditions documented | Independent starts, mixing, stable ESS/tails, comparable models and uncertainty |
| Final paper | **Not certified** | Correct claims, cite original sources, bounded inference |

## Nonnegotiable interpretation

Do **not** say that 18,900 sequential samples are 18,900 independent maps; do **not** report raw upper-tail fractions as exact p-values; do **not** call a sample legal simply because it is contiguous and population balanced; do **not** assert uniform sampling from ReCom; do **not** infer intent or illegality from a partisan score. The already observed county-split discrepancy is central, not a cosmetic concern.

## Tests

```bash
PYTHONPATH=src python -m pytest tests/test_research_audit.py -q
```

These are synthetic validations, not an assertion that the live Michigan graph run passed. Before use in a submission, add real-data integration tests that cover every accepted step and independently reconstruct source election joins.
