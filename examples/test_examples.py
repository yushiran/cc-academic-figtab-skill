"""The examples, run as the skill's tests. Synthetic data only: nothing from an unpublished paper ships in this repo.

GREEN  each template draws a figure that passes the audit; grids with column blocks and row labels, a crop row with
       two boxes, and a sample grid at 0 pt seams (references/qualitative.md)
RED    each defect the audit exists to catch is caught: collided labels, a word in the wrong face, a label anchored
       outside its axes and so never drawn, a page wider than the column; a zoom box under its own inset, a zoom
       that magnifies nothing
AMBER  each defect the audit warns about is named: maths set at the word size, a label hanging past its axes; and
       a figure whose tick pool holds labels from an earlier autoscale raises no false overlap; for grids, panels
       under the floor, abutting edges that merge, a header wider than its column, a block gap under 2.2 seams, a
       seam past the measured range, an inset of a small image, a low magnification, a row label longer than its
       row, unequal panels in a hand-built grid

    python examples/test_examples.py            # writes examples/out/*.pdf and *.png, exits 1 on any failure
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from academic_figure import C, audit, budget, figure, grid, mixed_xlabel, save  # noqa: E402

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


def green_panels():
    """Eight small panels whose y limits are set after the data: the tick pool keeps labels from the autoscale,
    which must not be reported as overlaps (they were, 2026-09-22)."""
    fig, axes = figure("cvpr", "full", height_in=2.6, nrows=2, ncols=4)
    fig.subplots_adjust(wspace=0.3, hspace=0.45, left=0.05, right=0.995, top=0.97, bottom=0.11)
    for i, ax in enumerate(axes.flat):
        ax.plot([1, 4, 16, 64], [20 + i, 30 + i, 31 + i, 31 + i], "-o", color=C.ACCENT, ms=2.6)
        ax.set_xscale("log")
        ax.set_ylim(19 + i, 33 + i)
    mixed_xlabel(axes[1, 0], [("evaluations ", "word"), ("$N$", "math"), (" (log scale)", "word")])
    save(fig, OUT / "panels.pdf")


def amber(name, build, needle):
    fig = build()
    issues = audit(fig)
    import matplotlib.pyplot as plt
    plt.close(fig)
    if any(sev == "WARN" and needle in msg for sev, msg in issues):
        print(f"AMBER {name}: warned, as it must")
        return
    failures.append(f"AMBER {name}: no WARN naming '{needle}' in {issues}")


def amber_small_math():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([0.01, 0.1], [30, 28], "-o", color=C.ACCENT)
    ax.set_xlabel("noise level $\\sigma_y$")                       # the symbol prints at the word size
    return fig


def amber_reach():
    fig, ax = figure("cvpr", "col", height_in=1.9)
    ax.plot([1, 2], [1, 2], "o", color=C.ACCENT)
    ax.set_ylim(0, 2.05)
    ax.annotate("Ours", (2, 2), xytext=(0, 6), textcoords="offset points", ha="center", va="bottom")   # hangs above the frame
    return fig


# --- result grids: the layouts of references/qualitative.md, and the defects its audit exists to catch -------------
def _field(seed, size=256, noise=0.0, dark=False):
    """A synthetic textured image: a colour field whose phase depends on the seed, so neighbouring panels differ at
    their edges; `dark` gives a near-black background with a bright disc, the case where an abutting edge vanishes."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size] * (256.0 / size)
    ph = rng.uniform(0, 6.28, 3)
    img = np.stack([128 + 90 * np.sin(xx / 23.0 + ph[0]), 128 + 90 * np.cos(yy / 31.0 + ph[1]),
                    128 + 60 * np.sin((xx + yy) / 41.0 + ph[2])], -1)
    if dark:
        disc = ((xx - 128) ** 2 + (yy - 128) ** 2) < 70 ** 2
        img = np.where(disc[..., None], img, 6.0)
    return np.clip(img + rng.normal(0, noise, img.shape), 0, 255)


def _png(arr, name):
    from PIL import Image
    p = OUT / name
    Image.fromarray(arr.astype("uint8")).save(p)
    return p


def _rows(n_rows, n_cols, tag, size=256, dark=False):
    """n_rows x n_cols panel paths: a masked measurement, noisy baselines, ours and the reference, per row."""
    rows = []
    for r in range(n_rows):
        row = []
        for c in range(n_cols):
            noise = 0.0 if c >= n_cols - 2 else (25.0 if c else 0.0)
            img = _field(100 * r, noise=noise, size=size, dark=dark)
            if c == 0 and not dark:
                s = img.shape[0]
                img[3 * s // 8: 5 * s // 8, 3 * s // 8: 5 * s // 8] = 128.0
            row.append(_png(img, f"{tag}_{r}_{c}.png"))
        rows.append(row)
    return rows


def green_grid_blocks():
    """A teaser-style grid: two blocks of four columns with block headers, rotated row labels, one row of numbers,
    and a 70 px box on 512 px images away from the inset's corner, so the inset keeps 0.40 and magnifies 2.9x."""
    rows = [a + b for a, b in zip(_rows(2, 4, "blocks_a", size=512), _rows(2, 4, "blocks_b", size=512))]
    fig, _ = grid(rows, ["Measurement", "Method A", "Ours", "Reference"] * 2, span="full", blocks=[4, 4],
                  block_headers=["(a) Pixel prior", "(b) Latent prior"], row_labels=["Deblurring", "Inpainting"],
                  numbers=["", "24.1", "27.9", "", "", "25.0", "28.3", ""], zoom={0: (300, 80, 370, 150)})
    save(fig, OUT / "grid_blocks.pdf")


def green_grid_croprow():
    """A crop row under each image row, two boxes per panel paired with their crops by colour (DAPS Fig. 1c)."""
    rows = _rows(2, 4, "crop", size=512)
    fig, _ = grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col", zoom_style="row",
                  zoom={0: [(60, 60, 140, 140), (340, 300, 420, 380)], 1: [(40, 300, 120, 380), (360, 80, 440, 160)]})
    save(fig, OUT / "grid_croprow.pdf")


def green_grid_samples():
    """Generated samples abut at 0 pt (8 of 9 flagship sample grids) and carry no headers."""
    rows = [[_png(_field(10 * r + c), f"samples_{r}_{c}.png") for c in range(6)] for r in range(3)]
    fig, _ = grid(rows, [""] * 6, span="col", seam=C.GRID_SEAM_SAMPLES, measurement_col=None)
    save(fig, OUT / "grid_samples.pdf")


def red_grid_covered():
    """The defect of SOLO fig9 and of this file's own 0.1.2 grid: the inset forced over its own zoom box."""
    rows = _rows(1, 4, "covered")
    fig, _ = grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col",
                  zoom={0: (170, 170, 210, 210)}, inset_corner="br")
    save(fig, OUT / "red_grid_covered.pdf")


def red_grid_nomag():
    """A crop row that shows nearly the whole image: 1.1x, under every flagship zoom surveyed."""
    rows = _rows(1, 4, "nomag")
    fig, _ = grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col", zoom_style="row",
                  zoom={0: (10, 10, 240, 240)})
    save(fig, OUT / "red_grid_nomag.pdf")


def amber_grid_floor():
    rows = _rows(1, 9, "floor")                                   # nine columns at column width: 24 pt panels
    return grid(rows, [""] * 9, span="col")[0]


def amber_grid_merge():
    rows = _rows(2, 4, "merge", dark=True)                        # dark backgrounds abutting at 0 pt
    return grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col", seam=0.0)[0]


def amber_grid_header():
    rows = _rows(1, 9, "header")
    return grid(rows, ["Measurement, noisy x4"] + [f"Method {i}" for i in range(7)] + ["Reference"], span="full")[0]


def amber_grid_blockgap():
    rows = _rows(1, 4, "blockgap")
    return grid(rows, ["Measurement", "Ours", "Measurement", "Ours"], span="col", blocks=[2, 2], block_gap=3.0)[0]


def amber_grid_wide_seam():
    rows = _rows(1, 4, "wideseam")
    return grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col", seam=6.0)[0]


def amber_grid_density():
    """A 3x zoom of a 64 px image: 9 source pixels spread over an 18 pt inset."""
    rows = _rows(1, 5, "density", size=64)
    return grid(rows, ["Measurement", "Method A", "Method B", "Ours", "Reference"], span="col",
                zoom={0: (40, 6, 49, 15)})[0]


def amber_grid_magnification():
    rows = _rows(1, 4, "lowmag")
    return grid(rows, ["Measurement", "Method A", "Ours", "Reference"], span="col", zoom={0: (130, 20, 196, 86)})[0]


def amber_grid_row_label():
    rows = _rows(2, 8, "rowlabel")
    return grid(rows, [""] * 8, span="col", row_labels=["Gaussian deblurring, noisy", "Box inpainting"])[0]


def amber_grid_uneven():
    """A grid built by hand, one panel smaller than its row: the geometry checks need no template, only
    fig._af_kind = "grid"."""
    fig, _ = figure("cvpr", "col", height_in=1.0)
    fig.axes[0].remove()
    fig._af_kind = "grid"
    W, H = 3.28125 * 72, 72.0
    for i, s in enumerate((60.0, 60.0, 50.0)):                   # squares in points, tops level at 70 pt
        ax = fig.add_axes([(2 + 62.5 * i) / W, (70 - s) / H, s / W, s / H])
        ax.imshow(_field(i).astype("uint8"), interpolation="none")
        ax.set_axis_off()
    return fig


if __name__ == "__main__":
    for name, fn in (("budget", green_budget), ("grid", green_grid),
                     ("grid, 1 pt seams", lambda: green_grid(C.GRID_SEAM_FALLBACK, "grid_seam")),
                     ("panels", green_panels), ("grid, blocks and row labels", green_grid_blocks),
                     ("grid, crop row with two boxes", green_grid_croprow), ("grid, samples at 0 pt", green_grid_samples)):
        try:
            fn()
            print(f"GREEN {name}: passed")
        except Exception as e:                                     # noqa: BLE001  (a test harness reports, it does not crash)
            failures.append(f"GREEN {name}: {type(e).__name__}: {e}")
    red("overlap", red_overlap, "two labels on top of each other")
    red("face", red_face, "a word in DejaVu Sans")
    red("undrawn", red_undrawn, "a label anchored outside its axes")
    red("grid, box under its inset", red_grid_covered, "a zoom box covered by its own inset")
    red("grid, zoom that magnifies nothing", red_grid_nomag, "a 1.1x zoom")
    amber("small maths", amber_small_math, "maths set at the word size")
    amber("reach", amber_reach, "reaching past their axes")
    amber("grid, panel floor", amber_grid_floor, "under the 28.5 pt")
    amber("grid, abutting dark edges", amber_grid_merge, "abutting panels merge")
    amber("grid, header too wide", amber_grid_header, "headers wider than their columns")
    amber("grid, block gap too small", amber_grid_blockgap, "do not read as blocks")
    amber("grid, seam too wide", amber_grid_wide_seam, "past the 4.9 pt")
    amber("grid, inset of a small image", amber_grid_density, "source pixels per printed point")
    amber("grid, low magnification", amber_grid_magnification, "lower quartile")
    amber("grid, row label too long", amber_grid_row_label, "row labels longer than their rows")
    amber("grid, unequal panels", amber_grid_uneven, "unequal panels within a row")
    print("\n" + ("ALL PASSED" if not failures else "FAILURES:\n  " + "\n  ".join(failures)))
    sys.exit(1 if failures else 0)
