# What a reviewer checks

An area chair reads a figure at print size, on a page, in about three seconds, and then again only if it earned a
second look. The checks below are in the order they are noticed. Each one names the rule of `contract.md` that
prevents the failure.

## The three-second read

1. **Is the claim visible before the caption?** The figure has one message, and the eye lands on it: our curve in
   the only accent, the operating point enlarged with its value, the ratio on a dimension line. (Rule 3 of
   `SKILL.md`; contract §6.)
2. **Can I read it?** No type under 6 pt at print size; nothing drawn big and scaled down. The most common single
   reason a figure is marked "unreadable". (§1, §2.)
3. **Does a baseline's failure show without zooming?** If the failure is texture, the inset shows it; if it cannot
   be seen at print size, the image is the wrong one. (§7.)

## The second look

4. **Is each baseline at the setting its authors used?** A point at a budget a method was never run at invites the
   objection that it was sandbagged. A single point at its own published setting is the honest construction. (§6.)
5. **Is the comparison fair?** The same test set, protocol and budget unit across every point on an axis, and `n`
   in the caption. (§9.)
6. **Does the axis hide anything?** A truncated bar axis, a log axis not labelled as log, a second y axis, a range
   that clips a crossing. (§5.)
7. **Is colour doing one job?** Ours is one hue in every figure, table and plot; a colour that means "correction" in
   Figure 2 does not mean "baseline" in Figure 5. And it survives greyscale: series separate by dash and marker too.
   (§3.)
8. **Is the error defined?** Every error bar or band states SD, SEM or a confidence interval, and over what unit.
   (§9.)

## What reads as generated

Reviewers now recognise the look of a figure no author checked: labels colliding, a legend box covering data,
default matplotlib blue, DejaVu Sans, `10^0` tick labels, a title inside the axes, shadows and gradients, an "Ours"
badge or a red ring round the contribution, two panels saying one thing. Every item is either forbidden by the
contract or failed by `save()`.

## What earns a figure its place

A figure that makes a reader stop is almost always one of three: a result grid where the baselines visibly fail
and ours does not (DAPS Fig. 1); a frontier where ours owns the corner the others cannot reach (DAPS Fig. 6); or the
problem itself made visible (ResNet's degradation curve). Restraint is what lets it land: one or two hues, one type
size, no decoration, the numbers in the tables.
