# Week 3 mathematics and limitations

## Efficiency-gap sign convention

The code defines

\[
EG=\frac{W_R-W_D}{T},
\]

where \(W_R\) and \(W_D\) are Republican and Democratic wasted votes and \(T\) is total two-party turnout. Under this convention, a positive value indicates more Republican wasted votes and therefore an advantage to Democrats. State this convention every time results are presented because other sources reverse the sign.

## Derivation of the equal-turnout shortcut

Let there be \(n\) districts, each with the same turnout \(t\). Let \(s\) be the Democratic number of seats and \(S=s/n\) its seat share. Let \(D\) be total Democratic votes and \(V=D/(nt)\) Democratic vote share.

Ignoring the one-vote integer correction, a winning party wastes its votes beyond \(t/2\), while a losing party wastes all its votes.

Across Democratic-won districts, Democratic wasted votes equal Democratic votes minus \(t/2\) per win. Across Democratic-lost districts, all Democratic votes are wasted. Thus

\[
W_D=D-\frac{st}{2}.
\]

Republican total votes are \(nt-D\). Republicans win \(n-s\) seats, so

\[
W_R=(nt-D)-\frac{(n-s)t}{2}.
\]

Subtracting and dividing by \(nt\):

\[
\begin{aligned}
EG
&=\frac{W_R-W_D}{nt}\\
&=\frac{nt-D-(n-s)t/2-D+st/2}{nt}\\
&=\frac{st-2D+nt/2}{nt}\\
&=S-2V+\frac12.
\end{aligned}
\]

## Assumptions and failure modes

The shortcut depends on equal district turnout, a two-party vote model, an approximately half-turnout winning threshold, and the project's declared sign convention. Actual turnout differences reweight districts, so statewide vote share and seat share no longer reproduce exact wasted-vote arithmetic. The code therefore reports both values and their difference.

Mean–median difference measures asymmetry in district vote shares, not intent. It can be near zero for a map with consequential packing and cracking, and it can be nonzero because of residential geography. Seats–votes disproportionality can likewise arise without line manipulation. These metrics should be treated as diagnostics whose meaning is conditional on the state's geography and election data.

## Election choice

The current sensitivity analysis uses 2016 and 2020 presidential results. This satisfies a multi-election comparison but does not measure actual congressional-candidate behavior. Presidential data offer complete statewide coverage and avoid uncontested House races, while congressional data may better reflect district-specific candidates, incumbency, and campaign effects. The paper must state this tradeoff explicitly.

## External validation protocol

For one state-election pair, manually cross-check statewide vote share, district winners, efficiency gap, and mean–median against an independent implementation using the same map and election. Record differences and confirm that sign conventions match before comparing efficiency gaps.
