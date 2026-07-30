# Detecting Gerrymandering with Metrics and Ensembles

This repository studies enacted congressional maps in Michigan and Missouri. It begins with precinct-level geography and election data, implements compactness and partisan metrics, and will culminate in GerryChain ensembles that compare enacted maps with many legally constrained alternatives.

## Current scope

- **Week 1:** precinct maps, enacted districts, dual graphs, population validation, and a 4×4 counting experiment.
- **Week 2:** Polsby–Popper, Reock, convex-hull ratio, synthetic stress tests, and boundary-resolution sensitivity.
- **Week 3:** efficiency gap, mean–median difference, seats–votes summaries, two-election sensitivity, and synthetic counterexamples.
- **Weeks 4–7:** ReCom ensembles, convergence diagnostics, outlier analysis, robustness checks, paper, and presentation.

See [`PROJECT_STATUS.md`](PROJECT_STATUS.md) for the live checklist.

## Repository layout

```text
configs/                 future chain settings
data/raw/                 local shapefiles and graph files
notebooks/                exploratory notebooks
outputs/figures/          generated figures by week
outputs/reports/          generated summaries by week
outputs/tables/           generated tables by week
scripts/                  reproducible analysis entry points
src/redistricting/        reusable package code
tests/                    unit tests
docs/                     methodology and mathematical notes
```

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The scripts expect state shapefiles somewhere below:

```text
data/raw/mi/
data/raw/mo/
```

Each shapefile must include `CD`, `TOTPOP`, and the election fields used by the corresponding script.

## Reproduce completed weeks

```bash
python scripts/week1_dual_graph_map.py
python scripts/week1_vote_seat_analysis.py
python scripts/week1_complete_representation_analysis.py
python scripts/week1_population_and_grid.py
python scripts/week2_compactness_analysis.py
python scripts/week2_resolution_sensitivity.py
python scripts/week3_partisan_metrics.py
pytest -q
```

Generated outputs are written under `outputs/`.

## Methodological boundary

A compactness score or partisan metric is not, by itself, proof of intentional or illegal gerrymandering. The eventual ensemble result will be interpreted only relative to the stated population, contiguity, compactness, and other modeled constraints. Legal conclusions require considerations that this model may not encode, including Voting Rights Act compliance and communities of interest.

## Data provenance

Complete [`docs/data_provenance.md`](docs/data_provenance.md) before publishing. Record the original source, download URL, retrieval date, map vintage, election definitions, coordinate reference system, and any preprocessing performed.
