# Corrected Stage 3 explicit-RNG Michigan warm-start diversity results

**Authoritative deterministic-RNG all-seed CI run:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162240056  
**Smoke replay confirming process-independent exact reproduction:** https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162110048  
**Important historical RNG erratum:** [stage3_rng_reproducibility_erratum.md](stage3_rng_reproducibility_erratum.md).

## Design

GerryChain 1.0.0's `MarkovChain` receives `rng=seed` **directly**, unlike the historical studies. Graph source SHA is pinned. The same eight warm seeds (101, 202, 303, 404 per condition), 800 states including enacted step 0, ±0.5% population deviation, ReCom and self-loop geographic caps are used. District labels are optimally permuted before comparing every final map.

The 5% label-invariant difference threshold, required both between each endpoint and reference and between all six pairs within a condition, **passed in both conditions**. This is auditable finite-time spatial separation, not stationarity, independence of draws from the legal-plan distribution or uniformity of ReCom sampling.

## Corrected results

| Condition | Distance from enacted reference | Pairwise warmup-endpoint distance | Geographic rejection fraction | Distance gate |
|---|---:|---:|---:|---|
| Closer (caps 760,18,20) | **10.77–17.03%** | **10.09–18.04%** | **71.71–78.60%** | PASS |
| Relaxed (caps 850,24,49) | **28.01–41.23%** | **23.91–39.82%** | **50.06–59.57%** | PASS |

### Seeded starts from the tighter geographic condition

| Seed | SHA-256 exact starting-map assignment | Reference distance | Graph cuts | Split counties | Split county+MCD |
|---|---|---:|---:|---:|---:|
| 101 | `a1cb09ace3596f11531170c14d8ed18a125d0acd7404cccb15df61956ddfa910` | 17.03% | 731 | 18 | 19 |
| 202 | `1bfdc79ef1ed8862cb1ac03bbcfe9cae02ba923128c9784dce56cc050b9112e0` | 10.77% | 715 | 18 | 20 |
| 303 | `a9b814df23174fe527663ad7716f1a1eb7cb9d7c5fa442583110841f574a3f57` | 14.76% | 660 | 18 | 20 |
| 404 | `a03356fe60f4e8dd6ce5a3a43aba1cd124c93e452d4f482b7543e8e78be999ee` | 12.80% | 699 | 17 | 20 |

Six exact pairwise fraction differences, sorted by seed pair (101-202,101-303,101-404,202-303,202-404,303-404): **18.04%, 13.20%, 10.43%, 17.94%, 15.54%, 10.09%**.

### Seeded starts from the relaxed geographic condition

| Seed | SHA-256 exact starting-map assignment | Reference distance | Graph cuts | Split counties | Split county+MCD |
|---|---|---:|---:|---:|---:|
| 101 | `fa6d219689c0fe1d47c1306bfb10a81cea59c1dd150be27e4f480ded14cf4287` | 31.48% | 789 | 24 | 49 |
| 202 | `031abb8e1e1d7fdd58ea39193482c9d87da34b062646d7fcb24eb5c3e563cdf8` | 41.23% | 745 | 24 | 49 |
| 303 | `0c8bf4b74a734f175cbaf61423f6630cd4736fb376b094f5c55198f55821e452` | 28.01% | 690 | 24 | 48 |
| 404 | `7b8a3989e54ec9cc9dd30824db727bd365e9fca2c7e1ec57cad24c6712c7fb2b` | 28.03% | 748 | 24 | 48 |

Six exact pairwise fraction differences (101-202,101-303,101-404,202-303,202-404,303-404): **39.82%, 30.64%, 23.91%, 30.61%, 38.02%, 25.95%**.

## Cross-process replay

In addition to the 8-seed analysis, **seed 101** in *both* geographic conditions was regenerated in separate Python processes, followed by an independently seeded 101-state sampler with `sample_seed=1101`. The complete plan-metric CSVs matched byte-for-byte, and independent reruns had identical warm-start SHA, final-state summary, and distance measurements. Each saved sampling map passed precinct, contiguity, population, split-proxy and election-score validation.

This study is the **current authoritative warm-start identity** for the following longer production run. The preceding [historic warmup report](stage3_warm_start_diversity_results.md) remains available for provenance but its seeds were not properly passed to GerryChain, so its hashes should not be substituted for these.

## Scientific limitations

The 5% condition was a research-defined diversity cutoff, not evidence of a stationary distribution. All warmups still share the enacted reference ancestor, and strict geographic caps have high rejection rates. Distances are precinct counts after relabeling, not area/population-weighted distances; the five artificial graph bridges remain physically unverified; county+MCD keys are not certified legal municipality polygons. VRA/community-of-interest constraints and a stationary or uniform target law remain unverified.

The corrected production sampler will use these *exact* warm hashes as a provenance gate, rather than silently accepting a different initial state with the same declared seed.
