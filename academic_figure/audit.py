"""The audit save() runs on every figure: what code can check, so that looking is spent on what it cannot.

Two layers. `audit(fig)` inspects the live matplotlib figure: missing glyphs, text cut off by the canvas, ANY two
visible texts overlapping (annotations, axis labels and tick labels alike), text lying on a data marker, a word
set in a face other than the contract's, type under the floor, and colours outside the palette. `audit_pdf()`
inspects the file written: its page width against the target, the fonts actually embedded, and the ink coverage
and gutters of the PNG twin.

The glyph capture and the tick-overlap test are adapted from scipilot-figure-skill's scripts/visual_qa.py
(Haojae, MIT; see NOTICE). The rest was written after a figure passed a narrower audit and was rejected on sight
for two collided labels and an axis title driven into its tick labels.
"""
from __future__ import annotations

import io
import itertools
import logging
import warnings
from pathlib import Path

from . import contract as C

SEVERITY = {"INFO": 0, "WARN": 1, "FAIL": 2}
_GLYPH_MARKERS = ("missing from", "Glyph", "findfont")
_ALLOWED_PDF_FONTS = ("Arimo", "Cmr", "Cmmi", "Cmsy", "Cmex", "DejaVuSans-Oblique")   # matplotlib's cm mathtext embeds Cm*
COLOUR_TOLERANCE = 18                                    # max per-channel distance (0-255) to count as a palette colour


# --- helpers ---------------------------------------------------------------------------------------
class _GlyphLog(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []

    def emit(self, record):
        msg = record.getMessage()
        if any(m in msg for m in _GLYPH_MARKERS):
            self.messages.append(msg)


def _draw_collect_glyphs(fig) -> list[str]:
    """Render once, collecting missing-glyph reports from both warnings and logging (versions differ)."""
    handler, logger = _GlyphLog(), logging.getLogger("matplotlib")
    level = logger.level
    logger.setLevel(logging.WARNING)
    logger.addHandler(handler)
    seen = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100)
        seen += [str(w.message) for w in caught if any(m in str(w.message) for m in _GLYPH_MARKERS)]
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
    return list(dict.fromkeys(seen + handler.messages))


def _texts(fig):
    """Every visible, non-empty Text, minus the tick labels an axis keeps pooled from an earlier autoscale: those
    still say '40' or '0.3', report visible, and are never drawn (they collided in pairs on a 2x4 panel figure,
    2026-09-22). Call after a draw, so the live tick set is the drawn one."""
    import matplotlib.text as mtext
    stale = set()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            lo, hi = sorted(axis.get_view_interval())
            live = [t for t in axis.get_major_ticks() + axis.get_minor_ticks() if lo <= t.get_loc() <= hi]
            pool = {t.label1 for t in axis.majorTicks} | {t.label1 for t in axis.minorTicks}
            stale |= pool - {t.label1 for t in live}       # pooled from an earlier autoscale, or located off the view
    return [t for t in fig.findobj(mtext.Text) if t.get_visible() and t.get_text().strip() and t not in stale]


def _is_math(text: str) -> bool:
    return text.strip().startswith("$") and text.strip().endswith("$")


def _hex(c) -> str | None:
    from matplotlib.colors import to_hex, to_rgba
    try:
        rgba = to_rgba(c)
    except (ValueError, TypeError):
        return None
    return None if rgba[3] == 0 else to_hex(rgba[:3])


def _near(h: str, allowed: tuple) -> bool:
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    for a in allowed:
        ar, ag, ab = (int(a[i:i + 2], 16) for i in (1, 3, 5))
        if max(abs(r - ar), abs(g - ag), abs(b - ab)) <= COLOUR_TOLERANCE:
            return True
    return False


# --- the figure audit --------------------------------------------------------------------------------
def audit(fig, overlap_tol_pt: float = 0.3) -> list[tuple[str, str]]:
    """Inspect a live figure. Returns [(severity, message)]; changes nothing."""
    from matplotlib.collections import Collection
    from matplotlib.image import AxesImage
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    issues = []
    glyphs = _draw_collect_glyphs(fig)
    if glyphs:
        issues.append(("FAIL", "missing glyphs, the page will print boxes: " + " | ".join(glyphs[:3])[:240]))
    fig.canvas.draw()            # the glyph pass rendered at 100 dpi, and a legend keeps the layout of its last draw;
    renderer = fig.canvas.get_renderer()   # measure everything after one draw at the figure's own dpi (found 2026-09-22)
    px_per_pt = fig.dpi / 72.0
    W, H = fig.bbox.width, fig.bbox.height
    texts = _texts(fig)

    # 1. text cut off. save() writes with a tight bounding box, which grows to include text past the canvas, so the
    #    canvas edge is not the risk; a text that clips to its axes and reaches past them is, since that part is lost
    clipped = []
    for t in texts:
        box = t.get_clip_box()
        if not t.get_clip_on() or box is None:
            continue
        bb = t.get_window_extent(renderer)
        if bb.x0 < box.x0 - 1 or bb.y0 < box.y0 - 1 or bb.x1 > box.x1 + 1 or bb.y1 > box.y1 + 1:
            clipped.append(t.get_text()[:24])
    if clipped:
        issues.append(("FAIL", f"text cut off by its axes: {list(dict.fromkeys(clipped))[:6]}"))

    # 1b. an annotation whose anchor lies outside its axes is not drawn at all, silently, though get_visible() is
    #     True: a label placed at the old x-limit and then pushed out by a later set_xlim vanishes this way
    import matplotlib.text as mtext
    undrawn = []
    for t in texts:
        if not isinstance(t, mtext.Annotation) or t.axes is None or t.get_annotation_clip() is False:
            continue
        if t.xycoords not in ("data", None) and t.get_annotation_clip() is None:
            continue
        if not t._check_xy(renderer):
            undrawn.append(t.get_text()[:24])
    if undrawn:
        issues.append(("FAIL", f"labels anchored outside their axes, so never drawn: {undrawn[:6]}"))
    texts = [t for t in texts if t.get_text()[:24] not in undrawn]

    # 2. any two visible texts overlapping: this is the check that catches collided labels and an axis title
    #    driven into its ticks, which a tick-only test misses
    boxes = [(t, t.get_window_extent(renderer)) for t in texts]
    tol = overlap_tol_pt * px_per_pt
    hits = []
    for (ta, a), (tb, b) in itertools.combinations(boxes, 2):
        if min(a.x1, b.x1) - max(a.x0, b.x0) > tol and min(a.y1, b.y1) - max(a.y0, b.y0) > tol:
            hits.append(f"'{ta.get_text()[:16]}' x '{tb.get_text()[:16]}'")
    if hits:
        issues.append(("FAIL", f"{len(hits)} overlapping text pairs: " + "; ".join(hits[:6])))

    # 3. text lying on a data marker (a label placed on a point it does not name, or on the curve)
    on_marker = []
    for ax in fig.axes:
        pts = []
        for ln in ax.get_lines():
            if ln.get_marker() in (None, "", "None", " ") or not ln.get_visible():
                continue
            xy = ax.transData.transform(ln.get_xydata())
            r = ln.get_markersize() * px_per_pt / 2
            pts += [(x, y, r) for x, y in xy]
        for t in texts:
            if t.axes is not ax or t in ax.get_xticklabels() or t in ax.get_yticklabels():
                continue
            bb = t.get_window_extent(renderer)
            if any(bb.x0 - r < x < bb.x1 + r and bb.y0 - r < y < bb.y1 + r for x, y, r in pts):
                on_marker.append(t.get_text()[:20])
    if on_marker:
        issues.append(("WARN", f"text on a data marker: {list(dict.fromkeys(on_marker))[:6]}"))

    # 4. faces and sizes: every word in Arimo at the one word size; maths in Computer Modern; nothing under the floor
    wrong_face, small, off_size = [], [], []
    for t in texts:
        s = t.get_fontsize()
        if s < C.FLOOR_PT - 1e-6:
            small.append(f"{t.get_text()[:16]} {s:.1f}pt")
        if _is_math(t.get_text()):
            continue
        if C.WORD_FACE not in (t.get_fontname() or ""):
            wrong_face.append(f"{t.get_text()[:16]} ({t.get_fontname()})")
        if abs(s - C.WORD_PT) > 0.05:
            off_size.append(f"{t.get_text()[:16]} {s:.1f}pt")
    if small:
        issues.append(("FAIL", f"type under the {C.FLOOR_PT} pt floor: {small[:6]}"))
    if wrong_face:
        issues.append(("FAIL", f"words not in {C.WORD_FACE}: {wrong_face[:6]}"))
    if off_size:
        issues.append(("WARN", f"words not at the one word size {C.WORD_PT} pt: {off_size[:6]}"))

    # 4b. maths inside a word-size text renders at the word size, where Computer Modern's x-height is a fifth
    #     under Arimo's and the symbol reads small (a legend's sigma_y, 2026-09-22). Tick labels are exempt, since one
    #     quantity keeps one tick form; anywhere else the run is set with mixed_label or mixed_xlabel.
    tick_texts = set()
    for ax in fig.axes:
        tick_texts.update(ax.get_xticklabels() + ax.get_yticklabels())
    small_math = [f"{t.get_text()[:20]} {t.get_fontsize():.1f}pt" for t in texts
                  if t not in tick_texts and "$" in t.get_text() and t.get_fontsize() < C.MATH_PT - 0.05]
    if small_math:
        issues.append(("WARN", f"maths set at the word size, not {C.MATH_PT} pt (use mixed_label / mixed_xlabel): "
                               f"{small_math[:6]}"))

    # 4c. a data-anchored label that reaches past its axes by more than a few points sits in the margin, where the
    #     tight bounding box grows to keep it and it reads as a stray (a label pushed above the frame, 2026-09-22)
    reach = []
    for ax in fig.axes:
        skip = {ax.xaxis.label, ax.yaxis.label, ax.title, *ax.get_xticklabels(), *ax.get_yticklabels()}
        if ax.get_legend() is not None:
            skip.update(ax.get_legend().get_texts())
        for t in texts:
            if t.axes is not ax or t in skip:
                continue
            if isinstance(t, mtext.Annotation) and t.xycoords not in ("data", None):
                continue                                             # placed off the axes on purpose
            bb = t.get_window_extent(renderer)
            over = max(ax.bbox.x0 - bb.x0, bb.x1 - ax.bbox.x1, ax.bbox.y0 - bb.y0, bb.y1 - ax.bbox.y1) / px_per_pt
            if over > 4.0:
                reach.append(f"{t.get_text()[:16]} {over:.0f}pt")
    if reach:
        issues.append(("WARN", f"labels reaching past their axes: {reach[:6]}"))

    # 5. colours: lines, markers, patches, collections and text against the palette and the series schemes
    allowed = tuple(C.PALETTE) + C.SERIES_MUTED + C.SERIES_BRIGHT + C.SERIES_HIGH_CONTRAST
    stray = set()
    for art in fig.findobj(lambda a: isinstance(a, (Line2D, Patch, Collection)) or hasattr(a, "get_color")):
        if isinstance(art, AxesImage) or not getattr(art, "get_visible", lambda: True)():
            continue
        cands = []
        if isinstance(art, Line2D):
            cands = [art.get_color(), art.get_markerfacecolor(), art.get_markeredgecolor()]
        elif isinstance(art, Patch):
            if art is fig.patch or any(art is ax.patch for ax in fig.axes):
                continue
            cands = [art.get_facecolor(), art.get_edgecolor()] if art.get_fill() else [art.get_edgecolor()]
        elif isinstance(art, Collection):
            cands = list(art.get_facecolors()) + list(art.get_edgecolors())
        elif hasattr(art, "get_color"):
            cands = [art.get_color()]
        for c in cands:
            h = _hex(c)
            if h and not _near(h, allowed):
                stray.add(h)
    if stray:
        issues.append(("WARN", f"colours outside the palette: {sorted(stray)[:8]}"))
    if getattr(fig, "_af_kind", None) == "grid":
        issues += audit_grid(fig)
    return issues


# --- the grid audit ----------------------------------------------------------------------------------
def _pt_rect(fig, ax):
    """An axes' rectangle (x0, y0, x1, y1) in points from the figure's bottom-left corner."""
    w, h = fig.get_size_inches() * 72.0
    b = ax.get_position()
    return (b.x0 * w, b.y0 * h, b.x1 * w, b.y1 * h)


def _edge_merges(a, b, levels):
    """Share of an abutting edge whose luminance steps under `levels` of 255: a and b are the two edge lines, (n, 3)."""
    import numpy as np
    lum = lambda v: (np.asarray(v, dtype=float)[..., :3] * (255.0 if np.asarray(v).dtype.kind == "f" else 1.0)
                     ) @ np.array([0.299, 0.587, 0.114])
    la, lb = lum(a), lum(b)
    if len(la) != len(lb):                                   # panels of one grid share a side; resample if not
        lb = np.interp(np.linspace(0, 1, len(la)), np.linspace(0, 1, len(lb)), lb)
    return float((np.abs(la - lb) < levels).mean())


def audit_grid(fig) -> list[tuple[str, str]]:
    """The checks a result grid needs beyond audit(). Each threshold is a number measured on flagship grids and held
    in contract.py; references/qualitative.md gives the survey. Geometry is read off the live figure, so a grid built
    by hand is checked too; magnification needs the zoom record that grid() leaves in fig._af_grid."""
    import statistics

    import numpy as np
    from matplotlib.patches import Rectangle
    st_median = statistics.median
    issues = []
    meta = getattr(fig, "_af_grid", None) or {}
    renderer = fig.canvas.get_renderer()
    px_per_pt = fig.dpi / 72.0
    img = [ax for ax in fig.axes if ax.images and ax.get_visible()]
    rect = {ax: _pt_rect(fig, ax) for ax in img}
    role = lambda ax: getattr(ax, "_af_role", None)

    def inside(a, b):
        ra, rb = rect[a], rect[b]
        return a is not b and ra[0] >= rb[0] - 0.05 and ra[1] >= rb[1] - 0.05 and ra[2] <= rb[2] + 0.05 \
            and ra[3] <= rb[3] + 0.05

    insets = [a for a in img if role(a) == "inset" or (role(a) is None and any(inside(a, o) for o in img))]
    panels = [a for a in img if a not in insets and role(a) != "crop"]
    if not panels:
        return issues
    rows = []
    for ax in sorted(panels, key=lambda a: -rect[a][3]):
        if rows and abs(rect[rows[-1][0]][3] - rect[ax][3]) < 1.0:
            rows[-1].append(ax)
        else:
            rows.append([ax])
    for row in rows:
        row.sort(key=lambda a: rect[a][0])
    side = lambda a: (rect[a][2] - rect[a][0], rect[a][3] - rect[a][1])

    # 1. the panel floor, and one panel size per row
    p = min(min(side(a)) for a in panels)
    if p < C.GRID_PANEL_FLOOR - 0.05:
        issues.append(("WARN", f"panels {p:.1f} pt, under the {C.GRID_PANEL_FLOOR} pt of the smallest panel in 90 "
                               f"flagship qualitative figures (DDNM Fig. 4): fewer columns, or the text width"))
    uneven = []
    for i, row in enumerate(rows):
        ws, hs = [side(a)[0] for a in row], [side(a)[1] for a in row]
        if (max(ws) - min(ws)) / max(ws) > 0.01 or (max(hs) - min(hs)) / max(hs) > 0.01:
            uneven.append(f"row {i}: {min(ws):.1f} to {max(ws):.1f} pt")
    if uneven:
        issues.append(("WARN", f"unequal panels within a row ({'; '.join(uneven[:4])}): a comparison gives every method "
                               f"the same area"))

    # 2. seams inside a block, block gaps, and abutting edges that vanish
    kinds = [k for k, _ in meta.get("gaps", [])]
    seams, blocks_, merged = [], [], []
    for i, row in enumerate(rows):
        g = [rect[b][0] - rect[a][2] for a, b in zip(row, row[1:])]
        if not g:
            continue
        kk = kinds if len(kinds) == len(g) else ["block" if x > st_median(g) + 1.5 else "seam" for x in g]
        seams += [x for x, k in zip(g, kk) if k == "seam"]
        blocks_ += [x for x, k in zip(g, kk) if k == "block"]
        for a, b, x in zip(row, row[1:], g):
            if x <= C.GRID_ABUT and _edge_merges(np.asarray(a.images[0].get_array())[:, -1],
                                                 np.asarray(b.images[0].get_array())[:, 0], C.GRID_MERGE_LEVELS) > 0.5:
                merged.append(f"row {i}")
    for up, down in zip(rows, rows[1:]):
        for a in up:
            b = next((d for d in down if abs(rect[d][0] - rect[a][0]) < 1.0), None)
            if b is not None and rect[a][1] - rect[b][3] <= C.GRID_ABUT and _edge_merges(
                    np.asarray(a.images[0].get_array())[-1], np.asarray(b.images[0].get_array())[0],
                    C.GRID_MERGE_LEVELS) > 0.5:
                merged.append("between rows")
    if seams and max(seams) > C.GRID_SEAM_MAX + 0.05:
        issues.append(("WARN", f"seams up to {max(seams):.1f} pt, past the {C.GRID_SEAM_MAX} pt within which 76 of 78 "
                               f"measured reconstruction grids lie (median 2.5)"))
    if seams and max(seams) - min(seams) > 0.3:
        issues.append(("WARN", f"seams from {min(seams):.1f} to {max(seams):.1f} pt inside one block: an odd seam reads "
                               f"as a grouping; give blocks their own gap (blocks=)"))
    seam = st_median(seams) if seams else 0.0
    if blocks_ and seam > C.GRID_ABUT and min(blocks_) < C.GRID_BLOCK_RATIO * seam:
        issues.append(("WARN", f"a block gap of {min(blocks_):.1f} pt is under {C.GRID_BLOCK_RATIO} seams of "
                               f"{seam:.1f} pt, so the blocks do not read as blocks (the tightest measured: ReSample "
                               f"Fig. 5 2.2x, D-Flow Fig. 5 2.3x)"))
    if merged:
        issues.append(("WARN", f"abutting panels merge along {len(merged)} edges ({', '.join(sorted(set(merged)))}): "
                               f"their edge luminance steps under {C.GRID_MERGE_LEVELS:.0f} of 255 on most of the "
                               f"edge; use the {C.GRID_SEAM} pt seam"))
    issues.append(("INFO", f"grid: {len(rows)} rows of {max(len(r) for r in rows)} panels at {p:.1f} pt, seams "
                           f"{seam:.2f} pt" + (f", block gaps {min(blocks_):.1f} pt" if blocks_ else "")))

    # 3. a zoom box under an inset of its own panel hides the region it marks
    covered = []
    for ax in panels:
        boxes = []
        for pa in ax.patches:
            if isinstance(pa, Rectangle) and not pa.get_fill() and pa.get_visible():
                e = pa.get_window_extent(renderer)
                half = pa.get_linewidth() / 2.0
                boxes.append((e.x0 / px_per_pt - half, e.y0 / px_per_pt - half, e.x1 / px_per_pt + half,
                              e.y1 / px_per_pt + half))
        for ins in (i for i in insets if inside(i, ax)):
            r = rect[ins]
            if any(min(b[2], r[2]) - max(b[0], r[0]) > 0.1 and min(b[3], r[3]) - max(b[1], r[1]) > 0.1 for b in boxes):
                covered.append(ax)
                break
    if covered:
        where = sorted({(next(i for i, row in enumerate(rows) if a in row)) for a in covered})
        issues.append(("FAIL", f"zoom box covered by an inset of its own panel in {len(covered)} panels (rows {where}):"
                               f" the region it marks is hidden; move or shrink the box, or use zoom_style='row'"))

    # 4. magnification and the source pixels an inset shows, from grid()'s zoom record
    zooms = meta.get("zooms", [])
    if zooms:
        mags = [z["magnification"] for z in zooms]
        mc = meta.get("measurement_col")
        dens = [z["px_per_pt"] for z in zooms if z["col"] != mc]
        lo = min(mags)
        z0 = min(zooms, key=lambda z: z["magnification"])
        side_px = z0["box_side"] * lo / C.ZOOM_MAGNIFICATION          # in the pixels the zoom boxes are given in
        hint = f"a box of about {side_px:.0f} px gives the survey's median {C.ZOOM_MAGNIFICATION:.0f}x"
        if lo < C.ZOOM_MAGNIFICATION_FAIL:
            issues.append(("FAIL", f"a zoom magnifying {lo:.2f}x, under the {C.ZOOM_MAGNIFICATION_FAIL}x of the least "
                                   f"magnifying flagship zoom: it repeats the panel; {hint}"))
        elif lo < C.ZOOM_MAGNIFICATION_WARN:
            issues.append(("WARN", f"a zoom magnifying {lo:.2f}x, under the {C.ZOOM_MAGNIFICATION_WARN}x lower quartile "
                                   f"of 23 flagship zooms (median 3.0x); {hint}"))
        if dens and min(dens) < C.ZOOM_SOURCE_PX_PER_PT:
            issues.append(("WARN", f"an inset shows {min(dens):.2f} source pixels per printed point, under "
                                   f"{C.ZOOM_SOURCE_PX_PER_PT}: it magnifies interpolation, not detail; zoom a larger "
                                   f"image, or drop the zoom, as the solver papers on 64 to 256 px images do"))
        issues.append(("INFO", f"zoom ({meta.get('zoom_style')}): magnification {lo:.2f} to {max(mags):.2f}x, "
                               f"{min(dens) if dens else float('nan'):.2f} source px per pt at the least"))

    # 5. headers that do not fit their column, or sit outside the measured sizes; row labels longer than their row
    wide, odd = [], []
    for t, room in meta.get("headers", []):
        w = t.get_window_extent(renderer).width / px_per_pt
        if w > room - 1.0:
            wide.append(f"'{t.get_text()[:16]}' {w:.1f} pt in {room:.1f}")
        if not C.GRID_HEADER_PT[0] <= t.get_fontsize() <= C.GRID_HEADER_PT[1]:
            odd.append(f"'{t.get_text()[:16]}' {t.get_fontsize():.1f} pt")
    if wide:
        issues.append(("WARN", f"headers wider than their columns: {wide[:4]}; abbreviate, or give the grid fewer "
                               f"columns"))
    if odd:
        issues.append(("WARN", f"headers outside the {C.GRID_HEADER_PT[0]} to {C.GRID_HEADER_PT[1]} pt of flagship "
                               f"grids (interquartile range): {odd[:4]}"))
    long_, inside_ = [], []
    for t, height in meta.get("row_labels", []):
        e = t.get_window_extent(renderer)
        h = e.height / px_per_pt
        if h > height:
            long_.append(f"'{t.get_text()[:16]}' {h:.1f} pt on a {height:.1f} pt row")
        # the label must stay in its gutter: a second line of a two-line label drawn on a one-line gutter lands on
        # the first panel (SOLO Fig. 6, 2026-09-23); the gutter is a property of the layout, so this is a FAIL
        x0, y0, x1, y1 = (v / px_per_pt for v in (e.x0, e.y0, e.x1, e.y1))
        for ax in img:
            r = rect[ax]
            dx = min(x1, r[2]) - max(x0, r[0])
            dy = min(y1, r[3]) - max(y0, r[1])
            if dx > 0.3 and dy > 0.3:
                inside_.append(f"'{t.get_text().replace(chr(10), ' ')[:20]}' {dx:.1f} pt into a panel")
                break
    if long_:
        issues.append(("WARN", f"row labels longer than their rows: {long_[:4]}; shorten them"))
    if inside_:
        issues.append(("FAIL", f"row labels drawn over the images: {inside_[:4]}; grid() sizes the gutter by the "
                               f"label's line count, so a label placed by hand needs the gutter widened"))
    return issues


# --- the file audit ---------------------------------------------------------------------------------
def audit_pdf(pdf: Path, target_pt: float, png: Path | None = None, kind: str = "plot") -> list[tuple[str, str]]:
    """The saved file: width against the target, embedded fonts, and (from the PNG twin) ink and gutters."""
    import re
    issues = []
    data = Path(pdf).read_bytes()
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    if m:
        w = float(m.group(1))
        if w > target_pt + 0.01:
            issues.append(("FAIL", f"page {w:.1f} pt wide, past the {target_pt:.1f} pt target: LaTeX would overflow"))
        elif w < target_pt - C.WIDTH_TOLERANCE_PT:
            issues.append(("WARN", f"page {w:.1f} pt wide against {target_pt:.1f}: it will not span the column"))
        else:
            issues.append(("INFO", f"page {w:.1f} x {float(m.group(2)):.1f} pt against the {target_pt:.1f} pt target"))
    fonts = sorted(set(re.findall(rb"/BaseFont\s*/([A-Z]{6}\+)?([A-Za-z0-9-]+)", data)))
    names = [f[1].decode() for f in fonts]
    bad = [n for n in names if not any(n.startswith(a) for a in _ALLOWED_PDF_FONTS)]
    if bad:
        issues.append(("FAIL", f"embedded fonts outside the contract: {bad}"))
    else:
        issues.append(("INFO", f"embedded fonts: {names}"))
    if png is not None and Path(png).exists():
        import numpy as np
        from PIL import Image
        a = np.asarray(Image.open(png).convert("L"))
        ink = 100.0 * float((a < 245).mean())
        cols = np.where((a < 245).any(0))[0]
        scale = a.shape[1] / (float(m.group(1)) if m else a.shape[1])
        left = cols[0] / scale if len(cols) else 0.0
        right = (a.shape[1] - 1 - cols[-1]) / scale if len(cols) else 0.0
        if kind == "grid":                                     # a result grid is images edge to edge by design
            issues.append(("INFO", f"ink {ink:.1f} % (a result grid: no range applies)"))
        else:
            lo, hi = C.INK_PLOT if kind == "plot" else C.INK_METHOD
            sev = "INFO" if lo <= ink <= hi else "WARN"
            issues.append((sev, f"ink {ink:.1f} % (contract for a {kind}: {lo:.0f} to {hi:.0f} %)"))
        if max(left, right) > C.GUTTER_MAX:
            issues.append(("WARN", f"gutters L {left:.1f} R {right:.1f} pt, over the {C.GUTTER_MAX:.0f} pt maximum"))
    return issues


def report(issues, pdf, png, reference=None) -> str:
    """Print the findings and the one instruction code cannot carry out. Returns PASS, WARN or FAIL."""
    worst = max((SEVERITY[s] for s, _ in issues), default=0)
    verdict = {0: "PASS", 1: "WARN", 2: "FAIL"}[worst]
    print(f"\n== audit of {Path(pdf).name}: {verdict}")
    for s, msg in sorted(issues, key=lambda i: -SEVERITY[i[0]]):
        print(f"  [{s}] {msg}")
    print(f"  NOW READ {png} with the Read tool before reporting anything: is it the figure intended, is every"
          f" label legible, does anything sit on the data, does the hue order match the paper's other figures?")
    if reference:
        print(f"  and compare it side by side with the reference: {reference}")
    return verdict
