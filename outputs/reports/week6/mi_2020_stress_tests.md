# Week 6 stress tests — Michigan

## Design

Election layer: 2020 presidential election

Population-tolerance ensembles:

- 1% tolerance: 8,100 post-burn-in sampled plans
- 2% tolerance: 18,900 post-burn-in sampled plans
- 3% tolerance: 8,100 post-burn-in sampled plans

The Week 6 investigations are:

1. **Constraint sensitivity:** whether the enacted plan's empirical position moves when the allowed district-population deviation changes.
2. **Geographic baseline:** whether the neutral ensemble itself departs from proportional seat allocation, which estimates how geography and the modeling constraints can produce disproportionality without treating proportionality as the sampling target.

## Investigation 1: population-tolerance sensitivity

| constraint_label   | metric         |   enacted_value |   ensemble_mean |   ensemble_median |   midrank_percentile |
|:-------------------|:---------------|----------------:|----------------:|------------------:|---------------------:|
| 1% tolerance       | dem_seats      |          7.0000 |          5.7163 |            6.0000 |              92.5309 |
| 1% tolerance       | efficiency_gap |          0.0033 |         -0.0995 |           -0.0794 |              95.2593 |
| 1% tolerance       | mean_median    |         -0.0140 |         -0.0310 |           -0.0313 |              95.1481 |
| 1% tolerance       | cut_edges      |        681.0000 |        842.6349 |          842.0000 |               0.0864 |
| 2% tolerance       | dem_seats      |          7.0000 |          5.7149 |            6.0000 |              92.5185 |
| 2% tolerance       | efficiency_gap |          0.0033 |         -0.0999 |           -0.0798 |              96.0741 |
| 2% tolerance       | mean_median    |         -0.0140 |         -0.0304 |           -0.0314 |              93.3280 |
| 2% tolerance       | cut_edges      |        681.0000 |        845.0066 |          842.0000 |               0.0317 |
| 3% tolerance       | dem_seats      |          7.0000 |          5.9257 |            6.0000 |              87.1111 |
| 3% tolerance       | efficiency_gap |          0.0033 |         -0.0841 |           -0.0782 |              92.2716 |
| 3% tolerance       | mean_median    |         -0.0140 |         -0.0278 |           -0.0272 |              87.9012 |
| 3% tolerance       | cut_edges      |        681.0000 |        841.0623 |          840.0000 |               0.1296 |

Observed percentile movement across the tested tolerances:

- Cut edges: 0.10-percentage-point range (small sensitivity by the declared descriptive rule).
- Democratic seats: 5.42-percentage-point range (small sensitivity by the declared descriptive rule).
- Efficiency gap: 3.80-percentage-point range (small sensitivity by the declared descriptive rule).
- Maximum population deviation: 0.00-percentage-point range (small sensitivity by the declared descriptive rule).
- Mean–median difference: 7.25-percentage-point range (small sensitivity by the declared descriptive rule).

These ranges are descriptive. A stable percentile across the tested values strengthens robustness only with respect to this particular constraint perturbation. It does not show robustness to every omitted rule.

## Multi-chain diagnostics

| constraint_label   | statistic                |   chain_count |   burn_in |   pooled_mean |   pooled_sd |   split_rhat |
|:-------------------|:-------------------------|--------------:|----------:|--------------:|------------:|-------------:|
| 1% tolerance       | dem_seats                |             3 |       300 |        5.7163 |      0.8044 |       1.0205 |
| 1% tolerance       | efficiency_gap           |             3 |       300 |       -0.0995 |      0.0629 |       1.0207 |
| 1% tolerance       | mean_median              |             3 |       300 |       -0.0310 |      0.0109 |       1.0100 |
| 1% tolerance       | cut_edges                |             3 |       300 |      842.6349 |     52.1765 |       1.0566 |
| 1% tolerance       | max_population_deviation |             3 |       300 |        0.0093 |      0.0007 |       1.0003 |
| 2% tolerance       | dem_seats                |             3 |       700 |        5.7149 |      0.8058 |       1.0180 |
| 2% tolerance       | efficiency_gap           |             3 |       700 |       -0.0999 |      0.0628 |       1.0183 |
| 2% tolerance       | mean_median              |             3 |       700 |       -0.0304 |      0.0105 |       1.0175 |
| 2% tolerance       | cut_edges                |             3 |       700 |      845.0066 |     53.7875 |       1.0304 |
| 2% tolerance       | max_population_deviation |             3 |       700 |        0.0187 |      0.0013 |       1.0014 |
| 3% tolerance       | dem_seats                |             3 |       300 |        5.9257 |      0.8319 |       1.0172 |
| 3% tolerance       | efficiency_gap           |             3 |       300 |       -0.0841 |      0.0652 |       1.0157 |
| 3% tolerance       | mean_median              |             3 |       300 |       -0.0278 |      0.0119 |       1.0167 |
| 3% tolerance       | cut_edges                |             3 |       300 |      841.0623 |     52.8885 |       1.0417 |
| 3% tolerance       | max_population_deviation |             3 |       300 |        0.0279 |      0.0019 |       1.0016 |

Split-Rhat is used as a warning diagnostic. Values near 1 support agreement among the tracked scalar distributions but do not prove that ReCom fully mixed over the space of valid maps.

## Investigation 2: geographic baseline

Baseline ensemble: **2% tolerance**

- Statewide Democratic two-party share: 51.413%
- Proportional Democratic-seat benchmark: 6.684 of 13
- Neutral-ensemble mean Democratic seats: 5.715
- Neutral-ensemble median Democratic seats: 6.000
- Neutral-ensemble 5–95% range: 4.000 to 7.000
- Geography/constraint gap, ensemble mean minus proportional benchmark: -0.969 seats
- Enacted minus neutral-ensemble mean: +1.285 seats
- Probability of a Democratic seat majority in the baseline ensemble: 13.93%

The neutral ensemble is not designed to force proportional representation. A systematic difference between its seat distribution and the proportional benchmark is evidence that residential geography and the chosen map constraints affect seat conversion. It is not proof that every part of the difference is unavoidable.

## Strongest limitations

1. **The comparison distribution is conditional on modeling choices.** ReCom, population tolerance, graph adjacency conventions, and any omitted constraints define which maps are treated as typical.
2. **No proof of uniform sampling or full mixing.** Trace plots and multi-chain agreement are practical diagnostics, not a theorem about the stationary distribution or mixing time.
3. **Important legal and political constraints are not modeled.** The baseline does not explicitly preserve Voting Rights Act opportunity districts, communities of interest, municipal boundaries, or county splits.
4. **Election-layer dependence.** Presidential votes are assigned to alternative districts as a fixed counterfactual layer; they do not model congressional candidates, incumbency, turnout changes, or voter adaptation.
5. **Artificial bridge edges.** Water-separated or disconnected precinct components were connected with documented modeling edges. These preserve graph operations but are not literal shared land borders.
6. **Correlated samples.** Consecutive MCMC plans are not independent, so row count is larger than effective sample size.
7. **Outlier status is not a legal conclusion.** The analysis can establish unusualness relative to a declared ensemble. It cannot by itself establish intent, causation, constitutional liability, or illegality.

## Strongest argument against the conclusion

The enacted plan can appear extreme because the ensemble omits real redistricting requirements or encodes an overly broad comparison class. Therefore, the correct claim is conditional: the enacted plan is or is not unusual **among maps generated under the stated proposal and constraints**. The analysis must not silently upgrade that conditional statement into a universal judgment about all legally valid maps.

Generated by `scripts/analyze_week6_stress_tests.py` using configuration for `mi_2020`.
