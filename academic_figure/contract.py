"""The figure contract: every number the figures of a paper share, in one place.

Nothing here is taste invented at a desk. Each value was measured from accepted flagship figures (He Kaiming's MoCo,
MAE, iMF, JiT, BNF, Drifting; DAPS, FlowDPS, CLAMP, DE-CM) or read off the venue's style file, and the comment beside
it says which. A figure script never types one of these numbers; it imports them, so that the plots and the Figma
diagrams of one paper land at the same widths, the same type sizes and the same colours.

Change a value here and every figure follows. Change it in a script and that figure has left the paper.
"""
from __future__ import annotations

# --- Geometry --------------------------------------------------------------------------------------
# (full text width, column width) in inches. A LaTeX point is 1/72.27 in and a PostScript point 1/72 in, so convert
# through inches. Measure a new venue once in the document body: \typeout{\the\textwidth, \the\columnwidth}.
VENUES = {
    "cvpr": (6.875, 3.28125),        # cvpr.sty: \textwidth 6.875in, \columnsep 0.3125in
    "iccv": (6.875, 3.28125),
    "wacv": (6.875, 3.28125),
    "eccv": (4.803, 4.803),          # LNCS single column, 122 mm
    "neurips": (5.5, 5.5),           # single column
    "iclr": (5.5, 5.5),
    "icml": (6.75, 3.25),
    "aaai": (7.0, 3.3125),
    "ieee": (7.16, 3.5),
}
PT_PER_IN = 72.0                     # the unit a PDF MediaBox and matplotlib both use
WIDTH_TOLERANCE_PT = 1.5             # a saved page may fall this far under the target; it may never exceed it

# --- Type ------------------------------------------------------------------------------------------
# Words in an Arial-class grotesque, symbols in Computer Modern, the maths font of the paper's own body. Measured on
# MoCo, Mask R-CNN, MAE, MeanFlow, iMF, JiT, BNF and Drifting: labels 4.9 to 9.6 pt, median 6.5.
WORD_FACE = "Arimo"                  # Arial's metrics, bundled in fonts/ so matplotlib can never fall back silently
WORD_PT = 6.5                        # EVERY word: labels, ticks, legends, column headers. One size, no hierarchy
MATH_PT = 8.0                        # CM x-height 0.43 em vs Arimo 0.52 em: 8 pt CM matches 6.5 pt Arimo optically
MATH_FONTSET = "cm"
FLOOR_PT = 6.0                       # nothing smaller, ever; three of five 2026 flagships ship 4.5 to 5.6 pt somewhere
# A tick takes the face of what it is. A plain number (1, 4, 16, 0.5, 33.96) is Arimo, like every word of the plot:
# DAPS Fig. 6 sets ticks and labels in one sans, and the paper's own PSNR values are Arimo. A mathematical object (a
# fraction such as 1/2 written as \tfrac12, a symbol such as pi or sigma) is Computer Modern, because the body sets
# it as maths and the figure must show the same object. One quantity keeps one tick form across the whole paper:
# t is fractions in CM everywhere or decimals in Arimo everywhere, never 1/2 in one figure and 0.5 in the next.

# --- Palette ---------------------------------------------------------------------------------------
# Thirteen values and no fourteenth (style-contract.md of academic-figure-figma). A colour is a term: one concept,
# one hue, across every figure, plot and table of the paper.
PAPER = "#FFFFFF"
INK = "#000000"                      # claim ink: labels, the claim path, axes and ticks
CONNECTOR = "#6C6D70"                # structural lines, route labels, baseline text (5.2:1, passes text)
FROZEN_TYPE = "#929497"              # type inside frozen machinery
BASELINE = "#919191"                 # the given or baseline lane: markers and lines of every method that is not ours
HAIRLINE = "#B4B5B8"                 # 0.3 pt raster-panel frames, reference lines
FROZEN_FILL = "#E6E7E8"
FROZEN_INNER = "#D1D1D3"
NO_GRAD = "#EAEAEB"
CLAIM_TINT = "#D6E6F2"               # the module the paper adds; at most two blocks per figure
CLAIM_LINE = "#2E7EB8"               # the objective that produces it; never a fill
ACCENT = "#E2822F"                   # THE QUANTITY THE PAPER ADDS. In a plot, ours. Fill and 1.8 pt line only
ACCENT_STROKE = "#CC752A"            # the same hue at 3.4:1, for a stroke under 1.2 pt or a marker under 3 pt
ACCENT_TEXT = "#A65F22"              # the same hue at 4.9:1, the only value of it allowed to carry a word
OPTIONAL = ("#E0EED4", "#FCE9F2")    # an output or loss block; an arm the method deletes
PALETTE = (PAPER, INK, CONNECTOR, FROZEN_TYPE, BASELINE, HAIRLINE, FROZEN_FILL, FROZEN_INNER, NO_GRAD, CLAIM_TINT,
           CLAIM_LINE, ACCENT, ACCENT_STROKE, ACCENT_TEXT) + OPTIONAL

# Several series that each need their own identity (an ablation with five variants, one line per baseline). Paul
# Tol's colour-blind-safe schemes, copied in SciencePlots' order from its styles/color/*.mplstyle (MIT). Ours stays
# the accent and is never in the cycle. "vibrant" is deliberately not shipped: its first colour, #EE7733, is an
# orange a reader cannot tell from the accent.
SERIES_MUTED = ("#CC6677", "#332288", "#DDCC77", "#117733", "#88CCEE", "#882255", "#44AA99", "#999933", "#AA4499",
                "#DDDDDD")
SERIES_BRIGHT = ("#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB")
SERIES_HIGH_CONTRAST = ("#004488", "#DDAA33", "#BB5566")   # three series that must survive a greyscale print
SERIES_DASHES = ("-", (0, (3, 1.5)), (0, (1, 1)), (0, (4, 1, 1, 1)), (0, (6, 2)), (0, (2, 2)))
SERIES_MARKERS = ("o", "s", "^", "D", "v", "P", "X")

# --- Strokes ---------------------------------------------------------------------------------------
# Structure: 0.3 hairline, 0.5 working, 0.9 claim, and nothing between or above (measured 0.48 to 0.72 pt working
# weights; ARC and BNF use one weight for a whole figure). Data lines in a plot are data, not structure, and take
# their own three values.
HAIR_W, WORK_W, CLAIM_W = 0.3, 0.5, 0.9
DATA_W, OURS_W = 1.1, 1.8            # a baseline series; our series
TICK_LEN = 2.5                       # major ticks out, left and bottom only; no minor ticks at column width
DASH_REFERENCE = (0, (3, 2))         # a reference level (a feedforward baseline, a teacher, a floor)
DASH_GUIDE = (0, (1, 1.5))           # a dotted drop from a point to a dimension line

# --- Markers ---------------------------------------------------------------------------------------
MARKER = 3.2                         # every data marker, filled
MARKER_OPERATING = 5.2               # the one point the tables report, filled, 0.6 pt white edge
MARKER_EDGE_OPERATING = 0.6

# --- Result grids (qualitative figures and teasers) ------------------------------------------------
# Measured 2026-09-23 from the image placements of 87 qualitative figures in 33 papers (44 PDFs read, every figure
# classified by eye): 54 comparisons, 24 single-method result grids, 9 generation sample grids. The gap lists and the
# reasons are in references/qualitative.md. A grid exported as one raster (DPS, Flower, FlowDPS, DAPS Fig. 1a-b) has
# no placements to measure and is not in these numbers.
GRID_SEAM = 2.5                      # pt of white between reconstructions, in both directions: median 2.48 over 54
                                     # comparisons (IQR 1.36-2.99, 3.7 % of the panel side); only 6 of 54 abut. The
                                     # vertical seam equals the horizontal one: median ratio 0.95 over 30 comparisons
GRID_SEAM_SAMPLES = 0.0              # generation sample grids abut: 8 of 9 (DiT, JiT, MAR, MeanFlow, LDM)
GRID_SEAM_FALLBACK = 1.0             # the 0.1.x seam for abutting panels that shared a tone; kept for its callers
GRID_SEAM_MAX = 4.9                  # pt: the seams of 76 of 78 reconstruction grids lie in 0 to 4.9 pt
GRID_ABUT = 0.3                      # pt: a seam at or under this abuts
GRID_MERGE_LEVELS = 8.0              # an abutting edge whose luminance steps under this (of 255) along most of its
                                     # length vanishes: the teaser's two MRI knees stepped 2.1 to 7.0 and read as one
GRID_MEASUREMENT_GAP = 2.0           # pt, only where the reconstructions abut: LDM F8 2.0, ReSample F3 2.4, DAPS F1a
                                     # 1.4. With a seam the measurement takes that seam, as 30 of 32 grids do
GRID_BLOCK_GAP = 9.3                 # pt between column blocks: median of 21 block gaps (IQR 6.1-14.3)
GRID_BLOCK_RATIO = 2.2               # a block gap reads as a boundary from 2.2 seams (ReSample F5 2.2, D-Flow F5 2.3)
GRID_PANEL_FLOOR = 28.5              # pt, the smallest panel of the 90 flagship qualitative figures (DDNM F4)
GRID_HEADER_GAP = 2.0                # pt, from the header baseline to the panel top
GRID_HEADER_PT = (6.25, 8.9)         # measured header sizes, interquartile range over 41 grids (median 7.8); the one
                                     # word size, 6.5, lies inside it, so headers take WORD_PT like every other word
GRID_NUMBER_GAP = 2.0                # pt, from the panel bottom to the numbers row
GRID_ROW_LABEL_GAP = 2.0             # pt of white between a rotated row label and its row
INSET_FRACTION = 0.40                # an overlaid inset spans this share of its panel: median of 16 vector-placed
                                     # magnifying insets in 11 papers (range 0.24-0.60); raster insets not measured
INSET_FRACTION_MIN = 0.30            # their lower quartile; grid() shrinks insets no further to uncover their boxes
INSET_CORNERS = ("br", "bl", "tr", "tl")   # bottom-right first: 9 of those 16 sit there (tr 3, bl 3, tl 1)
INSET_BORDER = WORK_W                # white 0.5 pt border round a single inset, so it separates from the image
INSET_BOX = CLAIM_W                  # the box marking the zoomed region; vector-drawn boxes measure 0.27 to 0.97 pt
INSET_BOX_COLOUR = ACCENT            # the region the claim is about; the one accent mark a grid spends
ZOOM_COLOURS = (ACCENT, SERIES_BRIGHT[0])  # a second box pairs with its crop by colour, as StableSR F1's red and
                                     # blue do; Tol's bright blue is a per-figure series colour, where CLAIM_LINE is
                                     # the objective of the diagrams and may not mean a second region
ZOOM_MAGNIFICATION = 3.0             # median of 23 zoomed comparisons (IQR 2.0-3.5, range 1.3-4.0)
ZOOM_MAGNIFICATION_WARN = 2.0        # the lower quartile: under it an inset mostly repeats its panel
ZOOM_MAGNIFICATION_FAIL = 1.3        # the smallest surveyed (DiffBIR F1): under it the inset magnifies nothing
ZOOM_SOURCE_PX_PER_PT = 1.5          # DERIVED, not measured: under this an inset prints each source pixel as a block
                                     # of 0.7 pt or more, so it magnifies interpolation. Measured: the zero-shot solver
                                     # papers, on 64-256 px images, zoom in 6 of 31 comparisons
PIXELS_PER_PT = 4.2                  # raster panels are resampled to this density before placement (600 dpi)

# --- Whitespace ------------------------------------------------------------------------------------
GUTTER_MAX = 10.0                    # pt of white left and right of the ink, measured on the render
INK_METHOD = (20.0, 40.0)            # % coverage of a method figure (JiT 19.9, iMF 23.6, ARC 36.9)
INK_PLOT = (4.0, 15.0)               # % of a data plot: DAPS Fig. 6 measures 6.0 and 6.1; a Pareto plot is sparse
