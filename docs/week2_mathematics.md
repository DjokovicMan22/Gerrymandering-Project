# Week 2 mathematics and limitations

## Compactness metrics

For district area \(A\) and perimeter \(P\), Polsby–Popper is

\[
PP=\frac{4\pi A}{P^2}.
\]

The isoperimetric inequality states

\[
P^2\ge 4\pi A,
\]

with equality only for a circle. Therefore \(0<PP\le1\) for a nondegenerate planar district. Polsby–Popper is the district's area divided by the area of a circle having the same perimeter.

A complete calculus-of-variations proof is beyond BC Calculus. The relevant optimization intuition is that, among shapes enclosing fixed area, boundary irregularity or elongation requires additional perimeter. Equivalently, among shapes with fixed perimeter, the circle encloses maximum area. The project should present this as a rigorous theorem with an optimization interpretation, not claim to derive the full theorem from elementary calculus.

Reock compactness is

\[
R=\frac{A}{\pi r_{\min}^2},
\]

where \(r_{\min}\) is the radius of the smallest enclosing circle. Convex-hull ratio is

\[
CH=\frac{A}{A_{\mathrm{hull}}}.
\]

The metrics penalize different geometric features. Polsby–Popper is highly sensitive to boundary length, Reock strongly penalizes geographic spread, and convex-hull ratio emphasizes indentations and disconnected or highly concave structure.

## Projection and resolution

Area and perimeter should be measured in a projected coordinate reference system, not longitude/latitude degrees. A projection still introduces distortion; record the CRS and avoid comparing values calculated under incompatible projections.

Polsby–Popper also depends on boundary resolution. Simplifying a boundary usually shortens its measured perimeter and may increase the score even though the political district has not changed. `scripts/week2_resolution_sensitivity.py` quantifies this effect by simplifying enacted district boundaries at several tolerances and recomputing all three metrics.

## External validation protocol

Select at least two districts per state, preferably one high-scoring and one low-scoring district. Record:

| State | District | Metric | Local value | External value | Difference | External source/date |
|---|---:|---|---:|---:|---:|---|
| Michigan |  | Polsby–Popper |  |  |  |  |
| Michigan |  | Reock |  |  |  |  |
| Missouri |  | Polsby–Popper |  |  |  |  |
| Missouri |  | Reock |  |  |  |  |

Values may differ because tools use different projections, boundary files, coastline treatment, or multipart geometry conventions. Explain discrepancies rather than forcing agreement.
