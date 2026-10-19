#!/usr/bin/env python3
"""Reproducible manuscript-to-XeLaTeX conversion: genuine numbered equations and floats."""
from __future__ import annotations
import argparse
import re
import subprocess
from pathlib import Path

COVER=r"""
\begin{center}
{\fontsize{17.2}{20}\selectfont\bfseries The Phantom Baseline\par}
\vspace{5pt}
{\fontsize{11.2}{14}\selectfont Geographic Assumptions, Mixing Failures, and Constraint Sensitivity
in Computational Redistricting\par}
\vspace{9pt}
{\footnotesize Research methods and computational sensitivity study \enspace$\cdot$\enspace October 2026\par}
\end{center}
\vspace{5pt}
"""
TABLE_1=r"""
\begin{table}[H]
\centering
\caption{Terminal outcomes after 800 recorded transitions under two exploratory geographic regimes.}
\label{tab:endpoints}
\begin{threeparttable}
\footnotesize
\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}X
>{\raggedleft\arraybackslash}p{0.287\linewidth}
>{\raggedleft\arraybackslash}p{0.287\linewidth}@{}}
\toprule
Outcome & Tighter constraints & Relaxed constraints\\
\midrule
Democratic seats & 7.219 [7.000, 7.438] & 6.813 [6.594, 7.031]\\
Efficiency gap & +0.02010 [+0.00300, +0.03722] &
$-0.01268$ [$-0.03036$, +0.00458]\\
Cut edges, KNN3 graph & 695.09 [686.00, 703.75] & 758.84 [746.66, 771.16]\\
Split source county groups & 17.97 [17.91, 18.00] & 23.81 [23.63, 23.97]\\
Split county--MCD groups & 19.94 [19.84, 20.00] & 47.94 [47.50, 48.34]\\
Reassigned precincts (\%) & 13.40 [12.05, 14.81] & 29.00 [27.75, 30.29]\\
\bottomrule
\end{tabularx}
\begin{tablenotes}[flushleft]
\footnotesize
\item \emph{Note.} Means and 95\% percentile bootstrap intervals from 32 independently seeded
terminal maps per condition. The 2020 presidential-vote overlay is counterfactual.
The proximity graph and fragmentation caps are not certified as Michigan legal rules.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
TABLE_2=r"""
\begin{table}[H]
\centering
\caption{Paired-seed terminal contrasts: tighter minus relaxed conditions.}
\label{tab:paired}
\begin{threeparttable}
\footnotesize
\begin{tabularx}{\linewidth}{@{}>{\raggedright\arraybackslash}X
>{\raggedleft\arraybackslash}p{0.18\linewidth}
>{\raggedleft\arraybackslash}p{0.31\linewidth}@{}}
\toprule
Terminal outcome & Mean difference & 95\% bootstrap interval\\
\midrule
Democratic seats & +0.406 & [+0.124, +0.719]\\
Efficiency gap & +0.03278 & [+0.00975, +0.05631]\\
KNN3 cut edges & $-63.75$ & [$-80.06$, $-46.91$]\\
Reassigned precincts (pp) & $-15.61$ & [$-17.79$, $-13.50$]\\
\bottomrule
\end{tabularx}
\begin{tablenotes}[flushleft]
\footnotesize
\item \emph{Note.} 32 seed-indexed pairs; 20,000 bootstrap resamples.
pp denotes percentage points. The regimes alter several caps simultaneously.
The contrasts are neither legal-map neutrality tests nor isolated causal effects.
\end{tablenotes}
\end{threeparttable}
\end{table}
"""
FIGURES={
1:("figure1_terminal_EG_ECDF",.90,
"Empirical cumulative distributions of efficiency gap under tighter and relaxed model constraints (32 independently seeded endpoints per regime). The vertical reference marker is the enacted plan under the same 2020 presidential-vote overlay; this is not a legal-map outlier test."),
2:("figure2_paired_seed_EG",.71,
"Efficiency-gap scores by shared seed identifier across the two regimes. The dashed diagonal marks equal values. Shared seed numbers do not imply identical proposals or matched geographic plans."),
3:("figure3_spatial_change_vs_EG",.90,
"Endpoint efficiency gap versus the fraction of precincts reassigned from the enacted reference after optimal label matching. Candidate geography is defined by the experimental proximity graph."),
}
def require(ok,msg):
    if not ok:raise ValueError(msg)
def prepare(s:str)->str:
    require(s.startswith("# The Phantom Baseline:"),"Unexpected manuscript title")
    k=s.find("\n## Abstract")
    require(k>0,"No abstract")
    s=COVER+"\n"+s[k:]
    s=s.replace("## Abstract\n\n",r"\begin{abstract}"+"\n",1)
    pos=s.index("**Keywords:**")
    s=s[:pos]+r"\end{abstract}"+"\n\n"+s[pos:]
    s=s.replace("**Keywords:**",r"\noindent\textbf{Keywords.}",1)
    s=s.replace("\n---\n","\n\n")
    s=re.sub(r"(?m)^## \d+\.\s+","## ",s)
    s=re.sub(r"(?m)^### \d+\.\d+\s+","### ",s)
    s=s.replace("### Figures: exact, independently checked endpoint data",
                "### Original-data figures {.unnumbered}")
    s=s.replace("## References","## References {.unnumbered}",1)
    s=s.replace("## Reproducibility and evidence appendix",
                r"\clearpage"+"\n"+r"\appendix"+"\n\n"+
                "## Reproducibility and evidence appendix",1)
    eq_count=0
    def equation(m):
        nonlocal eq_count
        eq_count+=1
        return "\n"+r"\begin{equation}"+"\n"+m.group(1).strip()+"\n"+r"\end{equation}"+"\n"
    s=re.sub(r"(?ms)^\$\$\s*\n(.*?)\n\$\$\s*$",equation,s)
    require(eq_count==4,f"Expected four display equations; found {eq_count}")
    a=s.find("**Table 1.")
    b=s.find("### Original-data figures {.unnumbered}",a)
    require(a>0 and b>a and "| Democratic seats" in s[a:b],"Table 1 marker mismatch")
    s=s[:a]+TABLE_1+"\n\n"+s[b:]
    a=s.find("**Table 2.")
    b=s.find("The paired bootstrap uses the joint seed-indexed",a)
    require(a>0 and b>a and "| Democratic seats" in s[a:b],"Table 2 marker mismatch")
    s=s[:a]+TABLE_2+"\n\n"+s[b:]
    for n,(stem,width,caption) in FIGURES.items():
        pattern=rf"(?ms)^!\[Figure {n}:.*?\]\(figures/{stem}\.svg\)\s*?\n\*\*Figure {n}\.\*\* [^\n]*"
        found=list(re.finditer(pattern,s))
        require(len(found)==1,f"Figure {n} not found once")
        fig=(r"\begin{figure}[H]"+"\n"+r"\centering"+"\n"+
             rf"\includegraphics[width={width:.2f}\linewidth]{{figures/{stem}.pdf}}"+"\n"+
             r"\caption{"+caption+"}\n"+rf"\label{{fig:stage4-{n}}}"+"\n"+r"\end{figure}")
        s=s[:found[0].start()]+fig+s[found[0].end():]
    mark="## References {.unnumbered}"
    s=s.replace(mark,mark+"\n\n"+r"\begingroup\small"+
                "\n"+r"\setlength{\parindent}{0pt}"+
                "\n"+r"\setlength{\parskip}{5pt}"+
                "\n"+r"\begin{hangparas}{1.25em}{1}",1)
    ix=s.index(r"\clearpage"+"\n"+r"\appendix")
    s=s[:ix]+r"\end{hangparas}"+"\n"+r"\endgroup"+"\n\n"+s[ix:]
    # Remove source-only editorial emphasis from academic typesetting.
    # Journal manuscripts should not scatter bold prose or show literal ** in abstracts.
    s=re.sub(r"\*\*(.+?)\*\*", r"\1",s)
    # The abstract is wrapped in a raw TeX environment. A literal percent
    # would comment out everything following it on the TeX input line;
    # escape it explicitly rather than silently truncate the contribution.
    abstract_start=s.index(r"\begin{abstract}")
    abstract_end=s.index(r"\end{abstract}",abstract_start)
    abstract=s[abstract_start:abstract_end].replace("%",r"\%")
    s=s[:abstract_start]+abstract+s[abstract_end:]
    # Avoid orphaned/unnumbered internal plotting section above figures.
    s=s.replace("### Original-data figures {.unnumbered}","")
    # The paper title is a TeX cover, not a numbered Markdown heading.
    # Shift section headings down one Markdown level so Pandoc produces
    # Section 1, Section 2, ... instead of Subsection 0.1, 0.2, ... .
    s=re.sub(r"(?m)^(#{2,4})(?= )",
             lambda m:"#"+m.group(1)[2:],s)
    # Allow immutable source hashes to wrap without overflowing text margins.
    s=re.sub(r"`([0-9a-f]{40,64})`",
             lambda m:r"\texttt{\seqsplit{"+m.group(1)+"}}",s)
    require(s.count(r"\begin{figure}[H]")==3 and s.count(r"\begin{table}[H]")==2,
            "Missing academic tables or figures")
    return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manuscript",type=Path,required=True)
    p.add_argument("--header",type=Path,required=True)
    p.add_argument("--prepared",type=Path,required=True)
    p.add_argument("--tex",type=Path,required=True)
    a=p.parse_args()
    a.prepared.parent.mkdir(parents=True,exist_ok=True)
    a.tex.parent.mkdir(parents=True,exist_ok=True)
    a.prepared.write_text(prepare(a.manuscript.read_text(encoding="utf-8")),encoding="utf-8")
    cmd=["pandoc",str(a.prepared),
         "--from=markdown+tex_math_dollars+raw_tex+pipe_tables+fenced_code_blocks",
         "--to=latex","--standalone","--number-sections",
         "--metadata=lang:en-US",
         "--variable=fontsize:10pt",
         "--variable=mainfont:STIX",
         "--variable=mathfont:STIX Math",
         "--variable=geometry:top=0.78in,bottom=0.78in,left=0.86in,right=0.86in",
         "--include-in-header",str(a.header),
         "--resource-path",str(a.manuscript.parent),
         "--output",str(a.tex)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stderr[-3500:])
    latex=a.tex.read_text(encoding="utf-8")
    require(latex.count(r"\begin{equation}")>=4,"No proper numbered equations")
    require(latex.count(r"\begin{figure}")>=3,"Missing LaTeX vector figures")
    require(latex.count(r"\begin{table}")>=2,"Missing LaTeX booktabs tables")
    require(r"\begin{hangparas}" in latex,"Missing bibliography hanging indents")
    print("STAGE4_PHANTOM_LATEX_SOURCE_PASS",len(latex),"bytes",
          latex.count(r"\begin{equation}"),"equations",
          latex.count(r"\begin{table}"),"tables")
if __name__=="__main__":main()
