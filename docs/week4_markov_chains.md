# Week 4 — Markov chains and the ReCom ensemble

## Research objective

Generate legally simplified alternative congressional plans while preserving two hard constraints:

1. every district remains contiguous;
2. every district remains within a declared population tolerance of ideal population.

The chain begins at the enacted plan. Step 0 is therefore not a random draw.

## Markov-chain fundamentals

A Markov chain has a state space and transition rule. Its next state depends on its current state, not the full path taken to reach it. In this project, one state is one complete districting plan.

For a three-state example, use

\[
P=
\begin{pmatrix}
0.5&0.5&0\\
0.25&0.5&0.25\\
0&0.5&0.5
\end{pmatrix}.
\]

Each row sums to one. A stationary distribution satisfies

\[
\pi P=\pi, \qquad \sum_i \pi_i=1.
\]

By symmetry, this example has stationary distribution

\[
\pi=(1/4,1/2,1/4).
\]

Check it by direct matrix multiplication before treating the real chain as a black box.

## What ReCom does

One ReCom proposal:

1. selects two adjacent districts;
2. merges their precinct subgraphs;
3. samples a spanning tree on the merged region;
4. cuts an edge that creates two contiguous pieces near the target population;
5. assigns those pieces back as two districts.

This changes many precinct assignments at once while preserving contiguity and population balance by construction. The method is based on DeFord, Duchin, and Solomon's ReCom family of chains.

## Tracked quantities

For every plan, the baseline pipeline records:

- Democratic seats under a specified election;
- exact efficiency gap from wasted votes;
- mean–median difference;
- number of cut edges;
- maximum population deviation;
- every district's Democratic two-party vote share.

The number of cut edges is a graph-boundary proxy, not a complete geometric compactness measure.

## Constraint table

| Choice | Baseline value | Reason | Limitation |
|---|---:|---|---|
| Population tolerance | ±2% | Debug-friendly congressional baseline | Wider than the enacted plan and not a legal conclusion |
| Contiguity | Required | Core districting constraint | Graph bridges and water conventions affect it |
| Proposal | ReCom | Efficient large moves | Sampling distribution depends on proposal design |
| Acceptance | Always accept valid proposal | Transparent baseline | Does not target a uniform distribution over plans |
| County splits | Not constrained yet | Keeps first chain simple | Omits a relevant redistricting criterion |
| Election | 2020 presidential by default | Complete precinct coverage | Presidential votes differ from House voting behavior |

All values must be reported with the final results. Do not describe the ensemble as simply “all possible neutral maps.” It is a sample produced by this exact algorithm and constraint set.

## Practical convergence checks

Run at least three chains with different random seeds. Compare:

- trace plots;
- post-burn-in histograms;
- means and ranges;
- split-Rhat as a rough scalar warning diagnostic.

Similar-looking traces and distributions increase confidence but do not prove true mixing. Redistricting-chain mixing times remain difficult to establish.

## Required run sequence

1. `100` steps: verify that the pipeline executes and outputs are sensible.
2. `1,000` steps: debug stability and inspect trace plots.
3. Three independent `5,000`-step chains: initial multi-chain comparison.
4. At least `20,000` total production samples after the pipeline is stable.

Do not interpret a 100-step or 1,000-step debugging run as the final ensemble.

## Reproducibility

Each run stores:

- state and election;
- number of steps;
- population tolerance;
- ReCom node repeats;
- random seed;
- ideal population;
- timestamp;
- plan-level and district-level CSV files.

A random seed makes a software run reproducible under the same environment. It does not make the sample statistically sufficient.
