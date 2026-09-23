# Exemplars

The flagship figures this skill was measured from, by paper and figure number, and the one or two things to take
from each. Open the paper and look before drawing a figure of the same type; a description is not a substitute.
Measurements marked *measured* were taken from the page render or the image itself; the rest are read from the
figure and its caption.

## Quality against compute

| paper | figure | take this | leave this |
| --- | --- | --- | --- |
| DAPS, CVPR 2025 oral | Fig. 6 | ours a connected swept curve, every baseline an isolated point at its own setting; **every point labelled in place**, the legend explaining only the two colour roles; top and right spines off; ink 6.0 and 6.1 % *measured* | a wall-clock x axis, which no other machine reproduces |
| DAPS | Fig. 13 | the "flat against falling" shape as the argument: one curve flat across the log axis while the other only reaches it at 1000+ | |
| DE-CM, ECCV 2026 | Fig. 2a | six curves and no legend, each named beside its own line; the operating values written on the curve ("FID 1.70") | log-log where one log axis suffices |
| AdaGen, TPAMI 2025 | Fig. 9 | the matched-quality speed-up written on an arrow ("1.64×") | |
| CLAMP, ICML 2026 | Fig. 3 | a broken axis to pull a slow baseline back into frame | its place in an appendix |
| Meng (distillation), CVPR 2023 | Fig. 6 | a dashed teacher reference line the other curves climb towards | |

None of the seven surveyed puts this figure at Figure 1; it sits at Figure 2 to 9.

## Result grids

Measured 2026-09-23 from the image placements of 87 qualitative figures in 33 papers, each read by eye;
`qualitative.md` §7 has the full table and §9 the method. Across the 54 comparisons the seam between panels has a
median of 2.5 pt and only 6 abut; generation sample grids abut (8 of 9). A figure placed as one raster (DPS, Flower,
FlowDPS, DAPS Fig. 1a to b) cannot be measured by placement.

| paper | figure | take this | leave this |
| --- | --- | --- | --- |
| DAPS, CVPR 2025 oral | Fig. 1 | four domains in one teaser (faces, natural images, a 768 px latent model, multi-coil MRI), each lettered sub-panel with its own competitors; LPIPS and PSNR under the method columns; a crop row with two coloured boxes in (c) and (d); separate-image blocks seamed 4.8 pt inside and 12.7 pt apart *measured*; the raster blocks (a) and (b) abut and set the measurement off by 1.4 pt *measured from pixels* | an MRI block with no baseline; raster blocks no one can edit |
| DAPS | Fig. 8 | 2.2 pt seams inside dashed task blocks, 10.9 pt between them *measured* | 4.4 pt headers |
| InverseBench | Fig. 8 | one changed condition per row, which breaks one method; PSNR in grey under every panel; the failure named in the caption | |
| PnP-Flow | Fig. 6 | a condition as a row (a zero initialisation) under which the baselines diverge and ours does not change; 3.3 pt seams at 63 pt *measured* | its Fig. 3: six methods at 47 pt that look alike |
| DiffPIR | Fig. 4 | each method's budget in its header; a categorical failure of DPS at a matched small budget; 2.5 pt seams *measured* | |
| ReSample | Fig. 7 | an identity change visible at a glance; a mixed number printed rather than hidden | |
| FLAIR | Fig. 2 | rotated task labels on the left; a crop row above each task row, joined to its box by a leader line | "Best viewed zoomed in" |
| SwinIR | Fig. 5 | an inset of about half the panel at the same corner in every column, 78 pt panels *measured* | a green box with a red inset frame: two colours for one device |
| StableSR | Fig. 1 | two boxes per panel, each paired with its inset by colour | its Fig. 5: eight 60 pt columns and a "zoom in" note |
| Restormer | Fig. 4 | readable content (licence-plate digits); "PSNR" in the reference panel's number slot as the legend of the number row | |
| MambaIR | Fig. 4 | a full image with its box beside a crop grid at about 4×, where the baselines' lattice aliasing shows | |
| RED-diff | Fig. 11 | one arrow on one gross artefact | a row that adds nothing |
| Mask R-CNN | Fig. 6 | methods down two rows, one difference, the failure named in the caption | |
| FlowDPS | Fig. 3 | the zoom inset: a box on the full image and the magnified crop overlaid in the same panel's bottom-right; measurement first, ground truth last | a single raster, not measured |
| DPS | Fig. 4 | measurement first, ground truth last, no numbers on the images | a single raster, not measured |
| Flower | Fig. 2 | ground truth first, the more common convention (19 of 56 comparisons) | a name and PSNR above every panel, which competes with the images |
| DDNM | Fig. 3 | methods down the rows and a severity sweep across the columns, the layout for a claim about severity | 4.5 pt headers; a yellow frame round ours |
| JiT | Fig. 8 | "Uncurated", with the guidance scale behind the reported FID: the honesty backstop of a curated main figure | |
| DiT | Fig. 7 | a controlled comparison (one noise, one class, twelve models), blocks abutting at 0 pt | |
| SSDM-MRI | Fig. 7 | the one error map in the first survey: greyscale in the image's own unit, amplified ×3, with arrows rather than boxes | |
| gQIR | Fig. 1 | a physical number printed under every panel (the capture frame rate) | |

## Teasers

In the survey the strong teasers are result grids (DAPS, DDRM, DDNM, DiffPIR, FlowDPS, gQIR) and the weak ones are
schematics alone (Flower, PSLD). DAPS is the only one that puts **named competitors, with numbers, inside the
teaser**, and it does so across four domains, so breadth and a head-to-head land at once. In the three CVPR 2026
papers checked for placement, Figure 1 is a full-width float at the top of page two, not on page one.

## Method figures and type

Measured for the `academic-figure-figma` skill's contract and shared here: MoCo, MAE, iMF, JiT, BNF and Drifting
set words in an Arial-class sans at 5.7 to 9.6 pt (median 6.5) beside Computer Modern symbols; ResNet Fig. 2 is
pure greyscale; MAE Fig. 1 runs one salmon at 1.7 % of the frame; coloured area in twelve flagship single-column
figures is 0.3 to 4.7 %, in one or two hues.
