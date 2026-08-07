# Michigan Gerrymandering Ensemble Analysis

**Question:** Is the enacted congressional map an outlier relative to neutral alternatives?

---

# Why sampling?

- A map is a constrained graph partition.
- Real precinct graphs have thousands of nodes.
- Enumeration is impossible, so the project uses MCMC sampling.

---

# Metrics before ensembles

- Compactness: Polsby–Popper, Reock, convex-hull ratio.
- Partisan metrics: efficiency gap, mean–median, seats.
- Key lesson: single metrics can mislead.

---

# ReCom ensemble

- Merge adjacent districts.
- Re-split with a random spanning tree.
- Enforce contiguity and population balance.
- Three chains × 7,000 steps; 700 burn-in per chain.

---

# Signature outlier result

Insert figure:

`outputs/figures/week5/mi_2020_signature_outlier_panel.png`

---

# Sorted-district structure

Insert figure:

`outputs/figures/week5/mi_2020_sorted_districts.png`

Shows packing/cracking structure beyond aggregate seat counts.

---

# Stress tests

Insert figures:

`outputs/figures/week6/mi_2020_constraint_percentiles.png`

`outputs/figures/week6/mi_2020_geography_baseline.png`

---

# Conclusion and limits

- The result is conditional on data, graph model, and constraints.
- Ensemble percentile is not automatically a legal conclusion.
- Main value: transparent, reproducible measurement.
