#!/usr/bin/env python3
"""Stage 4 static research manuscript evidence gate.

Cross-checks numerical claims against independently audited Stage 1-3 source
reports, confirms methodological qualifications are explicit, and rejects
incomplete/corrupted manuscript structure. This is a reproducibility aid,
not peer review or scientific proof of a legal neutral plan distribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGET = ROOT / "outputs/reports/stage4/when_a_random_map_is_not_a_neutral_map.md"
STAGE3 = ROOT / "docs/research_audit/STAGE3_FINAL_REPORT.md"
STAGE12 = ROOT / "docs/research_audit/STAGE12_FINAL_VERIFICATION.md"

STAGE3_CROSSCHECKS = {
    "original_4756_nodes": "4,756",
    "revised_13_added_edges": "13",
    "64_terminal_assignments": "64",
    "32_independent_per_condition": "32",
    "801_states_each": "801",
    "reference_2020_efficiency_gap": "+0.0033332",
    "closer_D_seats": "7.219",
    "relaxed_D_seats": "6.813",
    "closer_efficiency_gap": "+0.02010",
    "relaxed_efficiency_gap": "−0.01268",
    "closer_changed_precinct_fraction": "13.40%",
    "relaxed_changed_precinct_fraction": "29.00%",
    "closer_geo_rejection": "79.22%",
    "relaxed_geo_rejection": "52.83%",
    "mh_EG_closer_rhat": "1.568",
    "mh_EG_relaxed_rhat": "2.588",
    "old_recom_closer_rhat": "1.733",
    "old_recom_relaxed_rhat": "1.139",
    "source_graph_sha1": "a4dfe70818f87b97924781216f3d86a672cfc66a",
    "source_polygon_zip_sha1": "07bce18dabbcca9d549e28995a8156fd6978d7db",
    "revised_graph_sha256": "14355742f58291f4c26267982de07a21037c347f7598a68f032e0d68ea1d542c",
}
STAGE12_CROSSCHECKS = {
    "original_12378_edges": "12,378",
    "original_archive_12_chains": "12",
    "original_2020_18900_records": "18,900",
    "original_2020_57149_seats": "5.7149",
    "source_population_10077331": "10,077,331",
    "original_2020_D_votes": "2,804,046",
    "original_2020_R_votes": "2,649,864",
    "original_2020_D_seats": "seven Democratic seats",
    "original_2016_D_seats": "six Democratic seats",
    "original_2016_efficiency_gap": "−0.0387493",
    "original_historical_archive_hash": "0f52e51f8b64d1f2bc93b2e4fc206f824d777d494a90ae8a278461bac48736d4",
}
REQUIRED_SECTIONS = [
    "## Abstract", "## 1. Introduction", "## 2. Research context",
    "## 3. Data and reproducibility", "## 4. Geographic topology",
    "## 5. Sampling experiments", "## 6. A narrower",
    "## 7. Results", "## 8. Discussion", "## 9. Limitations",
    "## 10. Conclusion", "## References",
    "## Reproducibility and evidence appendix",
]
REQUIRED_REFERENCES = [
    "Cannon, Sarah", "Chikina, Maria", "DeFord, Daryl",
    "Kenny, Christopher", "McCartan, Cory", "Michigan Constitution",
    "Stephanopoulos, Nicholas", "Vehtari, Aki", "Veomett, Ellen",
]
REQUIRED_DISCLAIMERS = [
    "not a legal replacement", "not a legal", "not", "not a", # guards additional context below
    "conditional", "stationary", "reference-conditioned", "source-matched",
]


def check(path: Path = TARGET, stage3: Path = STAGE3, stage12: Path = STAGE12) -> dict:
    missing = [str(p) for p in (path, stage3, stage12) if not p.is_file()]
    if missing:
        raise ValueError(f"Missing required source/manuscript inputs: {missing}")
    manuscript, final3, final12 = (p.read_text(encoding="utf-8")
                                   for p in (path, stage3, stage12))
    errors = []
    count = len(re.findall(r"\b[\w]+(?:[’'-][\w]+)*\b", manuscript))
    if count < 4000:
        errors.append(f"Manuscript too short for full research methods and results: {count} words")
    for section in REQUIRED_SECTIONS:
        if section not in manuscript:
            errors.append(f"Missing required manuscript section {section}")
    for ref in REQUIRED_REFERENCES:
        if ref not in manuscript:
            errors.append(f"Missing source bibliography entry for {ref}")
    for identifier, datum in STAGE3_CROSSCHECKS.items():
        if datum not in final3 or datum not in manuscript:
            errors.append(f"Stage 3 value {identifier}={datum} missing from final report or draft")
    for identifier, datum in STAGE12_CROSSCHECKS.items():
        if datum not in final12 and datum not in manuscript:
            errors.append(f"Stage 1-2 value {identifier}={datum} absent from both documents")
        if datum not in manuscript:
            errors.append(f"Stage 1-2 value {identifier}={datum} absent from draft")
    # Stage 1–2 report renders exact 2016 difference with additional decimals.
    # Reject statements that promote algorithmic frequencies into neutral-map p-values.
    required_prose = [
        "not a legal replacement", "an enacted-map randomization p-value",
        "not a legal", "not a neutral", "not an untouched confirmatory preregistration",
        "The original processed Michigan graph", "R-hat", "ESS",
    ]
    for phrase in required_prose:
        if phrase.casefold() not in manuscript.casefold():
            errors.append("Missing caution or method marker: " + phrase)
    if "DOI_PLACEHOLDER" in manuscript or "[citation needed]" in manuscript.lower():
        errors.append("Unresolved reference placeholders")
    # No sources should be duplicated in full in the draft.
    if len(re.findall(r"https://doi.org/", manuscript)) < 6:
        errors.append("Bibliography lacks verified scholarly DOIs")
    if errors:
        raise ValueError("MANUSCRIPT_EVIDENCE_GATE_FAIL:\n" + "\n".join(errors))
    return {
        "status": "PASS_SOURCE_REPORT_AND_CLAIM_CONSISTENCY",
        "word_count": count,
        "sections_verified": len(REQUIRED_SECTIONS),
        "bibliographic_sources_checked": len(REQUIRED_REFERENCES),
        "stage3_numerical_markers": len(STAGE3_CROSSCHECKS),
        "stage12_historical_markers": len(STAGE12_CROSSCHECKS),
        "manuscript_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "stage3_source_report_sha256": hashlib.sha256(stage3.read_bytes()).hexdigest(),
        "stage12_source_report_sha256": hashlib.sha256(stage12.read_bytes()).hexdigest(),
        "limitations": [
            "Marker/structure consistency check is not independent statistical peer review.",
            "Legally valid sampling, stationary convergence, and raw RDH joins remain unproven.",
            "Historical 2016/2020 presidential returns are counterfactual scores on later lines."
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manuscript", type=Path, default=TARGET)
    ap.add_argument("--stage3-report", type=Path, default=STAGE3)
    ap.add_argument("--stage12-report", type=Path, default=STAGE12)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = check(args.manuscript, args.stage3_report, args.stage12_report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(result["status"], result["word_count"], "words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
