# Stage 3: independently seeded warm-start diversity (preregistered before interpreting results)

**Experiment:** source-controlled pilot on the `research/stages-1-3-validation` branch.  
**GitHub Actions:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39157734877

## Why this test

The previous 64,000-state Michigan ReCom experiment began all chains at the **same enacted district map** and failed selected R-hat/ESS gates. Different RNG seeds alone do not guarantee dispersed initial states, so a new pilot measures *actual map disagreement* after separately seeded warmups and refuses to call mere relabeling 'diverse.'

**Input:** Michigan's 4,756-node, 13-district graph, pinned upstream Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`; five artificial island connections of unverified physical validity. Electoral summaries are from the pipeline's counterfactual 2020 precinct presidential vote allocation, not actual 2022 congressional election returns.

## Defined test

- **Two geographic proxy conditions**: closer (max 760 graph cut edges, 18 split `COUNTYFIPS` groups, 20 split `COUNTYFIPS+MCDFIPS` groups); relaxed (850, 24, 49).
- **Population deviation**: 0.5%; source/enacted baseline used as starting map for *each* independently seeded path.
- **Seeds**: 101, 202, 303, 404, four paths per condition.
- **Warmup budget**: exactly 800 recorded states per seed, including the starting state (799 geographic-proposal attempts). Geographic-cap-invalid proposed states become counted self-loops; additional built-in population and contiguity checks remain enabled.
- **Geographical checks**: the final map is independently re-evaluated for all precincts, population tolerance, graph contiguity, source-group split counts, and fixed presidential scores before inclusion.
- **Distance**: exact *minimum precinct disagreements over all one-to-one district relabelings*, computed by maximum-overlap bipartite matching (subset dynamic programming with 13 districts). The assignment's original label numbering cannot create a false distance.
- **Gate A**: each of four final maps differs from the enacted reference on at least **5% of precinct nodes** (after optimal relabeling).
- **Gate B**: all six pairs of endpoints differ from one another on at least **5% of nodes** (after optimal relabeling).
- **Evidence**: eight endpoint hashes, seed-level geographic/rejection/movement summaries, and twenty label-invariant pairwise/reference distances. Store no source graph or full precinct-level assignment in the published artifacts.

**Interpretation:** Even if both distance gates pass, these are *endpoint maps from separate stochastic warmups with the same enacted ancestor*, NOT independent draws from a stationary, legally constrained, or uniform map distribution. Pairwise separation does not establish the chain's stationary law, proposal symmetry, convergence, adequate geographic realism, or compliance with Michigan law.

**Dispositions:** `DIVERSE_ENDPOINTS_NOT_STATIONARY` when both gates pass, or `INSUFFICIENT_START_DIVERSITY` otherwise. A failed threshold is an empirical finding, not a software failure; operational errors must cause a separate failing CI step.

**Next step after this pilot** is to integrate distance-qualified seed-specific initial assignments into separately executed sampling chains, then compare observed acceptance, within-chain movement, R-hat, ESS and spatial/geographic mixing proxies. Do not call Stage 3 scientifically complete solely on the basis of a pass here.
