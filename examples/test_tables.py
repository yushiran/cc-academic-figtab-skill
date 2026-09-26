"""The table tools, run as tests. Synthetic results only: nothing from an unpublished paper ships in this repo.

GREEN  tables built by header() and build() from their data pass verify() and the source audit with no WARN: two
       cells that print the same take the same mark, the second is the next distinct value, 0.0785 prints 0.079,
       a two-row task block takes no second mark, the task-block scope is inferred and stated, every name is on the
       canon; the CLI exits 0 on them
RED    each defect the audit or verify() exists to catch is caught: a 95-word caption, a hand-typed bold on a cell
       that is not the best, a tie marked only once, a vertical rule, an \\hline, an off-canon name (a forbidden
       variant in a table, a miscased one in the prose), a stale number that only verify() can see; the CLI exits 1
AMBER  each defect the audit warns about is named: decimals that differ within a column, marks in a column with no
       arrow, a per-block scope the caption's mark sentence does not state

    uv run --with pyyaml python examples/test_tables.py     # writes examples/out/tables/, exits 1 on any failure
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from academic_figure.tables import (Column, Row, audit_tex, build, caption_report, caption_words,  # noqa: E402
                                    check_names, component_columns, fmt, header, improvement, load_canon, verify)

OUT = ROOT / "examples" / "out" / "tables"
shutil.rmtree(OUT, ignore_errors=True)
for d in ("green", "red", "amber"):
    (OUT / d).mkdir(parents=True)
failures = []

# a result file, as a builder would read it: means per method, unrounded
RESULTS = {
    "tv":      dict(nfe=0, psnr=26.2249, ssim=0.5093, lpips=0.4212),
    "wavelet": dict(nfe=0, psnr=26.4712, ssim=0.5981, lpips=0.3956),
    "ram":     dict(nfe=0, psnr=30.8712, ssim=0.9081, lpips=0.1611),
    "pnpflow": dict(nfe=500, psnr=32.3491, ssim=0.9107, lpips=0.1384),
    "flower":  dict(nfe=500, psnr=33.1702, ssim=0.92804, lpips=0.0781),    # SSIM ties Ours x5, LPIPS ties Ours
    "otode":   dict(nfe=180, psnr=30.6523, ssim=0.8772, lpips=0.1293),
    "flowdps": dict(nfe=100, psnr=30.7401, ssim=0.8834, lpips=0.1352),
    "ours":    dict(nfe=8, psnr=33.3333, ssim=0.9271, lpips=0.0784),
    "ours5":   dict(nfe=24, psnr=33.4049, ssim=0.9279, lpips=0.0785),       # 0.0785 prints 0.079, half-up
}
COLS = [Column("nfe", "NFE", None, 0), Column("psnr", "PSNR", "+", 2), Column("ssim", "SSIM", "+", 3),
        Column("lpips", "LPIPS", "-", 3)]
ROWS = [Row("tv", "TV", "Classical"), Row("wavelet", "Wavelet", "Classical"), Row("ram", "RAM", "Supervised"),
        Row("pnpflow", "PnP-Flow", "Training-free"), Row("flower", "Flower", "Training-free"),
        Row("otode", "OT-ODE", "Training-free"), Row("flowdps", "FlowDPS", "Training-free"),
        Row("ours", "Ours", ours=True), Row("ours5", r"Ours$\times5$", ours=True)]
value = lambda r, c: RESULTS[r][c]                                         # noqa: E731
CAPTION = (r"Gaussian deblurring on CelebA-128, 1000 test images at $\sigma_y{=}0.05$, every baseline tuned on the "
           r"same 32 validation images. Best per column in bold, second underlined; our rows shaded.")

# task blocks, marked per block: a six-row block and a two-row block
TASKS = {("Gaussian deblurring", "flower"): (35.7412, 0.0751), ("Gaussian deblurring", "pnpflow"): (34.9133, 0.0962),
         ("Gaussian deblurring", "otode"): (33.0711, 0.0983), ("Gaussian deblurring", "flowdps"): (31.8803, 0.1262),
         ("Gaussian deblurring", "ours"): (35.5804, 0.0772), ("Gaussian deblurring", "ours5"): (35.7703, 0.0764),
         ("Box inpainting", "flower"): (31.8512, 0.0561), ("Box inpainting", "ours"): (32.8431, 0.0541)}
NAMES = dict(flower="Flower", pnpflow="PnP-Flow", otode="OT-ODE", flowdps="FlowDPS", ours="Ours", ours5=r"Ours$\times5$")
TCOLS = [Column("psnr", "PSNR", "+", 2), Column("lpips", "LPIPS", "-", 3)]
TROWS = [Row(f"{t}|{m}", NAMES[m], t, ours=m.startswith("ours")) for t, m in TASKS]
tvalue = lambda r, c: TASKS[tuple(r.split("|"))][0 if c == "psnr" else 1]  # noqa: E731
TCAPTION = r"Two tasks on CelebA-128, 1000 test images. Best per task and column in bold, second underlined."

CANON = OUT / "names.yaml"
CANON.write_text("""\
methods:
  tv: TV
  wavelet: Wavelet
  ram: RAM
  pnpflow: {name: PnP-Flow, forbid: [PnPFlow, PnP Flow]}
  flower: Flower
  otode: {name: OT-ODE, forbid: [OT ODE]}
  flowdps: {name: FlowDPS, forbid: [Flow-DPS]}
  ours: {name: Ours, forbid: ["(ours)"]}
metrics:
  nfe: {name: NFE, forbid: [Prior evals, NFEs]}
  lpips: {name: LPIPS, forbid: [LPIPS-vgg]}
tasks:
  gauss: {name: Gaussian deblurring, forbid: [Blur, Gaussian blur, Deblurring]}
  box: {name: Box inpainting, forbid: [Box, Box inpaint]}
datasets:
  celeba: {name: CelebA-128, forbid: [CelebA 128, CelebA128]}
""")


def table(label, caption=CAPTION, cols=COLS, rows=ROWS, fn=value, scope="table", spec=None, edit=lambda t: t,
          second=True, delta=None, lead=None):
    # lead = ["Type", "Method"] if scope == "table" else ["Task", "Method"]
    # spec = spec or "@{}ll" + "r" * len(cols) + "@{}"
    lead = lead or (["Type", "Method"] if scope == "table" else ["Task", "Method"])
    spec = spec or "@{}" + "l" * len(lead) + "r" * len(cols) + "@{}"
    tex = "\n".join([r"\begin{table}[t]", r"  \centering", rf"  \caption{{{caption}}}", rf"  \label{{{label}}}",
                     r"  \footnotesize", rf"  \begin{{tabular}}{{{spec}}}", header(cols, lead),
                     build(cols, rows, fn, scope=scope, second=second, delta=delta), r"    \bottomrule",
                     r"  \end{tabular}", r"\end{table}", ""])
    return edit(tex)


# a component ablation: three switches, four rows, the full model last
COMPONENTS = [("gate", "Gate"), ("grid", "Geometric grid"), ("onpol", "On-policy")]
CODES = {"a100": "100", "a110": "110", "a101": "101", "a111": "111"}
ABL = {"a100": (31.1212, 0.1123), "a110": (31.4644, 0.1041), "a101": (31.3813, 0.1072), "a111": (31.7109, 0.0993)}
AROWS = [Row("a100", "Gate only"), Row("a110", "Gate and grid"), Row("a101", "Gate and on-policy"),
         Row("a111", "Ours", ours=True)]
ACAPTION = r"Component ablation on CelebA-128, 1000 test images, Gaussian deblurring. Best per column in bold."
DELTA = r"$\Delta$ over the best baseline"


def write(path, *tables, prose=r"Table~\ref{tab:pixel} compares Flower, PnP-Flow and OT-ODE on CelebA-128."):
    path.write_text(prose + "\n\n" + "\n".join(tables))
    return path


def verdicts(path, canon=CANON):
    reports, text = audit_tex([path], canon)
    return reports, text, [(sev, check) for r in reports for sev, check, _ in r["checks"] if sev in ("WARN", "FAIL")]


def check(kind, name, ok, detail=""):
    if ok:
        print(f"{kind} {name}: " + {"GREEN": "passed", "RED": "caught, as it must be", "AMBER": "warned, as it must"}[kind])
    else:
        failures.append(f"{kind} {name}: {detail}")


def green():
    body = build(COLS, ROWS, value)
    check("GREEN", "ties take the same mark, the second is the next distinct value",
          body.count(r"\textbf{0.928}") == 2 and body.count(r"\underline{0.927}") == 1
          and body.count(r"\textbf{0.078}") == 2 and body.count(r"\underline{0.079}") == 1 and fmt(0.0785, 3) == "0.079",
          body)
    tbody = build(TCOLS, TROWS, tvalue, scope="group")
    box = tbody.split(r"\midrule")[-1]
    check("GREEN", "a two-row block takes bold only", r"\underline" not in box and box.count(r"\textbf") == 2, box)
    path = write(OUT / "green" / "results.tex", table("tab:pixel"), table("tab:tasks", TCAPTION, TCOLS, TROWS, tvalue,
                                                                            scope="group"))
    issues = verify(path, "tab:pixel", COLS, ROWS, value) + verify(path, "tab:tasks", TCOLS, TROWS, tvalue, scope="group")
    check("GREEN", "verify, tables built from their data", not issues, issues)
    reports, text, bad = verdicts(path)
    scoped = any("within each row block" in m for r in reports for _, _, m in r["checks"])
    check("GREEN", "audit, no WARN or FAIL, the block scope inferred", not bad and not text and scoped
          and all(r["verdict"] == "PASS" for r in reports), (bad, text, [r["checks"] for r in reports]))
    caps = caption_report(path)
    check("GREEN", "caption_report", [c["verdict"] for c in caps] == ["PASS", "PASS"], caps)
    got = improvement(COLS, ROWS, value)
    check("GREEN", "improvement() on the printed values: 33.33 - 33.17, 0.927 - 0.928, 0.078 - 0.078",
          got == {"nfe": None, "psnr": r"$+$0.16", "ssim": r"$-$0.001", "lpips": "0.000"}, got)
    dpath = write(OUT / "green" / "delta.tex", table("tab:delta", delta=DELTA))
    issues = verify(dpath, "tab:delta", COLS, ROWS, value, delta=DELTA)
    reports, _, bad = verdicts(dpath)
    recomputed = any(c == "delta" and s == "PASS" for r in reports for s, c, _ in r["checks"])
    check("GREEN", "a Δ row: verified, recomputed by the audit, left out of the marks", not issues and not bad
          and recomputed, (issues, bad, [r["checks"] for r in reports]))
    ccols, cvalue = component_columns(COMPONENTS, CODES, values=lambda r, c: ABL[r][0 if c == "psnr" else 1])
    apath = write(OUT / "green" / "ablation.tex", table("tab:abl", ACAPTION, ccols + TCOLS, AROWS, cvalue,
                                                        spec="@{}lcccrr@{}", second=False, lead=["Method"]))
    issues = verify(apath, "tab:abl", ccols + TCOLS, AROWS, cvalue, second=False)
    _, _, bad = verdicts(apath)
    ticks = apath.read_text().count(r"\checkmark")
    check("GREEN", "component columns: one ✓ per switched-on component, unranked, verified", not issues and not bad
          and ticks == sum(code.count("1") for code in CODES.values()), (issues, bad, ticks))
    run = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_tables.py"), str(OUT / "green"), "--canon",
                          str(CANON)], capture_output=True, text=True)
    check("GREEN", "CLI exits 0", run.returncode == 0, run.stdout + run.stderr)


def red(name, path, want, canon=CANON):
    _, text, bad = verdicts(path, canon)
    check("RED", name, ("FAIL", want) in bad or (want == "names" and text), bad)


def reds():
    long = CAPTION + " " + " ".join(["The protocol of every arm is restated here at length, as in the draft."] * 5)
    red(f"a caption of {caption_words(long)} words", write(OUT / "red" / "caption.tex", table("tab:long", long)),
        "caption")
    red("a hand-typed bold on a cell that is not the best",
        write(OUT / "red" / "bold.tex", table("tab:bold", edit=lambda t: t.replace("30.87", r"\textbf{30.87}"))), "marks")
    red("a tie marked only once",
        write(OUT / "red" / "tie.tex", table("tab:tie", edit=lambda t: t.replace(r"\textbf{0.928}", "0.928", 1))), "marks")
    red("a vertical rule", write(OUT / "red" / "vrule.tex", table("tab:vrule", spec="@{}ll|rrrr@{}")), "rules")
    red("an \\hline", write(OUT / "red" / "hline.tex", table("tab:hline", edit=lambda t: t.replace(r"\midrule", r"\hline"))),
        "rules")
    rows = [Row(r.key, "PnP Flow", r.cls) if r.key == "pnpflow" else r for r in ROWS]
    path = write(OUT / "red" / "names.tex", table("tab:names", rows=rows),
                 prose="Our controller beats Pnp-Flow on\nCelebA-128.")
    reports, text, _ = verdicts(path)
    got = {(h["found"], h["line"]) for h in check_names([path], load_canon(CANON))}
    lines = path.read_text().splitlines()
    want = {("PnP Flow", next(i for i, s in enumerate(lines, 1) if "PnP Flow" in s)), ("Pnp-Flow", 1)}
    check("RED", "an off-canon name in a table and a miscased one in the prose",
          any(c == "names" and s == "FAIL" for r in reports for s, c, _ in r["checks"]) and len(text) == 1
          and got == want, (got, want, text))
    stale = write(OUT / "red" / "stale.tex", table("tab:stale", edit=lambda t: t.replace("33.33", "33.31")))
    issues = verify(stale, "tab:stale", COLS, ROWS, value)
    _, _, bad = verdicts(stale)
    check("RED", "a stale number, seen by verify() and invisible to the audit",
          len(issues) == 1 and issues[0]["row"] == "ours" and issues[0]["column"] == "psnr" and issues[0]["line"]
          and not bad, (issues, bad))
    dstale = write(OUT / "red" / "delta.tex", table("tab:dstale", delta=DELTA,
                                                    edit=lambda t: t.replace(r"$+$0.16", r"$+$0.18")))
    red("a Δ row that disagrees with the printed cells", dstale, "delta")
    issues = verify(dstale, "tab:dstale", COLS, ROWS, value, delta=DELTA)
    check("RED", "the same stale Δ, seen by verify()", [(i["row"], i["column"]) for i in issues] == [("delta", "psnr")],
          issues)
    for name, codes in (("a code with a bit missing", dict(CODES, a110="11")),
                        ("two rows with one code", dict(CODES, a101="110"))):
        try:
            component_columns(COMPONENTS, codes)
            check("RED", f"component_columns: {name}", False, "not refused")
        except ValueError:
            check("RED", f"component_columns: {name}", True)
    run = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_tables.py"), str(OUT / "red")],
                         capture_output=True, text=True)
    check("RED", "CLI exits 1", run.returncode == 1, run.stdout[-400:] + run.stderr)


def amber(name, path, needle):
    reports, _ = audit_tex([path], CANON)
    msgs = [m for r in reports for s, _, m in r["checks"] if s == "WARN"]
    check("AMBER", name, any(needle in m for m in msgs), msgs)


def ambers():
    amber("decimals that differ within a column",
          write(OUT / "amber" / "decimals.tex", table("tab:dec", edit=lambda t: t.replace("33.17", "33.2"))), "decimals differ")
    amber("marks in a column with no arrow", write(OUT / "amber" / "arrow.tex", table(
        "tab:arrow", edit=lambda t: t.replace(r"SSIM~$\uparrow$", "SSIM"))), "columns with no arrow")
    amber("a per-block scope the caption does not state", write(OUT / "amber" / "scope.tex", table(
        "tab:scope", "Two tasks on CelebA-128. Best in bold, second underlined.", TCOLS, TROWS, tvalue, scope="group")),
        "does not say so")


if __name__ == "__main__":
    for fn in (green, reds, ambers):
        try:
            fn()
        except Exception as e:                                     # noqa: BLE001  (a test harness reports, it does not crash)
            import traceback
            failures.append(f"{fn.__name__}: {type(e).__name__}: {e}\n{traceback.format_exc()}")
    print("\n" + ("ALL PASSED" if not failures else "FAILURES:\n  " + "\n  ".join(map(str, failures))))
    sys.exit(1 if failures else 0)
