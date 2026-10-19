# Data provenance and source limitations

**Audit updated:** 2026-10-18 (source repositories inspected; archived experiment provenance is separate).  
**Scope:** Explicitly distinguish *identified upstream source*, *byte-matched processed graph*, *polygon-attribute cross-check*, *independently recreated raw Census/VEST joins*, and *legally certified plan geometry*. These are not equivalent.

## Source lineage shared by Michigan and Missouri

Professor Ellen Veomett and collaborators Arbie Hsu and Alusi published processed precinct shapefiles and GerryChain-style JSON graphs. Their README states that they obtained underlying Census redistricting, approved congressional-plan, and VEST precinct election layers from the [Redistricting Data Hub](https://redistrictingdatahub.org/) **in June 2024**, processed with [maup](https://github.com/mggg/maup), and modified small rook adjacencies (under 30.5 m) to queen adjacencies. Source data are covered by **CC BY-NC 4.0** and applicable [RDH attribution/use conditions](https://redistrictingdatahub.org/terms-and-conditions/). Neither a byte-identical processed graph nor a spatial alignment test proves the upstream raw-file join was independently reconstructed.

## Michigan — source identified and processed inputs independently checked

| Item | Recorded provenance |
|---|---|
| Published processed source | [Veomett et al., Michigan repository](https://github.com/eveomett-states/Michigan), README [metadata](https://github.com/eveomett-states/Michigan/blob/main/README.md) |
| Source processing notebook | [mi.ipynb](https://github.com/eveomett-states/Michigan/blob/main/mi.ipynb), Git blob `d4f615c70fbc9766dd5a772c6e86a2e20aea83d2` |
| Processed graph | [mi.json](https://github.com/eveomett-states/Michigan/blob/main/mi.json), pinned Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`, 7,651,302 bytes |
| Processed polygon archive | [mi.zip](https://github.com/eveomett-states/Michigan/blob/main/mi.zip), pinned Git blob `07bce18dabbcca9d549e28995a8156fd6978d7db`, 23,063,942 bytes |
| Dataset vintages | 2020 Census population; 2020 precinct geography; **2021 adopted congressional district** field `CD` (used from 2022 onward); VEST 2016 and 2020 presidential votes |
| District field | `CD` (13 congressional districts) |
| Population field | `TOTPOP` |
| Election fields | `PRE16D`, `PRE16R`, `PRE20D`, `PRE20R` (two-party presidential votes) |
| Geographic identifiers | `PRECINCT20` (precinct), `COUNTYFP20` (county), `cousubname20` (county subdivision; spelling/casing must be checked) |
| Geometry / coordinate system | Source polygon archive has been matched to the processed graph on 4,756/4,756 node records by population, congressional district and county; the original precinct shapefile's declared CRS was independently inspected as **EPSG:32616** in the source-matched Stage 1 geometry workflow. |
| Byte-verification method | `scripts/research_audit/download_source.py --acknowledge-source-terms` checks exact Git blob before saving; `verify_graph.py` audits all nodes and vote/population values. Original geometry ZIP separately pinned and source-attribute checked by the Stage 3 geometry audit. |
| Reconciled reference facts | 4,756 nodes; 12,378 original graph edges; 10,077,331 census population; 13 reference districts; max reference population deviation ~0.4019%; 2020 two-party presidential totals D=2,804,046, R=2,649,864 (from **processed** source graph, not independently official statewide totals) |
| Original graph disconnected components | 6 components, including geographically separate islands/precinct groups. The old code added **five arbitrary same-district bridges**; the revised Stage 3 KNN3 proximity model uses 13 district-blind candidate edges but remains **not a legally certified island/water connectivity graph**. |
| Raw upstream layers | [2020 Michigan census block PL 94-171](https://redistrictingdatahub.org/dataset/michigan-block-pl-94171-2020-by-table/), [2021 approved congressional plan](https://redistrictingdatahub.org/dataset/2021-michigan-congressional-districts-approved-plan/), [VEST 2016](https://redistrictingdatahub.org/dataset/vest-2016-michigan-precinct-and-election-results/), [VEST 2020](https://redistrictingdatahub.org/dataset/vest-2020-michigan-precinct-boundaries-and-election-results-shapefile/) |

**What was independently verified:** processed JSON source-byte identity, graph integrity, population and election-field finiteness/nonnegativity, precinct/polygon attribute alignment, 13-district reference scores and alternative adjacency geometry sensitivity (see [Stage 3 final report](research_audit/STAGE3_FINAL_REPORT.md)). **What was not independently verified:** rerunning all original 2020 block-to-precinct/VEST joins from original RDH releases, comparison to authoritative state-certified statewide election canvass, legal geography and Voting Rights Act compliance. The project must not silently substitute the KNN3 approximation for official adjacency.

## Missouri — upstream identified; exact local source use unverified

| Item | Recorded provenance |
|---|---|
| Published processed source | [Veomett et al., Missouri repository](https://github.com/eveomett-states/Missouri), [README](https://github.com/eveomett-states/Missouri/blob/main/README.md) |
| Processing notebook | [mo.ipynb](https://github.com/eveomett-states/Missouri/blob/main/mo.ipynb), Git blob `e1ed6dadf2e04813ede496178eec2d77c4e34e12` |
| Candidate processed graph | [mo.json](https://github.com/eveomett-states/Missouri/blob/main/mo.json), Git blob `664fee342977536065d0cf30ef0faff52631999d`, 6,095,571 bytes |
| Candidate polygon ZIP | [mo.zip](https://github.com/eveomett-states/Missouri/blob/main/mo.zip), Git blob `54703611c400c0d6da13e040c2dc1fc79fe4a6c0`, 33,588,861 bytes |
| Data vintage | 2020 Census; **2022 approved Missouri congressional plan** (field `CD`); 2016 and 2020 VEST presidential returns |
| Relevant fields | `CD`, `TOTPOP`, `PRE16D`, `PRE16R`, `PRE20D`, `PRE20R` |
| Processing caveat | Missouri source explicitly **nested precincts within counties**, unlike Michigan; both changed small rook adjacencies to queen adjacencies |
| Original raw sources | [2020 Missouri census blocks](https://redistrictingdatahub.org/dataset/missouri-block-pl-94171-2020-by-table/), [2022 approved congressional plan](https://redistrictingdatahub.org/dataset/2022-missouri-congressional-districts-approved-plan/), [VEST 2016](https://redistrictingdatahub.org/dataset/vest-2016-missouri-precinct-and-election-results/), [VEST 2020](https://redistrictingdatahub.org/dataset/vest-2020-missouri-precinct-and-election-results/) |

**Missouri status:** source URLs and candidate hashes are documented, but the original project's missing local Missouri inputs have **not** been byte-matched to this candidate, and Missouri has **not** undergone the Michigan Stage 3 ensemble validation. Do not present Missouri as a replicated second-state experiment.

## How to reproduce and check the exact Michigan processed input

```bash
python scripts/research_audit/download_source.py --acknowledge-source-terms
python scripts/research_audit/verify_graph.py \
  --graph data/raw/mi/mi/mi.json \
  --expected-git-blob a4dfe70818f87b97924781216f3d86a672cfc66a \
  --expected-nodes 4756 --expected-population 10077331 \
  --output outputs/research_audit/stage12_verified_graph.json
```

The downloader writes a separate `.provenance.json` manifest containing the actual **retrieval UTC time**, exact Git blob and SHA-256. This document's audit date is not a claim that every source was downloaded that day. Preserve generated manifests alongside research results; do not redistribute third-party graph/polygon bytes without checking their license and terms.

**Important:** The 2016/2020 presidential returns are applied **counterfactually to a 2021/2022-cycle congressional plan**. These are not observed 2016/2020 congressional seat outcomes. The older August paper should be read in that context.
