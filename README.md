# academic-figtab

A Claude Code skill for the figures and tables of an ML paper that are made of results: budget and Pareto
plots, ablation curves, qualitative comparison grids, teaser result grids, results tables. It draws the figures
at print size, in one paper's style, and refuses to hand one over until an audit passes and the render has been
read. It builds a table's body from the result files with the bold and underline marks computed from the data,
verifies a table against those files, and audits every table of a paper in its LaTeX source.

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
6 pt, a page wider than the column, an embedded font other than Arimo and Computer Modern, a second y axis, a
3D axes, bars off zero, a gap label that disagrees with its data, or two kinds of error bar. It warns on text
over a data marker or a line, colours or a colour map outside the palette, a title, offset tick text, a log
axis that does not say so, a framed legend or one over the data, error bars of no stated kind, ink outside its
range and wide gutters. `save(..., svg=True)` adds an SVG twin with live text for composition in Figma.

The other templates: `sweep()` for an ablation, sensitivity or robustness curve over one setting, `gap()` for a
measured difference labelled with its computed value, `radar()` and `shared_legend()` for per-metric radars,
`mixed_ylabel()` for a y label that is part symbol, `place_labels(..., leader=True)` for crowded points.

Tables:

```python
from academic_figure.tables import Column, Row, header, build, verify

cols = [Column("psnr", "PSNR", "+", 2), Column("lpips", "LPIPS", "-", 3)]
rows = [Row("pnpflow", "PnP-Flow", "Training-free"), Row("ours", "Ours", ours=True)]
body = header(cols, ["Type", "Method"]) + "\n" + build(cols, rows, lambda r, c: results[r][c])
verify("sec/experiments.tex", "tab:main", cols, rows, lambda r, c: results[r][c])   # [] when every cell matches
```

```sh
uv run --with pyyaml python scripts/audit_tables.py paper/ --canon names.yaml
```

The audit needs no spec. Per table it checks the caption's length, booktabs rules, the marks recomputed on the
printed values under the scope that explains them best, one precision per column, a Δ row recomputed from the
printed cells, and every name against a canon file of display names and forbidden variants. `build(...,
delta=...)` writes that Δ row from `improvement()`, and `component_columns()` the ✓ columns of an ablation. `references/tables.md` holds the contract, measured on 421
tables of 44 papers and 36 flagship tables read one by one.

## Install

```sh
claude plugin marketplace add yushiran/academic-skills
claude plugin install academic-figtab@yushiran-research
```

Until 0.4.0 the plugin was called `academic-figure` and lived at `cc-academic-figure-skill`; an old install is
removed with `claude plugin uninstall academic-figure@yushiran-research`. The Python package keeps its name,
`academic_figure`, so figure scripts need no change beyond the path they insert.

Requires matplotlib, numpy and Pillow; the table tools are pure Python and read a canon file with PyYAML. The
Arimo font is bundled (SIL OFL 1.1).

## Test

```sh
python examples/test_examples.py
python examples/test_plots.py
uv run --with pyyaml python examples/test_tables.py
```

The first draws one figure of each template from synthetic data and must pass (seven, four of them result grids);
builds five figures with a known defect each (collided labels, a word in DejaVu, a label anchored outside its axes,
a zoom box under its own inset, a zoom that magnifies nothing) and must fail all five; and eleven with a defect the
audit warns about, each of which must be named. The second does the same for the templates and checks added in
0.5.0: seven figures that must pass (sweeps on a log and a categorical axis, a gap, a mixed y label, radars with a
shared legend, leader lines out of a crowded cluster, an SVG twin), eight defects that must fail or be refused
(a second y axis, a 3D axes, bars on a truncated or a log axis, a typed gap, two kinds of error bar, a reported
setting never run, a radar with a missing value) and ten that must warn. The third builds tables from
synthetic results that must pass `verify()` and the audit (nine checks, a Δ row and a component ablation among
them), twelve with a defect that must fail (a long caption, a hand-typed bold, a tie marked once, a vertical
rule, an `\hline`, an off-canon name, a stale number, a stale Δ seen by the audit and by `verify()`, two refused
ablation codes, the CLI's exit code), and three that must warn.

## Credits

Adapted in part from [scipilot-figure-skill](https://github.com/Haojae/scipilot-figure-skill) (MIT) and
[SciencePlots](https://github.com/garrettj403/SciencePlots) (MIT). Several templates and checks of 0.5.0 were
suggested by [figures4papers](https://github.com/ChenLiu-1996/figures4papers) (CC BY-NC 4.0) and reimplemented
against this contract, with no code taken; see `NOTICE`.
