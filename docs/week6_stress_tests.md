# Week 6 — Stress-testing the conclusion

Week 6 attacks the Week 5 outlier result instead of treating the first ensemble as definitive.

## Investigation 1: population-tolerance sensitivity

The baseline ensemble permits each district population to differ from the ideal population by at most 2%. Week 6 adds shorter independent ensembles at 1% and 3% tolerances. The analysis then compares:

- Democratic-seat distributions;
- exact efficiency-gap distributions;
- mean–median distributions;
- cut-edge distributions;
- the enacted plan's empirical percentile under each constraint setting.

Changing the tolerance changes the sampled map space and can change ReCom's behavior. A conclusion that survives this perturbation is more credible than one reported under a single arbitrary setting. It is not universally robust: compactness bounds, county splits, municipal preservation, Voting Rights Act constraints, and communities of interest remain untested.

## Investigation 2: geography versus proportionality

The neutral ensemble's Democratic-seat distribution is compared with the fractional proportional benchmark

\[
S_{\mathrm{prop}} = V_D \times N,
\]

where \(V_D\) is statewide Democratic two-party vote share and \(N\) is the number of districts.

The ensemble is **not** designed to make seats proportional to votes. A difference between the neutral-ensemble mean and proportional benchmark estimates how residential geography and the selected constraints affect seat conversion. It should not be interpreted as proof that the full difference is inevitable under every valid map.

## Required interpretation

The correct conclusion has conditional form:

> Under the stated ReCom proposal, population tolerances, graph conventions, election layer, and omitted constraints, the enacted plan occupies a specified position in the sampled distribution.

The analysis does not independently establish intent, causation, legality, or constitutional liability.

## Diagnostics

Each tolerance uses multiple chains and reports split-Rhat for tracked scalar statistics. Split-Rhat near 1 is evidence of cross-chain agreement, not a proof of full mixing or uniform sampling.

## Limitations to retain in the final paper

1. ReCom and constraints define the comparison distribution.
2. MCMC observations are correlated.
3. True redistricting mixing time is unresolved in practical applications.
4. Presidential votes are a fixed counterfactual election layer.
5. VRA opportunity districts, communities of interest, county splits, and municipal preservation are not explicitly modeled.
6. Artificial bridge edges represent water/island connectivity rather than literal shared land borders.
7. Statistical unusualness is distinct from partisan intent and legal invalidity.
