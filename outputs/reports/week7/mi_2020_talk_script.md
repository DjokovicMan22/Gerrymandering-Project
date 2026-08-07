# Ten-minute talk script — Michigan ensemble analysis

## Slide 1 — Title
I studied whether the enacted congressional map in Michigan is unusual relative to alternative valid maps. The key point is that I am not asking whether a district looks weird. I am asking where the enacted plan falls in a sampled distribution of neutral alternatives.

## Slide 2 — Problem
A single district shape or a single partisan metric can mislead. Geography matters. Voters are clustered. Compactness is not the same as fairness. So the project needs a baseline.

## Slide 3 — Hypothesis
The hypothesis is that if the enacted plan is structurally unusual, it should appear in the tails of the ensemble on several forms of evidence: seats, efficiency gap, mean-median, sorted district vote shares, and robustness tests.

## Slide 4 — Data model
I represent precincts as graph nodes and shared borders as edges. Districting becomes a graph partition problem. The enacted plan is step zero. I added documented bridge edges for water-separated components so the graph is connected for ReCom.

## Slide 5 — ReCom method
ReCom merges two adjacent districts and splits them again using a random spanning tree. I ran three independent chains, 7,000 steps each, and removed 700 steps of burn-in from each chain.

## Slide 6 — Diagnostics
I checked that population deviation stays within tolerance, statewide vote share does not change, saved districts are graph-contiguous, trace plots fluctuate, and split-Rhat values are close to one for tracked scalar summaries.

## Slide 7 — Main result
This is the outlier panel. The vertical line is the enacted plan. The histograms are sampled alternatives. The important number is not just whether the enacted plan is above or below the mean; it is the empirical percentile.

## Slide 8 — Sorted districts
The sorted-district plot shows structure hidden by aggregate metrics. If the enacted plan is unusual at specific ranks, that helps distinguish packing or cracking patterns from a simple seat-count difference.

## Slide 9 — Representative maps
The map comparison ties the statistics back to actual district assignments. It shows the enacted plan, a typical sampled plan, and efficiency-gap extremes.

## Slide 10 — Stress tests
I changed population tolerance from 1% to 2% to 3%. If a conclusion collapses when tolerance changes, it is weak. If it survives, it becomes more credible.

## Slide 11 — Geography baseline
Proportionality alone is not enough because districts are geographic. The ensemble estimates what neutral plans tend to produce on the same geography.

## Slide 12 — Claim ladder
The analysis supports a conditional statistical claim, not a legal verdict. It says where the enacted plan falls relative to my sampled ensemble. It does not prove intent or illegality.

## Slide 13 — Limitations
The main limitations are unmodeled legal constraints, mixing uncertainty, election sensitivity, and graph-construction choices. I state these because they define the boundary of the result.

## Slide 14 — Conclusion
The project shows how mathematics can turn a vague argument about gerrymandering into a reproducible outlier-analysis framework. The strongest claim is conditional, but it is much stronger than visual intuition.

## Slide 15 — Questions
The prepared answers are: not a legal ruling, not partisan advocacy, not proof of perfect mixing, and not reducible to compactness or proportionality alone.
