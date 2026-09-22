---
name: academic-figure
description: Use when making any figure of an ML paper whose content is numbers or images the experiments produced — a budget or Pareto plot, an ablation curve, a bar comparison, a qualitative comparison grid, a teaser result grid, a training curve — or when a figure was rejected as not matching the paper's style, not at flagship level, or not print-ready. Method and architecture diagrams go to academic-figure-figma.
---

# academic-figure

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
from academic_figure import figure, save, budget, grid, mixed_label, C
```

1. **Claim.** One sentence: what the reader must be able to check off this figure.
2. **Numbers.** Read them from the result JSONL or CSV with a small loader in the figure's own script; print them
   as a table and check them against the paper's tables before drawing.
3. **Template, if one fits.** It already carries the grammar and the contract:

   | figure | call | reference to compare against |
   | --- | --- | --- |
   | quality against compute | `budget(ax, ours=[(x, y, N)], baselines=[(name, x, y)], operating=4, compare_to="Flower", reference=("RAM, no prior evaluations", y))` | DAPS Fig. 6 |
   | qualitative grid, teaser grid | `grid(panels, headers, numbers=..., measurement_col=0, zoom={row: (x0, y0, x1, y1)})` | DAPS Fig. 1, FlowDPS Fig. 3 |
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
- **Labels** in place, beside the thing they name, never a legend when they fit (DAPS labels seven methods).
- **Grids** reconstructions abut at 0 pt, or every seam 1 pt white when adjacent panels share a tone at their edge;
  the measurement column is set off by 1.8 pt either way; headers above; one row of numbers under the method
  columns; zoom insets bottom-right with a 0.9 pt accent box.
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
| handing over before reading the render | every defect above shipped once | rule 4 |

## Files

- `academic_figure/contract.py` — every number. `__init__.py` — `use`, `figure`, `save`. `audit.py` — the gate.
  `templates.py` — `budget`, `grid`, `mixed_label`, `place_labels`. `fonts/` — Arimo, SIL OFL 1.1.
- `references/contract.md` — the rules with their sources. `references/exemplars.md` — the flagship figures by
  paper and number, and what to take from each. `references/reviewer.md` — what a reviewer checks.
- `examples/` — runnable scripts that draw one figure of each type from bundled data, and double as the tests.
