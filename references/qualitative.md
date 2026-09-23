# Qualitative figures

A qualitative figure is where a paper shows what its numbers mean, and it is also where a paper can lie. This guide
covers the comparison grid, the teaser grid and the supplementary sample grid. Every number in it was measured on 90
flagship qualitative figures from 33 papers (section 9 says how, and where the evidence is thin). `contract.md` §7
holds the rules in short, `academic_figure/contract.py` holds the constants, and `grid()` draws them.

## 1. The claim comes first

Write the one sentence the reader must be able to check off the figure before choosing a single image. It names a
failure of the baselines and what ours gets right, in terms a reader can see at print size:

- "At 20 steps DPS returns a rooster for the squirrel, and DiffPIR recovers the squirrel" (DiffPIR Fig. 4).
- "PSLD changes the person's identity inside the box, and ReSample keeps it" (ReSample Fig. 7).
- "With a zero initialisation OT-ODE diverges to colour noise, and PnP-Flow's result does not change" (PnP-Flow Fig. 6).

Both readers of the survey found the same line between strong and weak figures. A strong comparison shows one of three
things: a baseline failing outright (a wrong object, a changed identity, aliasing stripes, noise blow-up), content the
reader can read (the licence-plate digits of Restormer Fig. 4), or an inset large enough to show texture (half the
panel in SwinIR Fig. 5). A weak comparison sits near the ceiling (real-noise denoising at 34 to 41 dB, 2×
super-resolution at 64 px), where every output looks the same and only the printed PSNR carries the claim. Panel size
does not decide it: the 19 strong comparisons have panels of median 64 pt and the 7 weak ones 59 pt.

If the sentence cannot be written, or the images do not show it at print size, the figure is not drawn. The table
carries the claim, and the grid goes to the supplement as the uncurated record.

## 2. Choosing the content

| choice | rule | evidence |
| --- | --- | --- |
| tasks | the tasks where the methods differ visibly at print size, not the ones where ours wins by the most dB | the strong and weak comparisons of section 1; SOLO fig9's two deblurring rows, alike at 70 pt |
| a changed condition | often stronger than one more task: a row whose condition breaks the baselines | PnP-Flow Fig. 6 (initialisation), InverseBench Fig. 8 (fewer receivers) |
| priors and domains | as many as the claim names; a method claimed to work on any prior shows each prior | DAPS Fig. 1 spans faces, natural images, a 768 px latent model and MRI; SOLO's teaser spans three priors, SOLO fig9 one |
| image size | a texture claim needs a large source; on 64 to 256 px images only gross failures read, with no zoom | the zero-shot solver papers zoom in 6 of their 31 comparisons, all on large images (DAPS's 768 px latent block, FLAIR) or medical slices (DDS), and none of their 64 to 256 px natural images; 16 of 20 restoration-network comparisons zoom, on large images |
| methods | the strongest baselines of the table, one set for the whole figure so the headers hold; 2 to 5 in the main text | median 4 per comparison (IQR 3 to 5); restoration networks show 4 to 9, zero-shot solvers 2 to 5; 4 of the 6 strong comparisons of set b show 2 to 4 |
| rows | 2 to 4 | median 3 over 54 comparisons |
| main text or supplement | the main text holds one claim per figure; the supplement holds every method on every task | DAPS: 7 figures in the main text, 15 sample grids in the appendix |
| the uncurated backstop | a supplementary grid of the first n test images by id, every method, chosen by no one. It is what makes a curated main figure credible | JiT Fig. 8 ("Uncurated", at the guidance scale behind the reported FID); JiT Fig. 5 points to it; SOLO's 28 supplementary grids |

## 3. The selection rule, and how the caption states it

Fix the rule before looking at any image, run it, write the chosen ids into the script with the date, and state the
rule in the caption.

1. The candidates are the test set, never the validation split.
2. Rank by the spread between methods on each image, for example the standard deviation of per-method PSNR. This does
   not favour ours. A ranking by our margin over the best baseline is a cherry-pick by construction, and if it is used
   the caption says so.
3. Choose by eye from a printed list of the top candidates with every method's numbers, and write down each departure
   from rank 1 with its reason (SOLO fig9 took rank 4 for deblurring because rank 1 was a dark image).
4. Every method in a row shows the same image.

The caption carries the rule in one clause. For a main figure: "Images: the largest spread between methods among the
1000 test images, rank 1 in each row except deblurring (rank 4, a brighter face)." For the supplement: "The first
three test images by id; no selection."

The field rarely does this. A selection statement appears in 2 of 56 comparisons ("Representative", RED-diff Fig. 11;
"several representative", StableSR Fig. 5) and in 6 of 9 sample grids (five "selected" or "curated", one "uncurated":
JiT Fig. 8, which also names the guidance scale behind its reported FID). Stating the rule is one of the few places
where a figure can be more honest than the field at no cost.

## 4. The layout grammar

| element | rule | measured |
| --- | --- | --- |
| orientation | methods across the columns, one row per image, task or condition | 37 of 48 baseline comparisons; a wrapped crop grid beside a full image in 9 (the house style of SwinIR, NAFNet, Uformer, Restormer, MambaIR, DiffBIR); methods down the rows in 2 (DDNM Fig. 3, Mask R-CNN Fig. 6), which suits a severity sweep across the columns |
| the measurement | the first column | first in 36 of 56, second after the ground truth in 12, absent in 7 |
| the ground truth | at one end of the run, the same end in every figure of the paper | first 19, right after the measurement 11, last 11, absent 15 (real-world data). Last puts ours beside it (DiffPIR, DDS, FLAIR, RED-diff); first shows the target before the attempts (PnP-Flow, EPS, Pokle, InverseBench) |
| ours | the last method column, headed "Ours" at the weight of the other headers | the last method column in 38 of 56 (28 last, 10 just before the ground truth); marked by position or a plain header in 35, bold in 17 (restoration networks), a coloured frame in 1 (DDNM Fig. 3); no badge anywhere |
| panel side | as large as the width allows: 2 to 5 methods at text width give 60 to 80 pt | comparisons at text width: median 62.8 pt (IQR 57.5 to 78.1); at column width 55.3 (IQR 39.5 to 76.4); the smallest of the 90, 28.5 pt (DDNM Fig. 4), is the floor |
| height | a main-text grid spends two or three image rows, about 250 pt at text width with one crop row; anything taller, a four-row grid with two crop rows at 490 pt, is supplementary material, and the main text keeps the two rows that carry the claim | the author's rule (SOLO, 2026-09-23: main-text space is the scarce resource); the survey's rows, median 3 over 54 comparisons |
| dropping a column | when the panels come out under 70 pt at text width, drop the weakest baseline before shrinking the panels: five methods at 67 pt against four at 79 pt | SOLO fig9 v2 to v3, Flow-Priors dropped, the panels grew by 12 pt and the crop row became legal at 1.5 source pixels per point |
| seam | **2.5 pt** of white, the same in both directions | median 2.48 over 54 comparisons (IQR 1.36 to 2.99, 3.7 % of the panel side); only 6 abut; the vertical seam equals the horizontal one (median ratio 0.95, n = 30) |
| seam, generated samples | 0 pt | 8 of 9 sample grids abut (DiT, JiT, MAR, MeanFlow, LDM) |
| the measurement's offset | none when there is a seam; 2.0 pt only when the reconstructions abut | the gap after the measurement equals the seam in 30 of 32 grids that put it first; the two that set it off abut: LDM Fig. 8 2.0 pt, ReSample Fig. 3 2.4 pt; DAPS Fig. 1(a), a single raster, 1.4 pt from its pixels |
| column blocks | 9.3 pt between blocks, and at least 2.2 seams | median of 21 block gaps (IQR 6.1 to 14.3); DAPS Fig. 8 seams 2.2 pt inside its task blocks and 10.9 pt between them; the tightest boundaries are ReSample Fig. 5 (2.2 seams) and D-Flow Fig. 5 (2.3) |
| zoom | none, unless the claim is texture on a large image; when the author wants a small difference legible on 256 px images, a crop row at the largest magnification that keeps 1.5 source pixels per point (2.1x for 120 px of 256 in a 79 pt panel), never an inset there (0.40 of the panel would magnify a 120 px crop 0.85x) | no zoom in 32 of 56 comparisons; the crop-row limit follows from the source-pixel floor below (SOLO fig9 v3) |
| zoom style | an overlaid inset when one square region per image suffices; a crop row under the image row for two regions or a wide one | crops beside a full image 10, overlaid inset 9, crop row 5 (DAPS Fig. 1c to d, DDS Figs. 7 to 8, FLAIR Figs. 2 and 5) |
| inset size and corner | 0.40 of the panel, in a corner that covers no box, bottom-right first, the same corner along a row | 16 vector-placed magnifying insets span 0.24 to 0.60 (median 0.40); 9 of them sit bottom-right, 3 top-right, 3 bottom-left, 1 top-left; SwinIR Fig. 5 keeps one corner in every column |
| magnification | 3× | median of 23 zooms (IQR 2.0 to 3.5, range 1.3 to 4.0) |
| source pixels | at least 1.5 source pixels per printed point in the inset | derived, not measured: under 1.5 each source pixel prints as a block of 0.7 pt or more, so the inset magnifies interpolation. DDS Fig. 9, the one low-resolution flagship inset found, shows about 1.6 (256 px slices at 2.5× in 63 pt panels) |
| zoom boxes | one per panel; a second one only in its own colour, with its crop framed in that colour | 1 box in 18 comparisons, 2 in 2 (StableSR Fig. 1 red and blue, DAPS Fig. 1 green and red) |
| box stroke and colour | 0.9 pt in the accent; a second box in Paul Tol's bright blue `#4477AA`, a per-figure series colour (the diagrams' claim blue already means the objective) | vector-drawn boxes 0.27 to 0.97 pt (median 0.74, n = 10); colours red 9, amber 3, green 3, lavender 2, so a warm hue dominates and the accent is the paper's one warm mark |
| headers | above the first row, at the word size, 2 pt above the panels, narrower than their column | above in 17 of the 31 solver-paper comparisons; below in 19 of the 25 in the other papers, the restoration networks among them; flagship sizes 6.25 to 8.9 pt (IQR over 41, median 7.8), which holds the contract's 6.5 |
| row labels | rotated on the left, one per task or condition row, shorter than the row | rotated in 14 of the 90 qualitative figures (FLAIR Fig. 2, ReSample Fig. 3, DDRM Fig. 1), horizontal in 7; a caption line under each row costs 9.5 pt of height per row, a rotated label 9.8 pt of width once |
| sub-panel letters | only for blocks the caption refers to by letter | 15 of 56 comparisons |
| numbers | never on the image; at most one row, under the method columns, with the metric named in the caption | none in 33 of 56, under the panels 15, on the panel 7; only 6 of the 23 figures that print numbers define them in the caption, and 5 more put the metric's name in the reference panel's number slot (Restormer, NAFNet) |
| error maps | not on natural images | 2 of 90 (DDS Figs. 7 to 8, viridis, MRI) |

## 5. The caption

- Length: median 23.5 words over 56 comparisons (IQR 15 to 35.5, range 6 to 93), 25 over all 90 qualitative figures.
  A main-text comparison fits in 25 to 40 words; a teaser runs longer (DAPS Fig. 1, 93).
- Parts, in this order: what is shown (task, dataset, noise level); the claim sentence, which 19 of the 56 carry;
  the selection rule; what the numbers are (metric, unit, per image or mean); the budget where the methods differ
  (DiffPIR Fig. 4 puts it in the headers instead).
- A row key only when the rows are not labelled in the figure. PnP-Flow keys its rows by number in the caption, and
  D-Flow names its tasks nowhere.
- Never "Zoom in for details". It appears in 8 of 56, and it concedes that the difference cannot be seen at print
  size; PnP-Flow Fig. 3 and StableSR Fig. 5, both weak, carry it.

A pattern: **[Task], [dataset], σ_y = [value].** [The claim, naming the failure.] Images: [the selection rule].
Numbers: PSNR (dB) of each image; the NFE of each method in its header.

## 6. Common mistakes

| mistake | what happens | the rule | seen in |
| --- | --- | --- | --- |
| one prior in a paper that claims three | the reader cannot check the breadth the abstract claims | cover each prior or domain the claim names | SOLO fig9 (CelebA 128 only), where DAPS Fig. 1 covers four domains and SOLO's own teaser three priors |
| rows where every method looks alike at print size | the row spends a quarter of the figure on nothing and suggests the method changes nothing | keep a row only if its difference shows without zooming; move the rest to the supplement | SOLO fig9 deblurring rows; Uformer Fig. 5 (34.4 to 35.1 dB, all alike); NAFNet Fig. 3 |
| an inset on a small image | 28 px of a 128 px face magnified 1.9× puts one source pixel on each printed point, so the inset shows interpolation | at least 1.5 source pixels per point; on 64 to 256 px images no zoom, or larger panels | SOLO fig9; `save()` warns |
| a zoom box under its own inset | a corner of the marked region is hidden in every panel | the inset takes a free corner; `grid()` chooses one and `save()` fails a covered box | SOLO fig9 (every row) and this skill's own 0.1.2 test grid |
| a measurement rebuilt with another random generator | the first column shows a noise draw that no method solved, and for motion blur and masks another operator | show the y the reconstructions answer: save it when the problem is solved, or rebuild it and check each reconstruction's measurement error against the logged value | SOLO fig9, its 28 supplementary grids and teaser v01 to v02, fixed 2026-09-23 (`fig_grids.verify()`) |
| the selection rule only in a code comment | the reader cannot tell a choice from a draw | state it in the caption | SOLO fig9 (`MAIN_ROWS` in `fig_grids.py`) |
| a ranking by our margin where the plan said the spread between methods | the images shown are the ones ours wins most, and the plan says otherwise | rank by the spread, or say "the largest margin in our favour" in the caption | SOLO: E51's plan against `pick.py` and `fig_grids.sheets()` |
| 0 pt seams between panels that share a tone | two dark backgrounds read as one panel | 2.5 pt seams; 0 pt only for generated samples | SOLO grid `celeba128_box` row 2; teaser v02 block (d); `save()` warns |
| a caption line under every task row | 9.5 pt of height per row, 38 pt over four rows | a rotated row label, 9.8 pt of width once | SOLO fig9 |
| eleven columns at text width | 45 pt panels and headers that fill their columns | 2 to 5 methods in the main text; the supplement may run wider, above 28.5 pt | SOLO supplementary grids |
| "Zoom in for details" | concedes that the difference cannot be seen at print size | enlarge the panels or the inset until it can | PnP-Flow Fig. 3, StableSR Fig. 5 |
| numbers without a name | the reader guesses PSNR, SSIM or LPIPS, and the unit | name the metric and unit in the caption, or in the reference panel's number slot | 12 of the 23 figures that print numbers |
| a larger panel for ours | unequal areas bias the comparison | equal panels in a comparison; `save()` warns | DiffBIR Fig. 1 |
| a column whose role changes between blocks | the column reading breaks | one role per column in every block | Uformer Fig. 5 (BM3D in the Target slot) |
| tasks named nowhere | the reader infers the task from the measurement | a rotated row label, or a row key in the caption | D-Flow Figs. 5, 8 and 9 |
| a main-text grid half a page tall | four image rows and two crop rows at text width, 495 x 494 pt, where the page is the paper's scarcest resource | two or three rows in the main text; the full grid in the supplement | SOLO fig9 v2 (2026-09-23), cut to two rows the same day |
| a figure that shows no advantage | rows where the strongest baselines match ours at print size, so the reader concludes the method changes nothing | rows where a strong baseline fails visibly, a crop row where the failure is small, and the budget in the caption (theirs 500 to 2,500 evaluations, ours 6 to 12) | SOLO fig9 v1: stripes and deblurring rows alike at 67 pt |
| a baseline set the figure does not need | every extra column costs panel size, and the weakest baseline's failure is already in the table | the strongest two or three, one set for every row | SOLO fig9 v1 to v3 |

## 7. Exemplars

Open the figure itself before borrowing from it. Numbers marked *measured* come from the image placements.

| paper | figure | take this | leave this |
| --- | --- | --- | --- |
| DAPS, CVPR 2025 oral | Fig. 1 | four domains in one teaser; named competitors with LPIPS and PSNR under the method columns; a crop row with two coloured boxes in (c) and (d); separate-image blocks 4.8 pt apart inside, 12.7 pt between *measured* | blocks (a) and (b) are single rasters, so they cannot be edited or measured by placement |
| DAPS | Fig. 8 | seams of 2.2 pt inside dashed task blocks and 10.9 pt between them *measured* | 4.4 pt headers |
| InverseBench | Fig. 8 | one changed condition per row, which breaks one method; PSNR in grey under every panel; the failure named in the caption | |
| PnP-Flow | Fig. 6 | a condition as a row (a zero initialisation): the baselines diverge and ours does not change, visible without a zoom | its Fig. 3: six methods at 47 pt that look alike |
| DiffPIR | Fig. 4 | each method's budget in its header ("DPS (100)"); a categorical failure at a matched small budget | |
| ReSample | Fig. 7 | an identity change seen at a glance; the numbers printed even where one is mixed (PSLD's better LPIPS in row 2) | |
| FLAIR | Fig. 2 | rotated task labels; a crop row above each task row, joined to its box by a leader line | "Best viewed zoomed in" |
| SwinIR | Fig. 5 | the inset takes about half of a 78 pt panel, at the same corner in every column *measured* | a green box with a red inset frame, two colours for one device |
| MambaIR | Fig. 4 | a full image with its box beside a crop grid at about 4×, where the lattice aliasing of the baselines shows | |
| StableSR | Fig. 1 | two boxes per panel, each paired with its inset by colour (red, blue) | its Fig. 5: eight 60 pt columns and a "zoom in" note |
| Restormer | Fig. 4 | readable content (licence-plate digits) as a legibility test; "PSNR" in the reference panel's number slot as the legend of the number row | |
| RED-diff | Fig. 11 | one arrow on one gross artefact decides the figure | a brain row that adds nothing |
| Mask R-CNN | Fig. 6 | methods down two rows, one difference, and the failure named in the caption | |
| DDNM | Fig. 3 | difficulty rising across the columns, so the baselines fail progressively in view | 4.5 pt headers; the yellow frame round ours |
| PSLD | Figs. 4 and 12 | four columns at 116 pt *measured*; the row where ours also fails is shown | |
| JiT | Fig. 8 | "Uncurated", with the guidance scale that gives the reported FID: the honesty backstop | |
| DiT | Fig. 7 | a controlled comparison: one noise, one class, twelve models, the blocks abutting at 0 pt | |
| MAE | Fig. 2 | measurement, output and ground truth as a triplet with its key in the caption; a footnote that answers the obvious objection | |
| DDRM | Fig. 1 | rotated scale labels (4×, 8×, 16×) and lettered task blocks in a single-method teaser | |
| EPS | Fig. 2 | | PSNR printed on the image, in yellow on a black box |

## 8. With `grid()`

```python
from academic_figure import grid, save, C
# a comparison: tasks down the rows named on the left, one zoom per row in a free corner
fig, axes = grid(panels, ["Measurement", "Flower", "PnP-Flow", "Ours", "Ground truth"], span="full",
                 row_labels=["Box inpainting", "Super-resolution"], zoom={0: (x0, y0, x1, y1)})
# two blocks of a teaser, each named above its columns, one row of numbers
fig, axes = grid(panels, headers, blocks=[4, 3], block_headers=["(a) Pixel prior", "(b) Latent prior"],
                 numbers=["", "24.77", "29.38", "", "", "36.07", "39.19"])
# two regions per image in a crop row under each image row (DAPS Fig. 1c)
fig, axes = grid(panels, headers, zoom={0: [box_a, box_b]}, zoom_style="row")
# a supplementary grid of generated samples: 0 pt seams, no headers, no measurement
fig, axes = grid(panels, [""] * 6, seam=C.GRID_SEAM_SAMPLES, measurement_col=None)
save(fig, "figs/fig_qualitative.pdf")
```

Zoom boxes are given in the pixels of the row's largest source, so a low-resolution measurement can be passed at its
own size. Panels are resampled with LANCZOS; a mask, or a low-resolution input meant to show its pixels, is enlarged
with NEAREST before it is passed. A grid built by hand sets `fig._af_kind = "grid"` to get the geometric checks.

`save()` then checks what code can:

- FAIL: a zoom box under an inset of its own panel; a zoom magnifying under 1.3×.
- WARN: panels under 28.5 pt; unequal panels within a row; seams over 4.9 pt, or unequal inside a block; a block gap
  under 2.2 seams; an abutting edge that steps under 8 of 255 in luminance along most of its length; a zoom
  magnifying under 2.0×; an inset showing under 1.5 source pixels per point; a header wider than its column or outside
  6.25 to 8.9 pt; a row label longer than its row.
- Left to the eye, since no code can judge them: whether each row's difference is visible at print size, and whether
  the measurement shown is the one the reconstructions answer.

## 9. The evidence, and its limits

- **Corpus.** 44 PDFs: 32 from the SOLO reference libraries (inverse problems with diffusion and flow priors,
  restoration networks, flow-matching foundations) and 12 of He Kaiming's papers. `scripts/measure_grids.py` found 388
  multi-image figures; 277 remain once the copies of one PDF held in several libraries are removed, from 33 papers.
  Eleven PDFs yield no multi-image grid, that is no page with three or more images above one caption: DPS, Flower
  and FlowDPS place their qualitative grids as single rasters, and MPRNet, PromptIR, ConvNeXt, DyT, MoCo, ResNet,
  SimSiam and ViTDet have none the detector can see.
- **Reading.** Two readers opened 97 of the renders, enlarged where panels were small: 90 are qualitative (56
  comparisons against baselines or between the authors' own variants and ablations, 25 single-method result grids,
  9 generation sample grids) and 7 are plots, a diagram or a dataset montage. Each was rated strong, moderate or
  medium, or weak by whether its claim can be checked at print size in about three seconds.
- **Geometry.** The seams, block gaps, measurement offsets and panel sides above were re-measured for this guide from
  the image placements of those 90 figures, every gap of every row kept (`academic_figure/grids.py`); 87 are usable.
  Three are dropped because the detector's rows are wrong (FLAIR Fig. 5, BiFlow Fig. 10, DiffPIR Fig. 3). A gap more
  than 1.5 pt wider than its row's median seam is counted as a block gap.
- **What placement cannot see.** A grid exported as one raster has no placements, so DPS Fig. 4, Flower Fig. 2,
  FlowDPS Fig. 3 and DAPS Fig. 1(a) to (b) are not in the seam statistics; DAPS Fig. 1(a) was measured from its pixels
  instead (the reconstructions abut, the measurement is set off by 1.4 pt, the rows by 0.1 pt). The seam statistics
  therefore describe grids assembled from separate images, and single-raster grids may abut more often.
- **Known detector errors,** found by the readers: boxes and insets drawn into a raster are missed (SwinIR Fig. 5,
  DDNM Fig. 1); the header and number counts pick up text of a neighbouring figure or table; Mask R-CNN's detection
  boxes count as zoom boxes; the renders of FLAIR Figs. 2, 4 and 5 showed the supplement's figures of the same
  numbers and were re-read from the main-text pages; the grid sizes of DiffPIR Fig. 3, SAM Fig. 3 and FLAIR Fig. 2
  are wrong.
- **Thin.** The inset fraction rests on 16 vector-placed insets (raster-drawn ones are not measured), the measurement
  offset on 3 grids and the box stroke on 10 vector-drawn boxes; the source-pixel floor is derived from print
  density, with one flagship figure consistent with it; the header sizes are the detector's and include some
  neighbouring text. Re-measure before relying on these, with `scripts/measure_grids.py` on the new paper.
