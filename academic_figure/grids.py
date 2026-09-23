"""Find the result grids (qualitative figures) of a PDF and measure them, the evidence behind contract §7.

A grid is read from the placements of its raster images: every panel is one image on the page, an image inside
another is an inset (a magnified crop overlaid on its panel), and the images above one "Figure n" caption are that
figure. A figure exported as a single raster shows one image and is reported as such rather than measured. Zoom boxes
are the stroked rectangles drawn over a panel; headers, row labels and numbers are the text spans around the panels.
"""
from __future__ import annotations

import re
import statistics as st

CAPTION_RE = re.compile(r"^\s*(Figure|Fig\.?)\s*(\d+)\s*[.:|]", re.I)
SELECTION_WORDS = ("random", "uncurated", "cherry", "selected", "first", "representative", "typical",
                   "zoom", "best viewed", "enlarge", "magnif", "close-up", "crop")


def _rect(b):
    import pymupdf
    return pymupdf.Rect(b)


def _images(page, min_side=10.0):
    seen, out = set(), []
    for info in page.get_image_info():
        r = _rect(info["bbox"])
        key = tuple(round(v, 1) for v in r)
        if key in seen or r.width < min_side or r.height < min_side:
            continue
        seen.add(key)
        out.append(r)
    return out


def _captions(page):
    out = []
    for b in page.get_text("blocks"):
        m = CAPTION_RE.match(b[4])
        if m:
            out.append((_rect(b[:4]), int(m.group(2)), " ".join(b[4].split())))
    return out


def _cluster(values, tol):
    groups = []
    for v in sorted(values):
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return groups


def _spans(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if s["text"].strip():
                    s = dict(s)
                    s["dir"] = l.get("dir", (1, 0))
                    out.append(s)
    return out


def _zoom_boxes(page, panels):
    """Stroked, unfilled rectangles lying on a panel: the boxes that mark a magnified region."""
    out = []
    for g in page.get_drawings():
        if g.get("fill") is not None or g.get("color") is None:
            continue
        r = g["rect"]
        if r.width < 3 or r.height < 3:
            continue
        for p in panels:
            if p.contains(r) and r.get_area() < 0.8 * p.get_area():
                out.append((r, g.get("width") or 0.0, "#%02x%02x%02x" % tuple(int(255 * c) for c in g["color"][:3])))
                break
    return out


def find_grids(doc, pages=None, min_panels=3):
    grids = []
    for pno in (pages if pages is not None else range(len(doc))):
        page = doc[pno]
        imgs = _images(page)
        if len(imgs) < min_panels:
            continue
        caps = _captions(page)
        if not caps:
            if len(doc) > 1:
                continue
            import pymupdf                                   # a standalone figure PDF: the whole page is figure 0
            caps = [(pymupdf.Rect(page.rect.x0, page.rect.y1, page.rect.x1, page.rect.y1), 0, "(standalone figure)")]
        # an image inside a larger image is an inset
        hosts = {}
        for i, r in enumerate(imgs):
            for j, p in enumerate(imgs):
                if i != j and p.contains(r) and p.get_area() > 1.5 * r.get_area():
                    hosts[i] = j
                    break
        panels = [r for i, r in enumerate(imgs) if i not in hosts]
        insets = [(imgs[i], imgs[j]) for i, j in hosts.items()]
        # each panel belongs to the nearest caption below it whose width overlaps it
        by_fig = {}
        for p in panels:
            below = [c for c in caps if c[0].y0 >= p.y1 - 2 and min(c[0].x1, p.x1) - max(c[0].x0, p.x0) > 0.3 * p.width]
            if below:
                c = min(below, key=lambda c: c[0].y0 - p.y1)
                by_fig.setdefault(c[1], (c, []))[1].append(p)
        spans = _spans(page)
        for number, (cap, ps) in by_fig.items():
            if len(ps) < min_panels:
                continue
            grids.append(_measure(page, pno, number, cap, ps, [ins for ins in insets if ins[1] in ps], spans))
    return grids


def _measure(page, pno, number, cap, panels, insets, spans):
    x0 = min(p.x0 for p in panels); x1 = max(p.x1 for p in panels)
    y0 = min(p.y0 for p in panels); y1 = max(p.y1 for p in panels)
    rows = _cluster([p.y0 for p in panels], 3.0)
    row_of = lambda p: next(i for i, g in enumerate(rows) if min(abs(p.y0 - v) for v in g) <= 3.0)
    by_row = {}
    for p in panels:
        by_row.setdefault(row_of(p), []).append(p)
    hgaps, vgaps = [], []
    for r in by_row.values():
        r.sort(key=lambda p: p.x0)
        hgaps += [b.x0 - a.x1 for a, b in zip(r, r[1:]) if -1 < b.x0 - a.x1 < 30]
    tops = sorted(by_row, key=lambda k: min(p.y0 for p in by_row[k]))
    for a, b in zip(tops, tops[1:]):
        ya = max(p.y1 for p in by_row[a]); yb = min(p.y0 for p in by_row[b])
        if -1 < yb - ya < 60:
            vgaps.append(yb - ya)
    widths = [p.width for p in panels]; heights = [p.height for p in panels]
    sizes = _cluster([round(w) for w in widths], 4.0)
    zooms = _zoom_boxes(page, panels)
    first_row = by_row[tops[0]]
    head = [s for s in spans if y0 - 16 <= s["bbox"][3] <= y0 + 1.5 and x0 - 2 <= s["bbox"][0] <= x1]
    left = [s for s in spans if s["bbox"][2] <= x0 + 1 and s["bbox"][0] >= x0 - 40 and y0 <= s["bbox"][1] <= y1]
    under = [s for s in spans if y0 < s["bbox"][1] < y1 + 12 and x0 <= s["bbox"][0] <= x1
             and any(ch.isdigit() for ch in s["text"]) and not any(p.contains(_rect(s["bbox"])) for p in panels)]
    corners = []
    for ins, host in insets:
        cx = "r" if ins.x1 > host.x1 - 0.3 * host.width else ("l" if ins.x0 < host.x0 + 0.3 * host.width else "c")
        cy = "b" if ins.y1 > host.y1 - 0.3 * host.height else ("t" if ins.y0 < host.y0 + 0.3 * host.height else "m")
        corners.append(cy + cx)
    text = cap[2]
    return dict(
        page=pno + 1, figure=number, width=round(x1 - x0, 1), height=round(y1 - y0, 1),
        span="full" if (x1 - x0) > 0.6 * page.rect.width else "col",
        panels=len(panels), rows=len(by_row), cols=max(len(r) for r in by_row.values()),
        panel_w=round(st.median(widths), 1), panel_h=round(st.median(heights), 1),
        panel_min=round(min(min(widths), min(heights)), 1), panel_sizes=len(sizes),
        seam_h=round(st.median(hgaps), 2) if hgaps else None,
        seam_h_range=(round(min(hgaps), 2), round(max(hgaps), 2)) if hgaps else None,
        seam_v=round(st.median(vgaps), 2) if vgaps else None,
        insets=len(insets), inset_ratio=round(st.median(i.width / h.width for i, h in insets), 2) if insets else None,
        inset_corner=max(set(corners), key=corners.count) if corners else None,
        zoom_boxes=len(zooms), zoom_stroke=round(st.median(z[1] for z in zooms), 2) if zooms else None,
        zoom_colours=sorted({z[2] for z in zooms})[:4],
        header_n=len(head), header_pt=round(st.median(s["size"] for s in head), 1) if head else None,
        row_labels=len(left), row_labels_rotated=sum(1 for s in left if tuple(round(v) for v in s["dir"]) != (1, 0)),
        numbers_under=len(under), caption=text[:220],
        selection=[w for w in SELECTION_WORDS if w in text.lower()],
        first_row_panels=len(first_row))
