"""The recurring figures of an ML paper, drawn to the contract, so a new paper copies a call instead of a style.

budget  quality against compute: ours swept as a curve, every baseline a single labelled point at its own
        published setting, a dimension line naming the ratio. DAPS Fig. 6 and CLAMP Fig. 3 are this construction.
grid    a result grid for a qualitative figure or a teaser: reconstructions abutting, the measurement column set
        off, headers above, one row of numbers below, zoom insets in the bottom-right. DAPS Fig. 1 and FlowDPS
        Fig. 3 are this construction.
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


def place_labels(ax, points, color=C.CONNECTOR, fixed=None):
    """Label each (name, x, y) beside its marker at the first candidate spot that collides with nothing placed yet
    and no marker. `fixed` maps a name to (dx, dy, ha, va) to override. Returns the Text artists."""
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
    out = []
    for name, x, y in points:
        tries = [fixed[name]] if fixed and name in fixed else _CANDIDATES
        for dx, dy, ha, va in tries:
            t = ax.annotate(name, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, color=color)
            bb = t.get_window_extent(renderer)
            own = [(mx, my, r) for mx, my, r in markers if abs(mx - ax.transData.transform((x, y))[0]) > 0.5
                   or abs(my - ax.transData.transform((x, y))[1]) > 0.5]
            if fixed and name in fixed or not _collides(bb, placed, own, 0.6 * px):
                placed.append(bb)
                out.append(t)
                break
            t.remove()
        else:                                              # nothing fits: keep the first spot and let the audit say so
            out.append(ax.annotate(name, (x, y), xytext=_CANDIDATES[0][:2], textcoords="offset points",
                                   ha="left", va="center", color=color))
    return out


def mixed_label(ax, xy, parts, xytext=(0, 0), color=C.INK, ha="left"):
    """parts = [("$N{=}4$", "math"), (", 33.96 dB", "word")]: laid left to right on one baseline."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    px = fig.dpi / 72.0
    x_off, arts = xytext[0], []
    for text, kind in parts:
        size = C.MATH_PT if kind == "math" else C.WORD_PT
        t = ax.annotate(text, xy, xytext=(x_off, xytext[1]), textcoords="offset points", ha="left", va="baseline",
                        color=color, fontsize=size)
        x_off += t.get_window_extent(renderer).width / px
        arts.append(t)
    if ha != "left":                                       # shift the whole run so its anchor is right or centre
        shift = -(x_off - xytext[0]) * (1.0 if ha == "right" else 0.5)
        for t in arts:
            dx, dy = t.xyann
            t.xyann = (dx + shift, dy)
    return arts


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


def grid(panels, headers, venue="cvpr", span="full", numbers=None, number_row=None, measurement_col=0,
         zoom=None, captions=None, header_color=C.INK):
    """A result grid. `panels[r][c]` is an image path; `headers[c]` the column header; `numbers[c]` the string
    printed under column c of row `number_row` (the last row by default), "" for none; `zoom[r]` a pixel box
    (x0, y0, x1, y1) in the source images of row r, drawn on each panel and magnified in its bottom-right corner;
    `captions[r]` an optional sub-panel caption under row r. Returns (fig, axes)."""
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Rectangle
    from PIL import Image

    from . import figure, width_in
    nr, nc = len(panels), len(panels[0])
    W = width_in(venue, span) * 72.0
    gap = C.GRID_MEASUREMENT_GAP if measurement_col is not None else 0.0
    p = (W - gap) / nc                                             # panel side in points
    head = C.WORD_PT + C.GRID_HEADER_GAP
    num = (C.WORD_PT + C.GRID_NUMBER_GAP) if numbers else 0.0
    cap = (C.WORD_PT + 3.0) if captions else 0.0
    H = head + nr * p + num + cap * nr
    fig, _ = figure(venue, span, height_in=H / 72.0)
    fig.axes[0].remove()
    fig._af_exact, fig._af_kind = True, "grid"                     # save() writes the page as laid out, no tight box
    axes = [[None] * nc for _ in range(nr)]
    number_row = nr - 1 if number_row is None else number_row
    side_px = int(round(p * C.PIXELS_PER_PT))
    for r in range(nr):
        for c in range(nc):
            x = c * p + (gap if measurement_col is not None and c > measurement_col else 0.0)
            y = H - head - (r + 1) * p - r * cap                         # points from the bottom
            ax = fig.add_axes([x / W, y / H, p / W, p / H])
            im = Image.open(panels[r][c]).convert("RGB")
            src_w, src_h = im.size
            s = min(src_w, src_h)
            im = im.crop(((src_w - s) // 2, (src_h - s) // 2, (src_w - s) // 2 + s, (src_h - s) // 2 + s))
            ax.imshow(np.asarray(im.resize((side_px, side_px), Image.LANCZOS)), interpolation="none")
            ax.set_axis_off()
            if zoom and r in zoom and zoom[r]:
                x0, y0, x1, y1 = zoom[r]
                k = side_px / s
                ax.add_patch(Rectangle((x0 * k, y0 * k), (x1 - x0) * k, (y1 - y0) * k, fill=False,
                                       ec=C.INSET_BOX_COLOUR, lw=C.INSET_BOX))
                f = C.INSET_FRACTION
                ins = fig.add_axes([(x + p * (1 - f)) / W, y / H, p * f / W, p * f / H])
                crop = Image.open(panels[r][c]).convert("RGB").crop((x0 + (src_w - s) // 2, y0 + (src_h - s) // 2,
                                                                     x1 + (src_w - s) // 2, y1 + (src_h - s) // 2))
                ins.imshow(np.asarray(crop.resize((int(side_px * f),) * 2, Image.LANCZOS)), interpolation="none")
                ins.set_xticks([]); ins.set_yticks([])
                for sp in ins.spines.values():
                    sp.set_visible(True); sp.set_edgecolor(C.PAPER); sp.set_linewidth(C.INSET_BORDER)
            axes[r][c] = ax
            if r == 0:
                fig.text((x + p / 2) / W, (H - C.WORD_PT * 0.2) / H, headers[c], ha="center", va="top",
                         color=header_color)
            if numbers and r == number_row and numbers[c]:
                fig.text((x + p / 2) / W, (y - C.GRID_NUMBER_GAP) / H, numbers[c], ha="center", va="top",
                         color=C.INK)
        if captions and captions[r]:
            fig.text(0.5, (H - head - (r + 1) * p - r * cap - num * (r == number_row) - 1.0) / H, captions[r],
                     ha="center", va="top", color=C.INK)
    return fig, axes
