# Week 6 installation and execution

## Files added

- `scripts/run_week6_sensitivity_chains.py`
- `scripts/analyze_week6_stress_tests.py`
- `src/redistricting/analysis/sensitivity.py`
- `configs/week6_mi_2020.json`
- `docs/week6_stress_tests.md`
- `tests/test_week6_sensitivity.py`

## Run order

```bash
python -m pip install -e .
pytest -q

python scripts/run_week6_sensitivity_chains.py \
  --state mi \
  --election 2020 \
  --epsilons 0.01 0.03 \
  --steps 3000 \
  --seeds 101 202 303

python scripts/analyze_week6_stress_tests.py \
  --config configs/week6_mi_2020.json \
  --name mi_2020
```

The new run generates 18,000 additional chain rows: three 3,000-step chains at 1% tolerance and three at 3% tolerance. The existing three 7,000-step Week 4 chains are reused as the 2% baseline.

## Main outputs

- `outputs/tables/week6/mi_2020_constraint_sensitivity.csv`
- `outputs/tables/week6/mi_2020_percentile_ranges.csv`
- `outputs/tables/week6/mi_2020_constraint_diagnostics.csv`
- `outputs/tables/week6/mi_2020_geography_baseline.csv`
- `outputs/tables/week6/mi_2020_seat_distribution.csv`
- `outputs/figures/week6/mi_2020_constraint_distributions.png`
- `outputs/figures/week6/mi_2020_constraint_percentiles.png`
- `outputs/figures/week6/mi_2020_geography_baseline.png`
- `outputs/reports/week6/mi_2020_stress_tests.md`

Trace plots for every sensitivity chain are saved under `outputs/figures/week6/traces/`.

## Git guidance

Do not commit the large Week 6 district-level chain files. Add these patterns to `.gitignore`:

```text
outputs/chains/week6/*_district_metrics.csv
outputs/chains/week6/*_assignments.json
```

Plan-level CSVs and metadata are substantially smaller and may be committed if repository size remains reasonable.
