#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REQUIRED = [
    "README.md",
    "PROJECT_STATUS.md",
    "docs/week1_methodology.md",
    "docs/week2_mathematics.md",
    "docs/week3_mathematics.md",
    "docs/week4_markov_chains.md",
    "docs/week5_outlier_analysis.md",
    "docs/week6_stress_tests.md",
    "outputs/reports/week7/mi_2020_final_paper.md",
    "outputs/reports/week7/mi_2020_final_paper.docx",
    "outputs/slides/week7/mi_2020_talk.pptx",
]


def main() -> None:
    missing = [p for p in REQUIRED if not Path(p).exists()]
    if missing:
        print("Missing required Week 7 deliverables:")
        for p in missing:
            print(f"  - {p}")
        raise SystemExit(1)
    print("Week 7 repo audit passed.")


if __name__ == "__main__":
    main()
