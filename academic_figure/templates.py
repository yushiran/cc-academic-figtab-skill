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


def place_labels(ax, points, color=C.CONNECTOR, fixed=None, candidates=None):
    """Label each (name, x, y) beside its marker at the first candidate spot that collides with nothing placed yet
    and no marker. `fixed` maps a name to (dx, dy, ha, va) to override; `candidates` replaces the default spots
    (right, left, above, below, the four diagonals) with a tuple of (dx, dy, ha, va). Returns the Text artists."""
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
        tries = [fixed[name]] if fixed and name in fixed else (candidates or _CANDIDATES)
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
        arts.append(t)
    for t in arts:                                         # centre the run on the axes
        dx, dy = t.xyann
        t.xyann = (dx - x_off / 2, dy)
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


_INSET_RECT = {"br": lambda f: (1 - f, 1 - f, 1, 1), "bl": lambda f: (0, 1 - f, f, 1),   # (x0, y0, x1, y1) in the
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
