---
name: academic-figtab
description: Use when making any figure or results table of an ML paper whose content is numbers or images the experiments produced — a budget or Pareto plot, an ablation curve, a bar comparison, a qualitative comparison grid, a teaser result grid, a training curve, a main comparison or ablation table — or when a figure or table was rejected as not matching the paper's style, not at flagship level, not print-ready, with a caption too long, marks that are wrong, or names that drift. Method and architecture diagrams go to academic-figure-figma.
---

# academic-figtab

Paper figures at print size in the paper's own style, with the review gate in code. The rules are numbers
measured from accepted flagship figures (He Kaiming's MoCo, MAE, iMF, JiT, BNF; DAPS, the CVPR 2025 oral; FlowDPS,
CLAMP, DE-CM), and `academic_figure/contract.py` holds every one of them. A figure script imports the contract; it
never types a size, a colour or a width.

## The four rules that cannot bend

1. **Draw at print size and never scale.** `figure("cvpr", "col")` opens the true column width; the PDF is
   included with `\includegraphics{...}` and no `width=`.
2. **Every number comes from the result files**, deduplicated by row key. None from memory, a message, or a table
   in the paper. An arm that has not run is left out and said so.
3. **One figure, one message, stated in one sentence before the first line of code.** If the sentence is missing,
   the figure becomes a plot of everything that was measured.
4. **Not done until the PNG has been read.** `save()` audits what code can check and raises on any FAIL; then Read
   its PNG twin and compare it side by side with the reference figure named for that figure type below. Report
   nothing to the user before both.

## Workflow

```python
import sys; sys.path.insert(0, "<this skill's base directory>")
from academic_figure import figure, save, budget, grid, mixed_label, mixed_xlabel, place_labels, C
```

1. **Claim.** One sentence: what the reader must be able to check off this figure.
2. **Numbers.** Read them from the result JSONL or CSV with a small loader in the figure's own script; print them
   as a table and check them against the paper's tables before drawing.
3. **Template, if one fits.** It already carries the grammar and the contract:

   | figure | call | reference to compare against |
   | --- | --- | --- |
   | quality against compute | `budget(ax, ours=[(x, y, N)], baselines=[(name, x, y)], operating=4, compare_to="Flower", reference=("RAM, no prior evaluations", y))` | DAPS Fig. 6 |
   | qualitative grid, teaser grid, supplementary sample grid | `grid(panels, headers, row_labels=..., blocks=..., numbers=..., zoom={row: box}, zoom_style="inset"\|"row")`; design first with `references/qualitative.md` (claim, content, selection rule, layout, caption) | DAPS Figs. 1 and 8, ReSample Fig. 7, PnP-Flow Fig. 6, JiT Fig. 8 |
   | results table | `from academic_figure.tables import Column, Row, header, build, verify`; `build()` writes the body with the marks computed from the data, `verify()` must return `[]`, then `scripts/audit_tables.py <paper_dir> --canon names.yaml`; contract and workflow in `references/tables.md` | DAPS Tab. 1, MAE Tab. 1, InverseBench Tab. 1 |
   | multi-task ability, when the author asks for a radar | one radar per metric on polar axes from `figure(..., subplot_kw=dict(projection="polar"))`, axes = the tasks in the table's order, min-max over the methods shown with the outer ring the best (lower-is-better metrics inverted), every method in its own `C.SERIES_MUTED` colour and `C.SERIES_DASHES` dash, ours `C.ACCENT` with a light fill, names in a frameless legend under the panels; rules in `references/contract.md` §6 | REX Fig. 5 (per-metric axes); the survey in the paper's `docs/RADAR_CHART_SURVEY` |
   | anything else | `figure()` plus matplotlib, colours only from `C` | the closest exemplar in `references/exemplars.md` |

4. **Save.** `save(fig, "figs/name.pdf", reference="<path of the reference image>")`. It closes the page to the
   column width by measurement, writes the PNG twin, audits and raises on a FAIL. Fix every FAIL; read every WARN
   and either fix it or say in one line why it stands.
5. **Look.** Read the PNG. Is it the figure intended, is every label legible at print size, does anything sit on
   the data, does it read as the same paper as the other figures? Then compare with the reference. Only now report,
   with the audit lines and what you checked by eye.

## The contract in one screen

Full table with sources in `references/contract.md`. The values that decide most figures:

- **Width** CVPR column 3.28125 in (236 pt), text 6.875 in (495 pt). **Type** every word Arimo 6.5 pt, every symbol
  Computer Modern 8 pt, floor 6.0. A tick takes the face of what it is: a plain number is Arimo, a fraction or a
  symbol is CM; one quantity keeps one tick form across the paper.
- **Colour** ours `#E2822F` (never on text: use black or `#A65F22`); every baseline `#919191` with `#6C6D70`
  labels; claim ink black; more series from Paul Tol's bright, muted or high-contrast, each with its own dash and
  marker. One concept, one hue, across every figure of the paper.
- **Lines** structure 0.5, hairline 0.3, claim 0.9; data 1.1, ours 1.8; markers 3.2, the operating point 5.2.
- **Axes** left and bottom spines only; ticks out, major only; no title; no grid; no second y axis; log axes say so.
- **Labels** in place, beside the thing they name, never a legend when they fit (DAPS labels seven methods);
  `place_labels()` finds the free spot. A label or axis label that mixes a symbol with words is set with
  `mixed_label()` / `mixed_xlabel()`, so the symbol gets its 8 pt: maths inside a plain label or a legend entry
  renders at 6.5 pt, where Computer Modern's x-height is a fifth under Arimo's and the symbol reads small. A legend
  entry cannot be mixed, so word it.
- **Grids** (measured on 87 flagship qualitative figures, `references/qualitative.md`): the claim sentence first, a
  visible failure per row or the row goes to the supplement; methods across the columns, measurement first, ours the
  last method column under a plain "Ours"; 2.5 pt seams both ways (0 pt only for generated samples), 9.3 pt between
  column blocks; panels as large as the width allows, never under 28.5 pt; no zoom unless the claim is texture on a
  large image, then 3× at 0.40 of the panel in a free corner with a 0.9 pt accent box, or on 256 px images a crop
  row at the largest magnification that keeps 1.5 source pixels per point; the selection rule stated in the caption;
  an uncurated supplementary grid of the first test images as the backstop. Main-text space is the scarce resource:
  two or three image rows there (a single column with the strongest baseline, ours and the truth when that carries
  the claim), the full grid in the supplement; drop the weakest baseline before shrinking the panels.
- **Tables** (421 tables of 44 papers measured, 36 flagship tables read, `references/tables.md`): caption above, 25
  to 50 words (main-text median 25; fail over 80), a title plus the setting, never the verdict or the column heads;
  `[t]`, never `[p]`; booktabs, no vertical rule, no `\hline`; `\footnotesize`, numbers in `r` columns at one
  precision per metric; bold best per column, underline the second only when the text uses the runner-up and never
  in a scope under three rows, both ranked on the printed values so ties share a mark, at most 40 % of cells marked,
  and any scope other than per column stated in the caption; an arrow on every ranked column; ours in the last rows
  below a dashed rule, tinted; one name per method, metric, task and dataset, from a canon file.
- **Whitespace** gutters at most 10 pt; ink 4 to 15 % for a plot, 20 to 40 % for a method figure.

## What reviewers see first

An area chair reads a figure at print size in about three seconds. What they punish, in the order they notice it:
type too small to read; a colour that means one thing here and another in the next figure; a legend to decode where
labels would do; a baseline shown at a setting its authors never used; an axis that hides where the curves cross;
decoration of any kind (shadows, 3D, gradients, "Ours" badges, red rings). What they reward: the claim readable
before the caption, the failure of a baseline visible without zooming, restraint. `references/reviewer.md` lists
the checks with the evidence behind each.

## Common mistakes, each one made at least once

| mistake | what happens | the rule |
| --- | --- | --- |
| drawing at default size, scaling in LaTeX | 6.5 pt labels print at 4 pt | draw at print size |
| no bundled font | matplotlib falls back to DejaVu without a word | `use()` raises if Arimo is missing |
| `set_xlim` after placing a label at the old limit | the label is never drawn and nothing says so | `save()` fails it |
| two panels saying one thing at column width | 105 pt panels, labels collide | one panel; the other metric goes in the caption |
| a colour picked by eye | a navy that appears in no other figure of the paper | colours only from `C` |
| `$\sigma_y$` inside `set_xlabel` or a legend entry | the symbol prints at 6.5 pt, visibly smaller than the words | `mixed_xlabel()`; word the legend |
| a label offset past the top of its axes | it hangs in the margin, half a line above the frame | `save()` warns; move it, or widen the limits |
| a step of 3 FID drawn on an axis 90 FID wide | the arrow is 8 pt long and hides under its own markers | zoom the cluster in an inset (F3 of the paper) |
| bold and underline typed by hand | 14 marks in two tables that the printed values do not earn, ties broken on unrounded means | `build()` ranks on the printed values; `verify()` |
| a table caption that carries the argument | 64 to 130 words, taller than the table it captions | 25 to 50 words; the verdict goes in the text |
| one task named two ways across tables | "Gaussian deblurring" in the main tables, "Blur" in two supplementary ones | a canon file and `check_names()` |
| handing over before reading the render | every defect above shipped once | rule 4 |

## Files

- `academic_figure/contract.py` — every number. `__init__.py` — `use`, `figure`, `save`. `audit.py` — the gate,
  with the grid checks in `audit_grid()`. `templates.py` — `budget`, `grid`, `mixed_label`, `mixed_xlabel`,
  `place_labels`. `fonts/` — Arimo, SIL OFL 1.1.
- `references/contract.md` — the rules with their sources. `references/qualitative.md` — how to design a
  qualitative figure, with the measured grammar and the common mistakes. `references/exemplars.md` — the flagship
  figures by paper and number, and what to take from each. `references/reviewer.md` — what a reviewer checks.
- `academic_figure/grids.py`, `scripts/measure_grids.py` — measure the result grids of any PDF (the evidence behind
  §7); `academic_figure/tables_measure.py`, `scripts/measure_tables.py` — the same for tables.
- `academic_figure/tables.py` — `Column`, `Row`, `header`, `build`, `verify`, `caption_report`, `load_canon`,
  `check_names`, `audit_tex`; pure Python, no matplotlib. `scripts/audit_tables.py` — audits every table of a paper
  in its LaTeX source with no spec. `references/tables.md` — the table contract with its sources, the workflow and
  the common mistakes.
- `examples/` — runnable scripts that draw one figure of each type from bundled data, and double as the tests;
  `examples/test_tables.py` does the same for the table tools.
