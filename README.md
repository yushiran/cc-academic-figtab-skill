# academic-figure

A Claude Code skill for the figures of an ML paper that are made of results: budget and Pareto plots,
ablation curves, qualitative comparison grids, teaser result grids. It draws them at print size, in one
paper's style, and refuses to hand one over until an audit passes and the render has been read.

Method and architecture diagrams are drawn in Figma by its sibling,
[academic-figure-figma](https://github.com/yushiran/Academic-Figure-Figma-CC-Skills); the two share one
palette, one pair of faces and one set of widths, so a paper's plots and diagrams look like the same paper.

## Why

A figure fails review for reasons that are small, measurable and easy to miss under a deadline: a label
scaled to 4 pt, a font that fell back to DejaVu without a warning, two labels printed on top of each other,
a colour that appears in no other figure of the paper. Each of those shipped at least once while this skill
was being written. It turns each into a number in `academic_figure/contract.py` or a check in `save()`.

The numbers are measured, not chosen: from He Kaiming's MoCo, MAE, iMF, JiT and BNF for type and restraint,
from DAPS (CVPR 2025 oral) for plots and result grids, and from FlowDPS, CLAMP and DE-CM for the variants.
`references/contract.md` gives the source of each.

## Use

```python
import sys; sys.path.insert(0, "<skill directory>")
from academic_figure import figure, save, budget, grid, C

fig, ax = figure("cvpr", "col", height_in=1.95)          # the true column width
budget(ax, ours=[(1, 30.1, 1), (4, 32.0, 4), (16, 31.9, 16)],
       baselines=[("Flower", 571, 31.6), ("FLAIR", 50, 28.5)],
       operating=4, compare_to="Flower", ticks=[1, 4, 16, 64, 256])
save(fig, "figs/budget.pdf")                             # closes the width, audits, raises on a FAIL
```

`save()` writes the PDF at the column or text width by measurement, writes a PNG twin, and fails the figure
on overlapping or undrawn labels, text cut off by its axes, missing glyphs, a word outside Arimo or under
6 pt, a page wider than the column, or an embedded font other than Arimo and Computer Modern. It warns on
text over a data marker, colours outside the palette, ink outside its range and wide gutters.

## Install

```sh
claude plugin marketplace add yushiran/academic-skills
claude plugin install academic-figure@yushiran-research
```

Requires matplotlib, numpy and Pillow. The Arimo font is bundled (SIL OFL 1.1).

## Test

```sh
python examples/test_examples.py
```

Draws one figure of each template from synthetic data and must pass; then builds three figures with a
known defect each (collided labels, a word in DejaVu, a label anchored outside its axes) and must catch all
three.

## Credits

Adapted in part from [scipilot-figure-skill](https://github.com/Haojae/scipilot-figure-skill) (MIT) and
[SciencePlots](https://github.com/garrettj403/SciencePlots) (MIT); see `NOTICE`.
