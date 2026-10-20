# Stage 4 — literature audit, manuscript revision, and submission-readiness review

**Date:** 18 October 2026 Pacific (GitHub CI timestamps 19 October UTC).  
**Research branch:** `research/stages-1-3-validation`; original `main` unchanged.  
**Current manuscript:** [When a Random Map Is Not a Neutral Map](../../outputs/reports/stage4/when_a_random_map_is_not_a_neutral_map.md).  
**Reading/submission PDF:** [15-page searchable typeset PDF](../../outputs/reports/stage4/when_a_random_map_is_not_a_neutral_map.pdf).

## 19 October 2026 publication-layout update

**Current authoritative paper:** [The Phantom Baseline — 16-page XeLaTeX PDF](../../outputs/reports/stage4/phantom_baseline.pdf) and [fully editable `.tex` source](../../outputs/reports/stage4/phantom_baseline.tex). The prior title and 15-page/three-figure description below refer to the original review draft; they are superseded by this update. The revised paper contains **four source-backed figures** (one real GIS topology map and three endpoint statistics plots), **three `booktabs` tables**, **four numbered math displays**, and a three-gate diagnostic protocol. The [final passing typesetting and scientific input audit](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39359458520) rendered **16 searchable pages**. Original graph and ZIP blob hashes were rechecked during topology rendering, all five historic project-added edges were measured from polygons, and source-score digests were reconciled before statistical plotting. This is a model-fragility study rather than legal-plan probability inference; external scholarly review is still required.

## 1. Revision completed

The manuscript now contains the full research argument and supporting material:

- An explicit separation between **computational reproducibility**, **geographic/legal model validity**, **stationary sampling** and **finite-horizon algorithmic inference**.
- A formally defined finite-time estimand `Q_{c,T}` conditional on the reference plan, experimental proximity graph, chosen geographic caps and exactly 800 recorded transitions.
- A complete account of the negative convergence results, including the two distinct proposals for which formal target-law arguments and observed movement did not coincide.
- Independence of the actual analysis unit: **one terminal map per each of 32 separately seeded chains per geographic condition**, rather than all correlated intermediate states.
- Three publication-style **SVG+PNG** figures made from the archived **original 64 independently validated terminal-map rows**, not hand-coded plot approximations. **All three are in the manuscript and PDF.**
- A secondary **paired-seed, 20,000-replicate bootstrap**, conditional on the fixed seed-indexed experimental design (32 pairs). Across the same 32 seed labels, tighter minus relaxed caps produced differences in conditional mean efficiency gap **+0.032778** (95% interval **[+0.009748,+0.056309]**), seats **+0.40625** (interval **[+0.124,+0.719]**), cut edges **−63.75** (interval **[−80.06,−46.91]**), and precincts reassigned **−15.606 percentage points** (interval **[−17.79,−13.50]**).
- A separate bibliographic source check and an explicit account of remaining scientific limits.

**These confidence intervals are NOT neutrality tests or proof of partisan gerrymandering.** They quantify sensitivity of **two exploratory, reference-anchored 800-transition procedures** that differ in **multiple caps simultaneously**. The same seed label need not imply the same Markov proposal sequence or geographic map correspondence.

## 2. Publisher- and primary-source bibliography check

The following manuscript references were checked against publisher, academic or primary-source metadata. Citation wording was compared with the listed sources. These references concern **methodology and legal criteria**, not new measurements of the analyzed Michigan map.

| Bibliography entry | Verified primary metadata | Scope used in manuscript |
|---|---|---|
| Cannon, Duchin, Randall & Rule, **2026**, *Spanning Trees and Redistricting: New Methods for Sampling and Validation* | [SIAM Review 68(2), 349–381; published online 13 May 2026; DOI 10.1137/24M166944X](https://epubs.siam.org/doi/10.1137/24M166944X) | Published reversible recombination and its **specific** stationary-law assumptions; does not certify our tuning pilot or legal Michigan graph. |
| Chikina, Frieze & Pegden, **2017**, *Assessing Significance in a Markov Chain without Mixing* | [PNAS 114(11), 2860–2864; DOI 10.1073/pnas.1617540114](https://pmc.ncbi.nlm.nih.gov/articles/PMC5358383/) | Special theoretical tests that do not require generic mixing *under a specified null and reversibility*. Not applied here; one cannot label our endpoint proportions their significance test. |
| DeFord, Duchin & Solomon, **2021**, *Recombination: A Family of Markov Chains for Redistricting* | [Harvard Data Science Review 3.1; DOI 10.1162/99608f92.eb30390f](https://hdsr.mitpress.mit.edu/pub/1ds8ptxu/release/4) | ReCom proposals and the need to specify graph, constraints and transition mechanism. |
| Kenny, McCartan, Simko, Kuriwaki & Imai, **2023**, *Widespread Partisan Gerrymandering Mostly Cancels Nationally, but Reduces Electoral Competition* | [PNAS 120(25): e2217322120; DOI 10.1073/pnas.2217322120](https://pubmed.ncbi.nlm.nih.gov/37310996/) | Credible state-specific baseline comparison under separately justified methods; **not** evidence our simplified caps are equivalent. |
| McCartan, Kenny, Simko, Garcia III, Wang, Wu, Kuriwaki & Imai, **2022**, *Simulated Redistricting Plans for the Analysis and Evaluation of Redistricting in the United States* | [Scientific Data 9:689; DOI 10.1038/s41597-022-01808-2](https://www.nature.com/articles/s41597-022-01808-2) | Demonstrates extensive state-level data engineering, legal-criterion modeling and validation that our Michigan sensitivity proxy has not completed. |
| Stephanopoulos & McGhee, **2015**, *Partisan Gerrymandering and the Efficiency Gap* | [University of Chicago Law Review 82(2), 831–900](https://chicagounbound.uchicago.edu/uclrev/vol82/iss2/4/) | Wasted-vote efficiency-gap definition and interpretation, without treating it as self-sufficient evidence of law violation. |
| Vehtari, Gelman, Simpson, Carpenter & Bürkner, **2021**, *Rank-Normalization, Folding, and Localization: An Improved R-hat for Assessing Convergence of MCMC* | [Bayesian Analysis 16(2), 667–718; DOI 10.1214/20-BA1221](https://research.aalto.fi/en/publications/rank-normalization-folding-and-localization-an-improved-r-hat-for/) | Motivation for rank R-hat and bulk/tail ESS diagnostics, as **diagnostics** rather than proofs of stationarity. |
| Michigan Constitution of 1963, article IV §6(13) | [Michigan Legislature's official operative text](https://legislature.mi.gov/Laws/MCL?objectName=mcl-Article-IV-6) | Ranked legal redistricting criteria including population/federal law, county-linked islands and contiguity, communities, partisan fairness, incumbent neutrality, county/city/township consideration and compactness. |
| Veomett, Hsu & Alusi, original processed Michigan graph and polygons | [Veomett Michigan repository and data processing notebook](https://github.com/eveomett-states/Michigan) | Processed precinct source; 2020 Census, 2016/2020 VEST presidential voting, 2021-adopted congressional map; separately pinned exact graph and ZIP Git blobs. |

**Citation discipline:** The precise official source indicates that the ranked criteria are legally important; this does not permit characterizing model-generated KNN3 maps as legally valid. The manuscript is independent writing summarizing methodologies, not a reproduction of any paper's text.

## 3. Original evidence and figures: reproducibility chain

| Layer | Verifiable evidence | Status |
|---|---|---|
| Source/archived mathematics | [Stage 1–2 official audit](STAGE12_FINAL_VERIFICATION.md) and [fully passing source/compactness workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183949679) | PASS within processed-source scope |
| Earlier proposal and convergence diagnosis | [Stage 3 reversible and ReCom diagnostic audit](STAGE3_FINAL_REPORT.md) | Negative results correctly preserved |
| Original 64 endpoint assignments | [Successful independent-seed experiment](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39180152601) | PASS within finite-horizon proxy model |
| Empirical figures and paired differences | [Figure source workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39203727983), `stage4_make_figures.py`; source score artifact hash `beba3320c3ae73bbbab192e797faaac629a4dd5bb30d098ff6d1123c25a2e32c` | Three SVG+PNG figures PASS; committed to research branch |
| Paper text and numeric-claim gate | [Stage 4 manuscript evidence audit](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39203675742), `stage4_verify_manuscript.py` | PASS for source-numeric markers and required limits |
| Searchable academic PDF | [Typeset PDF and visual first/last page preflight](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39204046502), `stage4_render_pdf.py` | **15 pages**, all three figures embedded, searchable text, no blank pages, source SHA-256 recorded |

The PDF and Markdown are two renderings of the **same full manuscript**, not two separate substantive submissions. Figures were archived both in their editable **generator source code** and in rendered vector/raster output; the original source polygon data were **not** redistributed in paper artifacts. An actions/checkout-generated PDF is not a substitute for a professional copyeditor or external peer review.

## 4. Simulated peer review: strongest objections and responses

**Objection 1 — “The KNN3 construction is not a legal Michigan adjacency graph.”**  
*Response:* Correct. It is labeled as a district-blind *local edge-selection rule* whose overall K parameter was chosen after checking reference connectivity. It cannot support substantive legal or neutral-map claims. Any future legal-ensemble paper must build official shoreline/island/county adjacency and encode the higher-priority legal conditions. **Status: unremedied, scientifically material for original legal hypothesis.**

**Objection 2 — “A finite-horizon reference-anchored sampler is not a neutral null distribution.”**  
*Response:* Correct. The paper does not claim it is. It defines an algorithm-conditional estimand and reports only the observed computational sensitivity, with no enacted-map p-value. The historical stationary-sampling hypothesis is a negative result. **Status: addressed by bounded claims, not by establishing a neutral target.**

**Objection 3 — “The closer and relaxed regimes change several constraints at once.”**  
*Response:* Correct. The paired mean differences **cannot** be assigned causally to county, MCD or boundary cuts individually. The paper describes them as contrasts between *composite algorithmic regimes*. **Status: explicitly limited.**

**Objection 4 — “Only 32 endpoints per regime; does pairing increase effective sample size?”**  
*Response:* No. Exactly **32** independently seeded terminal outcomes per regime and **32** matched seed identifiers inform the bootstrap; 51,264 correlated intermediate states were not treated as independent replicates. Paired intervals are conditional Monte Carlo summaries, not guarantees about different model configurations. **Status: finite-sample precision qualified.**

**Objection 5 — “The historic ReCom chains had a broken RNG seed procedure.”**  
*Response:* Yes. The original chain-specific generator was not seeded correctly, and the ZIP preserves scalar history rather than full map assignments. Numeric archive reproduction and source-based step-zero checks pass, but original trajectories cannot be replayed. The newer 64-run experiment independently seeds and replays chain-owned RNG streams. **Status: historic limitation preserved; new experiment reproducible.**

**Objection 6 — “A paper about an implementation failure could be mistaken for a result about gerrymandering.”**  
*Response:* The abstract, title, model section, result captions, discussion and conclusion consistently distinguish computational output from legal neutral-map inference. The *contribution* is a tested audit and bounded sensitivity analysis, not a Michigan partisan-liability finding. **Status: addressed in framing; domain reviewers should still assess contribution and venue fit.**

## 5. Remaining work before external submission

The manuscript is now a complete, evidence-reconciled **~6,600-word Markdown research draft**, and its **15-page PDF with figures** passed automated export checks. Before sending to journals or research competitions, obtain:

1. **Independent methodological feedback** on whether the finite-horizon sensitivity result constitutes a publishable methodological contribution and on the assumptions of paired-seed uncertainty. A statistics mentor or redistricting methods researcher should review it.
2. **Native structural copyediting** for formal citations, table references, source captions, equation display, and any target venue's word/figure/style requirements. The pipeline currently validates markers and source links; it does not prove a professional citation manager has checked every context.
3. **Clear source and license statements** for the original processed precinct data and GIS, preserving the CC BY-NC and RDH attribution/use restrictions.
4. For a **different**, stronger claim about legally valid Michigan maps: official polygon/island/municipal/VRA/COI reconstruction plus a scientifically justified target law and adequate convergence. This is **not necessary to accurately submit the present bounded methods study**, but would be necessary to change its conclusions.

**Current scientific decision:** the empirical calculations, derived figures, and PDF are reproducible and documented. **Stage 4 has a strong complete draft; external peer review and venue-specific preparation are still pending.** Any statement that the work *proves* intentional, illegal or statistically significant Michigan gerrymandering would exceed the evidence.
