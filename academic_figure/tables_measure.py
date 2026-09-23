"""Find the tables of a PDF and measure them, the evidence behind the table part of the contract.

A table starts from its caption: a paragraph that opens "Table n" or "Tab. n" with a stop, a colon or a bold label after
the number. A line that opens that way but continues a paragraph is a mention, not a caption. The table is grown outward
from the caption one element at a time (text line, rule, image) until a gap wider than a row, another caption, a plot, a
line of body text or the running head; a caption with no table above or below it is looked for beside one. When both
sides hold something table-like (floats stacked in a column), the side no other caption can claim wins, then the side
with rules, then the side the paper's other tables sit on, then the nearer one, and the record says so (side_ambiguous).
A rule is a stroked horizontal line or a filled rectangle under 2 pt tall, its dashes rejoined: one spanning 60 % of its
tabular's width is full, a shorter one partial (\\cmidrule), a short one directly under a number an underline (the
second-best mark), and a vertical stroke inside the region a vertical rule. Tabulars set side by side under one caption
are each measured against their own width. Sizes, bold, colour, arrows and decimals are read from the characters inside
the region.
"""
from __future__ import annotations

import re
import statistics as st
from collections import Counter

CAPTION_RE = re.compile(r"^\s*(Table|TABLE|Tab\.)\s*([A-Z]{0,2}\.?\d+(?:\.\d+)?)(\s*[.:|]|(?=\s)|$)")
OTHER_RE = re.compile(r"^\s*(Figure|FIGURE|Fig\.|Algorithm|Listing)\s*([A-Z]{0,2}\.?\d+(?:\.\d+)?)(\s*[.:|]|(?=\s)|$)")
REFS_RE = re.compile(r"^\s*(?:[0-9A-Z]{1,2}\.?\s+)?(References|REFERENCES|Bibliography|BIBLIOGRAPHY)\s*$")
NUM_RE = re.compile(r"\(?[+\-−–]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?:±\d+(?:\.\d+)?)?(?:%|×|[KMGB])?\)?[∗*†‡§¶]*")
YEAR_RE = re.compile(r"\(?(?:19|20)\d\d[a-z]?[),;]")               # the year of an author-year citation
BOLD_RE = re.compile(r"bold|black|heavy|demi|medi|cmbx|sfbx|lmbx|bx\d|-bd\b|bd$", re.I)
ARROWS, MARKS = "↑↓⇑⇓", "†‡§¶∗*"
LIGATURES = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"})
UNMAPPED = {"TeX-matha": {"Ò": "↑", "Ó": "↓", "˘": "±", "“": "="}}  # mathabx glyphs PDFs ship without a Unicode map
FIRST_GAP, ROW_GAP, SET_GAP = 30.0, 9.0, 16.0   # caption to table; row to row; to a rule or a row of cells (pt)


def _rect(b):
    import pymupdf
    return pymupdf.Rect(b)


def _white(c):
    return c is not None and len(c) >= 3 and min(c[:3]) >= 0.98


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(round(255 * v)) for v in (list(c) + [0, 0, 0])[:3])


def _lines(page):
    """Text lines: bbox, baseline, dominant size, text, characters (glyph, bbox, size, bold, coloured), block number."""
    import pymupdf
    flags = pymupdf.TEXTFLAGS_RAWDICT & ~pymupdf.TEXT_PRESERVE_IMAGES
    out = []
    for bno, b in enumerate(page.get_text("rawdict", flags=flags)["blocks"]):
        for l in b.get("lines", []):
            chars, base = [], Counter()
            for s in l["spans"]:
                bold = bool(s["flags"] & 16) or bool(BOLD_RE.search(s["font"]))
                fix = next((m for f, m in UNMAPPED.items() if f in s["font"]), {})
                rgb = (s["color"] >> 16 & 255, s["color"] >> 8 & 255, s["color"] & 255)
                hue = max(rgb) - min(rgb) > 64                           # coloured text, not black or grey
                chars += [(fix.get(c["c"], c["c"]), _rect(c["bbox"]), s["size"], bold, hue) for c in s["chars"]]
                base.update((round(s["size"], 1), round(c["origin"][1], 1)) for c in s["chars"] if c["c"].strip())
            text = "".join(c[0] for c in chars)
            if not text.strip():
                continue
            size = Counter(round(c[2], 1) for c in chars if c[0].strip()).most_common(1)[0][0]
            y = max((k for k in base if k[0] == size), key=lambda k: base[k])[1]      # baseline of the main size
            ink = [c[1] for c in chars if c[0].strip()]
            gap = max([b.x0 - a.x1 for a, b in zip(ink, ink[1:])] + [0.0])           # widest white run: cells
            alpha = sum(ch.isalpha() for ch in text) / max(1, len(ink))              # prose is mostly letters
            out.append(dict(bbox=_rect(l["bbox"]), base=y, size=size, text=text, chars=chars, block=bno, gap=gap,
                            alpha=alpha, flat=abs(l["dir"][1]) < 0.01))
    return out


def layout(pages_lines, height):
    """Body size, column width and column ranges, read from the justified lines of body text, and the band between
    the running heads and the running feet (text repeated at one height above or below the body on many pages)."""
    sizes, lines = Counter(), []
    for ls in pages_lines[:10]:
        for l in ls:
            sizes[l["size"]] += len(l["text"].strip())
            lines.append(l)
    body = sizes.most_common(1)[0][0]
    long = [l for l in lines if abs(l["size"] - body) <= 0.3 and len(l["text"].strip()) >= 40 and l["flat"]]
    colw = Counter(round(l["bbox"].width) for l in long).most_common(1)[0][0] if long else 240
    x0s = Counter(round(l["bbox"].x0) for l in long if abs(l["bbox"].width - colw) <= 2)
    cols = []
    for x, n in x0s.most_common():
        if n < 3 or len(cols) == 2:
            break
        if all(abs(x - c) > colw / 2 for c in cols):
            cols.append(x)
    cols = sorted(cols) or [72]
    first = min((l["bbox"].y0 for l in long), default=0.0)
    last = max((l["bbox"].y1 for l in long), default=height)
    heads, feet = {}, {}
    for p, ls in enumerate(pages_lines):
        for l in ls:
            b, key = l["bbox"], (round(l["bbox"].y0), re.sub(r"[\d\s]", "", l["text"]).lower())   # folios differ by digits
            if b.y1 <= first - 2 and b.y1 < 0.15 * height:
                heads.setdefault(key, {})[p] = b.y1
            elif b.y0 >= last + 2 and b.y0 > 0.85 * height:
                feet.setdefault(key, {})[p] = b.y0
    need = max(3, 0.3 * len(pages_lines))                        # pages, not lines, and early pages among them:
    run = lambda v: len(v) >= need and sum(1 for p in v if 1 <= p <= 6) >= 2   # not a caption repeated in an appendix
    top = max((max(v.values()) + 6 for v in heads.values() if run(v)), default=-1e4)
    bottom = min((min(v.values()) - 2 for v in feet.values() if run(v)), default=1e4)
    return dict(body=body, colw=colw, cols=[(c, c + colw) for c in cols], text=(cols[0], cols[-1] + colw),
                area=(top, bottom))


def _drawn(page):
    """Horizontal rules [x0, x1, y, thickness, dashed], vertical rules (x, y0, y1), filled boxes (rect, colour) and
    graphics (the rect of every path with a curve or two slanted lines: a curve or a marker of a plot, not part of a
    table; a single slanted line is the split cell of a \\diagbox and is skipped). A dashed rule arrives as one short
    stroke per dash and is rejoined."""
    h, v, f, gfx = [], [], [], []
    for g in page.get_drawings():
        stroke, fill, w = g.get("color"), g.get("fill"), g.get("width") or 0.0
        items = g["items"]
        slant = sum(1 for it in items if it[0] == "l" and min(abs(it[1].x - it[2].x), abs(it[1].y - it[2].y)) > 0.3)
        curves = sum(1 for it in items if it[0] == "c")
        if curves and len(items) - curves - slant >= 2:          # a rounded box: a highlighted cell, not a mark
            if fill is not None and not _white(fill):
                f.append((_rect(g["rect"]), fill))
            continue
        if curves or slant >= 2:
            if max(g["rect"].width, g["rect"].height) >= 2:
                gfx.append(_rect(g["rect"]))
            continue
        if slant:
            continue
        if fill is not None and stroke is None and items and all(it[0] == "l" for it in items):
            r = g["rect"]                                        # a filled polygon: a rule or a box
            items = [("re", r, 0)]
        for it in items:
            if it[0] == "l" and stroke is not None and not _white(stroke):
                a, b = it[1], it[2]
                if abs(a.y - b.y) < 0.3 and abs(a.x - b.x) >= 0.3:
                    h.append([min(a.x, b.x), max(a.x, b.x), (a.y + b.y) / 2, w])
                elif abs(a.x - b.x) < 0.3 and abs(a.y - b.y) >= 4:
                    v.append((a.x, min(a.y, b.y), max(a.y, b.y)))
            elif it[0] in ("re", "qu"):
                r = _rect(it[1] if it[0] == "re" else it[1].rect)
                if fill is not None and not _white(fill):
                    if r.height < 2 and r.width >= 2:
                        h.append([r.x0, r.x1, (r.y0 + r.y1) / 2, r.height])
                    elif r.width < 2 and r.height >= 4:
                        v.append(((r.x0 + r.x1) / 2, r.y0, r.y1))
                    elif r.width >= 2 and r.height >= 2:
                        f.append((r, fill))
                elif stroke is not None and not _white(stroke):
                    if r.height < 0.3 and r.width >= 2:
                        h.append([r.x0, r.x1, (r.y0 + r.y1) / 2, w])
                    elif r.width >= 2 and r.height >= 2:             # a framed box: its four sides
                        h += [[r.x0, r.x1, r.y0, w], [r.x0, r.x1, r.y1, w]]
                        v += [(r.x0, r.y0, r.y1), (r.x1, r.y0, r.y1)]
    h.sort(key=lambda r: (round(r[2], 1), r[0]))
    merged = []
    for r in h:                                                  # rejoin a rule drawn in pieces or in dashes
        m = merged[-1] if merged else None
        if m and abs(m[2] - r[2]) <= 0.3 and abs(m[3] - r[3]) <= 0.05:
            gap, short = r[0] - m[1], r[1] - r[0] < 8 and m[5] < 8
            if gap <= 1.0 or (short and gap <= 4.0):
                m[1], m[4], m[5] = max(m[1], r[1]), m[4] or (short and gap > 0.3), r[1] - r[0]
                continue
        merged.append([r[0], r[1], r[2], r[3], False, r[1] - r[0]])
    return [r[:5] for r in merged if r[1] - r[0] >= 2], v, f, gfx


def _is_caption(l, lines, lay, rx):
    m = rx.match(l["text"])
    if not m:
        return None
    if not m.group(3).strip():                                   # no stop or colon: the label must be bold
        label = [c for c in l["chars"][m.start(1):m.end(2)] if c[0].strip()]
        if not label or not all(c[3] for c in label):
            return None
    b, s = l["bbox"], l["size"]
    for o in lines:                                              # a line of the same paragraph right above it
        if (o is not l and abs(o["size"] - s) <= 0.3 and 0.7 * s <= l["base"] - o["base"] <= 1.8 * s
                and o["bbox"].x0 <= b.x0 + 20 and o["bbox"].x1 > b.x0 and o["bbox"].width >= 0.5 * lay["colw"]):
            return None
    return m


def _caption_block(start, lines, taken):
    """The caption paragraph: the start line and the lines that follow it at its size and inside its width."""
    size, row = start["size"], [start]
    reach = (3.0 if len(start["text"].split()) <= 2 else 1.5) * size    # a label set alone is spaced out by justification
    while True:                                                  # the label and the title can be separate lines
        right = max(o["bbox"].x1 for o in row)
        nxt = [o for o in lines if id(o) not in taken and o not in row and abs(o["base"] - start["base"]) <= 1.0
               and abs(o["size"] - size) <= 0.6 and -1 <= o["bbox"].x0 - right <= reach]
        if not nxt:
            break
        row.append(min(nxt, key=lambda o: o["bbox"].x0))
    block, base = list(row), start["base"]
    x0, x1 = start["bbox"].x0, max(o["bbox"].x1 for o in row)
    while True:
        cand = [o for o in lines if id(o) not in taken and o not in block and abs(o["size"] - size) <= 0.6
                and 0.7 * size <= o["base"] - base <= 1.8 * size
                and min(o["bbox"].x1, x1 + 2) - max(o["bbox"].x0, x0 - 2) >= 0.5 * o["bbox"].width]
        if not cand:
            break
        b = min(o["base"] for o in cand)
        row = sorted((o for o in cand if o["base"] <= b + 1.0), key=lambda o: o["bbox"].x0)
        if any(q["bbox"].x0 - p["bbox"].x1 > 1.5 * size for p, q in zip(row, row[1:])):
            break                                                # cells of a table row, not a caption line
        block += row
        base = b
    return block


def _captions(lines, lay):
    out, taken = [], set()
    for l in lines:
        for kind, rx in (("table", CAPTION_RE), ("other", OTHER_RE)):
            m = _is_caption(l, lines, lay, rx)
            if m:
                out.append(dict(kind=kind, number=m.group(2), start=l, label=m.group(0)))
                break
    starts = {id(c["start"]) for c in out}
    for c in sorted(out, key=lambda c: c["start"]["bbox"].y0):
        block = _caption_block(c["start"], lines, starts | taken)
        taken |= {id(o) for o in block}
        c["lines"] = block
        r = _rect(block[0]["bbox"])
        for o in block[1:]:
            r |= o["bbox"]
        c["rect"] = r
        c["rows"] = _count(o["base"] for o in block)
    return out


def _grow(cap, side, xr, lines, rules, images, stops, is_body, first_gap=FIRST_GAP):
    """Elements (rect, kind, obj) of the table on one side of the caption, nearest first, and the first gap."""
    lo, hi = xr

    def inside(x0, x1):
        return min(x1, hi) - max(x0, lo) >= 0.5 * max(x1 - x0, 0.5)

    els = [(l["bbox"], "text", l) for l in lines if inside(l["bbox"].x0, l["bbox"].x1)]
    els += [(_rect((r[0], r[2] - r[3] / 2, r[1], r[2] + r[3] / 2)), "rule", r) for r in rules if inside(r[0], r[1])
            and not (cap.x0 - 1 <= r[0] and r[1] <= cap.x1 + 1 and cap.y0 <= r[2] <= cap.y1 + 1.5)]  # caption underline
    els += [(im, "image", None) for im in images if inside(im.x0, im.x1)]
    els += [(s, "stop", None) for s in stops if inside(s.x0, s.x1)]
    if side == "below":
        els = sorted((e for e in els if e[0].y0 >= cap.y1 - 1), key=lambda e: e[0].y0)
        edge = cap.y1
    else:
        els = sorted((e for e in els if e[0].y1 <= cap.y0 + 1), key=lambda e: -e[0].y1)
        edge = cap.y0
    cells = Counter(round(o["base"] / 2) for _, k, o in els if k == "text")
    taken, first = [], None
    for r, kind, obj in els:
        gap = r.y0 - edge if side == "below" else edge - r.y1
        wide = kind == "rule" or (kind == "text" and cells[round(obj["base"] / 2)] >= 2)   # the next tabular of a stack
        if (gap > ((SET_GAP if wide else ROW_GAP) if taken else first_gap) or kind == "stop"
                or (kind == "text" and is_body(obj)) or (kind == "image" and taken and r.height > 24)):
            break                                                # a picture after table rows belongs to a figure
        taken.append((r, kind, obj))
        first = gap if first is None else first
        edge = max(edge, r.y1) if side == "below" else min(edge, r.y0)
    ruled = [r for r, k, _ in taken if k == "rule"]
    if ruled:                                                    # a stray line of body text past the outer rule
        out = max(r.y1 for r in ruled) if side == "below" else min(r.y0 for r in ruled)
        while (taken and taken[-1][1] == "text" and cells[round(taken[-1][2]["base"] / 2)] < 2
               and (taken[-1][0].y0 >= out - 0.5 if side == "below" else taken[-1][0].y1 <= out + 0.5)
               and is_body(taken[-1][2], loose=True)):
            taken.pop()
    return taken, first


def _beside(cap, side, lay, lines, rules, images, stops, is_body):
    """A table set beside its caption: the elements level with the caption on one side, grown up and down."""
    lo, hi = lay["text"]
    xr = (lo - 4, cap.x0 - 1) if side == "left" else (cap.x1 + 1, hi + 4)
    if xr[1] - xr[0] < 30:
        return [], None
    seed = [(l["bbox"], "text", l) for l in lines]
    seed += [(_rect((r[0], r[2] - r[3] / 2, r[1], r[2] + r[3] / 2)), "rule", r) for r in rules]
    seed = [e for e in seed if e[0].x0 >= xr[0] and e[0].x1 <= xr[1] and e[0].y1 >= cap.y0 - 4 and e[0].y0 <= cap.y1 + 4
            and not (e[1] == "text" and is_body(e[2]))]
    near = [e for e in seed if (cap.x0 - e[0].x1 if side == "left" else e[0].x0 - cap.x1) <= 30]
    if not near:
        return [], None
    if not seed:
        return [], None
    box = _rect(seed[0][0])
    for e in seed[1:]:
        box |= e[0]
    up, _ = _grow(box, "above", (box.x0, box.x1), lines, rules, images, stops, is_body, ROW_GAP)
    down, _ = _grow(box, "below", (box.x0, box.x1), lines, rules, images, stops, is_body, ROW_GAP)
    return seed + up + down, abs(cap.x0 - box.x1 if side == "left" else box.x0 - cap.x1)


def _tableish(taken):
    """A region is a table if it has a rule or an image, or two rows of two or more cells."""
    if any(k in ("rule", "image") for _, k, _ in taken):
        return True
    rows = Counter(round(o["base"] / 2) for _, k, o in taken if k == "text")
    return sum(1 for n in rows.values() if n >= 2) >= 2


def _tokens(line):
    """Cells of a line: runs of characters split at spaces and at gaps wider than a quarter of the type size."""
    toks, cur = [], None
    for ch, r, size, bold, hue in line["chars"]:
        if not ch.strip():
            cur = None
            continue
        if cur is not None and r.x0 - cur["rect"].x1 > 0.25 * size:
            cur = None
        if cur is None:
            cur = dict(text="", rect=_rect(r), bold=0, hue=0, sizes=Counter())
            toks.append(cur)
        cur["text"] += ch
        cur["rect"] |= r
        cur["bold"] += bold
        cur["hue"] += hue
        cur["sizes"][round(size, 1)] += 1
    for t in toks:
        t["size"] = t["sizes"].most_common(1)[0][0]
        t["bold"] = t["bold"] >= 0.5 * len(t["text"])
        t["hue"] = t["hue"] >= 0.5 * len(t["text"])
        m = NUM_RE.fullmatch(t["text"])
        t["num"] = m is not None and not YEAR_RE.fullmatch(t["text"])
        t["dec"] = len(m.group(1) or "") if t["num"] else None
    return toks


def _mode(values):
    values = [v for v in values if v is not None]
    return Counter(values).most_common(1)[0][0] if values else None


def _count(values, tol=2.0):
    """How many distinct positions: values closer than tol count once."""
    n, last = 0, None
    for v in sorted(values):
        if last is None or v - last > tol:
            n += 1
        last = v
    return n


def find_tables(doc, pages=None):
    """One record per table caption found; a caption with nothing next to it is returned as missed."""
    pages = list(pages if pages is not None else range(len(doc)))
    plines = {p: _lines(doc[p]) for p in pages}
    lay = layout([plines[p] for p in pages], doc[pages[0]].rect.height)
    ref = next(((p, l["bbox"]) for p in pages[1:] for l in plines[p]
                if REFS_RE.match(l["text"]) and l["size"] >= lay["body"] - 0.6), None)
    found, missed, drawn = [], [], {}
    for pno in pages:
        lines = plines[pno]
        caps = _captions(lines, lay)
        if not any(c["kind"] == "table" for c in caps):
            continue
        page = doc[pno]
        top, bottom = lay["area"]
        rules, vrules, fills, gfx = _drawn(page)
        rules = [r for r in rules if top <= r[2] <= bottom]
        images = [r for r in (_rect(i["bbox"]) for i in page.get_image_info()) if min(r.width, r.height) > 8]
        drawn[pno] = (rules, vrules, fills, gfx, images)
        in_caps = {id(o) for c in caps for o in c["lines"]}
        free = [l for l in lines if id(l) not in in_caps and top <= l["bbox"].y0 and l["bbox"].y1 <= bottom]
        crossed = {id(l) for l in free for x, y0, y1 in vrules      # a vertical rule runs through table rows only
                   if l["bbox"].x0 + 2 < x < l["bbox"].x1 - 2 and min(y1, l["bbox"].y1) - max(y0, l["bbox"].y0) > 0.5 * l["bbox"].height}

        def prose(l):                                            # a full line of running text, no cell gaps
            return (abs(l["size"] - lay["body"]) <= 0.35 and l["bbox"].width >= 0.7 * lay["colw"] and id(l) not in crossed
                    and len(l["text"].strip()) >= 30 and l["gap"] <= 0.8 * l["size"] and l["alpha"] >= 0.5)

        body_blocks = {b for b, n in Counter(l["block"] for l in free if prose(l)).items() if n >= 2}
        full = [l for l in free if prose(l)]
        tails = {id(l) for l in free for o in full                # the short last line of a paragraph
                 if o is not l and 0.8 * l["size"] <= l["base"] - o["base"] <= 1.6 * l["size"]
                 and abs(o["bbox"].x0 - l["bbox"].x0) <= 2 and abs(o["size"] - l["size"]) <= 0.35}

        def is_body(l, loose=False):                         # loose: a line of text past the rules at body size
            return prose(l) or ((loose or l["block"] in body_blocks or id(l) in tails)
                                and abs(l["size"] - lay["body"]) <= 0.35 and id(l) not in crossed
                                and l["gap"] <= 0.8 * l["size"] and l["alpha"] >= 0.5)

        for c in caps:
            if c["kind"] != "table":
                continue
            cap = c["rect"]
            stops = [o["rect"] for o in caps if o is not c] + gfx
            if c["rows"] >= 2:
                xr = (cap.x0 - 1, cap.x1 + 1)
            else:
                col = next((cr for cr in lay["cols"] if cap.x0 >= cr[0] - 4 and cap.x1 <= cr[1] + 4), None)
                xr = col or lay["text"]
            sides = {}
            for side in ("below", "above"):
                xs = xr
                if c["rows"] < 2:                               # a one-line caption: the table is as wide as its rules
                    near = [r for r in rules if min(r[1], cap.x1 + 10) - max(r[0], cap.x0 - 10) > 0
                            and ((side == "below" and 0 <= r[2] - cap.y1 <= FIRST_GAP)
                                 or (side == "above" and 0 <= cap.y0 - r[2] <= FIRST_GAP))]
                    if near:
                        y = min(near, key=lambda r: abs(r[2] - (cap.y1 if side == "below" else cap.y0)))[2]
                        row = [r for r in near if abs(r[2] - y) <= 1.0]
                        xs = (min(min(r[0] for r in row), cap.x0) - 2, max(max(r[1] for r in row), cap.x1) + 2)
                taken, first = _grow(cap, side, xs, free, rules, images, stops, is_body)
                if taken and _tableish(taken):
                    has_rule = any(k == "rule" for _, k, _ in taken)
                    has_text = any(k == "text" for _, k, _ in taken)
                    sides[side] = dict(taken=taken, first=first, score=(has_rule, has_text), xr=xs)
            if not sides:                                        # a caption set beside its table
                for side in ("left", "right"):
                    taken, first = _beside(cap, side, lay, free, rules, images, stops, is_body)
                    if taken and _tableish(taken):
                        sides[side] = dict(taken=taken, first=first, score=(True, True), xr=lay["text"])
                if len(sides) == 2:
                    sides.pop(max(sides, key=lambda k: sides[k]["first"]))
            rec = dict(page=pno + 1, table=c["number"], caption=c, sides=sides, free=free)
            if not sides:
                missed.append(rec)
            else:
                found.append(rec)
    # a caption with a table on both sides: not the table another caption can only have, then the side with rules,
    # then the side the paper puts its tables on elsewhere, then the nearer one
    for rec in found:
        for s in rec["sides"].values():
            s["rect"] = _rect(s["taken"][0][0])
            for r, _, _ in s["taken"][1:]:
                s["rect"] |= r
    only = [(rec["page"], next(iter(rec["sides"].values()))["rect"]) for rec in found if len(rec["sides"]) == 1]
    decided = [next(iter(rec["sides"])) for rec in found if len(rec["sides"]) == 1]
    usual = Counter(decided)
    for rec in found:
        s = rec["sides"]
        rec["side"] = next(iter(s)) if len(s) == 1 else None
        if rec["side"]:
            continue
        free = [k for k in s if not any(p == rec["page"] and (s[k]["rect"] & o).get_area() > 0.5 * s[k]["rect"].get_area()
                                        for p, o in only)]
        if len(free) == 1:
            rec["side"] = free[0]
        elif s["below"]["score"] != s["above"]["score"]:
            rec["side"] = max(s, key=lambda k: s[k]["score"])
        elif usual and max(usual.values()) >= 0.7 * sum(usual.values()):
            rec["side"] = usual.most_common(1)[0][0]
        else:
            rec["side"] = min(s, key=lambda k: s[k]["first"])
        rec["ambiguous"] = True
    out = []
    for rec in found:
        pno = rec["page"] - 1
        out.append(_measure(doc[pno], lay, ref, rec, rec["side"], rec["free"], *drawn[pno]))
    return out, [dict(page=r["page"], table=r["table"], caption=" ".join(r["caption"]["start"]["text"].split())[:120])
                 for r in missed]


def _tabulars(rules, lines):
    """Rules grouped into tabulars (rules overlapping in x), each split into full and partial against its width."""
    groups = []
    for r in sorted(rules, key=lambda r: r[0]):
        g = next((g for g in groups if min(r[1], g["x1"]) - max(r[0], g["x0"]) > 2), None)
        if g:
            g["rules"].append(r); g["x0"] = min(g["x0"], r[0]); g["x1"] = max(g["x1"], r[1])
        else:
            groups.append(dict(rules=[r], x0=r[0], x1=r[1]))
    for g in groups:
        tx = [l["bbox"] for l in lines if len(groups) == 1 or g["x0"] - 4 <= (l["bbox"].x0 + l["bbox"].x1) / 2 <= g["x1"] + 4]
        x0, x1 = min([g["x0"]] + [b.x0 for b in tx]), max([g["x1"]] + [b.x1 for b in tx])
        g["full"] = sorted((r for r in g["rules"] if r[1] - r[0] >= 0.6 * (x1 - x0)), key=lambda r: r[2])
        g["partial"] = [r for r in g["rules"] if r not in g["full"]]
    return groups


def _measure(page, lay, ref, rec, side, lines, rules, vrules, fills, gfx, images):
    c, got = rec["caption"], rec["sides"][side]
    region = _rect(got["taken"][0][0])
    for r, _, _ in got["taken"][1:]:
        region |= r
    cap = c["rect"]
    inl = [l for l in lines if region.x0 - 1 <= (l["bbox"].x0 + l["bbox"].x1) / 2 <= region.x1 + 1
           and region.y0 - 1 <= (l["bbox"].y0 + l["bbox"].y1) / 2 <= region.y1 + 1 and not l["bbox"].intersects(cap)]
    hr = [r for r in rules if region.y0 - 1 <= r[2] <= region.y1 + 1
          and min(r[1], region.x1 + 1) - max(r[0], region.x0 - 1) >= 0.5 * (r[1] - r[0])]
    toks = [dict(t, line=i) for i, l in enumerate(inl) for t in _tokens(l)]
    # underlines: a short rule whose ends match a number directly above it
    under = []
    for r in hr:
        if r[1] - r[0] > 60:
            continue
        for t in toks:
            tr = t["rect"]
            if (t["num"] and -2.0 <= r[2] - tr.y1 <= 1.0 and min(r[1], tr.x1) - max(r[0], tr.x0) >= 0.7 * (r[1] - r[0])
                    and r[1] - r[0] <= tr.width + 4):
                under.append(r)
                break
    rest = [r for r in hr if r not in under]
    groups = _tabulars(rest, inl)
    main = max(groups, key=lambda g: len(g["full"])) if groups else None
    notes = []                                                   # smaller text past the last full rule
    if main and len(main["full"]) >= 2:
        last, size = main["full"][-1][2], _mode(t["size"] for t in toks)
        if any((l["bbox"].y0 + l["bbox"].y1) / 2 < last for l in inl):
            notes = [l for l in inl if l["bbox"].y0 >= last - 0.3 and l["size"] < size - 0.25]
    note_ids = {id(l) for l in notes}
    core = [l for l in inl if id(l) not in note_ids]
    groups = _tabulars(rest, core)                               # widths again, without the notes
    main = max(groups, key=lambda g: len(g["full"])) if groups else None
    seq = [round(r[3], 2) for r in main["full"]] if main else []
    widths = []
    for w in sorted(round(r[3], 2) for g in groups for r in g["full"]):
        if not widths or w - widths[-1] > 0.04:
            widths.append(w)
    booktabs = any(len(g["full"]) >= 3 and min(g["full"][0][3], g["full"][-1][3]) > max(r[3] for r in g["full"][1:-1]) + 0.04
                   for g in groups)
    # header: the text above the first full rule that has text above it; else the first row
    header_y, prev = None, region.y0 - 1
    for r in (main["full"] if main else []):
        if any(prev - 0.5 <= l["bbox"].y0 and l["bbox"].y1 <= r[2] + 0.5 for l in core):
            header_y = (prev, r[2])
            break
        prev = r[2]
    if header_y is None and core:
        top = min(l["bbox"].y0 for l in core)
        header_y = (top - 0.5, top + 0.6 * max(l["size"] for l in core) + 1)
    head = [i for i, l in enumerate(inl) if header_y and header_y[0] - 0.5 <= l["bbox"].y0 and l["bbox"].y1 <= header_y[1] + 0.5
            and id(l) not in note_ids]
    body_toks = [t for t in toks if id(inl[t["line"]]) not in note_ids]
    cells = [t for t in body_toks if t["line"] not in head]
    vx = []
    for x, y0, y1 in vrules:
        if region.x0 - 1 <= x <= region.x1 + 1 and min(y1, region.y1) - max(y0, region.y0) >= 0.5 * (y1 - y0):
            if not any(abs(x - v) <= 1.0 for v in vx):
                vx.append(x)
    shade = [(r, col) for r, col in fills if region.x0 <= (r.x0 + r.x1) / 2 <= region.x1 and region.y0 <= (r.y0 + r.y1) / 2 <= region.y1
             and r.get_area() <= 1.05 * region.get_area() and r.height <= 0.8 * max(region.height, 1)]
    bands = []
    for r, _ in sorted(shade, key=lambda s: s[0].y0):
        if not bands or r.y0 > bands[-1] + 1.0:
            bands.append(r.y1)
        else:
            bands[-1] = max(bands[-1], r.y1)
    text = "".join(l["text"] for l in inl)
    ctext = _join(c["lines"]).translate(LIGATURES)
    words = [w for w in ctext[len(c["label"].strip()):].split() if any(ch.isalnum() for ch in w)]
    raster = any(im.intersects(region) and (im & region).get_area() >= 0.5 * region.get_area() for im in images)
    x0 = min([b.x0 for b in (l["bbox"] for l in core)] + [r[0] for r in rest]) if (core or rest) else region.x0
    x1 = max([b.x1 for b in (l["bbox"] for l in core)] + [r[1] for r in rest]) if (core or rest) else region.x1
    pno = rec["page"] - 1
    main_text = None
    if ref is not None:
        rp, rb = ref
        main_text = pno < rp or (pno == rp and (region.y1 <= rb.y0 + 1 or region.x1 <= rb.x0 + 5))
    decs = Counter(t["dec"] for t in cells if t["num"])
    return dict(
        page=rec["page"], table=c["number"], main_text=main_text,
        span="full" if (x1 - x0) > 0.6 * page.rect.width else "col", columns=len(lay["cols"]),
        width=round(x1 - x0, 1), height=round(region.height, 1),
        caption_position={"below": "above", "above": "below", "left": "right", "right": "left"}[side],
        caption_lines=c["rows"], caption_words=len(words), caption_text=ctext[:400],
        full_rules=len(main["full"]) if main else 0, rule_widths=widths, rule_seq=seq, booktabs=booktabs,
        partial_rules=sum(len(g["partial"]) for g in groups), dashed_rules=sum(1 for r in rest if r[4]),
        subtables=len(groups), vertical_rules=len(vx),
        body_pt=_mode(t["size"] for t in body_toks), header_pt=_mode(t["size"] for t in toks if t["line"] in head),
        paper_body_pt=lay["body"], text_lines=_count(l["base"] for l in core),
        bold_numeric=sum(1 for t in cells if t["num"] and t["bold"]), numeric_cells=sum(1 for t in cells if t["num"]),
        coloured_numeric=sum(1 for t in cells if t["num"] and t["hue"]),
        underlines=len(under),
        fills=dict(n=len(shade), rows=len(bands), colours=sorted({_hex(col) for _, col in shade})[:4]),
        arrows=sum(text.count(a) for a in ARROWS), plus_minus=text.count("±"),
        footnote_marks=sum(text.count(m) for m in MARKS),
        decimals={str(k): v for k, v in sorted(decs.items())},
        notes=dict(lines=len(notes), pt=_mode(l["size"] for l in notes), text=_join(notes)[:160]) if notes else None,
        raster=raster, side_ambiguous=rec.get("ambiguous", False),
        bbox=[round(v, 1) for v in region], caption_bbox=[round(v, 1) for v in cap])


def _join(lines):
    """Lines in reading order, joined into one string with end-of-line hyphens removed."""
    rows = []
    for l in sorted(lines, key=lambda l: l["base"]):
        if rows and l["base"] - rows[-1][0]["base"] <= 1.5:
            rows[-1].append(l)
        else:
            rows.append([l])
    out = ""
    for l in (l for row in rows for l in sorted(row, key=lambda l: l["bbox"].x0)):
        t = " ".join(l["text"].split())
        if out.endswith("-") and t[:1].islower():
            out = out[:-1] + t
        else:
            out = (out + " " + t).strip()
    return out


def _med(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "-"
    m = st.median(xs)
    return f"{m:g} [{min(xs):g}–{max(xs):g}]"


def _share(rs, f):
    return f"{100 * sum(1 for r in rs if f(r)) / len(rs):.0f}%" if rs else "-"


def summarise(records, groups):
    """Markdown lines: caption length by group and section, then rules, type and marks by group."""
    out = ["| group | where | papers | tables | caption words | caption lines | caption above / below / beside |",
           "|---|---|---|---|---|---|---|"]
    for name, rs in groups.items():
        for where, sel in (("main", [r for r in rs if r["main_text"]]), ("appendix", [r for r in rs if r["main_text"] is False])):
            pos = " / ".join(_share(sel, lambda r, p=p: r["caption_position"] in p) for p in (("above",), ("below",), ("left", "right")))
            out.append(f"| {name} | {where} | {len({r['paper'] for r in sel})} | {len(sel)} | {_med(r['caption_words'] for r in sel)} "
                       f"| {_med(r['caption_lines'] for r in sel)} | {pos} |")
    out += ["", "| group | tables | full span | >=3 full rules | booktabs (thick top+bottom) | vertical rules | dashed rules "
            "| body pt | body/text | header = body | bold numbers | underlines | coloured numbers | shaded rows | arrows | ± "
            "| notes | raster |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, rs in groups.items():
        ratio = [r["body_pt"] / r["paper_body_pt"] for r in rs if r["body_pt"]]
        out.append(f"| {name} | {len(rs)} | {_share(rs, lambda r: r['span'] == 'full')} | {_share(rs, lambda r: r['full_rules'] >= 3)} "
                   f"| {_share(rs, lambda r: r['booktabs'])} | {_share(rs, lambda r: r['vertical_rules'] > 0)} "
                   f"| {_share(rs, lambda r: r['dashed_rules'] > 0)} "
                   f"| {_med(r['body_pt'] for r in rs)} | {_med(round(x, 2) for x in ratio)} "
                   f"| {_share(rs, lambda r: r['header_pt'] == r['body_pt'])} | {_share(rs, lambda r: r['bold_numeric'] > 0)} "
                   f"| {_share(rs, lambda r: r['underlines'] > 0)} | {_share(rs, lambda r: r['coloured_numeric'] > 0)} "
                   f"| {_share(rs, lambda r: r['fills']['rows'] > 0)} "
                   f"| {_share(rs, lambda r: r['arrows'] > 0)} | {_share(rs, lambda r: r['plus_minus'] > 0)} "
                   f"| {_share(rs, lambda r: r['notes'])} | {_share(rs, lambda r: r['raster'])} |")
    out += ["", "| group | numeric cells | decimals 0 / 1 / 2 / 3 / 4+ (share of cells) | tables by modal decimals 0 / 1 / 2 / 3 / 4+ |",
            "|---|---|---|---|"]
    for name, rs in groups.items():
        pool, modal = Counter(), Counter()
        for r in rs:
            d = Counter({min(int(k), 4): 0 for k in r["decimals"]})
            for k, v in r["decimals"].items():
                d[min(int(k), 4)] += v
            pool.update(d)
            if d:
                modal[max(d, key=lambda k: (d[k], -k))] += 1
        n, m = sum(pool.values()), sum(modal.values())
        fmt = lambda c, t: " / ".join(f"{100 * c[k] / t:.0f}" for k in range(5)) if t else "-"
        out.append(f"| {name} | {n} | {fmt(pool, n)} | {fmt(modal, m)} |")
    return out
