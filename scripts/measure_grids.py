"""Measure the result grids of published papers, the evidence behind contract §7.

    uv run --with pymupdf python scripts/measure_grids.py --out /tmp/grids a.pdf b.pdf ...

Writes grids.json (one record per figure found) and grids.md (the table), and renders every figure found, panels and
caption, to <out>/renders/<paper>_fig<n>.png at 110 dpi so its grammar can be read by eye. A paper whose figures are
single rasters yields nothing and is listed as such.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymupdf  # noqa: E402

from academic_figure.grids import find_grids  # noqa: E402

COLS = ("paper", "page", "figure", "span", "width", "rows", "cols", "panels", "panel_w", "panel_min", "panel_sizes",
        "seam_h", "seam_v", "insets", "inset_ratio", "inset_corner", "zoom_boxes", "zoom_stroke", "header_pt",
        "row_labels", "row_labels_rotated", "numbers_under", "selection")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-pages", type=int, default=40)
    a = ap.parse_args()
    out = Path(a.out); (out / "renders").mkdir(parents=True, exist_ok=True)
    records, empty = [], []
    for p in a.pdfs:
        doc = pymupdf.open(p)
        name = Path(p).stem[:48]
        grids = find_grids(doc, pages=range(min(len(doc), a.max_pages)))
        if not grids:
            empty.append(name)
        for g in grids:
            g["paper"] = name
            records.append(g)
            page = doc[g["page"] - 1]
            cap = next((b for b in page.get_text("blocks") if b[4].lstrip().startswith(("Figure " + str(g["figure"]),
                        "Fig. " + str(g["figure"]), "Fig " + str(g["figure"])))), None)
            imgs = [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
            top = min([r.y0 for r in imgs if r.width > 8] + [page.rect.y1])
            clip = pymupdf.Rect(page.rect.x0, max(0, top - 18), page.rect.x1, (cap[3] + 4) if cap else page.rect.y1)
            page.get_pixmap(dpi=110, clip=clip).save(out / "renders" / f"{name}_fig{g['figure']}.png")
    (out / "grids.json").write_text(json.dumps(records, indent=1, default=str))
    with open(out / "grids.md", "w") as f:
        f.write("| " + " | ".join(COLS) + " |\n|" + "---|" * len(COLS) + "\n")
        for r in records:
            f.write("| " + " | ".join(str(r.get(c)) for c in COLS) + " |\n")
        f.write(f"\nNo multi-image grid found in: {', '.join(empty)}\n")
    print(f"{len(records)} grids from {len(a.pdfs) - len(empty)} of {len(a.pdfs)} papers; table {out / 'grids.md'}")


if __name__ == "__main__":
    main()
