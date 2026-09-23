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
| radar, only when the author asks for one | one radar per metric, never metrics of different units on one chart; axes = the tasks in the table's order, fixed for the paper; each axis min-max over the methods shown, the direction fixed so the outer ring is the best method (LPIPS and FID inverted), the worst on an inner ring at 0.15 rather than the centre, `ylim` 1.06 so a polygon on the ring stays clear of the labels; every method in its own `SERIES_MUTED` colour with its own `SERIES_DASHES` dash at 0.7 pt, ours `ACCENT` at 1.8 pt with a 0.12 fill; the metric name as the axes title; the names in a frameless legend under the panels (in-place labels collide on a 105 pt radar); at column width 2 x 2 radars need `wspace` about 0.4 so the right-hand label of one radar does not meet the left-hand label of the next; the ink audit warns near 35 %, which eight polygons on four radars produce and the caption's normalisation sentence explains | REX Fig. 5 (per-metric axes, min-max ranges stated), PixRestore (one radar per metric, axes = degradations); zero of 33 flagship inverse-problem papers use one, so the default is no radar; SOLO fig11 v1 to v3, 2026-09-23 |

## 7. Result grids (qualitative figures and teasers)

Measured 2026-09-23 on 90 flagship qualitative figures from 33 papers: the image placements of 87, every figure read
by eye. `qualitative.md` holds the design guide, the counts behind each row below and the limits of the evidence. The
0 pt seams of 0.1.x came from one grid, DAPS Fig. 1(a), which is a single raster; the grids assembled from separate
images mostly do not abut.

| rule | value | source |
| --- | --- | --- |
| the claim | one sentence naming a failure the reader sees at print size, written before any image is chosen | strong comparisons show a baseline failing outright, readable content or a half-panel inset; weak ones sit at the ceiling |
| axes of the grid | methods across the columns; one row per image, task or condition | 37 of 48 baseline comparisons; a wrapped crop grid in 9 (restoration networks); methods down the rows in 2, for a severity sweep |
| column order | the measurement first; the ground truth at one end of the run, the same end in every figure; ours the last method column | measurement first in 36 of 56; ground truth first 19, right after the measurement 11, last 11; ours the last method column in 38 of 56 |
| ours | a plain "Ours" header at the weight of the others; no frame, colour or badge | position or a plain header in 35 of 56, bold 17, a frame 1 (DDNM Fig. 3) |
| size of the figure | 2 to 5 methods and 2 to 4 rows in the main text; every method in the supplement | median 4 methods (IQR 3 to 5), median 3 rows |
| panel side | 60 to 80 pt at text width, never under **28.5 pt** | comparisons: median 62.8 pt at text width (IQR 57.5 to 78.1), 55.3 at column width; 28.5 pt is the smallest of the 90 (DDNM Fig. 4) |
| seams | **2.5 pt** of white, in both directions (`C.GRID_SEAM`) | median 2.48 over 54 comparisons (IQR 1.36 to 2.99, 3.7 % of the panel side), 6 abut; vertical against horizontal, median ratio 0.95 |
| seams of a sample grid | **0 pt** (`C.GRID_SEAM_SAMPLES`) | 8 of 9 generation sample grids abut |
| seam range | 0 to 4.9 pt, equal inside a block | 76 of 78 reconstruction grids |
| an abutting edge | steps at least 8 of 255 in luminance along most of its length, or it gets a seam | SOLO teaser v02: two MRI knees stepping 2.1 to 7.0 read as one panel |
| the measurement column | takes the seam; set off by **2.0 pt** only when the reconstructions abut | 30 of 32 give it the seam; LDM Fig. 8 2.0, ReSample Fig. 3 2.4 and DAPS Fig. 1(a) 1.4, all at 0 pt seams |
| column blocks | **9.3 pt** between blocks, at least 2.2 seams (`blocks=`) | median of 21 block gaps (IQR 6.1 to 14.3); DAPS Fig. 8 2.2 pt inside, 10.9 between; ReSample Fig. 5 2.2 seams, D-Flow Fig. 5 2.3 |
| headers | above the first row, at the word size, 2 pt above the panels, narrower than their column | above in 17 of 31 solver-paper comparisons; flagship sizes 6.25 to 8.9 pt (IQR over 41, median 7.8) |
| row labels | rotated on the left (`row_labels=`), shorter than the row; two lines when one is longer than the row, with the gutter one line thick per line of text; never over an image (audit FAIL) | rotated in 14 of 90, horizontal in 7; a caption line under each row costs 9.5 pt of height per row, a two-line gutter 17.6 pt of width once |
| numbers | at most one row, under the method columns, never on the image; the caption names metric and unit | none in 33 of 56, under 15, on the panel 7; 6 of the 23 that print numbers define them |
| zoom | none, unless the claim is texture on a large image | none in 32 of 56; the solver papers zoom none of their 64 to 256 px natural images |
| zoom style | an overlaid inset in a free corner, or a crop row under the image row (`zoom_style="row"`) | crops beside a full image 10, inset 9, crop row 5 (DAPS Fig. 1c to d, DDS Figs. 7 to 8, FLAIR) |
| inset | **0.40** of the panel, bottom-right first, never over its own box; a 0.5 pt white edge | 16 vector-placed insets, 0.24 to 0.60; bottom-right 9 of 16; `save()` fails a covered box |
| magnification | **3×**; warn under 2×, fail under 1.3× | median of 23 zooms (IQR 2.0 to 3.5, range 1.3 to 4.0) |
| source pixels in an inset | at least 1.5 per printed point | derived: under it each source pixel prints as a block of 0.7 pt or more; DDS Fig. 9 shows about 1.6 |
| zoom boxes | 0.9 pt in the accent, one per panel; a second in Tol's bright blue `#4477AA` (`C.ZOOM_COLOURS`), each crop framed in its box's colour | 1 box in 18, 2 in 2 (StableSR Fig. 1, DAPS Fig. 1); vector-drawn boxes 0.27 to 0.97 pt (median 0.74) |
| resampling | to 4.2 px per pt before placement, LANCZOS for images, NEAREST for masks and pixel-showing inputs | 600 dpi at print |
| the measurement shown | the exact y the reconstructions answer: saved when the problem is solved, or rebuilt and checked against the logged measurement error | SOLO fig9 and 28 grids showed a noise draw no arm solved until 2026-09-23 |
| image choice | a rule fixed before looking, stated in the caption, the chosen ids written into the script | a selection statement in 2 of 56 comparisons and 6 of 9 sample grids |
| the supplement | the first n test images by id, every method, captioned "no selection" | JiT Fig. 8; DAPS's 15 appendix grids |

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
