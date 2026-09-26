"""The plot templates and contract checks of 0.5.0, run as tests. Synthetic data only: nothing from an unpublished
paper ships in this repo. The ideas behind several of them were surveyed in figures4papers (Chen Liu, CC BY-NC 4.0);
no code was taken from it (see NOTICE).

GREEN  each new template draws a figure that passes the audit: a one-setting sweep on a log axis with the reported
       point enlarged, a variant with a setting never run left as a gap and a dashed reference; a sweep over
       non-uniform settings spaced as categories; a measured gap on a sweep; a y label that is part symbol, part
       words; two radars with one legend under them; labels led out of a crowded cluster; an SVG twin with live text
RED    each defect the audit exists to catch is caught: a second y axis, a 3D axes, bars on an axis that excludes
       zero, bars on a log axis, a gap whose typed text disagrees with the data, two kinds of error bar in one figure;
       and the templates refuse what they cannot draw: a reported setting that was never run, a radar with a gap
AMBER  each defect the audit warns about is named: a title on the axes, a scientific offset on the ticks, powers of
       ten on a log axis, a log axis whose label does not say so, a framed legend, a value printed "-0.00", a label
       across a line, a jet colour map, error bars whose kind is never stated, a legend drawn over the data

    python examples/test_plots.py            # writes examples/out/plots/*.pdf and *.png, exits 1 on any failure
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from academic_figure import (C, audit, declare_errors, figure, gap, mixed_xlabel, mixed_ylabel, radar, save,  # noqa: E402
                             shared_legend, sweep, place_labels)

OUT = ROOT / "examples" / "out" / "plots"
OUT.mkdir(parents=True, exist_ok=True)
failures = []


# --- GREEN -------------------------------------------------------------------------------------------------------------
def green_sweep():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    sweep(ax, [1, 2, 4, 8, 16],
          [("Ours", [30.1, 31.8, 32.0, 32.0, 31.95], "ours"),
           ("Ours, retrained at each N", [30.9, 31.6, 32.0, None, 32.1], "variant"),
           ("Method A", [26.2, 28.9, 30.4, 31.1, 31.4], "baseline")],
          reported=4, reference=("prior alone", 27.2), log=True,
          xlabel="prior evaluations per image (log scale)", ylabel="PSNR (dB)")
    save(fig, OUT / "sweep.pdf")


def green_sweep_categorical():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    sweep(ax, [0.01, 0.05, 0.1, 0.2],
          [("Ours", [34.0, 32.6, 30.9, 28.2], "ours"), ("Method A", [33.1, 31.3, 29.7, 26.9], "baseline")],
          reported=0.05, categorical=True, reported_symbol="\\sigma_y", ylabel="PSNR (dB)")
    mixed_xlabel(ax, [("measurement noise ", "word"), ("$\\sigma_y$", "math")])
    save(fig, OUT / "sweep_categorical.pdf")


def green_gap():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    sweep(ax, [0.01, 0.05, 0.1, 0.2],
          [("Ours", [34.0, 32.6, 30.9, 28.2], "ours"), ("Method A", [33.1, 31.3, 29.7, 26.9], "baseline")],
          categorical=True, ylabel="PSNR (dB)", xlabel="measurement noise")
    gap(ax, (1, 31.3), (1, 32.6), unit="dB")                        # computed: +1.30 dB
    save(fig, OUT / "gap.pdf")


def green_mixed_ylabel():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2, 4, 8], [-1.2, -0.3, 0.0, 0.05], "-o", color=C.ACCENT, lw=C.OURS_W)
    ax.axhline(0, color=C.BASELINE, lw=C.WORK_W, ls=C.DASH_REFERENCE)
    ax.set_xlabel("prior evaluations per image")
    mixed_ylabel(ax, [("$\\Delta$", "math"), ("PSNR (dB)", "word")])
    issues = audit(fig)
    if any("maths set at the word size" in m for _, m in issues):
        failures.append(f"GREEN mixed_ylabel: the symbol was set at the word size: {issues}")
    save(fig, OUT / "mixed_ylabel.pdf")


TASKS = ["Denoise", "Blur", "SR ×2", "Random", "Box", "Stripes", "Motion"]
VALUES = {"Ours": [33.3, 35.6, 34.0, 34.9, 32.8, 33.8, 33.0], "Method A": [33.2, 35.7, 33.2, 34.2, 31.9, 33.4, 33.3],
          "Method B": [32.4, 34.9, 31.6, 34.2, 31.0, 33.1, 31.5]}


def green_radar():
    fig, axes = figure("cvpr", "col", height_in=1.75, ncols=2, subplot_kw=dict(projection="polar"))
    fig.subplots_adjust(wspace=0.8, left=0.07, right=0.93, top=0.86, bottom=0.2)   # the task labels of the two
                                                                                    # radars must not read as one phrase
    lpips = {k: [0.1 - 0.001 * i + 0.002 * j for i in range(7)] for j, k in enumerate(VALUES)}
    radar(axes[0], TASKS, list(VALUES), VALUES, "+", title="PSNR")
    radar(axes[1], TASKS, list(VALUES), lpips, "-", title="LPIPS")
    shared_legend(fig)
    save(fig, OUT / "radar.pdf")


def green_leader():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    pts = [("Method A", 100, 30.1), ("Method B", 110, 30.15), ("Method C", 120, 30.05), ("Method D", 105, 30.2),
           ("Method E", 115, 30.0)]
    for _, x, y in pts:
        ax.plot(x, y, "o", color=C.BASELINE, ms=C.MARKER)
    ax.set_xscale("log")
    ax.set_xlim(20, 800)
    ax.set_ylim(28, 32)
    ax.xaxis.set_major_locator(FixedLocator([25, 50, 100, 200, 400, 800]))    # reader ticks, never 10^2
    ax.xaxis.set_major_formatter(FixedFormatter(["25", "50", "100", "200", "400", "800"]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("prior evaluations per image (log scale)")
    ax.set_ylabel("PSNR (dB)")
    labels = place_labels(ax, pts, leader=True)
    leaders = [t for t in ax.texts if getattr(t, "_af_leader_of", None) is not None]
    if not leaders or len(labels) != len(pts):
        failures.append(f"GREEN leader: {len(leaders)} leaders drawn for a cluster of {len(pts)} labels")
    save(fig, OUT / "leader.pdf")


def green_svg():
    fig, ax = figure("cvpr", "col", height_in=1.6)
    ax.plot([1, 2, 3], [1, 3, 2], "-o", color=C.ACCENT, lw=C.OURS_W)
    ax.set_xlabel("setting")
    ax.set_ylabel("PSNR (dB)")
    save(fig, OUT / "svg.pdf", svg=True)
    svg = (OUT / "svg.svg").read_text()
    if "Arimo" not in svg or "<text" not in svg:
        failures.append("GREEN svg: the SVG twin has no live Arimo text")


# --- RED ---------------------------------------------------------------------------------------------------------------
def red(name, build, expect):
    try:
        build()
    except RuntimeError:
        print(f"RED {name}: caught, as it must be")
        return
    failures.append(f"RED {name}: NOT caught ({expect})")


def refuses(name, build, expect):
    try:
        build()
    except ValueError as e:
        print(f"RED {name}: refused, as it must be ({str(e)[:70]})")
        return
    failures.append(f"RED {name}: NOT refused ({expect})")


def red_twin():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2, 3], [30, 31, 32], color=C.ACCENT, lw=C.OURS_W)
    ax2 = ax.twinx()
    ax2.plot([1, 2, 3], [0.2, 0.15, 0.1], color=C.BASELINE)
    save(fig, OUT / "red_twin.pdf")


def red_3d():
    fig = figure("cvpr", "col", height_in=1.9)[0]
    fig.axes[0].remove()
    ax = fig.add_subplot(projection="3d")
    ax.plot([0, 1], [0, 1], [0, 1], color=C.ACCENT)
    save(fig, OUT / "red_3d.pdf")


def red_bars_truncated():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.bar([0, 1, 2], [31.2, 32.0, 33.1], color=[C.BASELINE, C.BASELINE, C.ACCENT])
    ax.set_ylim(30, 34)                                                # the bar axis no longer starts at zero
    ax.set_ylabel("PSNR (dB)")
    save(fig, OUT / "red_bars.pdf")


def red_bars_log():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.bar([0, 1, 2], [10, 100, 1000], color=C.BASELINE)
    ax.set_yscale("log")
    ax.set_ylabel("prior evaluations (log scale)")
    save(fig, OUT / "red_bars_log.pdf")


def red_gap_text():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 1], [31.3, 32.6], "o", color=C.ACCENT)
    ax.set_ylim(30, 34)
    gap(ax, (1, 31.3), (1, 32.6), text="+2.00 dB")                   # the data say +1.30
    save(fig, OUT / "red_gap.pdf")


def red_mixed_kinds():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.errorbar([1, 2], [30, 31], yerr=[0.2, 0.3], color=C.ACCENT, lw=C.WORK_W)
    ax.errorbar([1.1, 2.1], [29, 30], yerr=[0.4, 0.5], color=C.BASELINE, lw=C.WORK_W)
    declare_errors(fig, "95 % paired-bootstrap CI over 1000 images")
    declare_errors(fig, "standard error over 5 seeds")
    save(fig, OUT / "red_kinds.pdf")


def refuse_sweep_reported():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    sweep(ax, [1, 2, 4], [("Ours", [30, 31, 32], "ours")], reported=8)


def refuse_radar_gap():
    fig, ax = figure("cvpr", "col", height_in=1.9, subplot_kw=dict(projection="polar"))
    radar(ax, TASKS, ["Ours", "Method A"], {"Ours": VALUES["Ours"], "Method A": VALUES["Method A"][:6] + [None]}, "+")


# --- AMBER -------------------------------------------------------------------------------------------------------------
def amber(name, build, needle):
    fig = build()
    issues = audit(fig)
    import matplotlib.pyplot as plt
    plt.close(fig)
    if any(sev == "WARN" and needle in msg for sev, msg in issues):
        print(f"AMBER {name}: warned, as it must")
        return
    failures.append(f"AMBER {name}: no WARN naming '{needle}' in {issues}")


def _line():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2, 3], [30, 31, 32], "-o", color=C.ACCENT, lw=C.OURS_W)
    ax.set_xlabel("setting")
    ax.set_ylabel("PSNR (dB)")
    return fig, ax


def amber_title():
    fig, ax = _line()
    ax.set_title("PSNR against the setting")
    return fig


def amber_offset():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2, 3], [1.0e-7, 3.0e-7, 5.0e-7], "-o", color=C.ACCENT)   # matplotlib writes "1e-7" over the ticks
    ax.set_xlabel("setting")
    ax.set_ylabel("error")
    return fig


def amber_power_ticks():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 10, 100, 1000], [28, 30, 31, 31.5], "-o", color=C.ACCENT)
    ax.set_xscale("log")                                               # matplotlib's default ticks: 10^0 ... 10^3
    ax.set_xlabel("prior evaluations per image (log scale)")
    ax.set_ylabel("PSNR (dB)")
    return fig


def amber_log_label():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 10, 100, 1000], [28, 30, 31, 31.5], "-o", color=C.ACCENT)
    ax.set_xscale("log")
    ax.set_xlabel("prior evaluations per image")                      # log scale, not said
    ax.set_ylabel("PSNR (dB)")
    return fig


def amber_framed_legend():
    fig, ax = _line()
    ax.plot([1, 2, 3], [29, 30, 30.5], "-o", color=C.BASELINE, label="Method A")
    ax.lines[0].set_label("Ours")
    ax.legend(frameon=True, loc="lower right")
    return fig


def amber_negzero():
    fig, ax = _line()
    ax.annotate("-0.00", (2, 31), xytext=(4, 0), textcoords="offset points", va="center")
    return fig


def amber_text_on_line():
    fig, ax = _line()
    ax.annotate("a label on the curve", (2, 31), ha="center", va="center")   # centred on the line it names
    return fig


def amber_jet():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.imshow(np.arange(16.0).reshape(4, 4), cmap="jet")
    ax.set_xlabel("column")
    ax.set_ylabel("row")
    return fig


def amber_errors_nokind():
    fig, ax = _line()
    ax.errorbar([1, 2, 3], [30, 31, 32], yerr=[0.3, 0.2, 0.25], color=C.ACCENT, lw=C.WORK_W, ls="none")
    return fig


def amber_legend_over_data():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    x = np.linspace(0, 1, 40)
    ax.plot(x, 30 + 2 * x, color=C.ACCENT, lw=C.OURS_W, label="Ours")
    ax.plot(x, 29.5 + 2 * x, color=C.BASELINE, lw=C.DATA_W, label="Method A")
    ax.set_xlabel("setting")
    ax.set_ylabel("PSNR (dB)")
    ax.legend(loc="center")                                            # on top of the two lines
    return fig


if __name__ == "__main__":
    for name, fn in (("sweep, log axis", green_sweep), ("sweep, categorical", green_sweep_categorical),
                     ("gap", green_gap), ("mixed_ylabel", green_mixed_ylabel), ("radar", green_radar),
                     ("leader", green_leader), ("svg twin", green_svg)):
        try:
            fn()
            print(f"GREEN {name}: passed")
        except Exception as e:                                     # noqa: BLE001  (a test harness reports, it does not crash)
            failures.append(f"GREEN {name}: {type(e).__name__}: {e}")
    red("twin y axis", red_twin, "a second y axis")
    red("3D axes", red_3d, "a 3D axes")
    red("bars on a truncated axis", red_bars_truncated, "bars whose axis excludes zero")
    red("bars on a log axis", red_bars_log, "bars on a log axis")
    red("gap text", red_gap_text, "a typed difference that disagrees with the data")
    red("two kinds of error bar", red_mixed_kinds, "two error kinds in one figure")
    refuses("sweep, reported setting never run", refuse_sweep_reported, "reported=8 on x without 8")
    refuses("radar with a missing value", refuse_radar_gap, "a None in a radar")
    amber("title", amber_title, "a title on the axes")
    amber("offset text", amber_offset, "offset")
    amber("powers of ten on a log axis", amber_power_ticks, "powers of ten")
    amber("log axis unlabelled", amber_log_label, "log scale")
    amber("framed legend", amber_framed_legend, "framed legend")
    amber("-0.00", amber_negzero, "-0.00")
    amber("text over a line", amber_text_on_line, "over a drawn line")
    amber("jet colour map", amber_jet, "colour map")
    amber("error bars with no kind", amber_errors_nokind, "error bars")
    amber("legend over the data", amber_legend_over_data, "legend over the data")
    print("\n" + ("ALL PASSED" if not failures else "FAILURES:\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)
