# Data sources and licenses

The **authoritative provenance record** for this research branch is [data_provenance.md](data_provenance.md). It documents upstream dataset links, vintages, verified Git blobs, election-field meanings, geographic preprocessing, and unresolved source-reconstruction gaps.

- **Michigan processed JSON / precinct geometry:** [Veomett et al. Michigan](https://github.com/eveomett-states/Michigan); graph Git blob `a4dfe70818f87b97924781216f3d86a672cfc66a`, polygon ZIP Git blob `07bce18dabbcca9d549e28995a8156fd6978d7db`.
- **Missouri processed data (candidate, not byte-matched to historical local data):** [Veomett et al. Missouri](https://github.com/eveomett-states/Missouri); graph Git blob `664fee342977536065d0cf30ef0faff52631999d`, polygon ZIP `54703611c400c0d6da13e040c2dc1fc79fe4a6c0`.
- **Original data providers:** [Redistricting Data Hub](https://redistrictingdatahub.org/) for 2020 Census, 2021/2022 congressional boundaries and 2016/2020 VEST presidential precinct election returns.
- **Data licensing:** [Creative Commons Attribution–NonCommercial 4.0](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en) plus applicable [Redistricting Data Hub use and attribution terms](https://redistrictingdatahub.org/terms-and-conditions/). Do not assume third-party inputs can be republished freely.
- **Source graph acquisition:** `python scripts/research_audit/download_source.py --acknowledge-source-terms` verifies Michigan source bytes before saving.
- **Research results and limitations:** [Stage 3 final report](research_audit/STAGE3_FINAL_REPORT.md).

**Scope:** Identifying and matching processed public inputs does **not** constitute independent reconstruction of all Census-to-precinct election joins, authoritative legal contiguity, VRA compliance or official election canvass reconciliation. All 2016/2020 presidential results on the adopted 2021/2022 congressional plans are **counterfactual scores**, not historical congressional seat counts.
