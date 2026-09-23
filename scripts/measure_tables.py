"""Measure the tables of published papers, the evidence behind the table part of the contract.

    uv run --with pymupdf python scripts/measure_tables.py --out /tmp/tables a.pdf b.pdf ... [--group Kaiming=resnet,moco]
    uv run --with pymupdf python scripts/measure_tables.py --out /tmp/tables --name tables_ours ours.pdf

Writes <name>.json (one record per table found) and <name>.md (the table, the captions with no table next to them, and
the summary by group), and renders every table found, region and caption, to <out>/table_renders/<paper>_tab<n>.png at
110 dpi so the detection can be checked by eye. --group NAME=prefix,prefix adds a summary row for the papers whose file
stem starts with one of the prefixes; "all" is always there.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pymupdf  # noqa: E402

from academic_figure.tables_measure import find_tables, summarise  # noqa: E402

COLS = ("paper", "page", "table", "main_text", "span", "width", "caption_position", "caption_lines", "caption_words",
        "full_rules", "rule_seq", "booktabs", "partial_rules", "dashed_rules", "vertical_rules", "subtables", "body_pt",
        "header_pt", "text_lines", "bold_numeric", "underlines", "coloured_numeric", "fills", "arrows", "plus_minus",
        "footnote_marks", "decimals", "notes")


def _cell(k, v):
    if k == "fills":
        return f"{v['rows']} rows {' '.join(v['colours'])}" if v["n"] else "0"
    if k == "notes":
        return f"{v['lines']} @{v['pt']}" if v else "-"
    if k == "decimals":
        return " ".join(f"{d}:{n}" for d, n in v.items()) or "-"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="tables")
    ap.add_argument("--max-pages", type=int, default=60)
    ap.add_argument("--group", action="append", default=[], help="NAME=prefix,prefix")
    a = ap.parse_args()
    out = Path(a.out); (out / "table_renders").mkdir(parents=True, exist_ok=True)
    records, missed, empty = [], [], []
    for p in a.pdfs:
        doc = pymupdf.open(p)
        name = Path(p).stem[:48]
        tables, miss = find_tables(doc, pages=range(min(len(doc), a.max_pages)))
        if not tables:
            empty.append(name)
        missed += [dict(m, paper=name) for m in miss]
        for t in tables:
            t["paper"] = name
            stem = f"{name}_tab{t['table']}"
            if any(r["paper"] == name and r["table"] == t["table"] for r in records):
                stem += f"_p{t['page']}"                     # numbering restarted in a supplement
            t["render"] = stem + ".png"
            records.append(t)
            page = doc[t["page"] - 1]
            clip = (pymupdf.Rect(t["bbox"]) | pymupdf.Rect(t["caption_bbox"])) + (-4, -4, 4, 4)
            page.get_pixmap(dpi=110, clip=clip & page.rect).save(out / "table_renders" / t["render"])
        doc.close()
    (out / f"{a.name}.json").write_text(json.dumps(records, indent=1, ensure_ascii=False))
    groups = {"all": records}
    for g in a.group:
        label, prefixes = g.split("=", 1)
        groups[label] = [r for r in records if r["paper"].startswith(tuple(prefixes.split(",")))]
    with open(out / f"{a.name}.md", "w") as f:
        f.write("| " + " | ".join(COLS) + " |\n|" + "---|" * len(COLS) + "\n")
        for r in records:
            f.write("| " + " | ".join(_cell(c, r.get(c)) for c in COLS) + " |\n")
        f.write(f"\nNo table found in: {', '.join(empty) or '-'}\n\nCaptions with no table next to them:\n")
        for m in missed:
            f.write(f"- {m['paper']} p{m['page']} Table {m['table']}: {m['caption']}\n")
        f.write("\n## Summary\n\n" + "\n".join(summarise(records, groups)) + "\n")
    print(f"{len(records)} tables from {len(a.pdfs) - len(empty)} of {len(a.pdfs)} papers, {len(missed)} captions missed; "
          f"table {out / (a.name + '.md')}")


if __name__ == "__main__":
    main()
