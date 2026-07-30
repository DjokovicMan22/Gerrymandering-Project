# Week 2 — The geometry of compactness

## Metrics implemented

- **Polsby–Popper** = 4πA / P²
- **Reock** = area / area of smallest enclosing circle
- **Convex-hull ratio** = area / area of convex hull

## Core lesson

Compactness metrics do not measure the same geometric defect. Polsby–Popper is extremely sensitive to perimeter inflation, Reock punishes elongated districts because the enclosing circle grows, and convex-hull ratio mostly punishes concavity while ignoring some boundary wiggles.

## Michigan

- **Polsby–Popper**: highest = District 7 (0.536); lowest = District 1 (0.035)
- **Reock**: highest = District 12 (0.573); lowest = District 5 (0.191)
- **Convex-hull ratio**: highest = District 7 (0.891); lowest = District 1 (0.488)

## Missouri

- **Polsby–Popper**: highest = District 7 (0.522); lowest = District 3 (0.138)
- **Reock**: highest = District 4 (0.528); lowest = District 6 (0.300)
- **Convex-hull ratio**: highest = District 7 (0.906); lowest = District 3 (0.637)

## Stress test interpretation

- **Long thin rectangle** → PP = 0.236, Reock = 0.112, hull ratio = 1.000. Hull ratio stays high, but Polsby–Popper and Reock punish elongation.
- **Smooth coastline-hugger** → PP = 0.431, Reock = 0.297, hull ratio = 0.887. Follows a wavy edge; perimeter grows while hull remains similar.
- **Jagged coastline / fractal-ish boundary** → PP = 0.235, Reock = 0.269, hull ratio = 0.970. Polsby–Popper drops sharply because perimeter explodes.
- **Simple square** → PP = 0.785, Reock = 0.637, hull ratio = 1.000. Reference shape: compact under all three metrics.

## Resolution / coastline paradox note

The jagged coastline example shows why Polsby–Popper is resolution-dependent: adding more boundary detail increases perimeter without necessarily changing area very much. That can sharply lower Polsby–Popper even when the overall district footprint looks similar.

## Validation note

If you later pull published values from Dave’s Redistricting App for the same districts, you can compare them directly against the CSV outputs generated here.
