# Stages 1–2 — independent verification and bounded completion report

**Decision:** **CLOSED for original-source identification, historical numeric reanalysis, reference-plan score verification, and compactness cross-checks.** The separate, stronger goals of reproducing the *exact original stochastic trajectories*, reconstructing all raw Census/VEST joins, and certifying Michigan legal geography **remain unverified**. Do not silently mark those as passed.

**Audit date:** 18 October 2026 (19 October UTC GitHub Actions).  
**Research branch:** `research/stages-1-3-validation`; default `main` not modified.  
**Authoritative successful Stage 1–2 workflow:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183710341  
**Standard regression suite:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183617102 (**80 passing synthetic/adversarial tests**).  
**Stage 3 final result:** [STAGE3_FINAL_REPORT.md](STAGE3_FINAL_REPORT.md).

## What changed from the original Stage 1 and 2 audits

The original October 17/18 reports were written against an August 2026 source snapshot that lacked raw precinct inputs and the scripts needed to rerun the original archived data. Those reports remain accurate **as historical assessments of that snapshot**. The current research branch has now completed additional independently executed checks, including the full original archived ZIP (checked into the repository) and the independently downloaded, immutable-hash-matched Michigan source graph and original source polygon ZIP.

### Stage 1: source and compactness evidence

| Check | Independent method and result | Status |
|---|---|---|
| Michigan original graph identity | Source file `mi.json` downloaded from Veomett's published repository, verified Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a` before use | **PASS** |
| Source polygon archive identity | Original `mi.zip` independently downloaded and verified Git blob `07bce18dabbcca9d549e28995a8156fd6978d7db` | **PASS** |
| Census / graph integrity | **4,756 precinct nodes**, **12,378 original edges**, **10,077,331 residents**, **13 reference districts**, source numeric field checks | **PASS for processed-source graph** |
| Polygon–graph matching | One-to-one 4,756-row source-attribute alignment from the original source-matched geometry audit; no unsupported arbitrary index join | **PASS** |
| Actual source coordinate system | Independently inspected original precinct shapefile CRS **EPSG:32616** | **PASS** |
| Week 2 Polsby–Popper | Dissolved original polygons by reference district and recomputed areas/perimeters and `4πA/P²` using an independent implementation; compared with all 13 saved district rows | **13/13 PASS** |
| Week 2 convex-hull ratio | Independently recomputed convex hull areas and `A / hull_area` from original polygons | **13/13 PASS** |
| Week 2 Reock | Independently computed minimum enclosing radius using **GEOS/Shapely `minimum_bounding_radius`**, *not* the project's randomized enclosing-circle routine, then scored `A / (πr²)` | **13/13 PASS**, within declared 0.01% relative numerical tolerance |
| Michigan upstream data lineage | Recorded Veomett authorship, 2020 Census, 2021 adopted congressional assignment, VEST 2016/2020, upstream RDH dataset links, processing notebook, SHA-1 Git blobs and licensing | **DOCUMENTED** |
| Missouri upstream data lineage | Recorded Missouri candidate graph/ZIP/notebook hashes and upstream data sources | **DOCUMENTED; historical local input NOT byte-matched** |
| Official state election canvass and raw join recreation | Original raw RDH Census/VEST releases not independently rejoined or reconciled to official statewide totals | **NOT VERIFIED** |
| Michigan official island/water/municipality/VRA/COI legality | Polygon proximity and graph contiguity do not prove statutory admissibility | **NOT VERIFIED** |

The Stage 1 data provenance stub and empty source register were replaced with [documented source provenance](../data_provenance.md) and [source index](../data_sources.md). Third-party original input files remain excluded from newly published CI output artifacts.

### Stage 2: original archived history and source-based scoring

**Original checked-in archive:** `strong_paper_review_packet.zip`, SHA-256  
`0f52e51f8b64d1f2bc93b2e4fc206f824d777d494a90ae8a278461bac48736d4`.

The new `stage12_archive_reanalysis.py` independently reads the original ZIP *in memory*, checks its 12 named archived chain CSVs for missing files, malformed/duplicate steps, missing or nonfinite metrics, invalid district counts and population-tolerance violations, and records each chain's SHA-256. It does not depend on the archived project's saved summary tables.

| Condition | Independent chain count | Post-burn-in **correlated observations** | Mean D seats | Mean efficiency gap | Observations meeting ±0.5% population tolerance |
|---|---:|---:|---:|---:|---:|
| Michigan 2016 presidential layer, ±2% | 3 | 18,900 | 4.672646 | −0.142474 | 0 |
| Michigan 2020 presidential layer, ±2% | 3 | 18,900 | 5.714921 | −0.099919 | **0** |
| Michigan 2020 presidential layer, ±1% | 3 | 8,100 | 5.716296 | −0.099539 | **4** |
| Michigan 2020 presidential layer, ±3% | 3 | 8,100 | 5.925679 | −0.084097 | **0** |

All **three seed-matched 2016/2020 archived chain pairs** have exactly identical 7,000-step cut-edge and population-deviation time series. This is **paired geographic scoring**, not six independent geographic runs. The 2020 reference seat-count inclusive upper tail is **2,633/18,900 = 13.9312%**, whereas its midrank is 92.5185%; these are different statistics because of ties. The efficiency-gap inclusive upper-tail count is **742/18,900**. None of these empirical frequencies is a legally neutral redistricting p-value.

**Independent source-based scoring:** `stage12_reference_crosscheck.py` aggregates the exact pinned source graph's precinct votes into the **13 enacted districts**, computes both elections' seat counts, mean–median scores, and wasted-vote efficiency gaps without invoking the original GerryChain updaters, and checks all **six archived 2016/2020 step-zero plan rows**. It separately checks **all 26 original Week 3 district rows** for district vote counts, Democratic shares and winners.

The independently scored reference has **7 Democratic seats and EG +0.003333205 (2020 presidential votes)** and **6 Democratic seats and EG approximately −0.03874928 (2016 presidential votes)**. These are counterfactual scores of a later 2021/2022-cycle districting plan, not election outcomes from those years under that plan.

**Detected one-vote 2016 floating-point issue:** Some processed 2016 precinct allocations are fractional. The original code uses `floor((D+R)/2)+1` for each district's winning threshold. Summing fractional precinct values in different orders can move a district total just across an integer boundary, changing one district's wasted-vote threshold by **one vote**. Independent 2016 EG `−0.038749278029653667` and one archived step-zero EG `−0.038749497891198` differ by approximately **2.20×10⁻⁷**, one vote divided by the statewide two-party total. The source reconciliation **records exact differences and enforces at most one vote's worth of 2016 EG tolerance**, rather than declaring bitwise equality or concealing the discrepancy. The 2020 EG is checked more strictly. This rounding ambiguity does not rescue the invalid stationary/legal-ensemble inference.

### Runtime safeguards and tests

- `src/redistricting/ensemble/partition.py` now rejects missing, negative, nonnumeric, NaN and infinite source population/election values, as well as zero-two-party-vote reference districts.
- `tests/test_stage12_audit.py` adds adversarial CSV-corruption and source-field tests.
- The regular `research-audit.yml` CI includes those tests and passed **80 tests**.
- The independent `stage12-reproducibility.yml` workflow passed **both jobs**: source/archived numeric verification and independent polygon compactness; its own adversarial subset passed **19 tests**.
- CI preserves derived JSON manifests and comparison scores as run artifacts. It does **not** republish the original third-party graph/polygon files.

### Evidence links and executable reproduction

- [Complete successful Stage 1–2 source, archive and geometry workflow](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183710341)
- [Passing 80-test synthetic and adversarial research audit](https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39183617102)
- `scripts/research_audit/stage12_archive_reanalysis.py` — exact original ZIP, 12 chain CSVs, hashes, tied-rank arithmetic, tolerance overlap and election pairing.
- `scripts/research_audit/stage12_reference_crosscheck.py` — independently aggregated precinct reference, six archive references, 26 Week 3 district rows.
- `scripts/research_audit/stage12_compactness_crosscheck.py` — original source ZIP, all 13 district compactness values, independent GEOS Reock.
- `scripts/research_audit/verify_graph.py` and `download_source.py` — source byte checks and processed graph input integrity.
- `docs/data_provenance.md` — dataset URLs, upstream processing and limits.

Reproduce with the workflow's pinned source URLs and license acknowledgement. The complete original archived ZIP is already in the repository, so the Stage 2 numeric check can run without retrieving a private research packet.

## What is and is not finished

**Finished:** The remaining executable Stage 1–2 checks supported by the public processed inputs and the saved original packet: source identity, source/polygon matching, 13-district compactness metrics, all 12 archived histories, paired-election geography, six independently scored reference plans, 26 saved district election rows, strict source-field gates, and the new automated regression suite.

**Not possible to establish from the archived files:** bit-for-bit recreation of every original 7,000-step chain transition or independent rescoring of all archived intermediate maps, because those historic outputs preserve only plan-level scalar metrics, not every complete precinct assignment, and the historic GerryChain RNG seeds were not correctly applied to its chain-owned generator. These limitations are **permanent for those specific historical runs unless the missing original assignments/complete RNG states are recovered**. The Stage 3 separately seeded, source-checked simulations are a new experiment, not retroactive validation of the old trajectories.

**Not a software-only checkbox:** independently recreate all original raw RDH Census/VEST joins, authoritative water/island topology, county/municipal definitions, communities of interest, VRA opportunity districts, and state-law admissibility. Those require authoritative source data, documented legal decisions and domain validation. Until then, the study is a **reproducible methods and geographic-sensitivity experiment**, not a legal-map gerrymandering significance test.

**Stage 4 handoff:** Proceed to a carefully scoped methods/sensitivity paper, cite the negative convergence evidence and this audit, and do not characterize the historic 18,900 correlated observations as 18,900 independent, equally likely legally acceptable maps.
