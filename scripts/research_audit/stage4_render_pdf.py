#!/usr/bin/env python3
"""Render the source-tracked Stage 4 manuscript into a searchable academic PDF.

Figures MUST exist in the development repository and were generated from the
source-pinned 64-map endpoint artifact. This is a layout/export validator, not
an assertion of external peer review or Michigan statutory legality.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import markdown
from pypdf import PdfReader
from weasyprint import CSS, HTML

CSS_PRINT = r"""
@page {
  size: letter;
  margin: 0.83in 0.82in 0.82in 0.82in;
  @bottom-center {
    content: "Page " counter(page);
    font-family: "Liberation Serif", "DejaVu Serif", serif;
    font-size: 8pt;
    color: #666666;
  }
  @top-right {
    content: "RESEARCH METHODS AND SENSITIVITY STUDY";
    font-family: "Liberation Sans", "DejaVu Sans", sans-serif;
    font-size: 7pt;
    letter-spacing: .05em;
    color: #666666;
  }
}
html {font-family:"Liberation Serif","DejaVu Serif",serif;color:#131a27}
body {font-size:10.35pt;line-height:1.39}
h1,h2,h3 {font-family:"Liberation Sans","DejaVu Sans",sans-serif;color:#10233d}
h1 {font-size:18pt;line-height:1.15;letter-spacing:-.025em;margin:0 0 .27in 0;
    page-break-after:avoid;font-weight:700}
h2 {font-size:12.3pt;line-height:1.25;margin:.22in 0 .085in 0;
    break-after:avoid;border-bottom:.6pt solid #bac3cf;padding-bottom:.045in}
h3 {font-size:10.5pt;line-height:1.25;margin:.17in 0 .075in 0;
    break-after:avoid;color:#213d5b}
p {margin:.075in 0 .10in 0;orphans:3;widows:3}
ul,ol {padding-left:.23in;margin:.09in 0 .11in 0}
li {margin:.04in 0}
hr {height:0;border:0;border-top:.5pt solid #cbd5e1;margin:.16in 0}
blockquote {border-left:2pt solid #9faabb;padding-left:.15in;color:#2d3748}
strong {font-weight:700}
em {font-style:italic}
table {border-collapse:collapse;table-layout:auto;width:100%;margin:.14in 0 .19in 0;
       font-family:"Liberation Sans","DejaVu Sans",sans-serif;font-size:8.0pt;
       break-inside:avoid}
thead {display:table-header-group}
th {font-weight:700;text-align:left;background:#edf1f4}
td,th {border-bottom:.5pt solid #d1d9e0;padding:.065in .045in;vertical-align:top}
tr {break-inside:avoid}
a {color:#27547b;text-decoration:none}
a:after {content:none}
img {max-width:100%;max-height:5.35in;height:auto;object-fit:contain;
     display:block;margin:.12in auto}
p:has(> img) {break-inside:avoid;margin:.12in 0 .035in 0}
p:has(> img)+p {font-size:9pt;color:#374151;break-before:avoid}
code {font-family:"Liberation Mono","DejaVu Sans Mono",monospace;
      font-size:8.6pt;overflow-wrap:anywhere}
pre {font-family:"Liberation Mono","DejaVu Sans Mono",monospace;
     font-size:8.5pt;background:#f3f5f7;padding:.095in;
     white-space:pre-wrap;break-inside:avoid}
pre code {font-size:8.5pt;overflow-wrap:normal}
"""

REQUIRED_FIGURES = [
    "figures/figure1_terminal_EG_ECDF.svg",
    "figures/figure2_paired_seed_EG.svg",
    "figures/figure3_spatial_change_vs_EG.svg",
]
REQUIRED_TEXT = [
    "When a Random Map Is Not a Neutral Map",
    "Geographic topology",
    "finite-horizon",
    "References",
    "32 independent",
    "0.03278",
    "Michigan",
]


def build(manuscript:Path,out:Path,manifest:Path)->dict:
    manuscript=manuscript.resolve()
    if not manuscript.is_file():
        raise FileNotFoundError(manuscript)
    text=manuscript.read_text(encoding="utf-8")
    for figure in REQUIRED_FIGURES:
        target=manuscript.parent/figure
        if not target.is_file() or target.stat().st_size<4000:
            raise ValueError(f"Missing unverified source-data figure: {figure}")
        if figure not in text:
            raise ValueError(f"Figure not integrated in manuscript Markdown: {figure}")
    if not all(x in text for x in REQUIRED_TEXT):
        raise ValueError("Input manuscript is missing required results/sections")
    html_body=markdown.markdown(
        text,extensions=["tables","fenced_code","toc","sane_lists"],output_format="html5")
    if html_body.count("<img ")!=len(REQUIRED_FIGURES):
        raise ValueError("Failed to embed all source-verified SVG figures in generated HTML")
    html=f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <title>When a Random Map Is Not a Neutral Map</title></head><body>
    {html_body}</body></html>"""
    document=HTML(string=html,base_url=manuscript.parent.as_uri()+"/").render(
        stylesheets=[CSS(string=CSS_PRINT)])
    out.parent.mkdir(parents=True,exist_ok=True)
    document.write_pdf(str(out))
    if out.stat().st_size<120000:
        raise ValueError("PDF suspiciously small; text or figures may be missing")
    reader=PdfReader(str(out))
    pages=len(reader.pages)
    if not 12<=pages<=60:
        raise ValueError(f"Unexpected academic manuscript pagination: {pages}")
    page_texts=[p.extract_text() or "" for p in reader.pages]
    combined="\n".join(page_texts)
    for fragment in REQUIRED_TEXT:
        if fragment not in combined:
            raise ValueError(f"Searchable PDF text does not contain {fragment}")
    if any(len(page.strip())<35 for page in page_texts):
        raise ValueError("Detected a blank or nearly blank typeset PDF page")
    metrics={
        "status":"PASS_MANUSCRIPT_SEARCHABLE_PDF_LAYOUT",
        "source_markdown_sha256":hashlib.sha256(manuscript.read_bytes()).hexdigest(),
        "pdf_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
        "pdf_bytes":out.stat().st_size,
        "page_count":pages,
        "source_figure_paths":REQUIRED_FIGURES,
        "all_three_figures_embedded":True,
        "no_nearly_blank_pages":True,
        "searchable_title_methods_and_results":True,
        "note":"Layout and artifact validation only; independent scientific/peer and legal-map review remains outstanding",
    }
    manifest.parent.mkdir(parents=True,exist_ok=True)
    manifest.write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    print("STAGE4_PDF_RENDER_PASS",json.dumps(metrics),flush=True)
    return metrics


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manuscript",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    args=p.parse_args()
    build(args.manuscript,args.output,args.manifest)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
