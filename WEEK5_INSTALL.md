# Week 5 patch installation and run sequence

Copy this patch into the `Goodproject` root so its `scripts/`, `src/`, `docs/`, and `tests/` folders merge with the existing project.

## 1. Install and test

```bash
cd ~/Goodproject
unzip -o gerrymandering_week5_patch.zip
rm gerrymandering_week5_patch.zip
python -m pip install -e .
pytest -q
```

The patch adds five Week 5 tests. The exact total depends on the tests already in the repository; all tests should pass.

## 2. Generate the 2020 statistical results

```bash
python scripts/run_week5_outlier_analysis.py \
  --glob 'outputs/chains/week4/mi_2020_chain[123]_7000steps_seed*_plan_metrics.csv' \
  --burn-in 700 \
  --name mi_2020 \
  --state-name Michigan \
  --election-label '2020 presidential election'
```

Expected core outputs:

```text
outputs/tables/week5/mi_2020_outlier_percentiles.csv
outputs/tables/week5/mi_2020_sorted_district_summary.csv
outputs/tables/week5/mi_2020_selected_plans.csv
outputs/tables/week5/mi_2020_recovery_targets.json
outputs/figures/week5/mi_2020_signature_outlier_panel.png
outputs/figures/week5/mi_2020_dem_seats_outlier.png
outputs/figures/week5/mi_2020_efficiency_gap_outlier.png
outputs/figures/week5/mi_2020_sorted_districts.png
outputs/reports/week5/mi_2020_outlier_summary.md
```

Open them:

```bash
open outputs/figures/week5/mi_2020_signature_outlier_panel.png
open outputs/figures/week5/mi_2020_sorted_districts.png
open outputs/reports/week5/mi_2020_outlier_summary.md
```

## 3. Recover and draw representative maps

This may take time because it deterministically replays only the chains containing the selected target steps. It verifies every recovered target against the stored metrics.

```bash
python scripts/recover_week5_map_examples.py \
  --targets outputs/tables/week5/mi_2020_recovery_targets.json \
  --shapefile data/raw/mi/mi/mi.shp \
  --name mi_2020 \
  --state-name Michigan \
  --election-label '2020 presidential election'
```

Open the map panel:

```bash
open outputs/figures/week5/mi_2020_plan_comparison_maps.png
```

## 4. Run the second-election analysis later

Generate matching 2016 chain outputs with the same seeds and settings:

```bash
python scripts/run_baseline.py --state mi --steps 7000 --seed 101 --chain-id chain1 --election 2016
python scripts/run_baseline.py --state mi --steps 7000 --seed 202 --chain-id chain2 --election 2016
python scripts/run_baseline.py --state mi --steps 7000 --seed 303 --chain-id chain3 --election 2016
```

Then analyze them:

```bash
python scripts/run_week5_outlier_analysis.py \
  --glob 'outputs/chains/week4/mi_2016_chain[123]_7000steps_seed*_plan_metrics.csv' \
  --burn-in 700 \
  --name mi_2016 \
  --state-name Michigan \
  --election-label '2016 presidential election'
```

Compare elections:

```bash
python scripts/compare_week5_elections.py \
  outputs/tables/week5/mi_2016_outlier_percentiles.csv \
  outputs/tables/week5/mi_2020_outlier_percentiles.csv \
  --labels '2016 presidential' '2020 presidential' \
  --name mi_election_robustness
```

## 5. Commit Week 5

First inspect sizes:

```bash
du -sh outputs/chains/week5 outputs/figures/week5 outputs/tables/week5
git status
```

Stage code, tests, documentation, figures, reports, and tables:

```bash
git add \
  WEEK5_INSTALL.md \
  docs/week5_outlier_analysis.md \
  scripts/run_week5_outlier_analysis.py \
  scripts/recover_week5_map_examples.py \
  scripts/compare_week5_elections.py \
  src/redistricting/analysis \
  tests/test_week5_outliers.py \
  outputs/figures/week5 \
  outputs/tables/week5 \
  outputs/reports/week5
```

The selected-assignment JSON is regenerable and may be omitted if it is large:

```bash
printf '\n# Regenerable Week 5 selected assignments\noutputs/chains/week5/*_selected_assignments.json\n' >> .gitignore
git add .gitignore
```

Review, commit, and push:

```bash
git diff --staged --stat
git commit -m 'Add Week 5 enacted-plan outlier analysis and signature figures'
git push
```
