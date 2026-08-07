# Week 7 Revision v3 — stronger paper and presentation

This patch replaces the weak Week 7 draft with a much more evidence-driven paper and deck.

## Install

```bash
mv ~/Downloads/gerrymandering_week7_strong_revision_patch.zip .
unzip -o gerrymandering_week7_strong_revision_patch.zip
rm gerrymandering_week7_strong_revision_patch.zip
python -m pip install -e .
python -m pip install python-docx python-pptx tabulate
pytest -q
```

## Build the stronger deliverables

```bash
python scripts/build_week7_deliverables.py \
  --name mi_2020 \
  --state-name Michigan \
  --election-label "2020 presidential election"

python scripts/build_week7_paper_docx.py --name mi_2020

python scripts/build_week7_deck.py \
  --name mi_2020 \
  --state-name Michigan \
  --election-label "2020 presidential election"
```

## Open outputs

```bash
open outputs/reports/week7/mi_2020_final_paper.md
open outputs/reports/week7/mi_2020_final_paper.docx
open outputs/reports/week7/mi_2020_talk_script.md
open outputs/slides/week7/mi_2020_talk.pptx
```

## What changed

- Stronger hypothesis and evidentiary standard.
- Clear executive result.
- More evidence tables from Week 4, 5, and 6.
- Explicit claim ladder: what the analysis supports and does not support.
- Better explanations of ensemble logic, diagnostics, sorted-district plots, and geography baseline.
- Stronger limitations and counterargument section.
- 15-slide deck with an evidence-first narrative.

The result is still a draft. You should manually revise the interpretation paragraphs after reading the actual figures and tables.
