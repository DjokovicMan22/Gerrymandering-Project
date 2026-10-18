# Stage 3: a provably reversible **proxy-constrained local** redistricting kernel

**Status:** newly implemented and under real Michigan feasibility testing.  
**Implementation:** `src/redistricting/ensemble/reversible.py`.  
**Operational pilot:** `.github/workflows/stage3-reversible-pilot.yml`.  
**Crucial distinction:** this is a **different** transition kernel from the earlier ReCom simulations and **must not** be pooled with them.

## Why build a separate kernel?

The preceding GerryChain ReCom experiments gave reproducible map histories but could not establish a known invariant or uniform target distribution under their custom rejection semantics. More steps cannot repair an unidentified stationary target. The present kernel is designed so that its *conditional* invariant law can be derived mathematically and tested by exact enumeration on a small graph, before assessing whether it moves adequately on the real precinct graph.

This design is not an assertion that a uniform distribution over all mathematically feasible precinct maps is the correct legal or substantive comparison for an enacted map.

## State space

Fix a graph `G=(V,E)`, precinct populations `p_v`, and **labeled** districts `1,...,K`. A state assigns every precinct exactly one district label and must satisfy all these implemented model constraints:

1. Exactly the same K nonempty district labels as the starting map.
2. Each district induces a connected subgraph of the **augmented** Michigan graph.
3. Each district's population is within ±epsilon of the fixed statewide ideal.
4. The number of edges crossing districts is at most a specified cap.
5. The number of split `COUNTYFIPS` and `COUNTYFIPS+MCDFIPS` source groups are at most their caps, where enabled.

This finite, labeled state set is `S`. The model graph includes five algorithmically constructed artificial island bridges whose physical validity is still **not** independently certified. Source municipality grouping is not an official legal hierarchy. These model states are **not** certified legal Michigan congressional plans.

## Proposal distribution (all probabilities explicit)

At map `x`, let `B(x)` be the set of edges joining unlike district labels and let `b_x=|B(x)|`. Choose one boundary edge **uniformly** from `B(x)`, and choose a move type with a *constant* `p` for a one-precinct flip or `1-p` for a two-precinct swap (pilot `p=0.5`). Each attempted transition is counted; rejected proposals hold the existing map.

**Flip:** Orient the chosen boundary edge uniformly (1/2 each direction). Assign its first endpoint `u` to the neighboring district `d`. Let `n_x(u,d)` be the number of graph neighbors of `u` with district label `d` in `x`. The proposal probability for this *particular* change, conditional on selecting flip, is

```text
q_flip(x -> y) = n_x(u,d) / (2 b_x).
```

The reverse move requires `u` to have neighbors in its original district `a` in `y`, and

```text
q_flip(y -> x) = n_y(u,a) / (2 b_y).
```

Note the number of boundary edges can **change** after a flip. Assuming symmetric flip probabilities without this correction is incorrect.

**Swap:** Swap the two labels at the chosen unlike-labeled boundary edge. The same undirected edge remains a boundary edge after swapping, so conditional move probabilities are

```text
q_swap(x -> y) = 1 / b_x,
q_swap(y -> x) = 1 / b_y.
```

Flips and swaps have disjoint nontrivial state changes (one vs two different precincts); the fixed move-mixture weights cancel in the respective reverse/forward ratios.

If a candidate is outside `S`, or the reverse proposal probability vanishes, the transition is rejected and counted as a self-loop. Otherwise the Metropolis–Hastings acceptance probability is

```text
alpha(x -> y) = min(1, q(y -> x) / q(x -> y)).
```

An accepted move receives the new state; no hidden GerryChain retry loop is used.

## Precise mathematical statement

Let the finite set `S` be restricted to a **communicating component** `C` of feasible **labeled** assignments under the two local moves. Consider any two distinct `x,y in C`.

Because the proposed change is one flip or one swap, the reverse proposal has the same move type, and the relevant constant mixture weight cancels. The probability of a transition satisfies

```text
P(x,y) = w * min(q(x,y), q(y,x)),
P(y,x) = w * min(q(y,x), q(x,y)),
```

with identical `w=p` or `w=1-p`. Therefore **P(x,y)=P(y,x)**. With `pi(x)=1/|C|`, we obtain exact detailed balance:

```text
pi(x) P(x,y) = pi(y) P(y,x).
```

Self-loops fill the remainder of each transition row, so rows sum to one. The uniform law over each communicating component `C` is stationary. Holding moves generally make chains aperiodic when their self-loop probability is positive.

This establishes reversibility **under the implemented graph and proxy constraints**, not practical convergence or uniqueness of the stationary law across the whole feasible set.

**Not established:** irreducibility across `S`, connectivity between distinct legal/topological districts maps, mixing time, effective sample size, legal-plan uniformity, independent initialized samples, physical accuracy of artificial bridges, or inclusion of Voting Rights Act / communities-of-interest requirements. Small precinct swaps/flips may be nearly always infeasible at ±0.5% and narrow geographic caps. In that case this exact kernel is theoretically interpretable but empirically unusable without better transitions.

## Tests and Michigan pilot

The companion `tests/test_reversible_kernel.py` enumerates all feasible labeled assignments of a small six-node cycle and independently counts each oriented boundary-edge flip/swap proposal. It verifies exact detailed balance and stochastic row feasibility for **every pair of feasible toy states**, as well as handling of nonreversible candidate moves, population rejection and seeded replay.

Real-data pilot: four chains (two distinct seeded warm assignments per geographic regime), each **2,001 states including its actual warmed start**, **2,000 attempted MH transitions**, ±0.5% population, exact source pinning, 50/50 flip/swap mixture, and 21 independently rescored full snapshots per chain. These runs test acceptance and movement, not convergence, effective sample size, or an enacted-map outlier hypothesis.

The pilot must report separate rejection reasons: population, district contiguity, geographic caps, and MH correction. Every attempted transition must have exactly one such disposition or an acceptance. Very low movement is a **negative feasibility result**, not evidence of successful sampling.

## Decision rule

- If the kernel produces meaningful, independently reproducible movement, proceed to longer sampling with multiple independent, distance-qualified starts and scalar + spatial diagnostics.
- If the kernel is largely immobile, do **not** declare Stage 3 complete: evaluate more efficient reversible proposals or a separately validated reversible ReCom variant, and/or a justified relaxation/augmentation of the constraint model.
- No pilot result will be described as proving Michigan gerrymandering, an election outcome under 2021-adopted lines, a legal-outlier probability or statistical significance.

The original project's `main` branch remains untouched.
