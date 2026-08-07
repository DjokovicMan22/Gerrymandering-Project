#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import pandas as pd

from redistricting.reporting.week7 import (
    compact_table_text,
    describe_extremeness,
    evidence_ledger,
    extract_percentile_rows,
    format_number,
    get_metric_row,
    image_markdown,
    infer_sample_count,
    markdown_table,
    metric_sentence,
    read_csv_if_exists,
    require_file,
    summarize_percentiles,
    top_sorted_deviations,
    write_text,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a stronger Week 7 paper, appendix, and talk script.")
    parser.add_argument("--name", default="mi_2020")
    parser.add_argument("--state-name", default="Michigan")
    parser.add_argument("--election-label", default="2020 presidential election")
    parser.add_argument("--comparison-name", default="mi_2016")
    parser.add_argument("--comparison-label", default="2016 presidential election")
    parser.add_argument("--burn-in", type=int, default=700)
    return parser.parse_args()


def find_chain_paths(name: str) -> list[Path]:
    patterns = [
        f"outputs/chains/week4/{name}_chain[123]_7000steps_seed*_plan_metrics.csv",
        f"outputs/chains/week4/{name.replace('_2020', '')}_2020_chain[123]_7000steps_seed*_plan_metrics.csv",
    ]
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(Path(p) for p in glob.glob(pattern))
    return sorted(set(paths))


def build_executive_claim(percentiles: pd.DataFrame | None) -> str:
    seats = get_metric_row(percentiles, "dem_seats")
    gap = get_metric_row(percentiles, "efficiency_gap")
    mm = get_metric_row(percentiles, "mean_median")
    parts = []
    if seats:
        parts.append(f"The enacted plan elects {format_number(seats.enacted_value, 0)} Democratic seats and sits at the {format_number(seats.percentile, 1)}th empirical percentile for Democratic seats.")
    if gap:
        parts.append(f"Its efficiency gap is {format_number(gap.enacted_value, 4)} and sits at the {format_number(gap.percentile, 1)}th empirical percentile.")
    if mm:
        parts.append(f"Its mean-median difference is {format_number(mm.enacted_value, 4)} and sits at the {format_number(mm.percentile, 1)}th empirical percentile.")
    if not parts:
        return "The generated percentile table must be inspected manually because its columns could not be parsed."
    return " ".join(parts)


def build_paper(args: argparse.Namespace) -> str:
    name = args.name
    percentiles = pd.read_csv(require_file(f"outputs/tables/week5/{name}_outlier_percentiles.csv"))
    sorted_summary = read_csv_if_exists(f"outputs/tables/week5/{name}_sorted_district_summary.csv")
    enacted_ranked = read_csv_if_exists(f"outputs/tables/week5/{name}_enacted_ranked_districts.csv")
    selected_plans = read_csv_if_exists(f"outputs/tables/week5/{name}_selected_plans.csv")
    diagnostics = read_csv_if_exists(f"outputs/tables/week4/{name}_production_diagnostics.csv")
    constraint = read_csv_if_exists(f"outputs/tables/week6/{name}_constraint_sensitivity.csv")
    percentile_ranges = read_csv_if_exists(f"outputs/tables/week6/{name}_percentile_ranges.csv")
    constraint_diag = read_csv_if_exists(f"outputs/tables/week6/{name}_constraint_diagnostics.csv")
    geography = read_csv_if_exists(f"outputs/tables/week6/{name}_geography_baseline.csv")
    seat_dist = read_csv_if_exists(f"outputs/tables/week6/{name}_seat_distribution.csv")
    comparison = read_csv_if_exists(f"outputs/tables/week5/{args.comparison_name}_outlier_percentiles.csv") if args.comparison_name else None

    chain_paths = find_chain_paths(name)
    sample_count = infer_sample_count(chain_paths, args.burn_in) or 18900
    chain_count = len(chain_paths) or 3
    deviations = top_sorted_deviations(sorted_summary)
    ledger = evidence_ledger(percentiles, diagnostics, constraint, geography, percentile_ranges)

    seats = get_metric_row(percentiles, "dem_seats")
    gap = get_metric_row(percentiles, "efficiency_gap")
    mm = get_metric_row(percentiles, "mean_median")
    cut = get_metric_row(percentiles, "cut_edges")
    hypothesis_direction = describe_extremeness(seats, "more Democratic seats than most sampled neutral plans", "fewer Democratic seats than most sampled neutral plans")

    comparison_text = ""
    if comparison is not None and not comparison.empty:
        comparison_text = f"""
### 7.3 Election-data sensitivity: {args.comparison_label} versus {args.election_label}

A credible gerrymandering analysis cannot score a plan using only the election that produces the most dramatic result. The geometry of the map is fixed, but each election supplies a different partisan field over the same geography. If the enacted plan is extreme under one election and ordinary under another, the correct conclusion is not simply that the map is or is not an outlier. The correct conclusion is that the outlier finding is election-sensitive.

The table below reports the same enacted-plan percentile calculation under the comparison election when available.

{markdown_table(comparison, digits=4)}

This robustness check is evidence, not decoration. It tests whether the conclusion is about the structure of the district plan or about a single election's temporary vote pattern. In the final version of this paper, this paragraph should state plainly which metrics are stable across elections and which move materially.
"""

    return f"""# Detecting Outlier Congressional Maps with Redistricting Ensembles: Evidence from {args.state_name}

**Student research paper draft**  
**Primary state:** {args.state_name}  
**Primary scoring election:** {args.election_label}  
**Main ensemble:** {chain_count} independent ReCom chains, 7,000 steps per chain, {args.burn_in}-step burn-in per chain  
**Post-burn-in sampled plans used in the main outlier analysis:** {sample_count:,}

## Abstract

This paper studies whether the enacted congressional districting plan in {args.state_name} is unusual relative to a neutral computational baseline. The baseline is an ensemble of alternative valid district maps generated using ReCom Markov-chain sampling. The central claim is intentionally narrower than a legal or political accusation: the analysis asks where the enacted plan falls within the distribution of sampled plans that satisfy the stated graph, population, and contiguity constraints. The project constructs the analysis from the ground up: it represents precincts as a graph, implements compactness and partisan metrics, runs multiple redistricting chains, removes burn-in, checks practical convergence diagnostics, computes empirical percentiles, analyzes rank-ordered district vote shares, and stress-tests the conclusion under alternate population tolerances and election data. The main result is that the enacted plan is not evaluated in isolation; it is evaluated against thousands of alternative maps drawn over the same state geography. The strongest defensible conclusion is conditional: under this data, graph model, ReCom proposal, population tolerance, and scoring election, the enacted map occupies the reported empirical position in the sampled ensemble. The analysis informs a gerrymandering question but does not by itself prove illegality, intent, or full exploration of the redistricting state space.

## 1. Research question, hypothesis, and evidentiary standard

The research question is:

> **Where does the enacted {args.state_name} congressional plan fall in the distribution of valid alternative plans generated by a neutral ReCom ensemble, and what does that position imply about whether the enacted plan is an outlier under the stated constraints?**

The working hypothesis is not simply “the map is gerrymandered.” That phrasing is too broad, too legalistic, and too dependent on intent. A stronger scientific hypothesis is:

> **Hypothesis.** If the enacted plan is structurally unusual, then its partisan outcomes and district-level vote-share structure will fall in the tails of the sampled neutral ensemble rather than near the ensemble center. This should be visible not only in one metric, but across several forms of evidence: seat outcomes, efficiency gap, mean-median difference, sorted-district vote shares, representative maps, and robustness checks.

The evidentiary standard used in this paper is cumulative. A single strange-looking district is not enough. A single partisan metric is not enough. A single chain is not enough. The paper therefore treats the claim as stronger only if several pieces of evidence point in the same direction:

1. The enacted plan has an extreme empirical percentile for at least one meaningful partisan metric.
2. The sorted-district plot shows structural deviations consistent with packing or cracking rather than only an aggregate arithmetic difference.
3. Independent chains show overlapping scalar distributions after burn-in.
4. The conclusion survives reasonable population-tolerance changes.
5. The conclusion is not purely an artifact of the scoring election.
6. The limitations are strong enough that the reader knows exactly what was not modeled.

This standard matters because redistricting is a high-dimensional problem. The number of possible district maps is enormous. Direct enumeration is impossible for a real state, so the relevant mathematical question becomes one of sampling and comparison: does the enacted plan look ordinary or unusual relative to the plans the model actually samples?

## 2. Executive result

{build_executive_claim(percentiles)}

The concise interpretation is that the enacted plan is **{hypothesis_direction}**. That statement is intentionally conditional. It refers to the sampled ensemble after burn-in, not to every possible legal map. It also refers to the {args.election_label}, not to all elections. The rest of the paper explains why this distinction is essential.

Key percentile results:

{summarize_percentiles(percentiles)}


## 3. Literature positioning: what this project borrows and what it does differently

This project is strongest when it is positioned as a small, reproducible version of a serious research design rather than as a standalone opinion about a map. The relevant literature suggests four methodological lessons.

**First, computational redistricting is useful because districting is too complex for visual intuition.** Guest, Kanayet, and Love (2019) argue that redistricting can be treated as a computational problem in which humans specify public criteria and machines search the resulting space. Their weighted k-means approach is an optimization method, not an ensemble method, but it gives this project an important framing: the issue is not whether a map looks strange, but whether a transparent algorithmic criterion produces a more defensible baseline. They also caution that the criteria themselves must be debated: compactness, municipal boundaries, communities, and legal requirements are not interchangeable goals. This paper adopts that lesson by separating measurement from judgment.

**Second, single-number partisan metrics are useful but incomplete.** Stephanopoulos explains the efficiency gap as a wasted-vote measure built from packing and cracking. That directly motivates this project's implementation of exact wasted votes and the efficiency-gap shortcut. But Stephanopoulos also frames gerrymandering as a problem of causes and consequences: mapmaking institutions, political geography, minority representation, and representational distortion all matter. This paper therefore uses the efficiency gap as one signal, not as the entire proof.

**Third, the closest methodological model is a simulation baseline.** Kenny, McCartan, Simko, Kuriwaki, and Imai (2023) compare enacted congressional plans to large sets of simulated alternatives that serve as a nonpartisan baseline. Their central design principle is the same as this project's: partisan effects should be separated from geography and redistricting rules by comparing the enacted map to alternative plans drawn under similar constraints. This project is smaller and state-specific, but the inferential structure is similar: the enacted map's statistic is meaningful only relative to a modeled distribution of counterfactual plans.

**Fourth, turnout and election data create an important limitation.** Bouton, Genicot, Castanheira, and Stashko (2024) show that when turnout differs across groups, the usual pack-and-crack story becomes more complicated. They call the resulting strategy pack-crack-pack: low-turnout supporters and high-turnout opponents may be packed, while other groups are cracked. This is important because this project scores plans using two-party vote totals but does not model turnout heterogeneity as an independent strategic dimension. That does not invalidate the ensemble analysis, but it means the paper should avoid claiming that efficiency gap, mean-median, or sorted-district plots capture every possible gerrymandering strategy.

The project therefore sits between three bodies of work: computational redistricting, partisan-fairness metrics, and simulation-based counterfactual baselines. Its contribution is not a new theorem or a national causal estimate. Its contribution is an independently implemented, reproducible state-level pipeline that applies these ideas to {args.state_name}, reports the enacted map's empirical position, and makes the assumptions visible.

### 3.1 Source-to-project crosswalk

| Source | What it contributes | How this project uses it | Limitation it exposes |
|---|---|---|---|
| Guest, Kanayet, and Love (2019) | Computational redistricting and explicit criteria | Motivates algorithmic baselines and compactness analysis | Optimization criteria are value choices, not neutral truths |
| Stephanopoulos (2017) | Efficiency gap, causes, consequences, representation | Motivates wasted-vote arithmetic and avoids treating metrics as pure geometry | Metrics need institutional and geographic context |
| Kenny et al. (2023) | Simulated nonpartisan baseline for enacted plans | Provides the closest template for ensemble comparison | Baseline validity depends on encoded rules and constraints |
| Bouton et al. (2024) | Turnout-sensitive pack-crack-pack strategy | Strengthens limitations and election-data caution | This project does not explicitly model turnout strategy |

The most important implication of this crosswalk is that the paper should not present the ensemble percentile as an isolated number. It should present the percentile as one part of a broader measurement chain: graph model → constraints → ReCom sampling → diagnostics → empirical percentile → robustness → limitations.

## 4. Why an ensemble is necessary

A redistricting plan is a partition of geographic units into districts. Even after population equality and contiguity are imposed, the number of valid maps remains too large to list. This is why the project does not attempt exhaustive enumeration. Instead, it uses a Markov chain to sample alternative plans. The purpose of sampling is to create a baseline distribution: a set of plans that are valid under the stated rules and generated without directly optimizing partisan outcome.

This changes the logic of the analysis. Without an ensemble, one might say “the enacted plan gives Party A seven seats” or “the efficiency gap is X.” Those statements are descriptive but incomplete. They do not say whether the outcome is unusual for the state’s political geography. With an ensemble, the question becomes comparative: if thousands of other valid plans drawn on the same geography usually produce a different seat count or a different partisan-metric distribution, then the enacted plan’s position becomes evidence of outlier status.

The ensemble does not magically remove all modeling choices. It makes them explicit. A map can be ordinary under one set of constraints and unusual under another. For this reason, the paper reports population tolerance, graph construction, burn-in, chain count, sample count, and practical convergence diagnostics. The claim is only as strong as the transparency of those choices.

## 4. Data model and graph construction

The computational object in the project is a precinct adjacency graph. Each precinct or voting tabulation district is a node. An edge connects two nodes when their polygons share a boundary segment. This is a graph-theoretic version of the map, and it is the object manipulated by the ReCom chain.

Each node stores at least four types of information:

- population, used to enforce approximate equality among congressional districts;
- enacted district assignment, used as the starting plan and baseline comparison;
- Democratic vote total for the scoring election;
- Republican vote total for the scoring election.

The graph uses rook adjacency rather than queen adjacency. Rook adjacency requires shared boundary length; queen adjacency would count point-touching polygons as adjacent. For redistricting, point contiguity is usually too weak to represent a meaningful connected district, so rook adjacency is the cleaner modeling convention.

A real geographic graph can contain islands and water-separated components. GerryChain’s ReCom procedure requires a connected graph. This project resolves disconnected components by adding explicit artificial bridge edges inside the same enacted district. These edges are not literal borders. They are modeling edges that preserve graph connectivity for water-separated pieces. The paper must state this clearly because hidden graph repairs would weaken the credibility of the analysis.

The production debug output documented five artificial bridge edges for Michigan, connecting disconnected components that otherwise made the dual graph unusable for ReCom. The audit then checked that saved district snapshots were graph-contiguous under the repaired graph.

## 5. Metrics before ensembles

### 5.1 Compactness metrics

Compactness metrics measure district shape. This project computes three different compactness scores: Polsby-Popper, Reock, and convex-hull ratio. Polsby-Popper is based on the isoperimetric ratio, comparing area to perimeter squared. Reock compares a district’s area to the area of its smallest enclosing circle. Convex-hull ratio compares a district’s area to the area of its convex hull.

These metrics are useful but limited. A low compactness score can identify suspicious shapes, but it does not prove partisan manipulation. Coastlines, water, municipal boundaries, and settlement patterns can all affect compactness. Polsby-Popper is especially sensitive to boundary resolution because perimeter increases when boundaries are represented with more detail. That is why the project includes a boundary-resolution sensitivity experiment rather than treating compactness as an objective truth.

The point of Week 2 was therefore not to find one perfect shape metric. It was to show why shape alone is insufficient and why a stronger analysis must move to partisan metrics and ensembles.

### 5.2 Partisan metrics

The project computes three basic partisan summaries: Democratic seats, efficiency gap, and mean-median difference.

**Democratic seats** count how many districts have Democratic two-party vote share above 50%. This is intuitive but incomplete because it reduces the entire map to one integer.

**Efficiency gap** measures the difference in wasted votes between parties, scaled by total two-party votes. Losing votes are wasted, and winning votes beyond what was needed to win are also wasted. The algebraic shortcut often written as \(EG = S - 2V + 1/2\) depends on equal-turnout assumptions. This project computes the exact wasted-vote version and uses the shortcut only as a diagnostic comparison.

**Mean-median difference** compares the mean district Democratic vote share with the median district Democratic vote share. It is a skewness-like statistic: if one party’s voters are packed into a few extremely high-vote-share districts, the distribution can become skewed.

No single metric is definitive. Efficiency gap can be distorted by unequal turnout and naturally clustered voters. Mean-median can miss some forms of bias and can behave strangely when the district vote-share distribution has unusual shape. Seat count is coarse. The purpose of computing several metrics is not to produce three independent proofs, but to see whether different summaries tell a coherent story.

## 6. ReCom ensemble method

The ReCom proposal works by selecting two adjacent districts, merging their nodes, and repartitioning the merged subgraph into two districts using a random spanning-tree procedure. This preserves contiguity by construction when the proposal succeeds and makes relatively large moves compared with single-precinct flip chains.

For the main analysis, the chain starts from the enacted plan. Each proposed plan must satisfy the population constraint. The main tolerance is 2%, meaning every sampled district population must remain within 2% of the ideal congressional district population. The chain records plan-level statistics at every step: Democratic seats, efficiency gap, mean-median difference, cut edges, and maximum population deviation. It also records district-level vote shares for the sorted-district plot.

The production ensemble consists of three independent 7,000-step chains. The first 700 steps of each chain are treated as burn-in and excluded from the main distribution. This leaves {sample_count:,} post-burn-in sampled plans. The enacted plan at step 0 is used as the observed comparison value and is not part of the post-burn-in ensemble distribution.

## 7. Diagnostics: why the run is not trusted blindly

A chain finishing successfully only proves that the program ran. It does not prove that the sampled distribution is scientifically useful. The project therefore performs several checks.

First, population deviation is checked directly. The production diagnostic table shows that sampled plans respect the declared population tolerance. Second, the statewide vote share is constant across plans, which confirms that the chain is moving precincts among districts rather than changing the underlying election. Third, saved assignment snapshots are checked for graph contiguity. Fourth, trace plots are inspected to confirm that tracked statistics fluctuate rather than remaining frozen. Fifth, split-Rhat is computed as a warning diagnostic across independent chains.

The practical diagnostics are summarized below:

{compact_table_text(diagnostics, max_rows=12, digits=4)}

A split-Rhat value close to one is reassuring for the tracked scalar summaries. It is not proof that the chain fully mixed over the entire space of valid redistricting plans. Redistricting state spaces are too complicated for that level of certainty in a student project. The honest claim is narrower: the independent chains show practical agreement on the reported summaries, and the remaining uncertainty is acknowledged in the limitations section.

## 8. Main outlier results

The main statistical output is the enacted plan’s empirical position within the ensemble. The table below gives the evidence directly.

{markdown_table(percentiles, digits=4)}

{metric_sentence(percentiles, "dem_seats", "Democratic seat count")}

{metric_sentence(percentiles, "efficiency_gap", "efficiency gap")}

{metric_sentence(percentiles, "mean_median", "mean-median difference")}

{metric_sentence(percentiles, "cut_edges", "cut edges")}

The figure below is the main signature figure. It shows the ensemble distribution for multiple metrics and marks the enacted plan as a vertical reference.

{image_markdown(f"outputs/figures/week5/{name}_signature_outlier_panel.png", f"{args.state_name} enacted plan compared with the post-burn-in ReCom ensemble under the {args.election_label}.")}

The evidentiary point is not merely whether the enacted plan is above or below the ensemble mean. The more important question is its empirical percentile. A plan near the 50th percentile is typical on that metric. A plan near the 0th or 100th percentile is unusual under the model. Intermediate values require more careful language.

## 9. Sorted-district evidence: looking inside the seat count

Aggregate metrics can hide structure. Two plans can produce the same number of seats while distributing voters very differently. The sorted-district plot addresses this by ranking each plan’s districts from most Democratic to least Democratic, then comparing the enacted plan’s rank-ordered vote shares with the ensemble distribution at each rank.

This plot is important because packing and cracking are structural patterns. Packing appears when one party’s strongest districts are much stronger than the ensemble would normally produce. Cracking appears when the party’s voters are spread just below competitiveness across several districts. A sorted-district plot can reveal these patterns even when a single aggregate metric is ambiguous.

{image_markdown(f"outputs/figures/week5/{name}_sorted_districts.png", f"Sorted-district comparison for {args.state_name}; enacted ranked districts are overlaid on the ensemble quantile bands.")}

The largest rank-level deviations from the ensemble median are:

{compact_table_text(deviations, ["rank", "enacted_dem_share", "median", "enacted_minus_ensemble_median", "absolute_deviation"], max_rows=6, digits=4)}

The enacted rank table is:

{compact_table_text(enacted_ranked, max_rows=15, digits=4)}

This section is where the paper should move from arithmetic to interpretation. If the strongest enacted Democratic districts are far above the ensemble median while competitive districts are weaker than usual, that is evidence consistent with packing. If several districts lie just below 50% when the ensemble usually gives them above 50%, that is evidence consistent with cracking. The final paper should describe the exact pattern shown in the figure rather than merely saying the line is “high” or “low.”

## 10. Representative maps

A statistical histogram is abstract, so the Week 5 pipeline also recovers representative maps. It identifies the enacted plan, a typical ensemble plan, and plans at efficiency-gap extremes. This connects scalar outlier analysis back to geographic district assignments.

{image_markdown(f"outputs/figures/week5/{name}_plan_comparison_maps.png", f"Comparison of enacted, typical, and extreme sampled plans for {args.state_name}.")}

The selected-plan table is:

{compact_table_text(selected_plans, max_rows=10, digits=4)}

The comparison maps should not be used as visual proof by themselves. Their role is explanatory: they let a reader see that the statistical results correspond to actual district maps, not to an abstract spreadsheet detached from geography.

## 11. Evidence ledger

A strong paper should explicitly connect each result to the claim it supports. The table below is the project’s evidence ledger.

{markdown_table(ledger, max_rows=12, digits=4)}

This ledger is also a guardrail against overstating the project. For example, chain diagnostics support practical credibility, but they do not prove perfect mixing. Geography baseline results support a more careful comparison than proportionality, but they do not encode every legal criterion. Percentiles show extremeness relative to the sampled ensemble, but not necessarily intent.

## 12. Robustness test 1: population-tolerance sensitivity

The first Week 6 stress test changes the population tolerance. The main analysis uses 2%, but the paper also compares 1% and 3%. This asks whether the enacted plan’s percentile is stable under a reasonable perturbation of the constraint.

{image_markdown(f"outputs/figures/week6/{name}_constraint_distributions.png", f"Metric distributions under alternate population tolerances for {args.state_name}.")}

{image_markdown(f"outputs/figures/week6/{name}_constraint_percentiles.png", f"Sensitivity of enacted-plan percentiles to population tolerance.")}

Constraint sensitivity table:

{compact_table_text(constraint, max_rows=25, digits=4)}

Percentile range table:

{compact_table_text(percentile_ranges, max_rows=10, digits=4)}

Constraint diagnostics:

{compact_table_text(constraint_diag, max_rows=15, digits=4)}

The interpretation should be specific. If a metric’s percentile moves only slightly across 1%, 2%, and 3%, that metric is robust to the tested population tolerance. If a metric moves substantially, the final conclusion must say so. Robustness does not mean nothing changes; it means the conclusion remains substantively similar under plausible modeling changes.

## 13. Robustness test 2: geography baseline

The second Week 6 stress test compares the ensemble seat distribution with a proportional benchmark. Proportionality asks how many seats a party would receive if seat share equaled statewide vote share. But congressional districting is geographic, not proportional. Voters are distributed unevenly across space, and that geography can create disproportional results even without intentional gerrymandering.

The ensemble provides a better baseline than proportionality alone because every sampled plan uses the same state geography and population constraint. If the ensemble itself regularly produces disproportional outcomes, then disproportionality by itself is weak evidence. If the enacted plan differs strongly from the ensemble mean, then the evidence is stronger.

{image_markdown(f"outputs/figures/week6/{name}_geography_baseline.png", f"Geographic baseline comparing proportional seats, ensemble mean seats, and enacted seats.")}

Geography baseline table:

{compact_table_text(geography, max_rows=5, digits=4)}

Seat distribution table:

{compact_table_text(seat_dist, max_rows=15, digits=4)}

This distinction is one of the most important conceptual points in the paper. The claim is not “the enacted plan is unfair because it is not proportional.” The stronger claim is “relative to an ensemble of valid geographic district plans, the enacted plan falls at the reported empirical position.” That statement uses geography as the baseline rather than ignoring it.

{comparison_text}

## 14. What the analysis supports

The analysis supports the following claims:

1. The project successfully constructs a reproducible redistricting pipeline for {args.state_name}.
2. The enacted plan can be represented as a graph partition and compared to sampled valid alternatives.
3. The production ReCom chains produce a large post-burn-in ensemble with practical scalar diagnostics.
4. The enacted plan’s seat count, efficiency gap, mean-median difference, and cut-edge count have measurable empirical percentiles within that ensemble.
5. Sorted-district analysis provides district-level structure beyond aggregate metrics.
6. Population-tolerance sensitivity and geography-baseline tests make the conclusion more mature than a single-metric result.

The analysis does **not** support the following claims:

1. It does not prove that the map is illegal.
2. It does not prove discriminatory intent.
3. It does not prove that the Markov chain sampled uniformly from all legal maps.
4. It does not fully model Voting Rights Act districts, communities of interest, municipal splits, incumbency, or every state-law criterion.
5. It does not prove that the chosen election is the only valid election for scoring partisan consequences.

This claim ladder is important for credibility. The project becomes stronger when it refuses to claim more than the evidence permits.

## 15. Limitations and strongest counterargument

The strongest counterargument is that the ensemble may not represent the full set of legally realistic plans. It includes population and contiguity constraints and uses ReCom to generate alternative maps, but it does not fully encode all real-world legal and political constraints. If an unmodeled constraint strongly shapes the enacted plan, then the enacted plan could appear extreme relative to the simplified ensemble even though it is explainable under a richer legal model.

A second limitation is mixing. The chain diagnostics show practical agreement on tracked statistics, but they do not prove complete exploration of the redistricting state space. Redistricting state spaces are high-dimensional, and rigorous mixing-time claims are difficult. The paper therefore uses trace plots and split-Rhat values as practical warning signals, not as mathematical proof.

A third limitation is election sensitivity. A map’s partisan consequences depend on the election used to score it. Presidential election data are useful because they are usually contested statewide and comparable across districts, but congressional elections include incumbency, uncontested races, and candidate-specific effects. A complete analysis should report multiple elections rather than selecting only one.

A fourth limitation is graph construction. Artificial bridge edges are necessary for water-separated components, but they are modeling decisions. They should be documented, and the analysis should avoid pretending that graph contiguity is identical to every legal definition of contiguity.

A fifth limitation is metric interpretation. Efficiency gap, mean-median difference, and seat count all compress complex geographic information. The sorted-district plot helps, but it still depends on the chosen election and ensemble. Stephanopoulos's efficiency-gap framework is powerful precisely because it gives an interpretable wasted-vote summary, but this paper should not treat that summary as a complete theory of representation.

A sixth limitation is turnout heterogeneity. The current project treats vote totals as the scoring field attached to precincts, but it does not explicitly model differential turnout rates, voter eligibility, or the possibility that mapmakers exploit turnout rather than only partisan vote share. The pack-crack-pack model of Bouton et al. shows why this matters: a map can be strategically designed around which supporters and opponents are likely to vote, not merely around where nominal partisan support is located. This strengthens the reason to report multiple metrics and to avoid saying that a non-extreme efficiency gap means no gerrymandering.

A seventh limitation is that this project is not a national causal study. Stephanopoulos studies causes and consequences across many plans and years; Kenny et al. estimate national and state-level effects using a large set of simulations. This paper is a focused state case study. That is acceptable, but it means the conclusion should be framed as a state-specific measurement result rather than a broad claim about American redistricting.

These limitations do not destroy the project. They define the boundary of the conclusion. A mature redistricting paper is not one that declares certainty; it is one that makes its assumptions visible and tests whether the conclusion survives reasonable challenges.

## 16. Conclusion

This project answers the original question by constructing a transparent mathematical baseline for {args.state_name}'s enacted congressional plan. The enacted plan is compared with a post-burn-in ensemble of {sample_count:,} sampled alternatives generated by ReCom under stated constraints. The result is reported through empirical percentiles, sorted-district structure, representative maps, population-tolerance sensitivity, and a geography baseline.

The final conclusion should be stated carefully:

> Under the stated precinct graph, artificial-bridge convention, population constraint, ReCom proposal, burn-in choice, and {args.election_label} scoring data, the enacted {args.state_name} plan falls at the reported empirical percentiles of the sampled ensemble. This is evidence about statistical outlier status relative to the modeled neutral baseline. It is not by itself a legal conclusion about intent or illegality.

That is the strongest defensible form of the project. It is mathematically serious, reproducible, and honest about its limitations.


## References

Guest, O., Kanayet, F. J., & Love, B. C. (2019). *Gerrymandering and computational redistricting*. Journal of Computational Social Science, 2, 119-131. https://doi.org/10.1007/s42001-019-00053-9

Kenny, C. T., McCartan, C., Simko, T., Kuriwaki, S., & Imai, K. (2023). *Widespread partisan gerrymandering mostly cancels nationally, but reduces electoral competition*. Proceedings of the National Academy of Sciences, 120(25), e2217322120. https://doi.org/10.1073/pnas.2217322120

Stephanopoulos, N. O. (2017). *The Causes and Consequences of Gerrymandering*. University of Chicago Public Law and Legal Theory Working Paper No. 629.

Bouton, L., Genicot, G., Castanheira, M., & Stashko, A. L. (2024). *Pack-Crack-Pack: Gerrymandering with Differential Turnout*. NBER Working Paper No. 31442.

These references should be treated as the core literature spine. Additional citations can be added for GerryChain/ReCom, the efficiency gap article by Stephanopoulos and McGhee, and any state-specific legal background.

## Appendix A. Reproducibility commands

Main production chains:

```bash
python scripts/run_baseline.py --state mi --steps 7000 --seed 101 --chain-id chain1
python scripts/run_baseline.py --state mi --steps 7000 --seed 202 --chain-id chain2
python scripts/run_baseline.py --state mi --steps 7000 --seed 303 --chain-id chain3
```

Week 4 diagnostics:

```bash
python scripts/analyze_week4_chains.py \
  outputs/chains/week4/mi_2020_chain1_7000steps_seed101_plan_metrics.csv \
  outputs/chains/week4/mi_2020_chain2_7000steps_seed202_plan_metrics.csv \
  outputs/chains/week4/mi_2020_chain3_7000steps_seed303_plan_metrics.csv \
  --burn-in 700 \
  --name mi_2020_production
```

Week 5 outlier analysis:

```bash
python scripts/run_week5_outlier_analysis.py \
  --glob 'outputs/chains/week4/mi_2020_chain[123]_7000steps_seed*_plan_metrics.csv' \
  --burn-in 700 \
  --name mi_2020 \
  --state-name "{args.state_name}" \
  --election-label "{args.election_label}"
```

Week 6 stress tests:

```bash
python scripts/run_week6_sensitivity_chains.py \
  --state mi \
  --election 2020 \
  --epsilons 0.01 0.03 \
  --steps 3000 \
  --seeds 101 202 303

python scripts/analyze_week6_stress_tests.py \
  --config configs/week6_mi_2020.json \
  --name mi_2020
```

## Appendix B. Hostile questions and concise answers

**Is this map illegal?**  
This project does not decide legality. It measures whether the enacted map is an outlier relative to sampled alternatives under stated constraints. Illegality requires legal standards, evidence, and judicial interpretation beyond this computation.

**Is this just partisan advocacy?**  
The method is structurally nonpartisan. It can flag maps favoring either party. The project reports the enacted plan's position in an ensemble and also reports limitations and sensitivity tests.

**How do you know the chain mixed?**  
I do not claim a rigorous proof of full mixing. I use three independent chains, burn-in removal, trace plots, overlapping scalar distributions, and split-Rhat diagnostics as practical checks. The paper explicitly treats mixing as a limitation.

**Why not just use compactness?**  
Compactness measures shape, not partisan consequence. A compact map can still advantage a party, and an irregular district can arise from legitimate geography or legal constraints. Compactness is useful vocabulary but not a sufficient standard.

**Why not just use proportional representation?**  
Congressional districts are geographic. Voter clustering can produce disproportional seat outcomes even without gerrymandering. The ensemble baseline is stronger because it compares the enacted plan with other valid maps drawn on the same geography.

**What would make the conclusion stronger?**  
More elections, more explicit legal constraints, a second-state replication, longer chains, independent external review, and comparison with another ensemble method would all strengthen the project.
"""


def build_talk_script(args: argparse.Namespace, paper: str) -> str:
    return f"""# Ten-minute talk script — {args.state_name} ensemble analysis

## Slide 1 — Title
I studied whether the enacted congressional map in {args.state_name} is unusual relative to alternative valid maps. The key point is that I am not asking whether a district looks weird. I am asking where the enacted plan falls in a sampled distribution of neutral alternatives.

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
"""


def main() -> None:
    args = parse_args()
    paper = build_paper(args)
    out = write_text(f"outputs/reports/week7/{args.name}_final_paper.md", paper)
    script = write_text(f"outputs/reports/week7/{args.name}_talk_script.md", build_talk_script(args, paper))
    print(f"Saved {out}")
    print(f"Saved {script}")
    print("This version is intentionally much longer and evidence-driven. Edit it manually before final submission.")


if __name__ == "__main__":
    main()
