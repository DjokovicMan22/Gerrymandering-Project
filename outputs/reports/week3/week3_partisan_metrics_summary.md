# Week 3 — Partisan metrics

## Metrics implemented from scratch

- **Efficiency gap:** Republican wasted votes minus Democratic wasted votes, divided by all two-party votes. Positive values use the convention of Democratic advantage.
- **Equal-turnout shortcut:** `EG = S - 2V + 0.5`, where `S` is Democratic seat share and `V` is Democratic statewide vote share.
- **Mean–median difference:** median Democratic district vote share minus mean Democratic district vote share.
- **Seats–votes summary:** districts won under the selected election compared with statewide two-party vote share.

## State results

| State | Election | D vote | D seats | Exact EG | Shortcut EG | Mean–median | Turnout CV |
|---|---|---:|---:|---:|---:|---:|---:|
| Michigan | 2020 Presidential | 51.4% | 7/13 | +0.3% | +1.0% | -1.4 pp | 0.080 |
| Michigan | 2016 Presidential | 49.9% | 6/13 | -3.9% | -3.6% | -2.1 pp | 0.067 |
| Missouri | 2020 Presidential | 42.2% | 2/8 | -11.0% | -9.3% | -8.5 pp | 0.071 |
| Missouri | 2016 Presidential | 40.2% | 2/8 | -6.4% | -5.4% | -8.4 pp | 0.070 |

## Synthetic counterexamples

| Scenario | D vote | D seats | Exact EG | Shortcut error | Mean–median |
|---|---:|---:|---:|---:|---:|
| Concentrated minority geography | 35.0% | 0/5 | -20.1% | +0.1 pp | +0.0 pp |
| Distributed competitive support | 35.0% | 3/5 | +40.0% | -0.0 pp | +17.0 pp |
| Unequal-turnout distortion | 51.7% | 2/5 | -40.5% | +27.0 pp | -8.4 pp |
| Packing and cracking pattern | 56.2% | 2/5 | -22.4% | +0.0 pp | -9.2 pp |

## Interpretation

No single metric establishes that a district map is fair or unfair. Efficiency gap depends on turnout and statewide vote balance. Mean–median can miss some forms of packing and cracking. Seats–votes outcomes can reflect residential geography as well as district boundaries. The Week 4 ensemble provides the state-specific baseline.

## Election sensitivity

This script analyzes every recognized Democratic/Republican election pair present in the source shapefile. If only `PRE20D` and `PRE20R` are present, add a second election dataset before claiming a multi-election sensitivity result.
