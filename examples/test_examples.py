"""The examples, run as the skill's tests. Synthetic data only: nothing from an unpublished paper ships in this repo.

GREEN  each template draws a figure that passes the audit
RED    each defect the audit exists to catch is caught: collided labels, a word in the wrong face, a label anchored
       outside its axes and so never drawn, a page wider than the column

    python examples/test_examples.py            # writes examples/out/*.pdf and *.png, exits 1 on any failure
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from academic_figure import C, budget, figure, grid, save  # noqa: E402

OUT = ROOT / "examples" / "out"
OUT.mkdir(exist_ok=True)
failures = []


def green_budget():
    fig, ax = figure("cvpr", "col", height_in=1.95)
    ours = [(1, 30.1, 1), (2, 31.8, 2), (4, 32.0, 4), (8, 32.0, 8), (16, 31.95, 16), (32, 31.95, 32)]
    base = [("Method A", 100, 27.1), ("Method B", 100, 25.3), ("Method C", 50, 28.5), ("Method D", 500, 31.6),
            ("Method E", 640, 30.7), ("Method F", 160, 28.6), ("Method G", 300, 28.7)]
    budget(ax, ours, base, operating=4, compare_to="Method D", reference=("Feedforward, no prior evaluations", 26.0),
           ticks=[1, 4, 16, 64, 256])
    ax.set_xlim(0.8, 820)
    save(fig, OUT / "budget.pdf")


def green_grid(seam=C.GRID_SEAM, name="grid"):
    from PIL import Image
    rng = np.random.default_rng(0)
    yy, xx = np.mgrid[0:256, 0:256]
    base = np.stack([128 + 90 * np.sin(xx / 23.0), 128 + 90 * np.cos(yy / 31.0), 128 + 60 * np.sin((xx + yy) / 41.0)], -1)
    paths = []
    for r in range(2):
        row = []
        for c, blur in enumerate([None, 9, 5, 0, 0]):
            img = base.copy()
            if blur is None:                                       # the measurement: a box masked to mid-grey
                img[96:160, 96:160] = 128
            elif blur:
                img = img + rng.normal(0, blur * 3, img.shape)
            p = OUT / f"grid_{r}_{c}.png"
            Image.fromarray(np.clip(img, 0, 255).astype("uint8")).save(p)
            row.append(p)
        paths.append(row)
    fig, _ = grid(paths, ["Measurement", "Method A", "Method B", "Ours", "Reference"], span="col",
                  numbers=["", "24.1 dB", "25.3 dB", "27.9 dB", ""], zoom={0: (96, 96, 160, 160)}, seam=seam)
    save(fig, OUT / f"{name}.pdf")


def red(name, build, expect):
    try:
        build()
    except RuntimeError:
        print(f"RED {name}: caught, as it must be")
        return
    failures.append(f"RED {name}: NOT caught ({expect})")


def red_overlap():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([166, 300], [30.57, 30.68], "o", color=C.BASELINE)
    ax.annotate("Method F", (166, 30.57), xytext=(4, 0), textcoords="offset points", va="center")
    ax.annotate("Method G", (160, 30.6), xytext=(4, 0), textcoords="offset points", va="center")
    ax.set_ylim(27, 34)            # a real plot's range; autoscaled to 0.11 dB the two points sit at opposite edges
    save(fig, OUT / "red_overlap.pdf")


def red_face():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2], [1, 2], color=C.ACCENT)
    ax.set_xlabel("prior evaluations", fontname="DejaVu Sans")
    save(fig, OUT / "red_face.pdf")


def red_undrawn():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 100], [30, 34], "o-", color=C.ACCENT)
    ax.set_xscale("log")
    ax.annotate("Feedforward", (0.5, 31), xytext=(2, 2), textcoords="offset points")
    ax.set_xlim(0.8, 200)
    save(fig, OUT / "red_undrawn.pdf")


if __name__ == "__main__":
    for name, fn in (("budget", green_budget), ("grid", green_grid),
                     ("grid, 1 pt seams", lambda: green_grid(C.GRID_SEAM_FALLBACK, "grid_seam"))):
        try:
            fn()
            print(f"GREEN {name}: passed")
        except Exception as e:                                     # noqa: BLE001  (a test harness reports, it does not crash)
            failures.append(f"GREEN {name}: {type(e).__name__}: {e}")
    red("overlap", red_overlap, "two labels on top of each other")
    red("face", red_face, "a word in DejaVu Sans")
    red("undrawn", red_undrawn, "a label anchored outside its axes")
    print("\n" + ("ALL PASSED" if not failures else "FAILURES:\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)
