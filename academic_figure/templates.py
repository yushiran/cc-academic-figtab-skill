"""The recurring figures of an ML paper, drawn to the contract, so a new paper copies a call instead of a style.

budget  quality against compute: ours swept as a curve, every baseline a single labelled point at its own
        published setting, a dimension line naming the ratio. DAPS Fig. 6 and CLAMP Fig. 3 are this construction.
grid    a result grid for a qualitative figure, a teaser block or a supplementary sample grid: 2.5 pt seams (the
        measured median), headers above, one row of numbers below, column blocks, rotated row labels, and a zoom as
        an inset in a free corner or as a crop row. references/qualitative.md gives the numbers and the exemplars.
mixed_label  one label that is part symbol and part words: the symbol in Computer Modern at 8 pt, the words in
        Arimo at 6.5 pt, on one baseline. matplotlib cannot size the two parts of one Text differently.
"""
from __future__ import annotations

from pathlib import Path

from . import contract as C

_CANDIDATES = ((4, 0, "left", "center"), (-4, 0, "right", "center"), (0, 5, "center", "bottom"),
               (0, -5, "center", "top"), (4, 4, "left", "bottom"), (4, -4, "left", "top"),
               (-4, 4, "right", "bottom"), (-4, -4, "right", "top"))


def _collides(bb, placed, markers, pad):
    for p in placed:
        if min(bb.x1, p.x1) - max(bb.x0, p.x0) > -pad and min(bb.y1, p.y1) - max(bb.y0, p.y0) > -pad:
            return True
    return any(bb.x0 - r < x < bb.x1 + r and bb.y0 - r < y < bb.y1 + r for x, y, r in markers)


def _lead_dirs():
    """16 directions, the ones nearest the horizontal first (a label reads best beside its point), each with the
    alignment that keeps the label on the far side of its anchor."""
    import math
    out = []
    for deg in (0, 22.5, -22.5, 45, -45, 180, 157.5, -157.5, 135, -135, 67.5, -67.5, 90, -90, 112.5, -112.5):
        ux, uy = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        out.append((ux, uy, "left" if ux > 0.3 else "right" if ux < -0.3 else "center",
                    "bottom" if uy > 0.3 else "top" if uy < -0.3 else "center"))
    return tuple(out)


_LEAD_DIRS = _lead_dirs()


def _near_segment(p, q, markers):
    """Whether the segment p-q (display units) passes over any (x, y, r) marker."""
    (x0, y0), (x1, y1) = p, q
    L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2 or 1e-9
    for mx, my, r in markers:
        s = max(0.0, min(1.0, ((mx - x0) * (x1 - x0) + (my - y0) * (y1 - y0)) / L2))
        if (x0 + s * (x1 - x0) - mx) ** 2 + (y0 + s * (y1 - y0) - my) ** 2 < r * r:
            return True
    return False


def _lead_out(ax, name, xy, color, placed, markers, renderer, px, paths=()):
    """The label stepped outwards from its point (C.LEADER_STEPS) to the first spot inside the axes that collides with
    nothing and lies on no line of `paths`, joined to the point by a hairline leader that crosses no label and no
    marker; None when nothing is free."""
    from matplotlib.path import Path as MPath
    X, Y = ax.transData.transform(xy)
    others = [(mx, my, r) for mx, my, r in markers if abs(mx - X) > 0.5 or abs(my - Y) > 0.5]
    box = ax.bbox
    for dist in C.LEADER_STEPS:
        for ux, uy, ha, va in _LEAD_DIRS:
            t = ax.annotate(name, xy, xytext=(dist * ux, dist * uy), textcoords="offset points", ha=ha, va=va,
                            color=color)
            bb = t.get_window_extent(renderer)
            sx, sy = min(max(X, bb.x0), bb.x1), min(max(Y, bb.y0), bb.y1)      # the label's edge nearest the point
            seg = MPath([(sx, sy), (X, Y)])
            inside = box.x0 <= bb.x0 and bb.x1 <= box.x1 and box.y0 <= bb.y0 and bb.y1 <= box.y1
            if inside and not _collides(bb, placed, others, 0.6 * px) and not any(seg.intersects_bbox(p) for p in placed) \
                    and not _near_segment((sx, sy), (X, Y), others) \
                    and not any(p.intersects_bbox(bb.padded(0.4 * px), filled=False) for p in paths):
                placed.append(bb)
                lead = ax.annotate("", xy, xytext=((sx - X) / px, (sy - Y) / px), textcoords="offset points",
                                   arrowprops=dict(arrowstyle="-", color=C.CONNECTOR, lw=C.HAIR_W, shrinkA=0.8,
                                                   shrinkB=C.MARKER / 2 + 0.6))
                lead._af_leader_of = t                               # the audit checks that it crosses no label
                return t
            t.remove()
    return None


def _line_paths(ax):
    """The drawn lines of an axes as display-unit paths (a marker-only line draws no path)."""
    return [ln.get_transform().transform_path(ln.get_path()) for ln in ax.get_lines()
            if ln.get_visible() and ln.get_linestyle() not in ("None", "none", "", " ")]


def _first_clear(ax, anchor, make, candidates):
    """Build a label with each candidate in turn, make(candidate) returning its artists, and keep the first whose
    extent lies on no drawn line, no marker but the anchor's and no other text; when none is clear, the first, for the
    audit to judge."""
    from matplotlib.transforms import Bbox
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    paths = _line_paths(ax)
    X, Y = ax.transData.transform(anchor)
    markers = []
    for ln in ax.get_lines():
        if ln.get_marker() not in (None, "", "None", " "):
            r = ln.get_markersize() * px / 2
            markers += [(mx, my, r) for mx, my in ax.transData.transform(ln.get_xydata())
                        if abs(mx - X) > 0.5 or abs(my - Y) > 0.5]
    placed = [t.get_window_extent(renderer) for t in ax.texts if t.get_text()]
    first = None
    for cand in candidates:
        arts = make(cand)
        bb = Bbox.union([a.get_window_extent(renderer) for a in arts])
        if not any(p.intersects_bbox(bb.padded(0.4 * px), filled=False) for p in paths) \
                and not _collides(bb, placed, markers, 0.6 * px):
            for a in first or []:
                a.remove()
            return arts
        if first is None:
            first = arts
        else:
            for a in arts:
                a.remove()
    return first


def place_labels(ax, points, color=C.CONNECTOR, fixed=None, candidates=None, leader=False, inside=False,
                 avoid_lines=False):
    """Label each (name, x, y) beside its marker at the first candidate spot that collides with nothing placed yet
    and no marker. `fixed` maps a name to (dx, dy, ha, va) to override; `candidates` replaces the default spots
    (right, left, above, below, the four diagonals) with a tuple of (dx, dy, ha, va). With `leader`, a label that
    fits nowhere beside its point steps outwards to the first free spot and is joined to it by a 0.3 pt leader in
    the connector grey; with `inside`, a spot that reaches past the axes does not count as free; with `avoid_lines`,
    neither does one on a drawn line. A label that found no free spot is marked `_af_fallback`. Returns the Text
    artists."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    markers = []
    for ln in ax.get_lines():
        if ln.get_marker() not in (None, "", "None", " "):
            r = ln.get_markersize() * px / 2
            markers += [(x, y, r) for x, y in ax.transData.transform(ln.get_xydata())]
    placed = [t.get_window_extent(renderer) for t in ax.texts]
    paths = _line_paths(ax) if avoid_lines else []
    out = []
    for name, x, y in points:
        tries = [fixed[name]] if fixed and name in fixed else (candidates or _CANDIDATES)
        for dx, dy, ha, va in tries:
            t = ax.annotate(name, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, color=color)
            bb = t.get_window_extent(renderer)
            own = [(mx, my, r) for mx, my, r in markers if abs(mx - ax.transData.transform((x, y))[0]) > 0.5
                   or abs(my - ax.transData.transform((x, y))[1]) > 0.5]
            # if fixed and name in fixed or not _collides(bb, placed, own, 0.6 * px):
            box = ax.bbox
            within = not inside or (bb.x0 >= box.x0 - 0.5 * px and bb.x1 <= box.x1 + 0.5 * px
                                    and bb.y0 >= box.y0 - 0.5 * px and bb.y1 <= box.y1 + 0.5 * px)
            clear = not any(p.intersects_bbox(bb.padded(0.4 * px), filled=False) for p in paths)
            if fixed and name in fixed or (within and clear and not _collides(bb, placed, own, 0.6 * px)):
                placed.append(bb)
                out.append(t)
                break
            t.remove()
        else:                                              # nothing fits: keep the first spot and let the audit say so
            # out.append(ax.annotate(name, (x, y), xytext=_CANDIDATES[0][:2], textcoords="offset points",
            #                        ha="left", va="center", color=color))
            t = _lead_out(ax, name, (x, y), color, placed, markers, renderer, px, paths) if leader else None
            if t is None:
                dx, dy, ha, va = tries[0]
                t = ax.annotate(name, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, color=color)
                t._af_fallback = True
            out.append(t)
    return out


def mixed_label(ax, xy, parts, xytext=(0, 0), color=C.INK, ha="left", xycoords="data"):
    """parts = [("$N{=}4$", "math"), (", 33.96 dB", "word")]: laid left to right on one baseline. `xycoords` as
    for annotate, so ("axes fraction", "data") anchors a row label at the axes edge. The run is set with
    va="baseline", so to centre it on a marker give xytext a dy of about -2."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    x_off, arts = xytext[0], []
    for text, kind in parts:
        size = C.MATH_PT if kind == "math" else C.WORD_PT
        t = ax.annotate(text, xy, xycoords=xycoords, xytext=(x_off, xytext[1]), textcoords="offset points", ha="left",
                        va="baseline", color=color, fontsize=size, annotation_clip=False)
        x_off += t.get_window_extent(renderer).width / px
        arts.append(t)
    if ha != "left":                                       # shift the whole run so its anchor is right or centre
        shift = -(x_off - xytext[0]) * (1.0 if ha == "right" else 0.5)
        for t in arts:
            dx, dy = t.xyann
            t.xyann = (dx + shift, dy)
    return arts


def mixed_xlabel(ax, parts, color=C.INK, labelpad_pt=4.0):
    """An x-axis label that is part symbol and part words, set like mixed_label: the symbol in Computer Modern at
    8 pt, the words in Arimo at 6.5 pt, centred under the axes one label pad below the tick labels, where
    set_xlabel would put it. Maths inside set_xlabel renders at the word size, where Computer Modern's x-height is
    a fifth under Arimo's and the symbol reads small; this is the way round it."""
    fig = ax.figure
    ax.set_xlabel("")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    low = min([ax.bbox.y0] + [t.get_window_extent(renderer).y0 for t in ax.get_xticklabels() if t.get_text()])
    y_off = -((ax.bbox.y0 - low) / px + labelpad_pt + 0.9 * C.WORD_PT)   # baseline one ascent under the label's top
    x_off, arts = 0.0, []
    for text, kind in parts:
        size = C.MATH_PT if kind == "math" else C.WORD_PT
        t = ax.annotate(text, (0.5, 0.0), xycoords="axes fraction", xytext=(x_off, y_off), textcoords="offset points",
                        ha="left", va="baseline", color=color, fontsize=size, annotation_clip=False)
        x_off += t.get_window_extent(renderer).width / px
        t._af_axis_label = "x"                             # the audit reads it as the axis label (a log axis says so)
        arts.append(t)
    for t in arts:                                         # centre the run on the axes
        dx, dy = t.xyann
        t.xyann = (dx - x_off / 2, dy)
    return arts


def mixed_ylabel(ax, parts, color=C.INK, labelpad_pt=4.0):
    """A y-axis label that is part symbol and part words, set like mixed_xlabel but rotated to read bottom to top:
    the symbol in Computer Modern at 8 pt, the words in Arimo at 6.5 pt, on one baseline, centred on the axes one
    label pad left of the widest tick label. The bundled Arimo has no Delta or sigma, so "ΔPSNR (dB)" is
    [("$\\Delta$", "math"), ("PSNR (dB)", "word")]."""
    fig = ax.figure
    ax.set_ylabel("")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    left = min([ax.bbox.x0] + [t.get_window_extent(renderer).x0 for t in ax.get_yticklabels() if t.get_text()])
    gap = (ax.bbox.x0 - left) / px + labelpad_pt                # pt from the axes' left edge to the label's right edge
    y_off, arts = 0.0, []
    for text, kind in parts:
        size = C.MATH_PT if kind == "math" else C.WORD_PT
        t = ax.annotate(text, (0.0, 0.5), xycoords="axes fraction", xytext=(-gap, y_off), textcoords="offset points",
                        rotation=90, rotation_mode="anchor", ha="left", va="baseline", color=color, fontsize=size,
                        annotation_clip=False)
        y_off += t.get_window_extent(renderer).height / px
        t._af_axis_label = "y"
        arts.append(t)
    fig.canvas.draw()
    right = max(t.get_window_extent(renderer).x1 for t in arts)
    dx = (ax.bbox.x0 - gap * px - right) / px                  # the run's descent side, `gap` left of the axes
    for t in arts:                                             # and centred on the axes' height
        x, y = t.xyann
        t.xyann = (x + dx, y - y_off / 2)
    return arts


def declare_errors(fig, kind):
    """What the error bars or bands of this figure are, in the words the caption uses: "95 % paired-bootstrap CI over
    the 1000 test images". The audit warns on bars or bands with no stated kind and fails a figure given two."""
    fig._af_errors = list(getattr(fig, "_af_errors", [])) + [str(kind)]
    return fig


def budget(ax, ours, baselines, operating=None, compare_to=None, reference=None, label_fixed=None,
           xlabel="prior evaluations per image (log scale)", ylabel="PSNR (dB)", unit="dB", ticks=None,
           ours_name="Ours", operating_symbol="N", ratio_text="{r:.0f}$\\times$ fewer prior evaluations",
           operating_offset=(2, -11)):
    """Quality against compute.

    ours      [(x, y, n)] swept, n the budget parameter of each point (N)
    baselines [(name, x, y)] one point each at its published setting
    operating the n of the point the tables report; drawn larger and labelled with its value
    compare_to the baseline name the dimension line measures against, normally the strongest
    reference (name, y) a level with no place on the x axis, such as a feedforward network: a dashed line
    """
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator
    if reference is not None:
        ax.axhline(reference[1], color=C.BASELINE, lw=C.WORK_W, ls=C.DASH_REFERENCE, zorder=1)
    for name, x, y in baselines:
        ax.plot(x, y, "o", color=C.BASELINE, ms=C.MARKER, zorder=3)
    xs, ys = [o[0] for o in ours], [o[1] for o in ours]
    ax.plot(xs, ys, "-o", color=C.ACCENT, lw=C.OURS_W, ms=C.MARKER, zorder=5)
    op = next((o for o in ours if o[2] == operating), None)
    if op is not None:
        ax.plot(op[0], op[1], "o", color=C.ACCENT, ms=C.MARKER_OPERATING, mec=C.PAPER,
                mew=C.MARKER_EDGE_OPERATING, zorder=6)
    ax.set_xscale("log")
    if ticks:
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in ticks]))
        ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    top = None
    if op is not None and compare_to is not None:
        cx, cy = next((x, y) for n, x, y in baselines if n == compare_to)
        top = max(op[1], cy) + 0.06 * (max(ys + [y for _, _, y in baselines]) - min(ys + [y for _, _, y in baselines]))
        for x, y in ((op[0], op[1]), (cx, cy)):
            ax.plot([x, x], [y, top], color=C.INK, lw=C.HAIR_W, ls=C.DASH_GUIDE, zorder=2)
        ax.annotate("", xy=(op[0], top), xytext=(cx, top),
                    arrowprops=dict(arrowstyle="<->", color=C.INK, lw=C.WORK_W, shrinkA=0, shrinkB=0, mutation_scale=5))
        ax.annotate(ratio_text.format(r=cx / op[0]), ((op[0] * cx) ** 0.5, top), xytext=(0, 2.5),
                    textcoords="offset points", ha="center", va="bottom", color=C.INK)
    lo, hi = ax.get_ylim()
    if top is not None:
        ax.set_ylim(lo, max(hi, top + 0.08 * (hi - lo)))
    if reference is not None:                              # x in axes fraction: a later set_xlim cannot push it out
        ax.annotate(reference[0], (0.01, reference[1]), xycoords=("axes fraction", "data"), xytext=(0, 2.5),
                    textcoords="offset points", ha="left", va="bottom", color=C.CONNECTOR)
    ax.annotate(ours_name, (xs[-1], ys[-1]), xytext=(5, 0), textcoords="offset points", ha="left", va="center",
                color=C.INK)
    if op is not None:
        mixed_label(ax, (op[0], op[1]), [(f"${operating_symbol}\\!=\\!{operating}$", "math"),   # the paper's tight $N{=}4$
                                         (f", {op[1]:.2f} {unit}", "word")], xytext=operating_offset)
    place_labels(ax, baselines, fixed=label_fixed)
    return ax


_END = ((4, 0, "left", "center"), (4, 4, "left", "bottom"), (4, -4, "left", "top"), (0, 5, "center", "bottom"),
        (0, -5, "center", "top"))                          # a curve's name: beside its last point, right first


def sweep(ax, x, series, reported=None, reference=None, xlabel="", ylabel="", unit="dB", categorical=False, log=False,
          reported_symbol="N", reported_offset=(2, -11), decimals=2, label_fixed=None):
    """One setting swept: an ablation, a sensitivity or a robustness curve, one panel per metric sharing x (contract
    section 6). The idea follows the one-setting sweeps surveyed in figures4papers; no code is taken from it.

    x          the swept values in order; they are the ticks, so no tick sits at a value that was never run
    series     [(name, ys, role)], role "ours", "variant" (a retrained or ablated version of ours: its own Tol muted
               colour, dash and marker) or "baseline" (the baseline grey); a None in ys is a setting not run, drawn as a
               gap and never interpolated
    reported   the x the tables report: ours enlarged there and labelled with its value; refused when it was not swept
    reference  (name, y), a level with no place on the x axis, dashed, as in budget()
    categorical  non-uniform settings (sigma_y 0.01, 0.05, 0.1, 0.2) spaced equally, their values as the tick labels
    log        a log axis with the swept values as ticks; the xlabel then says "(log scale)"
    Each name goes beside its curve's last point, with no legend; the x limit grows so the names stay in the axes."""
    import math

    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

    from .tables import fmt
    xs = list(x)
    if reported is not None and reported not in xs:
        raise ValueError(f"reported={reported} is not one of the swept values {xs}: a setting never run cannot be the "
                         f"operating point")
    pos = list(range(len(xs))) if categorical else xs
    if log and not categorical:
        ax.set_xscale("log")
    if reference is not None:
        ax.axhline(reference[1], color=C.BASELINE, lw=C.WORK_W, ls=C.DASH_REFERENCE, zorder=1)
    ends, ours, k = [], None, 0
    for name, ys, role in series:
        if len(ys) != len(xs):
            raise ValueError(f"{name}: {len(ys)} values for {len(xs)} settings")
        yv = [float("nan") if v is None else float(v) for v in ys]
        if role == "ours":
            style, colour, ours = dict(color=C.ACCENT, lw=C.OURS_W, marker="o", ms=C.MARKER, zorder=5), C.INK, yv
        elif role == "variant":
            style = dict(color=C.SERIES_MUTED[k % len(C.SERIES_MUTED)], lw=C.DATA_W,
                         ls=C.SERIES_DASHES[1 + k % (len(C.SERIES_DASHES) - 1)],
                         marker=C.SERIES_MARKERS[1 + k % (len(C.SERIES_MARKERS) - 1)], ms=C.MARKER, zorder=4)
            colour, k = C.INK, k + 1
        elif role == "baseline":
            style, colour = dict(color=C.BASELINE, lw=C.DATA_W, marker="o", ms=C.MARKER, zorder=3), C.CONNECTOR
        else:
            raise ValueError(f"{name}: role is 'ours', 'variant' or 'baseline', not {role!r}")
        ax.plot(pos, yv, label=name, **style)                  # the label only feeds the legend fallback
        run = [i for i, v in enumerate(yv) if not math.isnan(v)]
        if not run:
            raise ValueError(f"{name}: no setting was run")
        ends.append((name, [(pos[i], yv[i]) for i in reversed(run)], colour))        # the last point first
    ax.xaxis.set_major_locator(FixedLocator(pos))
    ax.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in xs]))
    ax.xaxis.set_minor_locator(NullLocator())
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    if reported is not None:
        if ours is None:
            raise ValueError("reported= needs a series with role 'ours'")
        i_rep = xs.index(reported)
        if math.isnan(ours[i_rep]):
            raise ValueError(f"ours has no value at the reported setting {reported}")
        ax.plot(pos[i_rep], ours[i_rep], "o", color=C.ACCENT, ms=C.MARKER_OPERATING, mec=C.PAPER,
                mew=C.MARKER_EDGE_OPERATING, zorder=6)
    # room on the right for the names, closed form: a name d + w wide beside a point at x_a ends inside the axes when
    # (x_a - lo) / (hi - lo) <= 1 - (d + w) / W, in log units on a log axis
    f = math.log10 if ax.get_xscale() == "log" else (lambda v: v)
    finv = (lambda u: 10 ** u) if ax.get_xscale() == "log" else (lambda u: u)
    lo, hi = ax.get_xlim()
    widths = {}
    for name, _, _ in ends:
        t = ax.text(0, 0, name)
        widths[name] = t.get_window_extent(renderer).width
        t.remove()

    def room(names):
        need = hi
        for name, run_pts, _ in ends:
            share = 1 - (5.0 * px + widths[name]) / ax.bbox.width
            if name in names and share > 0.4:
                need = max(need, finv(f(lo) + (f(run_pts[0][0]) - f(lo)) / share))
        return need

    def layout(xmax, names=True):
        """Set the x limit and write every label: the operating point's value, the reference's name, then each
        series' name beside its last point, else beside an earlier point of its curve, else led out from the last."""
        ax.set_xlim(lo, xmax)
        made, at_end = [], []
        if reported is not None:
            xy = (pos[i_rep], ours[i_rep])
            parts = [(f"${reported_symbol}\\!=\\!{reported:g}$", "math"),
                     (f", {fmt(ours[i_rep], decimals)} {unit}".rstrip(), "word")]
            dx, dy = reported_offset                           # the given spot first, then the other three corners
            spots = [((dx, dy), "left"), ((dx, 5.0), "left"), ((-dx, dy), "right"), ((-dx, 5.0), "right")]
            made += _first_clear(ax, xy, lambda s: mixed_label(ax, xy, parts, xytext=s[0], ha=s[1]), spots)
        if reference is not None:
            made.append(_reference_label(ax, reference[0], reference[1]))
        for name, run_pts, colour in (ends if names else []):
            for j, (xa, ya) in enumerate(run_pts):
                t = place_labels(ax, [(name, xa, ya)], color=colour, fixed=label_fixed,
                                 candidates=_END if j == 0 else _CANDIDATES, inside=True, avoid_lines=True)[0]
                if not getattr(t, "_af_fallback", False):
                    break
                t.remove()
            else:
                j = None
                t = place_labels(ax, [(name, *run_pts[0])], color=colour, candidates=_END, leader=True, inside=True,
                                 avoid_lines=True)[0]
            made.append(t)
            if j == 0 and t.get_ha() == "left":
                at_end.append(name)
        return made, at_end

    def clear(made):
        for a in [a for a in ax.texts if getattr(a, "_af_leader_of", None) in made] + made:
            a.remove()

    x_all = room([e[0] for e in ends])
    made, at_end = layout(x_all)
    if any(getattr(t, "_af_fallback", False) for t in made[len(made) - len(ends):]):
        clear(made)                                            # a name that fits nowhere: every name in a frameless
        layout(hi, names=False)                                # legend clear of the data (contract section 5)
        _free_legend(ax, [e[0] for e in ends])
        return ax
    x_end = room(at_end)                                       # the room only the names at a curve's end need
    if x_end < x_all:
        misses = sum(bool(getattr(t, "_af_fallback", False)) for t in made)
        clear(made)
        made2, at_end2 = layout(x_end)
        if sum(bool(getattr(t, "_af_fallback", False)) for t in made2) > misses or set(at_end2) != set(at_end):
            clear(made2)
            layout(x_all)
    return ax


def _free_legend(ax, names):
    """A frameless legend of `names` in the first corner or side of the axes where it covers no data and no label,
    else in a row under the axes."""
    from .audit import _covers_data
    fig = ax.figure
    handles = {label: h for h, label in zip(*ax.get_legend_handles_labels())}
    hs = [handles[n] for n in names if n in handles]
    renderer = fig.canvas.get_renderer()
    for loc in ("lower right", "upper left", "lower left", "upper right", "center right", "center left",
                "lower center", "upper center"):
        leg = ax.legend(hs, names, loc=loc, frameon=False)
        fig.canvas.draw()
        bb = leg.get_window_extent(renderer)
        texts = [t.get_window_extent(renderer) for t in ax.texts if t.get_text()]
        if not _covers_data(ax, bb, renderer) and not any(bb.overlaps(t) for t in texts):
            return leg
        leg.remove()
    low = (ax.get_tightbbox(renderer).y0 - ax.bbox.y0) / ax.bbox.height - 0.02
    return ax.legend(hs, names, loc="upper center", bbox_to_anchor=(0.5, low), ncols=len(hs), frameon=False)


def _reference_label(ax, name, y):
    """The name of a reference level at one end of its dashed line, above or below it, on no drawn line or marker."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    paths = _line_paths(ax)
    markers = []
    for ln in ax.get_lines():
        if ln.get_marker() not in (None, "", "None", " "):
            markers += [(mx, my, ln.get_markersize() * px / 2) for mx, my in ax.transData.transform(ln.get_xydata())]
    placed = [t.get_window_extent(renderer) for t in ax.texts]
    first = None
    for xf, ha, dy, va in ((0.01, "left", 2.5, "bottom"), (0.99, "right", 2.5, "bottom"), (0.01, "left", -2.5, "top"),
                           (0.99, "right", -2.5, "top")):
        t = ax.annotate(name, (xf, y), xycoords=("axes fraction", "data"), xytext=(0, dy), textcoords="offset points",
                        ha=ha, va=va, color=C.CONNECTOR)
        bb = t.get_window_extent(renderer)
        if not any(p.intersects_bbox(bb.padded(0.4 * px), filled=False) for p in paths) \
                and not _collides(bb, placed, markers, 0.6 * px):
            if first is not None:
                first.remove()
            return t
        if first is None:
            first = t                                          # nothing is free: keep the first and let the audit say
        else:
            t.remove()
    return first


def _signed(text):
    """A printed difference with its sign, the minus as U+2212: "+1.30", "−0.04", "0.00"."""
    return text if float(text) == 0 else ("+" + text if not text.startswith("-") else "−" + text[1:])


def gap(ax, a, b, axis="y", mode="difference", unit="dB", decimals=2, text=None, offset_pt=3.0, weight="work", at=None):
    """The difference between two points of the data as a dimension line, labelled with the value computed from them.
    budget()'s ratio line is the axis="x", mode="ratio" case.

    a, b     (x, y) points taken from the data; the gap is b minus a (mode "difference") or a over b ("ratio"), read
             along `axis`
    axis     "y": a vertical arrow offset_pt right of the points; "x": a horizontal arrow at height `at` (by default just
             above both points), with dotted drops from each point
    text     None prints the value with its sign and unit; a string with {v} is formatted with the printed value; any
             other string is checked against the value, and the audit fails a mismatch (a typed gap goes stale)
    weight   "work" (0.5 pt), or "claim" (0.9 pt) when the gap is the figure's point"""
    import re
    from decimal import Decimal

    from matplotlib.transforms import offset_copy

    from .tables import fmt
    i = 1 if axis == "y" else 0
    va, vb = float(a[i]), float(b[i])
    value = vb - va if mode == "difference" else va / vb
    shown = _signed(fmt(value, decimals)) if mode == "difference" else fmt(value, decimals)
    if text is None:
        label = f"{shown} {unit}".strip() if mode == "difference" else f"{shown}×"
    elif "{v" in text:
        label = text.format(v=shown)
    else:
        label = text
    mismatch = False
    if text is not None and "{v" not in text:
        m = re.search(r"[+\-−]?\d+(?:\.(\d+))?", text)
        if m is None:
            mismatch = True
        else:
            typed = Decimal(m.group(0).replace("−", "-").lstrip("+"))
            mismatch = typed != Decimal(fmt(value, len(m.group(1) or "")))
    lw = C.CLAIM_W if weight == "claim" else C.WORK_W
    arrow = dict(arrowstyle="<->", color=C.INK, lw=lw, shrinkA=0, shrinkB=0, mutation_scale=C.GAP_MUTATION)
    guide = dict(arrowstyle="-", color=C.INK, lw=C.HAIR_W, ls=C.DASH_GUIDE, shrinkA=C.MARKER / 2 + 0.5, shrinkB=0)
    if axis == "y":
        xa = max(a[0], b[0])
        tr = offset_copy(ax.transData, fig=ax.figure, x=offset_pt, y=0, units="points")
        ann = ax.annotate("", xy=(xa, vb), xycoords=tr, xytext=(xa, va), textcoords=tr, arrowprops=arrow)
        for p in (a, b):
            if p[0] != xa:
                ax.annotate("", xy=(xa, p[1]), xycoords=tr, xytext=p, textcoords="data", arrowprops=guide)
        at = lambda s: va * (vb / va) ** s if ax.get_yscale() == "log" else va + s * (vb - va)   # s of the way a to b
        up = 1.0 if vb >= va else 0.0                          # the arrow's upper end, as a share of the way a to b
        spots = [(side, s, "center", 0.0) for side in (1, -1) for s in (0.5, 0.25, 0.75)] + \
            [(side, up, "bottom", 1.5) for side in (1, -1)] + [(side, 1.0 - up, "top", -1.5) for side in (1, -1)]
        _first_clear(ax, (xa, at(0.5)), lambda c: [ax.annotate(       # beside the arrow, else past one of its ends
            label, (xa, at(c[1])), xycoords=tr, xytext=(2.0 if c[0] > 0 else -2.0 - 2.0 * offset_pt, c[3]),
            textcoords="offset points", ha="left" if c[0] > 0 else "right", va=c[2], color=C.INK)], spots)
    else:
        lo, hi = ax.get_ylim()
        top = at if at is not None else max(a[1], b[1]) + 0.06 * (hi - lo)
        for p in (a, b):
            ax.plot([p[0], p[0]], [p[1], top], color=C.INK, lw=C.HAIR_W, ls=C.DASH_GUIDE, zorder=2)
        ann = ax.annotate("", xy=(va, top), xytext=(vb, top), arrowprops=arrow)
        mid = (va * vb) ** 0.5 if ax.get_xscale() == "log" else (va + vb) / 2
        ax.annotate(label, (mid, top), xytext=(0, 2.5), textcoords="offset points", ha="center", va="bottom",
                    color=C.INK)
        if top > hi:
            ax.set_ylim(lo, top + 0.08 * (hi - lo))
    fig = ax.figure
    fig._af_gaps = list(getattr(fig, "_af_gaps", [])) + [dict(value=value, computed=shown, text=label,
                                                              mismatch=mismatch, arrow=ann)]
    return ann


def radar(ax, tasks, methods, values, direction, ours="Ours", title=None):
    """One metric over the tasks on polar axes, when the author asks for a radar (contract section 6): the tasks in the
    table's order, each spoke min-max over the methods shown with the outer ring the best ("+" higher is better, "-"
    lower), the worst on the inner ring C.RADAR_FLOOR, every other method in its own Tol muted colour and dash at
    C.RADAR_LINE_W, ours in the accent at 1.8 pt with a light fill, the metric as the axes title. A missing value is
    refused: a radar has no way to show one. Put the names under the panels with shared_legend()."""
    import math

    import numpy as np
    if direction not in ("+", "-"):
        raise ValueError("direction is '+' (higher is better) or '-' (lower is better)")
    for m in methods:
        v = values.get(m)
        if v is None or len(v) != len(tasks) or any(x is None or (isinstance(x, float) and math.isnan(x)) for x in v):
            raise ValueError(f"{m}: one value per task ({len(tasks)}), none missing; a radar cannot show a missing "
                             f"value, so leave the method out or use a table")
    arr = np.array([[float(x) for x in values[m]] for m in methods])
    lo, hi = arr.min(0), arr.max(0)
    span = np.where(hi > lo, hi - lo, 1.0)
    frac = np.where(hi > lo, (arr - lo) / span if direction == "+" else (hi - arr) / span, 1.0)
    r = C.RADAR_FLOOR + (1 - C.RADAR_FLOOR) * frac
    theta = np.linspace(0, 2 * np.pi, len(tasks), endpoint=False)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, C.RADAR_YLIM)
    ax.set_yticks([])
    ax.set_xticks(theta)
    ax.set_xticklabels(tasks)
    ax.grid(False)
    ax.spines["polar"].set_visible(False)
    ring = np.linspace(0, 2 * np.pi, 181)
    for rr in (C.RADAR_FLOOR, 1.0):
        ax.plot(ring, np.full_like(ring, rr), color=C.HAIRLINE, lw=C.HAIR_W, zorder=1)
    for th in theta:
        ax.plot([th, th], [0, 1.0], color=C.HAIRLINE, lw=C.HAIR_W, zorder=1)
    k = 0
    for m in [m for m in methods if m != ours] + [m for m in methods if m == ours]:
        i = methods.index(m)
        tt, rr = np.append(theta, theta[0]), np.append(r[i], r[i][0])
        if m == ours:
            ax.plot(tt, rr, color=C.ACCENT, lw=C.OURS_W, zorder=5, label=m)
            ax.fill(tt, rr, color=C.ACCENT, alpha=C.RADAR_FILL_ALPHA, lw=0, zorder=4)
        else:
            ax.plot(tt, rr, color=C.SERIES_MUTED[k % len(C.SERIES_MUTED)], lw=C.RADAR_LINE_W,
                    ls=C.SERIES_DASHES[k % len(C.SERIES_DASHES)], zorder=3, label=m)
            k += 1
    if title:
        ax.set_title(title, pad=2.0 + 1.2 * C.WORD_PT + 2.5)          # clear of the top task's label
    return ax


def shared_legend(fig, entries=None, where="below", ncols=None):
    """One frameless legend for small multiples, in a strip under (or right of) the panels and never in a panel's
    slot: every labelled artist of every axes, each name once in first-seen order; `entries` picks and orders the
    names. One row when it fits the figure's width, else two."""
    import math
    handles = {}
    for ax in fig.axes:
        for h, name in zip(*ax.get_legend_handles_labels()):
            if name and not name.startswith("_") and name not in handles:
                handles[name] = h
    names = [n for n in (entries or list(handles)) if n in handles]
    if not names:
        raise ValueError("no labelled artists to put in a legend")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer) for ax in fig.axes if ax.get_visible()]
    inv = fig.transFigure.inverted()
    w_pt, h_pt = fig.get_size_inches() * 72.0
    kw = dict(frameon=False, borderaxespad=0.0, columnspacing=1.2, handletextpad=0.5)
    if where == "below":
        y0 = inv.transform((0, min(b.y0 for b in boxes)))[1] - 2.0 / h_pt
        make = lambda n: fig.legend([handles[k] for k in names], names, loc="upper center", bbox_to_anchor=(0.5, y0),
                                    ncols=n, **kw)
        leg = make(ncols or len(names))
        if ncols is None:
            fig.canvas.draw()
            if leg.get_window_extent(renderer).width > fig.bbox.width:
                leg.remove()
                leg = make(math.ceil(len(names) / 2))
    elif where == "right":
        x1 = inv.transform((max(b.x1 for b in boxes), 0))[0] + 2.0 / w_pt
        leg = fig.legend([handles[k] for k in names], names, loc="center left", bbox_to_anchor=(x1, 0.5),
                         ncols=ncols or 1, **kw)
    else:
        raise ValueError("where is 'below' or 'right'")
    return leg


_INSET_RECT ={"br": lambda f: (1 - f, 1 - f, 1, 1), "bl": lambda f: (0, 1 - f, f, 1),   # (x0, y0, x1, y1) in the
               "tr": lambda f: (1 - f, 0, 1, f), "tl": lambda f: (0, 0, f, f)}         # unit square, y down


def _hits(a, b, margin=0.0):
    return min(a[2], b[2]) - max(a[0], b[0]) > -margin and min(a[3], b[3]) - max(a[1], b[1]) > -margin


def _corners(boxes, f, margin, forced=()):
    """Corners for the insets of one row at fraction f, none covering a box of the row or another inset; boxes are in
    the unit square. A corner forced for box i is taken as given (the audit judges it). None when no arrangement
    exists at this f."""
    chosen = []
    for i, _ in enumerate(boxes):
        own = forced[i] if i < len(forced) else None
        for k in ([own] if own else C.INSET_CORNERS):
            ins = _INSET_RECT[k](f)
            if k in chosen or any(_hits(ins, _INSET_RECT[q](f)) for q in chosen):
                continue
            if not own and any(_hits(ins, b, margin) for b in boxes):
                continue
            chosen.append(k)
            break
        else:
            return None
    return chosen


def _square(src):
    """A panel source (path or PIL image) as an RGB image centre-cropped to a square."""
    from PIL import Image
    im = (src if hasattr(src, "convert") else Image.open(src)).convert("RGB")
    w, h = im.size
    s = min(w, h)
    return im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))


def grid(panels, headers, venue="cvpr", span="full", numbers=None, number_row=None, measurement_col=0,
         zoom=None, captions=None, header_color=C.INK, seam=C.GRID_SEAM, *, blocks=None, block_gap=C.GRID_BLOCK_GAP,
         block_headers=None, row_labels=None, zoom_style="inset", inset_corner=None, measurement_gap=None):
    """A result grid: a qualitative comparison, a teaser block or a supplementary sample grid. Returns (fig, axes),
    axes[r][c] the panel of row r, column c. Every default is the median of the grids measured in
    references/qualitative.md.

    panels[r][c]     an image path or a PIL image, centre-cropped square and resampled to 4.2 px per pt
    headers[c]       the column header above the first row, "" for none
    numbers[c]       a string under column c of row `number_row` (the last row by default), "" for none
    measurement_col  the input's column. It is set off by C.GRID_MEASUREMENT_GAP only where the reconstructions abut
                     (seam 0): with a seam, 30 of 32 measured grids give the measurement that same seam.
                     `measurement_gap` overrides the choice
    seam             pt of white between panels in both directions: 2.5 by default, C.GRID_SEAM_SAMPLES (0) for a
                     grid of generated samples, which abut in 8 of 9 flagships
    zoom[r]          a box (x0, y0, x1, y1), or a list of two, in the pixels of the row's largest source, drawn on
                     every panel of row r. zoom_style="inset" magnifies each in a corner of its panel that covers no
                     box (bottom-right first; `inset_corner` forces one), shrinking the insets of the whole figure
                     towards C.INSET_FRACTION_MIN when a box leaves no corner free; zoom_style="row" puts the crops
                     side by side in a row under the image row, framed in their box colours (DAPS Fig. 1c, DDS Fig. 7).
                     A second box is drawn in the second of C.ZOOM_COLOURS
    captions[r]      a sub-panel caption under row r
    row_labels[r]    the name of row r, rotated on the left of the row (FLAIR Fig. 2, ReSample Fig. 3)
    blocks           column counts per block, e.g. [3, 3]: groups separated by `block_gap` (9.3 pt, the median);
                     block_headers[b] names block b in a line above the column headers
    """
    import numpy as np
    from matplotlib.patches import Rectangle
    from PIL import Image

    from . import figure, width_in
    nr, nc = len(panels), len(panels[0])
    if any(len(row) != nc for row in panels) or len(headers) != nc:
        raise ValueError(f"every row needs {nc} panels and there must be {nc} headers")
    if zoom_style not in ("inset", "row"):
        raise ValueError("zoom_style is 'inset' or 'row'")
    W = width_in(venue, span) * 72.0
    zooms = {}
    for r, z in (zoom or {}).items():
        if z is None or len(z) == 0:
            continue
        if not 0 <= r < nr:
            raise ValueError(f"zoom names row {r}; the grid has rows 0 to {nr - 1}")
        bx = [tuple(b) for b in z] if hasattr(z[0], "__len__") else [tuple(z)]   # one box, or a list of boxes
        if len(bx) > len(C.ZOOM_COLOURS):
            raise ValueError(f"row {r}: at most {len(C.ZOOM_COLOURS)} zoom boxes per panel (the survey's maximum)")
        asp = [(b[3] - b[1]) / (b[2] - b[0]) for b in bx]
        if zoom_style == "inset" and any(abs(a - 1) > 0.02 for a in asp):
            raise ValueError(f"row {r}: an inset shows a square box; a wide box needs zoom_style='row'")
        if max(asp) - min(asp) > 0.02 * max(asp):
            raise ValueError(f"row {r}: the boxes of one row need one aspect ratio")
        zooms[r] = bx

    # columns: the gap before column c is a block gap, the measurement gap or the seam
    starts, acc = set(), 0
    if blocks:
        if sum(blocks) != nc:
            raise ValueError(f"blocks {blocks} do not add up to the {nc} columns")
        for b in blocks[:-1]:
            acc += b
            starts.add(acc)
    m = measurement_col is not None and 0 <= measurement_col < nc - 1
    mgap = measurement_gap if measurement_gap is not None else (
        C.GRID_MEASUREMENT_GAP if seam <= C.GRID_ABUT else seam)
    gaps = [("block", block_gap) if c in starts else ("measurement", mgap) if m and c == measurement_col + 1
            else ("seam", seam) for c in range(1, nc)]
    # a rotated label is one line thick per line of text: a two-line label ("Super-resolution\n×4") needs two, or its
    # second line lands inside the first panel (SOLO Fig. 6, 2026-09-23)
    lab_lines = max((str(l).count("\n") + 1 for l in row_labels if l), default=1) if row_labels else 0
    lab = (lab_lines * 1.2 * C.WORD_PT + C.GRID_ROW_LABEL_GAP) if row_labels else 0.0
    p = (W - lab - sum(g for _, g in gaps)) / nc                              # panel side in points
    xs = [lab]
    for _, g in gaps:
        xs.append(xs[-1] + p + g)

    # rows, from the top: block headers, headers, then per row the image, its crop row, numbers and caption
    line = C.WORD_PT + C.GRID_HEADER_GAP
    top = (line if block_headers else 0.0) + (line if any(headers) else 0.0)
    number_row = nr - 1 if number_row is None else number_row
    crop_h = {r: (p / len(bx)) * (bx[0][3] - bx[0][1]) / (bx[0][2] - bx[0][0])
              for r, bx in zooms.items()} if zoom_style == "row" else {}
    num_h, cap_h = C.WORD_PT + C.GRID_NUMBER_GAP, C.WORD_PT + 3.0
    tops, y = [], top
    for r in range(nr):
        tops.append(y)
        y += p + (seam + crop_h[r] if r in crop_h else 0.0)
        y += (num_h if numbers and r == number_row else 0.0) + (cap_h if captions else 0.0)
        y += seam if r < nr - 1 else 0.0
    H = y
    fig, _ = figure(venue, span, height_in=H / 72.0)
    fig.axes[0].remove()
    fig._af_exact, fig._af_kind = True, "grid"                     # save() writes the page as laid out, no tight box
    side_px = int(round(p * C.PIXELS_PER_PT))
    sq = [[_square(panels[r][c]) for c in range(nc)] for r in range(nr)]

    # insets: one fraction for the whole figure, the largest at which every box has a free corner
    corners, f = {}, C.INSET_FRACTION
    if zooms and zoom_style == "inset":
        forced = ((inset_corner,) if isinstance(inset_corner, str) else tuple(inset_corner)) if inset_corner else ()
        margin = (C.INSET_BOX / 2 + 0.5) / p                       # half the box stroke and half a point, in the unit
        unit = {}
        for r, bx in zooms.items():
            s_ref = max(im.size[0] for im in sq[r])
            unit[r] = [tuple(v / s_ref for v in b) for b in bx]
        for step in range(int(round(100 * (C.INSET_FRACTION - C.INSET_FRACTION_MIN))) + 1):
            f = C.INSET_FRACTION - step / 100.0
            corners = {r: _corners(u, f, margin, forced) for r, u in unit.items()}
            if all(corners.values()):
                break
        else:                                  # a box that leaves no corner free even at the smallest measured inset:
            f = C.INSET_FRACTION               # the default corner, and the audit fails the covered box
            corners = {r: _corners(u, f, margin, forced) or _corners(u, f, -1.0, forced or C.INSET_CORNERS)
                       for r, u in unit.items()}

    meta = dict(panel_pt=p, seam=seam, gaps=gaps, blocks=list(blocks) if blocks else None,
                measurement_col=measurement_col if m else None, zoom_style=zoom_style, inset_fraction=f,
                zooms=[], headers=[], row_labels=[])
    axes = [[None] * nc for _ in range(nr)]
    for r in range(nr):
        yb = H - tops[r] - p                                              # the panel's bottom, points from the bottom
        s_ref = max(im.size[0] for im in sq[r])
        for c in range(nc):
            x, im = xs[c], sq[r][c]
            s = im.size[0]
            ax = fig.add_axes([x / W, yb / H, p / W, p / H])
            ax.imshow(np.asarray(im.resize((side_px, side_px), Image.LANCZOS)), interpolation="none")
            ax.set_axis_off()
            ax._af_role = "panel"
            axes[r][c] = ax
            k = side_px / s_ref                                           # display pixels per box pixel
            for i, b in enumerate(zooms.get(r, [])):
                colour = C.ZOOM_COLOURS[i]
                ax.add_patch(Rectangle((b[0] * k - 0.5, b[1] * k - 0.5), (b[2] - b[0]) * k, (b[3] - b[1]) * k,
                                       fill=False, ec=colour, lw=C.INSET_BOX))
                crop = im.crop(tuple(int(round(v * s / s_ref)) for v in b))
                if zoom_style == "inset":
                    ux0, uy0, ux1, uy1 = _INSET_RECT[corners[r][i]](f)
                    rect = (x + ux0 * p, yb + (1 - uy1) * p, f * p, f * p)
                    shape = (int(round(side_px * f)),) * 2
                else:
                    w = p / len(zooms[r])
                    rect = (x + i * w, yb - seam - crop_h[r], w, crop_h[r])
                    shape = (int(round(w * C.PIXELS_PER_PT)), int(round(crop_h[r] * C.PIXELS_PER_PT)))
                ins = fig.add_axes([rect[0] / W, rect[1] / H, rect[2] / W, rect[3] / H])
                ins.imshow(np.asarray(crop.resize(shape, Image.LANCZOS)), interpolation="none")
                ins.set_xticks([]); ins.set_yticks([])
                ins._af_role = "inset" if zoom_style == "inset" else "crop"
                single = zoom_style == "inset" and len(zooms[r]) == 1
                for sp in ins.spines.values():                             # one inset: a white edge; several, or a
                    sp.set_visible(True)                                   # crop row: the box colour pairs them
                    sp.set_edgecolor(C.PAPER if single else colour)
                    sp.set_linewidth(C.INSET_BORDER if single else C.INSET_BOX)
                box_px = (b[2] - b[0]) * s / s_ref                         # the crop's width in this panel's pixels
                meta["zooms"].append(dict(row=r, col=c, box=i, corner=corners[r][i] if zoom_style == "inset" else None,
                                          box_pt=(x + b[0] / s_ref * p, yb + (1 - b[3] / s_ref) * p,
                                                  (b[2] - b[0]) / s_ref * p, (b[3] - b[1]) / s_ref * p),
                                          box_side=b[2] - b[0], inset_pt=rect,
                                          magnification=rect[2] / ((b[2] - b[0]) / s_ref * p),
                                          px_per_pt=box_px / rect[2]))
            if r == 0 and headers[c]:
                t = fig.text((x + p / 2) / W, (H - top + line - C.WORD_PT * 0.2) / H, headers[c], ha="center",
                             va="top", color=header_color)
                room = p + min([g for j, (_, g) in enumerate(gaps) if j in (c - 1, c)] or [0.0])
                meta["headers"].append((t, room))
        bottom = yb - (seam + crop_h[r] if r in crop_h else 0.0)           # under the crop row, if there is one
        if numbers and r == number_row:
            for c in range(nc):
                if numbers[c]:
                    fig.text((xs[c] + p / 2) / W, (bottom - C.GRID_NUMBER_GAP) / H, numbers[c], ha="center",
                             va="top", color=C.INK)
            bottom -= num_h
        if captions and captions[r]:
            fig.text(((lab + W) / 2) / W, (bottom - 1.0) / H, captions[r], ha="center", va="top", color=C.INK)
        if row_labels and row_labels[r]:
            t = fig.text(0.0, (yb + p / 2) / H, row_labels[r], rotation=90, ha="left", va="center", color=C.INK)
            meta["row_labels"].append((t, p))
    if block_headers:
        edges = [0] + sorted(starts) + [nc]
        for b, name in enumerate(block_headers):
            if name:
                x0, x1 = xs[edges[b]], xs[edges[b + 1] - 1] + p
                t = fig.text(((x0 + x1) / 2) / W, (H - C.WORD_PT * 0.2) / H, name, ha="center", va="top",
                             color=header_color)
                meta["headers"].append((t, x1 - x0))
    fig._af_grid = meta
    return fig, axes
