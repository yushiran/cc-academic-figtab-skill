"""Audit the tables of a paper in its LaTeX source, every live .tex file under a directory, with no spec needed.

    uv run --with pyyaml python scripts/audit_tables.py <paper_dir> [--canon names.yaml]

Per table, PASS, WARN or FAIL for: the caption's length against references/tables.md; a vertical rule in the column
spec, and \\hline or \\cline; the bold and underline marks, recomputed on the printed cells under the scope that
explains them best (per column, per row block or per row), each column's direction read from its header arrow, with
the columns that have no arrow named; decimals that differ within a numeric column; and, given a canon, every
off-canon name in the table, then every one outside the tables. Commented lines and \\iffalse blocks are skipped, so a
table kept there for the record is not audited. Exits 1 on any FAIL or any off-canon name.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from academic_figure.tables import audit_tex  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paper", help="the paper's directory; every .tex file under it is read")
    ap.add_argument("--canon", help="names.yaml: one display name per method, metric, task and dataset, and the "
                                    "variants each forbids")
    a = ap.parse_args()
    root = Path(a.paper).resolve()
    paths = sorted(p for p in root.rglob("*.tex") if p.is_file())
    reports, text_hits = audit_tex(paths, a.canon)
    rel = lambda p: str(Path(p).resolve().relative_to(root))
    for r in reports:
        where = f"{rel(r['path'])}:{r['line']}"
        what = f"{r['env']}[{r['placement']}]" if r["placement"] else r["env"]
        pos = f", caption {r['position']}" if r["position"] else ""
        print(f"{r['verdict']:<5} {', '.join(r['labels']) or '(no label)'}  {where}  {what}{pos}")
        for sev, check, msg in r["checks"]:
            print(f"      {msg}" if not sev else f"  {sev:<5} {check:<9} {msg}")
        if a.canon is None:
            print(f"  {'-':<5} {'names':<9} not checked (no --canon)")
        print()
    if a.canon is not None:
        print(f"Off-canon names outside the tables: {len(text_hits)}")
        for h in text_hits:
            print(f"  {rel(h['path'])}:{h['line']}: '{h['found']}' for '{h['name']}'")
        print()
    n = {s: sum(r["verdict"] == s for r in reports) for s in ("PASS", "WARN", "FAIL")}
    files = len({r["path"] for r in reports})
    print(f"{len(reports)} tables in {files} of {len(paths)} .tex files: {n['PASS']} PASS, {n['WARN']} WARN, "
          f"{n['FAIL']} FAIL")
    sys.exit(1 if n["FAIL"] or text_hits else 0)


if __name__ == "__main__":
    main()
