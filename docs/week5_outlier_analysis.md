# Week 5 — Enacted-plan outlier analysis

## Question

Where does the enacted congressional plan fall relative to the post-burn-in ReCom ensemble generated under the Week 4 constraints?

The comparison is conditional on the exact model:

- the precinct graph and its documented artificial water/island bridges;
- ReCom as implemented by the installed GerryChain version;
- required contiguity;
- the declared population tolerance;
- no county-split, Voting Rights Act, or communities-of-interest constraint in the baseline;
- the chosen election data.

The ensemble must not be described as a uniform sample of every legally valid map.

## Empirical percentile

For an enacted value \(x\) and sampled values \(X_1,\dots,X_N\), this project reports the midrank percentile

\[
100\frac{\#(X_i<x)+\tfrac12\#(X_i=x)}{N}.
\]

Half of tied observations are placed below the enacted value. This matters for discrete outcomes such as seat counts. Inclusive lower and upper tail percentages are also saved.

These quantities describe the enacted plan's location in the sampled distribution. They are not automatically classical p-values because:

1. MCMC observations are correlated;
2. the reference distribution is algorithm- and constraint-dependent;
3. true mixing is not proven;
4. the enacted plan was not randomly generated under a classical null experiment.

## Headline figures

### Signature statistical panel

The pipeline creates distributions for:

- Democratic seats;
- efficiency gap;
- mean–median difference;
- cut edges.

Each distribution marks the enacted plan and reports its empirical percentile.

### Sorted-district plot

For every sampled plan, district Democratic vote shares are sorted from most Democratic to least Democratic. At each rank, the plot displays:

- ensemble 5th–95th percentile band;
- ensemble interquartile band;
- ensemble median;
- enacted district value.

This shows where the enacted plan creates unusually safe, competitive, or opposition-leaning districts. It can reveal structural patterns consistent with packing or cracking, but those terms should be used cautiously unless the pattern survives election and constraint sensitivity checks.

### Comparison maps

The pipeline selects four plans:

1. enacted plan;
2. robustly typical sampled plan;
3. sampled plan with minimum efficiency gap;
4. sampled plan with maximum efficiency gap.

Because Week 4 did not save every full assignment, the map script replays the recorded chain seeds and captures only the selected steps. It verifies the recovered metrics against the saved production CSV before drawing a map. A replay mismatch is treated as an error, not ignored.

## Direction of the efficiency gap

The Week 4 implementation uses

\[
\frac{\text{Republican wasted votes}-\text{Democratic wasted votes}}
{\text{total two-party votes}}.
\]

Therefore:

- positive values indicate more Republican wasted votes under this sign convention;
- negative values indicate more Democratic wasted votes.

Always state the sign convention beside the result.

## Robustness requirement

The Week 5 result is preliminary until the same sampled-map logic is evaluated with another election. The recommended comparison is 2016 versus 2020 presidential data on the same constraint structure. After both analyses exist, `scripts/compare_week5_elections.py` produces the election-sensitivity table and figure.

## Required interpretation paragraph

Use this language as the baseline and replace only the bracketed result:

> The enacted plan falls at the [X]th empirical percentile of the sampled ReCom distribution for [metric] under the stated constraints and election data. This means the enacted value is unusual, or not unusual, relative to this specific comparison ensemble. It does not establish that the chain sampled uniformly from all valid maps, prove partisan intent, or resolve whether the plan is legally impermissible.
