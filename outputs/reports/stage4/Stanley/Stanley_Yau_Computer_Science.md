\begin{titlepage}
\thispagestyle{empty}
\begin{center}
\vspace*{0.9in}
{\Huge\bfseries The Phantom Baseline}\par
\vspace{.18in}
{\large Geographic Graph Artifacts, Reversible-Chain Mobility, and Constraint Sensitivity}\par
\vspace{.48in}
{\LARGE\bfseries Stanley}\par
\vspace{.25in}
{\large Computer Science Research Report}\par
\vspace{.19in}
{\normalsize S.-T. Yau High School Science Award — Paper Layout}\par
\vfill
{\small Algorithms \quad $\cdot$ \quad Geospatial Computation \quad $\cdot$ \quad October 2026}
\end{center}
\end{titlepage}

\thispagestyle{empty}
\begin{center}
{\large\bfseries Abstract}
\end{center}
When I attempted to evaluate a computational redistricting baseline for Michigan, three different obstacles demanded an explanation. The underlying precinct graph required artificial connections to become usable. Long Markov-chain runs produced extensive numerical output without convincing convergence. Finally, changing geographic-fragmentation caps shifted simulated political outcomes. These problems raised one methodological question: what evidence is needed before a map ensemble can serve as a neutral comparison?

I audited the processed 4,756-precinct Michigan graph, examined the geometry of its artificial connections, studied mixing in both recombination and locally reversible Markov chains, and evaluated a fixed-horizon sensitivity experiment with 64 independently verified terminal maps. The historical graph-repair procedure used enacted district labels to add five connections between polygons separated by approximately 42–280 km. Tested recombination and local Metropolis–Hastings configurations failed prespecified convergence diagnostics; for one relaxed MH condition, efficiency-gap $\widehat R$ reached 2.588 and bulk effective sample size was 4.8. In the finite-horizon comparison, relaxing three geographic-proxy caps increased average precinct reassignment from 13.40% to 29.00% and decreased mean Democratic seats by 0.406 and efficiency gap by 0.03278. The paired-bootstrap 95% interval for the tighter-minus-relaxed efficiency-gap contrast was [+0.00975, +0.05631].

These are conditional algorithmic findings, not estimates from a certified distribution of legally permissible Michigan districts. They motivate a three-gate audit: independently validate the geographic graph, demonstrate target-specific sampler reliability, and measure sensitivity to consequential modeling choices.

\newpage
\pagenumbering{arabic}
\pagestyle{fancy}

# Summary of technical contributions

I investigated a computational redistricting pipeline through three independent tests rather than claim a new election-law conclusion. **Geographic-state-space test:** reconstruct artificial adjacencies from source GIS and measure their polygon separation. **Markov-chain test:** derive and verify the detailed-balance correction of a boundary-edge flip/swap kernel while measuring practical acceptance and between-chain mixing. **Finite-horizon sensitivity test:** change a prespecified set of administrative proxies and analyze separately seeded terminal distributions instead of claiming stationary legal-map probabilities.

These are methodological contributions, not a universal theorem about every redistricting program. In the current implementation, the original adjacency repair used enacted labels; separate MH configurations had limited mobility; and the joint relaxation of three caps moved the average terminal efficiency-gap score. The claim becomes scientifically meaningful only with a reproducible record of *how* each of those statements was checked.

## Research structure

The report proceeds from source verification and graph definitions to diagnostic testing, a finite-horizon experiment, and an adversarial evidence ledger. Original results are distinguished from the upstream ReCom literature and from the published source GIS. The annexed derivation below demonstrates the invariant law of the implemented local MH correction *within a communicating component*, not the irreducibility of the entire proxy-feasible state space.

# 1. Introduction

My initial research question seemed straightforward: how unusual is an enacted congressional map compared with maps produced by a redistricting algorithm? Yet the computational workflow exposed a prior question. Compared with *which* maps? A program can generate a thousand districts that look plausible on a screen while failing to establish which plans are possible, which plans are likely under its sampling law, or whether successive simulated maps convey new statistical information.

In the Michigan pipeline I examined, an apparently routine connectivity repair was not routine at all. It joined precinct-graph components using the enacted congressional district assignment as a guide. Some chosen vertices were far apart in the original geographic data. When I then investigated chain behavior, more steps did not cure inadequate mixing. Changing the modeled fragmentation limits also changed the simulated outcomes. The errors were not all the same. They operated at different levels.

This is why I frame the work as an audit of the **baseline** rather than a test accusing any particular map of intentional gerrymandering. Ensemble methods have an established research foundation: ReCom methods and redistricting simulation have been developed in substantial prior work (DeFord, Duchin, and Solomon 2021; McCartan et al. 2022; Kenny et al. 2023). I do not infer that those published methods suffer the errors of this particular pipeline. Instead, I ask whether an individual computational implementation has established the prerequisites for its own inference.

I evaluate three failure channels. First, the geographic graph determines which district assignments are connected and therefore enter the modeled state space. Second, the transition mechanism must explore its intended distribution adequately; a long log is not enough. Third, an ensemble can change when the researcher changes limits on cut edges or administrative splits. The last point matters even when every program runs as instructed.

The result is an audit with a definite stopping rule. If geographic adjacency lacks an independent defense, simulated contiguity cannot certify real contiguity. If mixing fails, an empirical percentile cannot be presented as a stationary probability. If modeling choices shift the result, those choices belong in the main findings. They are not implementation trivia.

# 2. Research Design and Source Verification

## 2.1 What the simulation is allowed to claim

I represent precincts by vertices of a graph $G=(V,E)$. An edge records a chosen adjacency relation. A district assignment $x$ gives each precinct one of 13 congressional labels. For a geographic-cap regime $c$, the implemented state space $S_c(G)$ includes assignments that meet the code's connectedness, population and fragmentation requirements. This is a *modeled* feasible set, not the set of all Michigan-legal congressional maps.

The distinction between a graph and the real state is essential. A generated plan may be contiguous in $G$ even when its connectivity depends on edges without geographic or legal justification. Conversely, removing an edge may exclude a plan that is geographically valid under a special shoreline or island convention. A probability distribution defined over the wrong set of maps cannot be rescued by improving its numerical precision.

I use efficiency gap and Democratic seats scored from a counterfactual 2020 presidential-vote overlay as *outcomes*, not as definitions of legal validity. The enacted 2021 Michigan congressional plan scores seven Democratic seats and approximately +0.0033332 efficiency gap under the project's sign convention. Those are historical-data overlays, not observed congressional election results under the later district boundaries (Stephanopoulos and McGhee 2015).

## 2.2 Provenance before inference

The processed Michigan input has 4,756 precinct nodes and 12,378 graph edges. I compared the processed graph and precinct-polygon archive with identifiable public source files attributed to Veomett and collaborators. The source graph's Git blob identity is `a4dfe70818f87b97924781216f3d86a672cfc66a`; the polygon archive's corresponding identifier is `07bce18dabbcca9d549e28995a8156fd6978d7db`. Source checks reconciled population, district and county fields across all 4,756 processed records.

This does not mean I independently reconstructed every upstream Census or VEST join. I did not. Byte identity verifies which processed file entered an experiment. It does not verify every decision that produced that file. I retained that boundary throughout the analysis.

Independent arithmetic checks also exposed a one-vote-level sensitivity in an earlier 2016 seat-count calculation arising from fractional precinct vote allocation and floating-point aggregation order. Such a discrepancy is small but instructive: an equation can be correct while a threshold outcome remains sensitive to the order of computation. I recorded the issue rather than silently discarding it.

# 3. Geographic Topology: The First Gate

## 3.1 Five edges that changed the graph

The published Michigan graph originally had six disconnected components. A historical repair procedure inserted five edges to join those components. It used enacted congressional labels to choose endpoints compatible with the enacted plan. As a result, the procedure made the reference assignment connected partly *because it had consulted that assignment in constructing the graph*.

I checked the original polygon geometry. The shortest polygon-to-polygon gaps associated with the five inserted connections were approximately 42.3, 117.3, 134.3, 169.7 and 280.2 km. These were not documented physical contacts or independently justified legal water connections. An edge of that type is a modeling choice with consequences: it changes feasible contiguity, district boundary counts, and potentially the proposals of boundary-driven chains.

It is not a small cartographic issue. It changes what the algorithm regards as possible.

\begin{figure}[H]
\centering
\includegraphics[width=.91\linewidth,height=.33\textheight,keepaspectratio]{outputs/reports/stage4/figures/figure_topology_artificial_bridges.pdf}
\caption{Five historical artificial Michigan graph connections measured against processed precinct geometry. The project visualization was generated in Python using GIS geometry and Matplotlib; source precinct geometry is attributed to Veomett and collaborators (2024), and the archived source bytes were independently checked. The segments depict synthetic graph edges, not validated travel corridors or legal adjacency.}
\end{figure}

## 3.2 A distance-based alternative is not automatically neutral

I examined a separate proximity-based construction. A minimum-spanning tree among disconnected components reduced the total candidate connection distance to approximately 19.63 km, but did not preserve connectivity for every enacted district. The next sensitivity experiment considered $K$ nearest contacts with $K=1,3,10,25,50$. The smallest tested value meeting the graph-connectivity and reference-representability tests was $K=3$: thirteen added candidate edges, none longer than approximately 17.8 km.

The KNN3 alternative does not select individual edges using enacted district labels. However, the overall choice of $K=3$ followed checks against the enacted reference. That is still a selection decision. Nor does proximity independently establish legal adjacency under Michigan's shoreline, island, or county rules. I therefore use this graph to expose sensitivity, not to certify the lawful universe of maps.

## 3.3 Missouri as a follow-up test, not a replication

The repository also contains an exploratory Missouri precinct dual-graph overlay. Missouri supplies a useful future test because its geographic setting differs from Michigan's shorelines and islands. But a plotted overlay cannot prove that an underlying graph is disconnected, that bridges were inserted, or that any inserted bridges were inappropriate. The local Missouri inputs have not been independently byte-matched and audited under this protocol. No cross-state prevalence estimate follows.

\begin{figure}[H]
\centering
\includegraphics[width=.73\linewidth,height=.24\textheight,keepaspectratio]{outputs/figures/week1/mo_precinct_dual_graph_overlay.png}
\caption*{\textbf{Supplementary Figure S1.} Exploratory Missouri dual-graph overlay generated during earlier project work using Python, GeoPandas and Matplotlib. The source-data match, component structure, and existence or legality of any synthetic adjacency remain unverified. This illustration is not evidence of a national failure rate.}
\end{figure}

A real replication would pin Missouri's source files, inventory connected components, reconstruct any exceptional edges and measure their actual geometric separations. Until then, the Missouri figure poses a question; it does not answer it.

# 4. Sampling: The Second Gate

## 4.1 Correct arithmetic does not establish correct sampling

The historic ReCom archive contained substantial simulation output. In one 2020 presidential-vote condition at ±2% population tolerance, its post-burn-in files recorded 18,900 correlated states and a mean of 5.7149 Democratic seats. Yet none of those particular maps met the later ±0.5% population assumption. Nor did the original random-seed settings make their chain trajectories exactly replayable: GerryChain's internal random-number generator required explicit initialization separate from Python's global seed.

Those archives cannot be promoted retroactively into valid draws from a new, more restrictive target. I preserved the historical calculations while declining to interpret their recorded percentiles as probabilities under the final model.

After correcting random-number initialization, the audit ran eight explicitly seeded ReCom chains, each recording 4,001 states across two geographic-cap regimes. The scalar diagnostics still failed. Efficiency-gap rank-normalized $\widehat R$ was 1.733 with bulk effective sample size 9.4 under closer constraints; under relaxed constraints those values were 1.139 and 20.4. The prespecified standards were $\widehat R\le 1.01$ and bulk effective sample size at least 400.

Thousands of saved observations yielded very little effective information about the reported statistic. The chain moved. The inference did not become reliable.

## 4.2 Reversible Metropolis–Hastings did not solve finite-time mobility

I also examined a local boundary-edge Metropolis–Hastings transition rule. From the current map, it proposes a one-precinct boundary flip or a two-precinct label swap, checks the modeled population and connectedness conditions, and accepts feasible proposals with the correction


$$
\alpha(x,y)=\min\!\left\{1,\frac{q(y,x)}{q(x,y)}\right\}.
$$


A small-graph exact enumeration verified detailed balance for that implementation. Its invariant law is uniform only on each accessible communicating component of labeled, proxy-feasible assignments. It does not prove that the chain can reach every feasible assignment, or that its stationary law is substantively desirable.

In one 2,000-proposal closer-cap pilot, 635 transitions failed population checks, 602 failed contiguity, 547 failed geographic proxy checks, 32 failed the MH correction, and only 184 were accepted. These categories follow the program's sequential rejection checks. They cannot be interpreted as separately estimated causal effects of each constraint.

Pilot acceptance across tested runs was 9.20%–15.95%. After 2,000 attempted transitions, the assignments had moved only 1.7%–3.7% of precincts away from their warm starts. In later eight-chain MH testing, efficiency-gap convergence diagnostics were worse under the relaxed cap set than under the closer one:

| Efficiency-gap diagnostic | Closer MH condition | Relaxed MH condition |
|:---|---:|---:|
| Rank-normalized $\widehat R$ | 1.568 | 2.588 |
| Bulk effective sample size | 7.1 | 4.8 |

\noindent{\footnotesize\textit{Table 1 credit.} Derived from the executed eight-chain reversible-MH diagnostic report, computed using Python and rank-normalized MCMC diagnostics (Vehtari et al. 2021). The 2,000-step pilot rejection counts come from a separate experiment.}

The theoretical distinction matters. Cannon et al. (2026) analyze a specified reversible spanning-tree-weighted recombination method. The local flip/swap MH kernel tested here is **not** that method and targets a different invariant distribution. Two restrictive GerryChain pilots of a reversible ReCom implementation also failed to change their maps over 200 proposals, but that short operational result does not refute Cannon and colleagues' theorem or establish general immobility.

The broader lesson is precise. Detailed balance concerns the distribution a valid chain would preserve. Mixing diagnostics concern whether its finite output supports estimating that distribution. Both are necessary for a stationary-ensemble claim.

# 5. Fixed-Horizon Sensitivity: The Third Gate

## 5.1 A narrower question the experiment can answer

The mixing failures led me to frame the final experiment around a quantity that could actually be measured: the output of a **specified algorithm after 800 transitions from the enacted reference**, rather than a claimed equilibrium distribution over all lawful maps.

For the enacted starting assignment $x_0$, experimental graph $G_{\mathrm{KNN3}}$, cap regime $c$, and implemented transition procedure $P_c$, I define


$$
Q_{c,800}(A)=\Pr\!\left[X_{800}\in A\mid X_0=x_0,G=G_{\mathrm{KNN3}},P=P_c\right].
$$


This distribution exists as a finite-horizon property of the code. It need not be a legal or neutral baseline. The distinction prevents the central interpretive error of the historical archive.

I compared the following *composite* regimes under the same ±0.5% population tolerance:

| Constraint cap | Closer regime | Relaxed regime |
|:---|---:|---:|
| Graph cut edges | 760 | 850 |
| Split source county groups | 18 | 24 |
| Split source county–MCD groups | 20 | 49 |

\noindent{\footnotesize\textit{Table 2 credit.} Parameter values transcribed from the executed \texttt{stage3-finite-horizon-ensemble.yml} workflow. The categories are research proxies and are not certified Michigan statutory constraints.}

I ran the documented design as 32 separately seeded trajectories per regime (seeds 10001–10032). Each recorded 801 states including the enacted step-zero assignment. I treated only the final map from each trajectory as an independent Monte Carlo observation. The resulting 64 retained assignments were checked against the source node set, model-graph contiguity, population tolerance, geographic proxy limits, seat and efficiency-gap rescoring, and recorded SHA-256 identities. Replay of seed 10001 in each regime reproduced the endpoint records.

This yields 32 experimental endpoints per regime, not 25,632 statistically independent observations per regime. I used 10,000 endpoint-resampling draws to estimate conditional bootstrap intervals for regime means. For cross-regime differences, I resampled whole seed-indexed pairs 20,000 times. Same numerical seed labels across procedures do not mean identical proposal histories.

## 5.2 The result

The cap change coincided with greater geographic movement and a different partisan score distribution. Table 3 reports the independently scored endpoints.

| Outcome | Closer regime (mean) | Relaxed regime (mean) |
|:---|---:|---:|
| Democratic seats | 7.219 | 6.813 |
| Efficiency gap | +0.02010 | −0.01268 |
| Graph cut edges | 695.09 | 758.84 |
| Reassigned precincts | 13.40% | 29.00% |

\noindent{\footnotesize\textit{Table 3 credit.} Compiled in Python from 64 source-verified terminal records generated by the project's GerryChain workflow; 32 separate seeds per condition. The 2020 vote overlay is counterfactual. Means describe a finite-horizon procedure, not legally valid map frequencies.}

Relaxing the caps increased average geographic reassignment by 15.61 percentage points. Democratic seats fell by 0.406 on average. Efficiency gap fell by 0.03278. The paired-bootstrap tighter-minus-relaxed 95% interval for efficiency gap was [+0.00975, +0.05631]; for Democratic seats it was [+0.124, +0.719]. These intervals quantify variability across seeded *program runs*. They are not confidence intervals for an unknown lawful-map distribution.

\begin{figure}[H]
\centering
\includegraphics[width=.82\linewidth,height=.32\textheight,keepaspectratio]{outputs/reports/stage4/figures/figure1_terminal_EG_ECDF.pdf}
\caption{Empirical efficiency-gap cumulative distributions for the two cap regimes, with the 2020 enacted-reference overlay. Visualization generated by the project's Python/Matplotlib Stage 4 workflow from the independently verified 64-endpoint score artifact. Source inputs: Veomett et al. processed Michigan data. These curves are not stationary legal-map null distributions.}
\end{figure}

The closer regime rejected an average 79.22% of proposals on geographic checks, compared with 52.83% under the relaxed regime. The two groups also differed in their realized cut-edge and administrative-split counts. Taken together, the findings describe a model that explored different areas of assignment space and produced measurably different outcomes when three caps changed together.

I cannot attribute the partisan-score change to a single cap. I cannot conclude that greater movement *caused* the efficiency-gap shift. A controlled one-at-a-time cap experiment would be needed to isolate those mechanisms.

\begin{figure}[H]
\centering
\includegraphics[width=.82\linewidth,height=.30\textheight,keepaspectratio]{outputs/reports/stage4/figures/figure2_paired_seed_EG.pdf}
\caption{Efficiency-gap endpoints indexed by the same 32 seed labels under the two cap regimes. Visualization generated by the project's Python/Matplotlib Stage 4 workflow from individually verified terminal maps. Seed pairing is an indexing device; it does not imply paired Markov transitions.}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=.82\linewidth,height=.30\textheight,keepaspectratio]{outputs/reports/stage4/figures/figure3_spatial_change_vs_EG.pdf}
\caption{Endpoint efficiency gap against the proportion of precinct nodes reassigned from the enacted map after optimal label matching. Visualization generated by the project's Python/Matplotlib Stage 4 workflow; 64 independently verified endpoints. Neither axis establishes legal-map validity or a causal mediation effect.}
\end{figure}

An additional enacted-reference comparison illustrates why the outcome needs careful naming. Sixteen of 32 closer-condition endpoints and thirteen of 32 relaxed-condition endpoints had an efficiency gap at least as large as the enacted reference overlay. Those frequencies describe the fixed-horizon code under a fixed starting state. Calling either a gerrymandering p-value would be unjustified.

# 6. An Adversarial Evidence Ledger

What should a researcher provide before interpreting a simulated ensemble? I propose three checks, with failure evidence preserved instead of concealed.

**Gate A: geographic provenance.** Identify the exact processed data and legal adjacency convention; enumerate disconnected components and exceptional edges; independently measure the actual geometry of every repair; test whether reference districts become connected because the benchmark labels influenced graph construction. The Michigan historical repair fails the independence question.

**Gate B: identifiable target and mixing evidence.** State the probability law the transition method purports to sample. Specify random-number initialization, independent starts, convergence diagnostics and effective sample size. A proof of local detailed balance does not compensate for empirical confinement. The tested ReCom and MH configurations failed this gate.

**Gate C: assumption sensitivity.** Hold what can be held constant, vary consequential geography and constraint choices, and disclose signed effect sizes with uncertainty based on genuinely independent computational units. The finite-horizon Michigan comparison reveals a model-choice effect, although its three caps change jointly.

The executed code includes a record of parameters, seed identities, expected input graph bytes, SHA-256 derived-graph and terminal-map fingerprints, reproducible scoring checks, deliberately rejected corrupt records, and a source-linked figure-generation path. These checks let another researcher reject certain substituted inputs and inconsistent outputs. They do not make the experiment immune to researcher discretion.

The same logic applies to the visualizations. They come from specific score and GIS artifacts; a reader should be able to recover what data produced each figure. Yet a passing GitHub Actions job verifies *configured software checks*, not the substantive neutrality of the result. I use the term **adversarial evidence ledger** for a documented collection of both successful tests and failure conditions.

# 7. Scope of the Audit and Boundaries of Inference

This paper does not establish the neutral probability distribution of legally admissible Michigan districts. The KNN3 graph is an experimental proximity model. The fragmentation caps are numerical proxies rather than a complete implementation of Michigan law. Voting Rights Act considerations, communities of interest and detailed official shoreline rules have not been independently certified in the simulation.

The vote overlays apply 2016 or 2020 presidential preferences to a plan adopted in 2021. Presidential precinct totals cannot reproduce candidate-specific congressional voting, incumbency or subsequent turnout. The original local election joins were not independently reconstructed from every raw input. Nor was every intermediate MCMC assignment separately rescored: the audit checked all retained terminal maps and specified periodic saved maps.

The final cap choices followed exploratory pilot work. They were fixed before the reported 64-endpoint aggregation but were not externally preregistered. Only 32 terminal maps inform each finite-horizon mean, and the comparison changes three fragmentation caps at once. These limitations delimit the estimand. They do not erase the measured change between the implemented procedures.

The Missouri overlay is a follow-up candidate, not a second-state result. Testing geographic contamination across a systematic sample of states would be the natural next experiment.

# 8. Conclusion

A simulation can be completely reproducible and still fail to justify the baseline it claims to represent. My Michigan audit documents three separable questions: Were the artificial geographic connections independently defensible? Did the Markov chain adequately explore a specified target? Did the measured outcomes remain stable when important geographic assumptions changed?

For this pipeline, the historical graph repair depended on the enacted plan and inserted connections spanning 42–280 km. The tested stationary-sampler configurations failed diagnostic gates. A deliberately narrower, finite-horizon experiment detected a +0.03278 tighter-minus-relaxed mean efficiency-gap contrast with a paired-bootstrap interval excluding zero.

I do not infer that every redistricting study makes these errors. I infer that no ensemble should acquire statistical authority merely from its size, reproducibility, or use of a nominally nonpartisan algorithm. Geography defines the possible maps. The sampler determines how they are weighted. Researcher choices shape both. Each part requires evidence.

The proposed standard is practical: publish an adversarial computational ledger, and refuse to call an ensemble a neutral baseline until its particular inferential claims survive geographic, sampling and sensitivity checks.

# 9. Methodological Derivation and Algorithm-Validation Annex

## 9.1 Detailed balance for a local proposal graph

Let $C$ be a communicating component of the finite set of feasible labeled district assignments under fixed geographic model $G$ and cap regime $c$. Let $q(x,y)$ denote the actual proposal probability of selecting $y$ from $x$, including the multiplicity of boundary-edge orientations that lead to the same map. The implemented acceptance rule is

$$
\alpha(x,y)=\min\!\left(1,\frac{q(y,x)}{q(x,y)}\right).
$$

For distinct $x,y\in C$ with positive forward and reverse proposal probabilities, take the uniform candidate invariant law $\pi(x)=1/|C|$. Then

$$
\pi(x)q(x,y)\alpha(x,y)
=\frac{\min\{q(x,y),q(y,x)\}}{|C|}
=\pi(y)q(y,x)\alpha(y,x).
$$

Holding self-loops absorb invalid proposals and rejections. These identities establish detailed balance for the specified local transition operator, assuming the stated finite model and correct implementation of $q$. Exact enumeration on a small graph checked the implemented rule. It **does not** establish whether all feasible assignments form one communicating class, whether a practical chain mixes adequately, or whether the conditional uniform law is an appropriate legal neutral-map distribution. The proposal is also distinct from Cannon et al.'s spanning-tree-based reversible ReCom law.

## 9.2 Rejection-accounting diagnostic

In one closer-cap pilot of 2,000 attempted steps, the sequential validation ledger recorded 635 population failures, 602 contiguity failures, 547 geographic-proxy failures, 32 MH acceptance failures and 184 accepted moves; their total is exactly 2,000. Failure categories describe the implementation's *ordering* of checks and do not isolate the marginal effect of each constraint.

## 9.3 Researcher contribution record

Implementation decisions, code provenance, source datasets, experimental parameters, and the roles of any collaborators or tools can be examined against the repository's documented workflow and commit history. The derivation above establishes detailed balance for the specified model; it does not establish overall irreducibility, legally valid topology, or finite-horizon equilibrium.

\newpage
\pagenumbering{gobble}

# References


Cannon, Sarah, Moon Duchin, Dana Randall, and Parker Rule. 2026. “Spanning Trees and Redistricting: New Methods for Sampling and Validation.” *SIAM Review* 68 (2): 349–381. https://doi.org/10.1137/24M166944X.

Chikina, Maria, Alan Frieze, and Wesley Pegden. 2017. “Assessing Significance in a Markov Chain without Mixing.” *Proceedings of the National Academy of Sciences* 114 (11): 2860–2864. https://doi.org/10.1073/pnas.1617540114.

DeFord, Daryl, Moon Duchin, and Justin Solomon. 2021. “Recombination: A Family of Markov Chains for Redistricting.” *Harvard Data Science Review* 3 (1). https://doi.org/10.1162/99608f92.eb30390f.

Kenny, Christopher T., Cory McCartan, Tyler Simko, Shiro Kuriwaki, and Kosuke Imai. 2023. “Widespread Partisan Gerrymandering Mostly Cancels Nationally, but Reduces Electoral Competition.” *Proceedings of the National Academy of Sciences* 120 (25): e2217322120. https://doi.org/10.1073/pnas.2217322120.

McCartan, Cory, Christopher T. Kenny, Tyler Simko, George Garcia III, Kevin Wang, Melissa Wu, Shiro Kuriwaki, and Kosuke Imai. 2022. “Simulated Redistricting Plans for the Analysis and Evaluation of Redistricting in the United States.” *Scientific Data* 9. https://doi.org/10.1038/s41597-022-01808-2.

Michigan Constitution of 1963, art. IV, § 6(13). Michigan Legislature. https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6.

Stephanopoulos, Nicholas O., and Eric M. McGhee. 2015. “Partisan Gerrymandering and the Efficiency Gap.” *University of Chicago Law Review* 82 (2): 831–900. https://chicagounbound.uchicago.edu/uclrev/vol82/iss2/4/.

Vehtari, Aki, Andrew Gelman, Daniel Simpson, Bob Carpenter, and Paul-Christian Bürkner. 2021. “Rank-Normalization, Folding, and Localization: An Improved R-hat for Assessing Convergence of MCMC.” *Bayesian Analysis* 16 (2): 667–718. https://doi.org/10.1214/20-BA1221.

Veomett, Ellen, with Arbie Hsu and Alusi. “Michigan JSON and Shapefile” (processed precinct GIS, election and population data; source README and notebook). Source materials obtained from the Redistricting Data Hub, June 2024. https://github.com/eveomett-states/Michigan. CC BY-NC 4.0 and applicable Redistricting Data Hub conditions.

