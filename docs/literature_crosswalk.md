# Literature Crosswalk for Final Gerrymandering Paper

Use this document to keep the final paper grounded in real literature rather than only project outputs.

## Guest, Kanayet, and Love (2019) — computational redistricting

**Use for:** framing why computational methods matter. Their paper argues that districting is complex enough that algorithmic methods can make the criteria and optimization process explicit.

**Connection to this project:** your project does not optimize one compactness criterion like weighted k-means; it samples alternative maps. Still, both approaches reject visual intuition as the standard.

**Best place in paper:** introduction, compactness section, limitations about criteria.

## Stephanopoulos (2017) — causes and consequences

**Use for:** efficiency gap background, packing/cracking interpretation, and why partisan skew matters for representation.

**Connection to this project:** your project implements efficiency gap but treats it as one metric inside an ensemble, not a standalone verdict.

**Best place in paper:** partisan metrics section and stakes/implications section.

## Kenny et al. (2023) — simulated nonpartisan baselines

**Use for:** methodological credibility. Their paper compares enacted plans against simulated alternatives to separate partisan effects from geography and redistricting rules.

**Connection to this project:** this is the closest high-level analogy to your method. You are doing a smaller state-level version with your own GerryChain/ReCom pipeline.

**Best place in paper:** ensemble method, inference framing, geography baseline.

## Bouton et al. (2024) — turnout heterogeneity and pack-crack-pack

**Use for:** a serious limitation and possible future extension. Their model shows that turnout heterogeneity can create strategies that ordinary pack/crack metrics may miss.

**Connection to this project:** your analysis uses vote totals but does not independently model turnout rates. That should be acknowledged as a limitation rather than hidden.

**Best place in paper:** limitations, future work, and hostile questions.
