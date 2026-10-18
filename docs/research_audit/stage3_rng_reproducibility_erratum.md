# Stage 3 reproducibility erratum — GerryChain 1.0.0 random streams

**Discovered:** October 18, 2026 during independent Stage 3 sampling replay.  
**Provenance:** failed strict warmup-hash replay workflow https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39161790509; successful corrected replay workflow https://github.com/DjokovicMan22/Gerrymandering-Project/actions/runs/39162110048.

## What was wrong

The original simulation code passed `random.seed(seed)` and `numpy.random.seed(seed)` but did not pass the random seed into GerryChain 1.0.0's `MarkovChain` constructor. As of this version, **GerryChain owns its independent RNG** and `random.seed()` does not control it. Thus historical files labeled seed 101/202/etc. describe distinct observed trajectories but **DO NOT define exactly reproducible trajectories**. The exact old warmup hashes cannot be regenerated reliably from those integers.

Under identical input bytes and nominal seed 101, the first strict replay failed as follows:
- Closer historic endpoint hash `5b3887ca...`; rerun without a chain RNG `88eadb8c...`.
- Relaxed historic endpoint hash `0649670b...`; rerun without a chain RNG `60b36d01...`.

This is a **reproducibility limitation and metadata error**, not evidence of invalid arithmetic on the archived maps. Previous full 64k-state score histories, spatial-fragmentation profiles and 5%-diversity checks remain observational analyses of their archived generated states, but cannot claim a deterministic seed-based replay.

## Correction

1. Pass `rng=seed` to GerryChain's `MarkovChain` during warmup; `rng=config.seed` to the sampling-chain constructor.
2. Pin `gerrychain==1.0.0` in project dependencies and use `PYTHONHASHSEED=0` for CI consistency.
3. Run the exact same Michigan graph, warmup and sampling configuration twice in **independent Python processes**. Compare their complete plan-metric CSVs (byte for byte), warmup endpoint hashes and post-sample distance summaries. CI separately checks archived full snapshots.
4. Re-execute the all-seed warmup diversity matrix under the corrected RNG and record new hashes/distances. Do not compare old endpoint hash values to the corrected generator or merge old and corrected chain histories as though they share identical sampling trajectories.
5. For new independent seed-specific sample chains, use **different explicit warmup and sampling RNG seeds**; record source SHA, reference-score JSON, chain metadata and dependency versions.

Corrected paired smoke runs with warm seed 101 and sampling seed 1101 **passed in both geographic conditions**, each with 11 independently validated sampled assignments and matched archived scalar scores. The exact warmup hashes in the corrected runs were:
- Closer `a1cb09ace3596f11531170c14d8ed18a125d0acd7404cccb15df61956ddfa910`.
- Relaxed `fa6d219689c0fe1d47c1306bfb10a81cea59c1dd150be27e4f480ded14cf4287`.

These hashes are **corrected 800-state RNG-seeded outcomes**, and are not interchangeable with the old unseeded historic hashes.

## Continuing limitations

Seeding the RNG establishes **trajectory reproducibility**, not a proof of stationarity, irreducibility, reversibility, uniform district sampling or legality. Geographic-cap-invalid proposed states create holding self-loops. GerryChain ReCom itself is not established to have the intended uniform legal-map target under this custom constraint system. Island bridge edges and source municipal boundaries remain independently unverified.

For current evidence, use the later *explicit-chain-RNG* studies, not seed labels from the earlier runs.

**Authoritative implementation:** `src/redistricting/ensemble/start_diversity.py` and `src/redistricting/ensemble/chain.py`. GerryChain's current reproducibility guidance documents `MarkovChain(..., rng=2024)` and notes that Python-global `random.seed` does not affect GerryChain: https://pypi.org/project/gerrychain/.
