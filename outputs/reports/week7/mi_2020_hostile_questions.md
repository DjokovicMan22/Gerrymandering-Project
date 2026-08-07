# Hostile Question Prep

## Is this map illegal?

No. This project does not decide legality. It estimates whether the enacted plan is statistically unusual relative to sampled alternatives under stated constraints. Legal conclusions require legal standards, evidence of intent, and doctrines not fully encoded here.

## Isn't this just partisan?

The method is structurally nonpartisan. It does not optimize for either party. It asks where the enacted plan falls relative to a neutral ensemble. The same workflow could flag a map favoring Democrats or Republicans.

## How do you know your Markov chain mixed?

I do not claim a proof of perfect mixing. I used three independent chains, trace plots, distribution comparison, burn-in, and split-Rhat diagnostics. Those are practical checks, not a theorem. The conclusion is stated relative to the sampled ensemble.

## Why use presidential election data?

Presidential data are statewide, complete, and available for every precinct. Congressional election data can include uncontested races and candidate-specific effects. The limitation is that presidential results do not perfectly predict congressional outcomes, so I report election-data sensitivity.

## Why did you add artificial bridge edges?

The graph had disconnected island or water-separated components. GerryChain requires connectivity. I added deterministic bridge edges within the same enacted district and disclosed them. I did not delete islands or connect across arbitrary districts.

## Why not just use compactness?

Compactness is useful but insufficient. It measures geometry, not partisan consequence. A weird-looking district may reflect legitimate geography, and a compact district can still contribute to a biased plan.

## Why not compare directly to proportional representation?

Proportionality is a useful reference, but district elections are geographic. If voters are clustered, neutral district maps can naturally be disproportional. The ensemble estimates the geographic baseline.

## What is the strongest criticism of your project?

The ensemble is not the same as the complete legal universe of possible maps. It depends on the chosen units, constraints, proposal mechanism, and election data. That is why I report the assumptions explicitly and avoid legal overclaims.

## What would make the project stronger?

More legal constraints, additional elections, replication on another state, longer chains, and feedback from a redistricting expert would improve credibility. But the current project already demonstrates the full ensemble-analysis pipeline.
