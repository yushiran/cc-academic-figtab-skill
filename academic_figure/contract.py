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
# Ticks take the face of their axis label: a word label ("prior evaluations") gets Arimo ticks, a symbol label ($t$,
# $\sigma_y$) gets Computer Modern ticks. This reconciles "a number on an axis is mathematics" with every flagship
# ML plot, which sets count axes in the sans.

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
# Measured on DAPS Fig. 1 (CVPR 2025 oral): reconstructions abut edge to edge in both directions, and only the
# measurement column is set off, by 4 px of a 111 px panel.
GRID_SEAM = 0.0                      # between reconstruction panels, and between rows
GRID_MEASUREMENT_GAP = 1.8           # pt, between the measurement column and the rest
GRID_HEADER_GAP = 2.0                # pt, from the header baseline to the panel top
GRID_NUMBER_GAP = 2.0                # pt, from the panel bottom to the numbers row
INSET_FRACTION = 0.42                # a zoom inset spans this share of its panel's width, in the bottom-right corner
INSET_BORDER = WORK_W                # white 0.5 pt border round the inset, so it separates from the image
INSET_BOX = CLAIM_W                  # the box marking the zoomed region on the full image
INSET_BOX_COLOUR = ACCENT            # the region the claim is about; the one accent mark a grid spends
PIXELS_PER_PT = 4.2                  # raster panels are resampled to this density before placement (600 dpi)

# --- Whitespace ------------------------------------------------------------------------------------
GUTTER_MAX = 10.0                    # pt of white left and right of the ink, measured on the render
INK_METHOD = (20.0, 40.0)            # % coverage of a method figure (JiT 19.9, iMF 23.6, ARC 36.9)
INK_PLOT = (4.0, 15.0)               # % of a data plot: DAPS Fig. 6 measures 6.0 and 6.1; a Pareto plot is sparse
