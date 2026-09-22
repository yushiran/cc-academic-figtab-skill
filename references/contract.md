# The figure contract

Every rule a figure of the paper obeys, as a number with its source. `academic_figure/contract.py` holds the same
values for code; this file holds the reasons. When the two disagree the code is wrong, and both are changed in
one commit.

The sources are accepted flagship figures measured from their PDFs or their page renders, never taste: He
Kaiming's MoCo, MAE, iMF, JiT, BNF and Drifting for type and restraint; DAPS (CVPR 2025 oral) for plots and
result grids; FlowDPS, CLAMP, DE-CM and AdaGen for the variants noted. Method diagrams drawn in Figma follow the
`academic-figure-figma` skill's `style-contract.md`, which shares this palette and these faces.

## 1. Size

| rule | value | source |
| --- | --- | --- |
| width | the venue's column or text width, exactly; CVPR 3.28125 in (236.25 pt) or 6.875 in (495 pt) | `cvpr.sty`; measure a new venue with `\typeout{\the\textwidth, \the\columnwidth}` |
| scaling in LaTeX | none: `\includegraphics{f.pdf}` with no `width=` | an 8 pt label drawn at default size and scaled to a column prints at 5 pt |
| page tolerance | at most 1.5 pt under the target, never over | over overflows the column; `save()` closes the gap by measurement |
| height | what the content needs: a plot 1.7 to 2.2 in at column width; a result grid is set by its panel side | DAPS Fig. 6 aspect 2.0 per panel |
| format | vector PDF; the PNG twin exists only to be read back | |

## 2. Type

| rule | value | source |
| --- | --- | --- |
| words | Arimo Regular, **6.5 pt, one size**: labels, ticks, legends, headers, numbers | median of 22 label sizes across 8 flagship papers, range 4.9 to 9.6 |
| symbols | Computer Modern (TeX `cmmi`, `cmr`, `cmsy`), **8 pt** | CM's x-height (0.43 em) at 8 pt matches Arimo's (0.52 em) at 6.5 pt |
| floor | 6.0 pt, absolute | three of five 2026 flagships ship 4.5 to 5.6 pt somewhere; do not copy them |
| bold, italic | none in the artwork except real maths; the caption is the only place for bold | |
| a label that is part symbol, part words | two runs on one baseline: `mixed_label()`; for an axis label `mixed_xlabel()`; a legend entry cannot be split, so it is worded | matplotlib cannot size two parts of one Text; maths inside a 6.5 pt string prints at 6.5 pt, and the audit warns |
| tick labels | the face of **what the tick is**: a plain number (1, 4, 16, 0.5, 33.96) in Arimo like every other word; a mathematical object (a fraction ½ set as `\tfrac12`, a symbol π or $\sigma$) in CM | DAPS Fig. 6 sets ticks and labels in one sans; the paper's fig1_path sets its PSNR values in Arimo and its $t$ knots ½ ¾ ⅞ in CM, since the body writes them as maths |
| one quantity, one tick form | $t$ is fractions in CM in every figure, or decimals in Arimo in every figure; never ½ in one figure and 0.5 in the next | a colour is a term, and so is a notation |
| `mathtext.default` | never set it | `"it"` embeds `cmti10`, the text italic, where TeX sets a variable in `cmmi10` |
| tight relation | `$N\!=\!4$`, not `$N = 4$` | the paper writes a parameter value `$N{=}4$`; mathtext ignores the braces |

## 3. Colour

A colour is a term: one concept, one hue, across every figure, plot and table of the paper.

| role | value | where |
| --- | --- | --- |
| ours | `#E2822F` at 1.8 pt with filled markers | the accent the diagrams give the quantity the paper adds |
| ours, when it must be text | `#A65F22` (4.9:1), or black | the accent at 2.8:1 cannot carry a word |
| ours, a stroke under 1.2 pt or a marker under 3 pt | `#CC752A` (3.4:1) | |
| every baseline | markers and lines `#919191`, their labels `#6C6D70` (5.2:1) | the baseline lane |
| a reference level (a feedforward net, a teacher, a floor) | `#919191` 0.5 pt, dashed (3, 2) | |
| claim ink: axes, ticks, labels, the dimension line | `#000000` | |
| several series with their own identity | Paul Tol bright, muted or high-contrast, plus a dash and a marker each | SciencePlots (MIT); greyscale and colour-blind safe |
| never | a hue outside the palette, a rainbow or jet map, vibrant's orange beside the accent, a saturated fill | |

Heat maps and error maps take `viridis` or, for signed data, `RdBu_r`; an error map on natural images is not a
flagship convention (only SSDM-MRI in our survey uses one) and needs a reason.

## 4. Lines and marks

| rule | value |
| --- | --- |
| structure: axes, ticks, guides | 0.5 pt |
| hairline: raster-panel frame, grid if any | 0.3 pt |
| claim stroke: a zoom box, a dimension line's weight when it is the figure's point | 0.9 pt, at most three per figure |
| a baseline data line | 1.1 pt |
| our data line | 1.8 pt |
| markers | filled discs 3.2 pt; the operating point 5.2 pt with a 0.6 pt white edge |
| arrowheads | one silhouette per figure |

## 5. Axes

| rule | value | source |
| --- | --- | --- |
| spines | left and bottom only, 0.5 pt, black | DAPS Fig. 6, every Kaiming plot |
| ticks | out, major only, 2.5 pt long, 0.5 pt wide, 2 pt pad; no minor ticks at column width | minor ticks are noise at 236 pt |
| log axis | when the data span more than a decade; say so in the axis label, "(log scale)"; ticks at values a reader uses (1, 4, 16, 64, 256), never `10^0` | DiffPIR, DAPS Fig. 13, DE-CM, Meng |
| grid | none, unless values must be read off; then 0.3 pt `#E6E7E8` under the data | |
| truncation | a bar axis starts at zero; a line axis may not, and never hides a crossing | |
| two y axes | never | |
| title inside the figure | never; the caption is the title | |
| legend | none when the series can be labelled in place (DAPS labels seven methods, DE-CM six curves); otherwise frameless, outside the data or in the emptiest quadrant | |

## 6. Plot grammar

| figure | construction | source |
| --- | --- | --- |
| quality against compute | ours a swept curve; every baseline one point at its own published setting, labelled in place; a dimension line above the data naming the ratio; the operating point enlarged and its value written | DAPS Fig. 6, CLAMP Fig. 3, DE-CM Fig. 2a, AdaGen Fig. 9 |
| the compute axis | prior evaluations (or NFE), not seconds; seconds are not reproducible across machines and stay in the tables | |
| where it goes | never Figure 1; flagships place it at Fig. 2 to 9 | 7 of 7 surveyed |
| an ablation over one setting | one panel per metric sharing x, ours marked at the reported value | |
| bars | only for a count or a single number per condition; show every point when n < 10 | |

## 7. Result grids (qualitative figures and teasers)

| rule | value | source |
| --- | --- | --- |
| axes of the grid | methods across the columns, tasks or images down the rows | DPS, FlowDPS, Flower, SSDM-MRI |
| column order | measurement, baselines, ours, ground truth | DPS, FlowDPS |
| seams | **0 pt** between reconstructions, horizontally and vertically, so the eye diffs across the edge and each panel gets the largest side the width allows | DAPS Fig. 1, measured |
| the one exception | when adjacent panels share a tone at their boundary (two skies, two dark backgrounds) and an abutting edge would vanish, **every** seam becomes **1.0 pt** white (`grid(..., seam=C.GRID_SEAM_FALLBACK)`); never one seam alone | a grid with one odd seam reads as a grouping |
| the measurement column | set off by **1.8 pt**, whatever the seam: the measurement is an input, not an output | DAPS Fig. 1: 4 px of a 111 px panel |
| strength of the evidence | the seam rule rests on one measured exemplar, DAPS, plus the reading argument above; DPS, FlowDPS and Flower have not been measured | re-measure when a second grid is borrowed from |
| headers | above the first row, 6.5 pt, 2 pt above the panels | |
| numbers | at most one row, under the method columns only, 6.5 pt; never on the image | DAPS Fig. 1; DPS, DiffPIR, FlowDPS keep them in tables |
| zoom inset | a 0.9 pt box in the accent on the full image; the crop magnified in the panel's own bottom-right corner at 42 % of its width, with a 0.5 pt white border | FlowDPS Fig. 3 (DAPS puts crops in a row below, which costs a row per task) |
| resampling | to 4.2 px per pt before placement, LANCZOS for images, NEAREST for masks | 600 dpi at print |
| panel side | large enough to show the failure that justifies the row; a hole-fill reads at 45 pt, texture needs an inset | |
| image choice | by the spread between methods, printed as a ranked list, and then by eye; the chosen ids written into the script | a figure is where a paper can lie; the choice has to be auditable |

## 8. Whitespace

| rule | value | source |
| --- | --- | --- |
| gutters | at most 10 pt of white left and right of the ink | JiT 0.2 / 0.0, iMF 0.0 / 9.3, FlowDPS 6.3 / 3.5 |
| ink coverage of a method figure | 20 to 40 % | JiT 19.9, iMF 23.6, ARC 36.9 |
| ink coverage of a plot | 4 to 15 % | DAPS Fig. 6: 6.0 and 6.1 %; a Pareto plot where one method owns a corner is sparse by construction |
| when both bind | grow the elements, never the gaps | |

## 9. Data

| rule | value |
| --- | --- |
| every number | read from the result files the experiment wrote, never typed, never from memory or a message |
| duplicates | deduplicated by the row key before any mean (an array that ran twice doubles some rows) |
| an arm that has not run | left out and said so in the caption, never interpolated |
| comparable conditions only | a different budget, protocol or test-set size is a separate panel or an annotation |
| n and the unit of replication | in the caption |

## 10. The review gate

`save()` refuses to hand a figure over while any of these holds: two visible texts overlap; a label is anchored
outside its axes and so never drawn; a text is cut off by its axes; a glyph is missing; a word is in a face other
than Arimo or under 6 pt; the page is wider than the target; a font other than Arimo or Computer Modern is
embedded. It warns on text over a data marker, colours outside the palette, a page more than 1.5 pt narrow, ink
outside its range and gutters over 10 pt.

Then it prints the path of the PNG twin, and **the figure is not done until that PNG has been read with the Read
tool and compared side by side with the named reference figure.** Code checks what code can. A person or an agent
looking at it is the only check for whether it is the figure intended.
