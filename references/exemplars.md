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

| paper | figure | take this |
| --- | --- | --- |
| DAPS, CVPR 2025 oral | Fig. 1 | reconstructions abut at 0 pt in both directions and only the measurement column is set off, 4 px of a 111 px panel *measured*; bold headers above; numbers under the method columns of one row only; lettered sub-panels, each with its own competitors, across four domains (faces, natural images, 768 px latent, multi-coil MRI); an MRI sub-panel with no baselines at all |
| FlowDPS | Fig. 3 | the zoom inset: a yellow box on the full image and the magnified crop overlaid in the same panel's bottom-right; measurement first, ground truth last |
| DPS | Fig. 4 | measurement first, ground truth last, no numbers on the images |
| Flower | Fig. 2 | ground truth first (the other convention); a name and PSNR above every panel, which is dense and competes with the images |
| DDNM | Fig. 3 | methods down the rows and a severity sweep across the columns: the right layout when the claim is about severity |
| SSDM-MRI | Fig. 7 | the one error map in the survey: greyscale in the image's own unit, amplified ×3, with arrows rather than boxes |
| gQIR | Fig. 1 | a physical number printed under every panel (the capture frame rate): the compute-adjacent number beside the image |

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
