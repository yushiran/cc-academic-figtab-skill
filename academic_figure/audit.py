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
