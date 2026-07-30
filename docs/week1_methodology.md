# Week 1 methodology

## State selection

Michigan and Missouri were chosen as a two-state comparison for technical rather than partisan reasons. Both datasets contain precinct geometry, enacted congressional assignments, total population, and multiple statewide elections in a form that can be processed through a common pipeline. Their different political geography and district structures make them useful for testing whether the same measurements behave consistently across states. Michigan is the primary state for the first ensemble because it has more congressional districts and therefore a richer distribution of possible seat outcomes. Missouri serves as the replication state.

This choice does not imply a conclusion about either enacted map. The analysis asks whether each enacted plan is unusual relative to alternative plans generated under declared constraints.

## Graph representation

Each precinct is represented by a graph node. An edge joins two precincts when they share a boundary segment under **rook adjacency**. Point-only contact is excluded because permitting a district to remain connected through a single corner gives a weaker and often legally or geographically implausible notion of contiguity.

Water-separated precincts and islands can make the raw rook graph disconnected. Any artificial bridge must be:

1. geometrically and administratively defensible;
2. recorded explicitly rather than inserted silently;
3. applied consistently during enacted-plan validation and ensemble generation; and
4. included in the limitations section because it changes the state-space definition.

## Population equality

For district populations \(P_1,\dots,P_k\), ideal population is

\[
P^* = \frac{\sum_i P_i}{k}.
\]

District relative deviation is

\[
\delta_i = \frac{P_i-P^*}{P^*}.
\]

The validation script reports every district's population, absolute deviation, relative deviation, and the maximum absolute deviation. This is a descriptive check of the enacted assignment. The population tolerance used in future ensembles must be stated separately.

## Why sampling is necessary

Even a 4×4 grid has many assignments of cells to two equal-size districts, and contiguity filtering is already nontrivial. For real precinct graphs, exhaustive enumeration is infeasible because the number of assignments grows combinatorially. The Week 1 grid experiment provides a small reproducible illustration; Week 4 replaces enumeration with Markov-chain sampling.

## Constraints not yet modeled

Population equality and contiguity are necessary but not sufficient descriptions of a legally valid plan. The eventual limitations section must discuss at least Voting Rights Act requirements, communities of interest, political-subdivision splits, incumbency rules where applicable, and the modeling choices used to represent water connectivity.
