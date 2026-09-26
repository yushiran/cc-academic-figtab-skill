# The table contract

Every rule a results table of the paper obeys, as a number with its source. `academic_figure/tables.py` holds the
thresholds the code needs; `build()` writes a table body from the result files, `verify()` checks a table against
them, and `scripts/audit_tables.py` audits every table of a paper in its LaTeX source. When this file and the code
disagree the code is wrong, and both are changed in one commit.

Four bodies of evidence, all gathered on 2026-09-23 (section 10 has their limits):

- **survey**: 421 tables of 44 papers measured from their PDFs by `scripts/measure_tables.py`, 240 of them in the
  main text: 12 papers of He Kaiming's group ("Kaiming" below), 16 inverse-problem solver papers, 9 restoration
  networks and 6 generative models. Numbers are medians [range] or shares of tables.
- **reading**: 36 main-text tables of 18 flagship papers (the Kaiming group plus DAPS, DPS, DDNM, FlowDPS, Restormer
  and SwinIR) read by eye for what each caption carries and how the marks work; 24 of them are Kaiming tables (14
  comparisons, 10 ablations).
- **notes**: 85 tables of 14 inverse-problem and generative papers read one by one (DAPS, DDRM, DDNM, RED-diff, PSLD,
  DiffPIR, D-Flow, Flower, EPS, DPS, InverseBench, MAE, LDM, Uformer).
- **SOLO audit**: the 11 live tables of the SOLO paper (Tabs. 1 to 7 in the main text, 8 to 11 in the supplement),
  every mark recomputed from the printed cells, every name compared with `docs/TERMINOLOGY.md` and `docs/GLOSSARY.md`.

## 1. Caption

| rule | value | source |
| --- | --- | --- |
| length | **25 to 50 words**; the audit warns over 50 and fails over 80 | survey: main-text median 25 [2 to 145] over 240 tables, 90th percentile 58, 16 % over 50, 2 % over 80; Kaiming 29, inverse 20, restoration 20, generative 31. Reading: Kaiming headline tables about 50 [15 to 94], comparisons 49.5, ablations 51; inverse and restoration 21.5 [5 to 112]. SOLO Tabs. 1 to 7: 108 [82 to 130], 11 lines |
| it opens with | a title naming what is compared and on what: "Main results on the two pixel priors." | notes: a title in 84 of 85 captions |
| it carries | the setting (test set, n, resolution, noise level); provenance or fairness when a row was not run by us, or not as its authors ran it ("as reported by the original papers", "implemented by us under the same setting"); a symbol or column the header cannot define; a mark rule only when it is not bold-best per column | reading: setting in 21 of 24 Kaiming captions, provenance 7, a definition 9, a mark rule 4 |
| it leaves to the text | the verdict of a comparison, and the numbers | reading: 9 of 14 Kaiming comparison captions give no verdict; 1 of 24 restates a number |
| a takeaway | at most one sentence, a concession or an objection pre-empted, never a number | reading: 10 of 24 (ablations 5 of 10, comparisons 5 of 14), a number in one |
| ablation sub-captions | a bold title and one verdict sentence each | reading: MAE Tab. 1's six sub-tables |
| never | the column heads restated with their arrows; a definition the Setup already gives; an experiment shown nowhere else; one fact said twice | SOLO audit: Tab. 1 restates every head and redefines NFE (86 words); Tab. 2 reports in its caption a measurement shown nowhere else and explains the dashes twice (120 words) |
| notes under the table | none: what a note would say goes in the caption or the text | reading: 0 of 36 |

## 2. Position, placement, width

| rule | value | source |
| --- | --- | --- |
| caption position | **above** the table, the same in every table of the paper | the CVPR template sets `\caption` before `tabular`; survey: above in 34 % overall, inverse 56 %, restoration 78 %, Kaiming 3 %; SOLO 100 % |
| placement | `[t]`; never `[p]` for a main-text table | SOLO audit: Tabs. 1 and 2 at `table*[p]` held back Tabs. 3 to 7, so all seven printed after the references (pp. 9 to 12) although Tabs. 3 to 5 are cited on p. 7 |
| width | single column (`table`) where it fits; `table*` for a main comparison with column groups | survey: full width in 38 % overall, Kaiming 13 %, inverse 58 %; SOLO Tabs. 1 and 2 |
| size | at most 16 numeric columns and about 10 rows per block; more goes to the supplement | the 14 flagship main comparisons SOLO surveyed for Tab. 1 stay within 16 numeric columns (source comment of `tab:main`); reading: very large tables are one of the four causes of a weak table |
| scaling | never `\resizebox` or `\scalebox`; cut a column or widen the float | derived: a scaled table prints at whatever size the box needed, off every rule of section 4 |

## 3. Rules

| rule | value | source |
| --- | --- | --- |
| booktabs | `\toprule` and `\bottomrule` 0.8 pt, `\midrule` 0.5 pt, `\cmidrule(lr)` under a column group | survey: booktabs (three or more full rules, thick top and bottom) in 41 % overall, inverse 73 %, Kaiming 2 %; measured widths top 0.8, mid 0.5; SOLO 100 % |
| vertical rules, `\hline`, `\cline` | none; the audit fails them | survey: vertical rules in 48 % overall, inverse 22 %, restoration 92 %, Kaiming 68 %; SOLO 0 % |
| the Kaiming-group exception | his papers draw `\hline` and vertical rules as a consistent style of their own; a paper is booktabs or that style, never a mix, and this house is booktabs | survey |
| dashed rule | `\cdashline{2-N}[1pt/1.5pt]` before our rows inside a block; `\cdashline{1-N}` between method classes | SOLO house style (`build()`); reading: Kaiming sets ours in the last rows below a rule in 12 of 14 comparisons |

## 4. Type and alignment

| rule | value | source |
| --- | --- | --- |
| body size | about **0.8** of the text: `\footnotesize` at 10 pt; `\scriptsize` (0.7) only when the table cannot otherwise fit its width | survey: median 0.80 [0.40 to 1.13], 8 pt; Kaiming 0.80 [0.63 to 0.93]; restoration 0.74; SOLO 0.70 in every table |
| header | at the body size | survey: 93 % |
| numeric columns | right-aligned (`r`) at one precision per column, so the decimal points align | SOLO audit: Tab. 1 centres its metric columns and the decimal points drift 1.8 pt between three- and two-digit FIDs |
| maths in a row label | not below the body size | SOLO audit: Tab. 6's `\tfrac` row labels print at 5.0 pt |

## 5. Grouping and our rows

| rule | value | source |
| --- | --- | --- |
| row classes | the method class as a leading merged-cell column (`\multirow`), the rows of one class together; the task instead, when each task is a block | notes: DAPS Tab. 1 (task blocks by `\multirow`), InverseBench Tab. 1 (a Category column, a rule between classes), Uformer Tab. 2; SOLO Tabs. 3 and 5 |
| column groups | a `\multicolumn` label over its columns and a `\cmidrule(lr)` under it, one level only | notes: InverseBench Tab. 4, a two-level header over 12 columns of mean (std), is one of the weak tables |
| our rows | the last rows of each block, below a dashed rule, tinted `oursrow` cell by cell so the tint stops at the merged class cell | reading: last rows below a rule in 12 of 14 Kaiming comparisons; survey: shaded rows in 17 % overall, SOLO 82 %; `\cellcolor` over `\rowcolor` is the SOLO decision of 2026-09-21 |
| our rows' name | the method's name, or "Ours" when it has none; never "(ours)" appended | reading: Kaiming never labels "(ours)"; inverse papers do in 5 of 6 |
| one device, one meaning | the tint marks the rows of the method as reported in every table, every reported row tinted; a column name (Type) is one taxonomy; × is one operation per table | SOLO audit: the tint means our rows in Tabs. 1 to 5 and 10, the reported setting in Tabs. 6 and 7 (one of our reported rows untinted), our columns in Tab. 11; Type names two different taxonomies in Tabs. 3 and 5; Tab. 5 uses × for two different operations |
| a constant column | shown once, not once per group | SOLO audit: Tab. 5's two NFE columns and Tab. 2's three are identical in every row; Tab. 2 reaches 18 numeric columns at `\tabcolsep` 1.5 pt |
| one cell, one number | never a slash triplet (PSNR/SSIM/FID) in a cell | reading: one of the four causes of a weak table; notes: DDNM Tabs. 1 and 2 |
| an ablation split in two | by when the choice is made: the training-time choices, each row a separately trained model, in one table; the inference budget and the inference-time settings of the reported model in the other. A column that is constant within a table (NFE at the reported budget) appears only where it varies; one concept (the training images, by kind and by count) is never split across the two tables; a block whose rows are retrained models belongs to the training table even when it reads like a setting (the sampler's knots) | the author's decision on SOLO Tabs. 6 and 7 (2026-09-23), replacing a components-against-settings split in which "generated, 12,000" headed a block in both tables and an NFE column read the same value in every row of two blocks |
| a method leaves the table | its rows are commented out, not deleted; every mark is re-derived by the table's builder; the prose that counted or introduced it changes in the same commit | SOLO 2026-09-23: one method's exit changed 14 marks in tab:latent and 3 in tab:amortised, found by regenerating, not by eye |

## 6. Marks

| rule | value | source |
| --- | --- | --- |
| best | **bold**, per column | reading: bold best in 16 of 24 Kaiming tables; survey: bold numbers in 59 % |
| second | **underlined** only when the runner-up is a fact the text uses (the closest competitor per column), and never in a scope of fewer than three rows (`SECOND_MIN`) | reading: Kaiming underlines a second in 0 of 24; survey: underlines in 2 % of Kaiming tables, 26 % inverse, SOLO 82 %; SOLO Tab. 4 states the two-row rule |
| no marks | a legitimate design when the table is not a ranking (an ablation, a sweep) or ours is not best | reading: 6 of 24 Kaiming tables |
| ranked on | the **printed** values: cells that print the same take the same mark, and the second is the next distinct value (dense ranking) | SOLO audit: all 14 mark mismatches (Tabs. 1 and 2) are ties broken on unrounded means |
| typed by | nobody: `build()` computes the marks from the result files, `verify()` and the audit recompute them | SOLO audit |
| scope | per column over the whole table is the default and needs no words; any other scope (per task block, per row) is stated once, in the caption's mark sentence ("best per task and column in bold") | reading: bold explained in 0 of 16 Kaiming bold-best tables, a mark rule stated in 4 of 24, all non-standard; SOLO audit: Tabs. 10 and 11 follow per-block and per-row scopes their captions never state |
| how many | at most **40 %** of the ranked cells (`MARKED_MAX`); with blocks of four rows or fewer, bold only | best and second in blocks of five mark 40 %; SOLO Tab. 4 marks 56 %, Tab. 10 53 %, Tab. 11 68 % |
| colour | never a mark by colour alone; colour carries a finding (a green delta, a grey reference row), not a rank | reading: Kaiming's colour carries a finding (green deltas, red and green cells, grey de-emphasis), never a rank; colour-only marks are one of the four causes of a weak table; notes: D-Flow Tab. 1 ranks by cell shading alone and DDRM Tabs. 1 and 2 mark the second in blue alone, neither explained |
| arrows | ↑ or ↓ in the header of every ranked column, `PSNR~$\uparrow$`; none on a column that is not ranked (NFE, seconds) | survey: arrows in 66 % of inverse tables, 16 % of Kaiming's (top-1 and AP have one obvious direction), SOLO 91 %; the audit reads each column's direction from its arrow |

## 7. Numbers

| rule | value | source |
| --- | --- | --- |
| decimals | PSNR 2, SSIM 3, LPIPS 3, FID 1, NFE 0, seconds 2; one precision per metric in every table of the paper | survey: inverse papers print 2 for PSNR and FID and 3 for SSIM and LPIPS, Kaiming 1 decimal in 64 % of his tables. FID keeps 1 because its estimator noise at n = 1000 is 0.5 to 1 (SOLO `CLAUDE.md`), so a second decimal is noise |
| rounding | half-up at the printed precision, from the shortest decimal form (0.0785 prints 0.079) | `fmt()`; the SOLO table builders round half-up |
| a missing value | `--`, meaning not run, and said once | SOLO audit: a dash means not run in Tab. 2, nothing trained in Tab. 3, not applicable in Tab. 8 |
| ± | not in a main table; the per-image spread or the paired bootstrap goes to the supplement | survey: ± in 8 % of tables; SOLO rules: the error bar is the paired bootstrap over images |
| one precision per column | the audit warns on a numeric column with two decimal counts | SOLO audit: Tab. 7's NFE column mixes 8.9 with integers; seconds print at 1 decimal in Tab. 9 and 2 in Tab. 1 |

## 8. Naming

| rule | value | source |
| --- | --- | --- |
| one name per method, metric, task and dataset | the same spelling in every table, caption, figure and paragraph, fixed in a canon file of display names and forbidden variants, checked by `check_names()` and `audit_tables.py --canon`; a lapse is a FAIL | SOLO audit: 37 concepts spelled 124 ways, among them Gaussian deblurring as "Blur" (Tabs. 10, 11), NFE as "Prior evals" (Tab. 9), one prior's model name in three forms (Tab. 2), CelebA-128 as "CelebA 128²" (Tab. 1), FlowDPS as "FLowDPS" |
| headers | the canonical name plus the arrow; no abbreviation the text never introduces | SOLO audit: "SR" in Tab. 10, "OT" and "CFG" in Tab. 8 are introduced nowhere |
| row labels | every symbol defined in the caption or the text | SOLO audit: Tab. 6's g₁ and k₁ are defined nowhere |
| figure scripts | passed to `check_names()` with the `.tex` files, since a figure's labels are the same names | SOLO audit: three method names occur only in figure legends, spelled as the text never spells them |

The canon is a YAML file; an entry is a name, or a name with the variants it forbids, under any category key.
Variants are matched in the LaTeX source as written, case-sensitively, and never inside a canonical name ("Box" is
not reported inside "Box inpainting"). A name with a capital after its first letter is also reported in any other
casing ("FLowDPS" for FlowDPS) without being listed:

```yaml
methods:
  flowdps: FlowDPS
  pnpflow: {name: PnP-Flow, forbid: [PnPFlow, PnP Flow]}
tasks:
  gauss: {name: Gaussian deblurring, forbid: [Blur, Gaussian blur, Deblurring]}
  box: {name: Box inpainting, forbid: [Box, Box inpaint]}
metrics:
  nfe: {name: NFE, forbid: [Prior evals]}
datasets:
  celeba: {name: CelebA-128, forbid: ["CelebA $128^2$"]}
```

## 9. Data and message

| rule | value | source |
| --- | --- | --- |
| every number | from the result files, by the table's own builder, deduplicated by row key; never typed, never copied from another table | SOLO audit: seven run times of one of our rows in Tab. 9 disagree with Tab. 1, copied before the method's code changed |
| verified | `verify()` returns nothing before any commit that touches the table | a stale number keeps its mark consistent, so only a check against the data sees it (the RED test of `examples/test_tables.py`) |
| a shared cell | one protocol, one value: a cell two tables share holds the same number | SOLO audit: a row of Tab. 11 does not reproduce the matching column of Tab. 10 under the same stated protocol (a different problem draw) |
| the caption's protocol | read from the run configuration, not from memory | SOLO audit: Tab. 2's caption states one noise level for all seven tasks, wrong for two of them |
| the message | one sentence the table exists to support, written before it is built; the layout brings it out (a Δ column when the claim is a loss relative to a reference) and a results paragraph states it | SOLO audit: Tab. 11 ranks absolute PSNR while its claim is the loss against a reference row; Tab. 3's prose makes per-task claims the table cannot show |
| cited and discussed | every table cited in the text, with a results paragraph | SOLO audit: Tabs. 7 and 9 are never cited; Tabs. 1, 2, 6, 7 and 9 have no results prose |

## 10. Workflow

1. **Spec.** Write the one sentence the table must let a reader check. Define the columns and rows once, with the
   canonical names, and the canon file.
2. **Build.** A loader reads the result files and deduplicates by row key; `header()` and `build()` write the body.

   ```python
   import sys; sys.path.insert(0, "<this skill's base directory>")
   from academic_figure.tables import Column, Row, header, build, verify

   cols = [Column("nfe", "NFE", None, 0), Column("psnr", "PSNR", "+", 2), Column("ssim", "SSIM", "+", 3),
           Column("lpips", "LPIPS", "-", 3), Column("fid", "FID", "-", 1)]
   rows = [Row("pnpflow", "PnP-Flow", "Training-free"), Row("flower", "Flower", "Training-free"),
           Row("ram", "RAM", "Supervised"), Row("ours", "Ours", ours=True), Row("ours5", r"Ours$\times5$", ours=True)]
   value = lambda r, c: results[r].get(c)                  # None prints --
   body = header(cols, ["Type", "Method"]) + "\n" + build(cols, rows, value)   # scope="group" for task blocks
   ```

   The body goes between `\begin{tabular}{@{}ll rrrrr@{}}` and `\bottomrule`; `second=False` gives bold only.

   A difference the text cites is computed, never typed. `improvement(cols, rows, value)` gives our row minus the
   best other row per ranked column, from the printed values ($+$0.16, $-$0.001, 0.000; `relative=True` for a
   percentage), and `build(..., delta=r"$\Delta$ over the best baseline")` prints it as a last row under a
   `\midrule`, never marked. The label starts with Δ, which is how the audit finds the row: it leaves it out of the
   marks and the decimals and recomputes every cell from the printed cells (FAIL on a mismatch). A component
   ablation's ✓ columns come from `component_columns([(key, header)], {row: "101"}, values=value)`: unranked text
   columns (`c` in the column spec, `amssymb` for `\checkmark`), which refuse a code of the wrong length and two rows
   with one code, and whose value_fn hands every other column to `values`.
3. **Verify.** `verify("sec/experiments.tex", "tab:main", cols, rows, value)` lists every cell whose number or mark
   differs from the data, every row missing on either side and every header that is not its column's name and arrow.
   It must return `[]`.
4. **Audit.** `uv run --with pyyaml python scripts/audit_tables.py <paper_dir> --canon names.yaml` reads every live
   `.tex` file, needs no spec, and must print no FAIL; each WARN is fixed or answered in one line.
5. **Compile.** Zero errors, no overfull box from a table, the page count expected.
6. **Read the render.** At print size: do the marks point at the claim, do the tint and the dashed rule find ours at
   a glance, does anything wrap or collide, does the caption say only what the table cannot?

## 11. Common mistakes, from the SOLO audit

| mistake | table | what happened | the rule |
| --- | --- | --- | --- |
| ties broken on unrounded means | `tab:main`, `tab:latent` | 14 marks the printed values do not earn: 9 tied cells marked differently, 5 runners-up after a tied best left bare | rank on the printed value (section 6) |
| a scope nobody states | `tab:robust-noise`, `tab:robust-operator` | marks per σ_y block and per row, captions silent | state a non-default scope once |
| half the table marked | `tab:supervised` 56 %, `tab:robust-noise` 53 %, `tab:robust-operator` 68 % | best and second in scopes of two to four rows | at most 40 %; bold only in small scopes |
| marks with no direction | `tab:robust-noise` | 40 marks in the per-task columns Blur, SR, Box, Motion, which carry no arrow | an arrow on every ranked column |
| captions that carry the argument | all 11 | 64 to 130 words, 9 over 80; the caption blocks of `tab:amortised`, `tab:supervised` and `tab:mri` taller than their tables | 25 to 50 words (section 1) |
| a caption that restates the header | `tab:main` | every column head with its arrow, NFE and time redefined | the header carries its own names |
| stale numbers | `tab:supp-celeba-full` | seven run times of one of our rows disagree with `tab:main` | build from the result files; `verify()` |
| a protocol from memory | `tab:latent` | one noise level stated for every task | read the run configuration |
| off-canon names | `tab:robust-noise`, `tab:robust-operator`, `tab:supp-celeba-full`, `tab:latent` | Blur, SR, Box, Motion; "Prior evals" for NFE; three forms of one model name | the canon and `check_names()` |
| full-page floats | `tab:main`, `tab:latent` | `[p]` pushed all seven main tables past the references | `[t]` |
| a column repeated per group | `tab:mri`, `tab:latent` | identical NFE columns; 18 numeric columns at `\tabcolsep` 1.5 pt | a constant column once |
| one device, three meanings | `tab:ablation`, `tab:sensitivity`, `tab:robust-operator` | the tint means our rows, the reported setting, our columns | one meaning per device |
| mixed precision | `tab:sensitivity`, `tab:supp-celeba-full` | NFE 8.9 among integers; seconds at 1 decimal against 2 in `tab:main` | one precision per metric |
| centred numbers | `tab:main` | decimal points drift 1.8 pt | `r` columns |
| a table no text discusses | `tab:sensitivity`, `tab:supp-celeba-full` | never cited; five tables have no results prose | cite and state the message |

## 12. The evidence, and its limits

- **Survey.** Caption words are the rendered tokens after the "Table n." label; `caption_words()` counts the LaTeX
  source the same way (a maths group one word, `\cref` two) and agrees within one word with the SOLO audit's count of
  the rendered captions on all 11 tables, within four with `measure_tables.py`'s. The main text ends at the
  References heading. DyT's captions are undercounted (first line only), and the sub-captions of Mask R-CNN Tab. 2
  and MAE Tab. 1 are not counted.
- **Thin.** The caption thresholds of 50 and 80 words are set from distributions (the Kaiming headline median and
  the 98th percentile of the survey), not from any acceptance outcome. Dense ranking of ties has no count behind it:
  the reading did not record how flagship tables break ties, and dense ranking is chosen because it keeps the rule
  on printed values and is what SOLO Tab. 3 states. The 40 % marked ceiling and the three-row floor for a second mark
  rest on SOLO's own tables. "Underline only when the runner-up matters" sets Kaiming (0 of 24) against the inverse
  papers (26 %), two fields that disagree. Caption position splits the same way (Kaiming below in 97 %, restoration
  above in 78 %); the rule follows the CVPR template. FID at 1 decimal departs from the inverse papers' 2 on SOLO's
  estimator-noise measurement alone. The `[t]` placement rule and the 16-column ceiling come from SOLO, not from the
  421-table survey. The notes and the reading overlap in DAPS, DDNM, DPS and MAE and were made by different readers.
- **What the audit cannot see.** It reads the source, not the PDF: type size, overfull boxes, a table that prints
  after the references, and a tint that fails to show are checked by compiling and reading the render. It infers
  the mark scope from the marks (per column, per block between `\midrule`s, or per row across columns of one name),
  so a table whose rule is none of these reports its mismatches under the closest one. It cannot tell a stale number
  from a fresh one; only `verify()` against the result files can.
