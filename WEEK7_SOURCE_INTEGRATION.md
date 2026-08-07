# Week 7 Source Integration Patch

This patch strengthens the final paper and deck by explicitly cross-referencing four uploaded sources:

1. Guest, Kanayet, and Love (2019), computational redistricting and explicit criteria.
2. Stephanopoulos (2017), efficiency gap, causes, consequences, and representation.
3. Kenny et al. (2023), simulated nonpartisan baselines and competition effects.
4. Bouton et al. (2024), turnout heterogeneity and pack-crack-pack limitations.

Run the normal Week 7 build commands after installing the patch:

```bash
python scripts/build_week7_deliverables.py --name mi_2020 --state-name Michigan --election-label "2020 presidential election"
python scripts/build_week7_paper_docx.py --name mi_2020
python scripts/build_week7_deck.py --name mi_2020 --state-name Michigan --election-label "2020 presidential election"
```

The paper now includes a literature-positioning section, source-to-project crosswalk, stronger limitations, and bibliography.
The deck now includes a research-context slide connecting the project to the uploaded literature.
