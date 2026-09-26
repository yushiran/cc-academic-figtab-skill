"""academic_figure: paper figures at print size, in one paper's style, with the review gate built into save().

    import sys; sys.path.insert(0, "<this skill's base directory>")
    from academic_figure import figure, save, C
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot(x, y, color=C.ACCENT, lw=C.OURS_W)
    save(fig, "figs/fig_budget.pdf", venue="cvpr", span="col")   # closes the width, audits, raises on a FAIL

save() is the point of the package. It is where the habits that fail under deadline pressure are enforced by code:
the page is closed to the column width by measurement, the render is audited for overlapping and clipped text,
fonts that are not the contract's, colours outside the palette and type under the floor, and a PNG twin is
written for the one check no code can make, a person or an agent looking at it.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import contract as C
from .audit import audit, audit_pdf, audit_svg, report

HERE = Path(__file__).resolve().parent
FONT = HERE / "fonts" / "Arimo-Regular.ttf"
_READY = False


def use() -> None:
    """Register the bundled Arimo and install the contract's rcParams. Idempotent; figure() calls it."""
    global _READY
    import matplotlib
    from matplotlib import font_manager
    if not FONT.exists():                                             # never let matplotlib fall back to DejaVu silently
        raise FileNotFoundError(f"{FONT} is missing; the contract's word face cannot be set")
    font_manager.fontManager.addfont(str(FONT))
    matplotlib.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [C.WORD_FACE],
        "mathtext.fontset": C.MATH_FONTSET,             # never set mathtext.default: "it" pulls in cmti10, the TEXT
                                                        # italic, where TeX sets a variable in cmmi10 (tested 2026-09-22)
        "font.size": C.WORD_PT, "axes.labelsize": C.WORD_PT, "axes.titlesize": C.WORD_PT,
        "xtick.labelsize": C.WORD_PT, "ytick.labelsize": C.WORD_PT, "legend.fontsize": C.WORD_PT,
        "text.color": C.INK, "axes.labelcolor": C.INK, "xtick.color": C.INK, "ytick.color": C.INK,
        "axes.edgecolor": C.INK, "axes.linewidth": C.WORK_W,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "axes.axisbelow": True,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": C.TICK_LEN, "ytick.major.size": C.TICK_LEN,
        "xtick.major.width": C.WORK_W, "ytick.major.width": C.WORK_W,
        "xtick.minor.visible": False, "ytick.minor.visible": False,
        "xtick.major.pad": 2.0, "ytick.major.pad": 2.0, "axes.labelpad": 2.5,
        "lines.linewidth": C.DATA_W, "lines.markersize": C.MARKER,
        "legend.frameon": False, "legend.handlelength": 1.6, "legend.borderaxespad": 0.3,
        "axes.prop_cycle": __import__("cycler").cycler(color=list(C.SERIES_BRIGHT)),
        "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.pad_inches": 0.01,
        "pdf.fonttype": 42, "ps.fonttype": 42, "text.usetex": False, "axes.unicode_minus": True,
    })
    _READY = True


def width_in(venue: str = "cvpr", span: str = "col") -> float:
    full, col = C.VENUES[venue]
    return col if span == "col" else full


def figure(venue: str = "cvpr", span: str = "col", height_in: float | None = None, aspect: float = 0.6,
           nrows: int = 1, ncols: int = 1, **kw):
    """A figure at its FINAL printed width. `span` is "col" or "full"; height from `height_in` or `aspect`."""
    import matplotlib.pyplot as plt
    use()
    w = width_in(venue, span)
    fig, ax = plt.subplots(nrows, ncols, figsize=(w, height_in or w * aspect), **kw)
    fig._af_target = (venue, span)                                    # save() closes the width against this
    return fig, ax


def _mediabox_width(path: Path) -> float:
    m = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*\]", path.read_bytes())
    return float(m.group(1)) if m else float("nan")


def save(fig, path, venue: str | None = None, span: str | None = None, reference: str | None = None,
         allow_fail: bool = False, svg: bool = False) -> Path:
    """Write the vector PDF at the target width, a PNG twin, and the audit; raise on any FAIL.

    The tight bounding box trims margins, so the page lands narrower than the column. save() measures the page it
    wrote, widens the figure by the shortfall and writes again, up to three times, so the printed figure spans the
    column with no scaling in LaTeX. Include it with \\includegraphics and no width= argument. `svg` also writes an
    SVG twin with live text, for placing the plot inside a composite figure in Figma; the PDF stays the paper file."""
    import matplotlib.pyplot as plt
    path = Path(path)
    assert path.suffix == ".pdf", "paper figures ship as vector PDF; the PNG is the read-back twin"
    path.parent.mkdir(parents=True, exist_ok=True)
    venue, span = venue or fig._af_target[0], span or fig._af_target[1]
    target = width_in(venue, span) * C.PT_PER_IN
    exact = getattr(fig, "_af_exact", False)                          # a grid is laid out to the width by construction
    kind = getattr(fig, "_af_kind", "plot")
    # bbox_inches=None means "the rcParams default", which is tight; the figure's own box is what switches it off
    whole = {"bbox_inches": fig.bbox_inches, "pad_inches": 0} if exact else {}
    w_prev = got_prev = None
    for _ in range(6):
        fig.savefig(path, **whole)
        got = _mediabox_width(path)
        if exact or target - C.WIDTH_TOLERANCE_PT <= got <= target:
            break
        w, h = fig.get_size_inches()
        gain = C.PT_PER_IN                                            # page points gained per inch of figure width
        if w_prev is not None and abs(w - w_prev) > 1e-6:            # a layout whose labels hang off the axes answers
            g = (got - got_prev) / (w - w_prev)                       # with less or more than one; use the measured gain
            if 0.3 * C.PT_PER_IN < g < 3.0 * C.PT_PER_IN:
                gain = g
        w_prev, got_prev = w, got
        fig.set_size_inches(w + (target - 0.5 * C.WIDTH_TOLERANCE_PT - got) / gain, h)
    png = path.with_suffix(".png")
    fig.savefig(png, dpi=300, **whole)
    issues = audit(fig) + audit_pdf(path, target, png, kind=kind)
    if svg:
        import matplotlib
        with matplotlib.rc_context({"svg.fonttype": "none"}):                  # text as text, editable in Figma
            fig.savefig(path.with_suffix(".svg"), **whole)
        issues += audit_svg(path.with_suffix(".svg"), _mediabox_width(path))
    verdict = report(issues, path, png, reference)
    plt.close(fig)
    if verdict == "FAIL" and not allow_fail:
        raise RuntimeError(f"{path.name} failed the audit; fix every FAIL above before handing it over")
    return path


# from .templates import budget, grid, mixed_label, mixed_xlabel, place_labels  # noqa: E402  (templates import the contract, not this module)
from .templates import (budget, declare_errors, gap, grid, mixed_label, mixed_xlabel, mixed_ylabel,  # noqa: E402
                        place_labels, radar, shared_legend, sweep)

# __all__ = ["C", "use", "figure", "save", "width_in", "audit", "budget", "grid", "mixed_label", "mixed_xlabel", "place_labels"]
__all__ = ["C", "use", "figure", "save", "width_in", "audit", "budget", "grid", "mixed_label", "mixed_xlabel",
           "mixed_ylabel", "place_labels", "sweep", "gap", "radar", "shared_legend", "declare_errors"]
