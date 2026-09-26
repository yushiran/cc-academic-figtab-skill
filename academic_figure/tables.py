"""Results tables: built from the result files, verified against them, audited in the LaTeX source.

    from academic_figure.tables import Column, Row, header, build, verify, caption_report, load_canon, check_names
    cols = [Column("psnr", "PSNR", "+", 2), Column("ssim", "SSIM", "+", 3), Column("lpips", "LPIPS", "-", 3)]
    rows = [Row("pnpflow", "PnP-Flow", "Training-free"), Row("flower", "Flower", "Training-free"),
            Row("ours", "Ours", ours=True)]
    value = lambda row, col: results[row][col]          # read from the result files, never typed
    tex = header(cols, ["Type", "Method"]) + "\\n" + build(cols, rows, value) + "\\n\\\\bottomrule"
    verify("sec/experiments.tex", "tab:main", cols, rows, value)   # [] when every number and mark matches the data

Marks are computed on the printed values, so two cells that print the same take the same mark, and the second is the
next distinct value (dense ranking). `references/tables.md` holds the contract and the evidence behind every threshold
below; `scripts/audit_tables.py` runs the source checks of `audit_tex()` over a paper directory with no spec at all.
Pure Python, no matplotlib; `load_canon()` needs PyYAML to read a YAML file.
"""
from __future__ import annotations

import bisect
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from itertools import groupby
from pathlib import Path

CAPTION_PASS = 50        # words; the Kaiming headline median; 84 % of 240 flagship main-text captions are shorter
CAPTION_FAIL = 80        # longer than 98 % of them (main-text median 25, 90th percentile 58); SOLO Tabs. 1-7: 108
SECOND_MIN = 3           # a second mark needs three ranked cells in its scope: of two, the second is only the other
MARKED_MAX = 0.4         # best and second in blocks of five mark 40 %; SOLO Tabs. 4, 10, 11 (2-4 rows) mark 53-68 %
NUMERIC_COLUMN = 0.8     # a column is numeric, and held to one precision, when this share of its filled cells is
DASH = "[1pt/1.5pt]"     # the arydshln pattern of the dashed rule before our rows
OURS_COLOUR = "oursrow"
MISSING = "--"
ARROW = {"+": r"~$\uparrow$", "-": r"~$\downarrow$"}
SCOPE_WORDS = re.compile(r"\b(per|each|within|across|among)\b", re.I)   # a caption that states a scope uses one


@dataclass(frozen=True)
class Column:
    key: str                         # what value_fn is asked for
    header: str                      # the canonical name; the arrow is added from `direction`
    direction: str | None = None     # "+" higher is better, "-" lower is better, None: not ranked
    decimals: int | None = 2         # None: printed as given (an integer count, a text column)
    group: str | None = None         # the column group above it (a prior, a dataset), ruled by \cmidrule


@dataclass(frozen=True)
class Row:
    key: str
    name: str                        # the canonical name, "Ours" for ours
    cls: str | None = None           # the leading merged cell: the method class, or the task of a task block
    ours: bool = False               # tinted, and set below a dashed rule


# ---------------------------------------------------------------------------------------------- printing, ranking
def fmt(value, decimals=2) -> str:
    """The printed form: half-up at `decimals` from the shortest decimal form, so 0.0785 prints 0.079."""
    if value is None:
        return MISSING
    if isinstance(value, str) or decimals is None:
        return str(value)
    q = Decimal(repr(float(value))).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    return f"{abs(q) if q == 0 else q:f}"


def _isnum(s) -> bool:
    return isinstance(s, str) and re.fullmatch(r"-?\d+(\.\d+)?", s) is not None


def rank(cells: dict, direction: str, second: bool = True) -> dict:
    """{id: "b" | "u"} for {id: printed value}: every cell equal to the best printed value is bold, every cell equal
    to the next distinct one underlined, the latter only with SECOND_MIN cells or more. One cell ranks nothing."""
    vals = {k: Decimal(v) for k, v in cells.items() if _isnum(str(v))}
    if len(vals) < 2 or direction not in ("+", "-"):
        return {}
    order = sorted(set(vals.values()), reverse=direction == "+")
    out = {k: "b" for k, v in vals.items() if v == order[0]}
    if second and len(vals) >= SECOND_MIN and len(order) > 1:
        out.update({k: "u" for k, v in vals.items() if v == order[1]})
    return out


def _expected(columns, rows, value_fn, scope="table", second=True):
    if scope not in ("table", "group"):
        raise ValueError(f"scope is 'table' or 'group', not {scope!r}")
    printed = {(r.key, c.key): fmt(value_fn(r.key, c.key), c.decimals) for r in rows for c in columns}
    scopes = [list(rows)] if scope == "table" else [list(g) for _, g in groupby(rows, key=lambda r: r.cls)]
    marks = {}
    for c in columns:
        for grp in scopes:
            for k, m in rank({r.key: printed[(r.key, c.key)] for r in grp}, c.direction, second).items():
                marks[(k, c.key)] = m
    return printed, marks


# -------------------------------------------------------------------------------------------------- building
def header(columns, lead=("Method",)) -> str:
    """\\toprule, the group row with its \\cmidrule(lr)s if any column has a group, the names with their arrows, and
    \\midrule. `lead` names the label columns: ("Method",), or ("Type", "Method") when the rows have a class."""
    n, out = len(lead), [r"\toprule"]
    if any(c.group for c in columns):
        cells, rules, j = [""] * n, [], n + 1
        for g, run in groupby(columns, key=lambda c: c.group):
            k = len(list(run))
            cells.append(rf"\multicolumn{{{k}}}{{c}}{{{g}}}" if g and k > 1 else (g or ""))
            if g:
                rules.append(rf"\cmidrule(lr){{{j}-{j + k - 1}}}")
            j += k
        out += [" & ".join(cells) + r" \\", "".join(rules)]
    out += [" & ".join(list(lead) + [c.header + ARROW.get(c.direction, "") for c in columns]) + r" \\", r"\midrule"]
    return "\n".join(out)


def build(columns, rows, value_fn, scope="table", second=True, ours_colour=OURS_COLOUR, delta=None, delta_ours=None,
          relative=False) -> str:
    """The body rows of a table, one LaTeX line per row. value_fn(row_key, column_key) returns a number, a string or
    None (printed "--"). The best printed value of each ranked column is bold and the second underlined, per column
    over the whole table (scope="table") or within each run of rows sharing a class (scope="group", task blocks).
    With a class, rows sharing it are one \\multirow block; blocks are split by \\midrule when they are the marks'
    scope and by a dashed rule otherwise. Our rows are tinted cell by cell, so the tint stops at the merged class
    cell, and a dashed rule sets them off from the rows above them in their block. `delta` names a last row, under
    a \\midrule, of our row's difference from the best other row per ranked column (improvement(); `delta_ours` picks
    our row when there are two), never marked; the audit recomputes it from the printed cells. It needs a label
    that starts with Δ, such as r"$\\Delta$ over the best baseline", and scope="table"."""
    printed, marks = _expected(columns, rows, value_fn, scope, second)
    lead = 2 if any(r.cls for r in rows) else 1
    n = lead + len(columns)
    blocks = [list(g) for _, g in groupby(rows, key=lambda r: r.cls)] if lead == 2 else [list(rows)]
    out = []
    for b, block in enumerate(blocks):
        if b:
            out.append(r"\midrule" if scope == "group" else rf"\cdashline{{1-{n}}}{DASH}")
        for i, r in enumerate(block):
            if r.ours and i and not block[i - 1].ours:
                out.append(rf"\cdashline{{{lead}-{n}}}{DASH}")
            cells = [r.name] + [_marked(printed[(r.key, c.key)], marks.get((r.key, c.key))) for c in columns]
            if r.ours:
                cells = [rf"\cellcolor{{{ours_colour}}}{x}" for x in cells]
            if lead == 2:
                cls = block[0].cls or ""
                cls = rf"\shortstack[l]{{{cls}}}" if "\\\\" in cls else cls
                span = cls and len(block) > 1
                cells.insert(0, "" if i else (rf"\multirow{{{len(block)}}}{{*}}{{{cls}}}" if span else cls))
            out.append(" & ".join(cells) + r" \\")
    if delta:
        if scope != "table":
            raise ValueError("a delta row belongs to a table ranked as a whole (scope='table'), not to task blocks")
        if not plain(delta).startswith("Δ"):
            raise ValueError(f"the delta row's label must start with Δ ($\\Delta$), so the audit can find it: {delta!r}")
        out += [r"\midrule", _delta_row(columns, rows, value_fn, delta, delta_ours, relative, lead)]
    return "\n".join(out)


def _marked(text, mark):
    return rf"\textbf{{{text}}}" if mark == "b" else rf"\underline{{{text}}}" if mark == "u" else text


def _signed_tex(d: Decimal) -> str:
    """A difference as a table prints it: $+$0.16, $-$0.001, and 0.00 with no sign."""
    return f"{d:f}" if d == 0 else (r"$+$" if d > 0 else r"$-$") + f"{abs(d):f}"


def improvement(columns, rows, value_fn, ours=None, against=None, relative=False) -> dict:
    """{column key: the signed difference of our row from the best of the others, printed} for every ranked column,
    None for the rest. Computed from the printed values, so a reader who subtracts two cells of the table gets the
    same number; the text that cites "+0.42 dB over the strongest baseline" cites this. `ours` is our row's key (the
    first row marked ours by default), `against` the keys to compare with (every row not ours by default); with
    `relative` the difference is a percentage of the baseline, at one decimal. The idea follows RNAGenScape's
    improvement annotation in figures4papers; no code is taken from it."""
    mine = ours or next(r.key for r in rows if r.ours)
    others = [r for r in rows if (r.key in against if against is not None else not r.ours)]
    out = {}
    for c in columns:
        if c.direction not in ("+", "-") or c.decimals is None:
            out[c.key] = None
            continue
        m = fmt(value_fn(mine, c.key), c.decimals)
        theirs = [Decimal(p) for p in (fmt(value_fn(r.key, c.key), c.decimals) for r in others) if _isnum(p)]
        if not _isnum(m) or not theirs:
            out[c.key] = None
            continue
        best = max(theirs) if c.direction == "+" else min(theirs)
        d = Decimal(m) - best
        if relative:
            out[c.key] = None if best == 0 else _signed_tex(
                (d / abs(best) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)) + r"\%"
        else:
            out[c.key] = _signed_tex(d)
    return out


def _delta_row(columns, rows, value_fn, delta, delta_ours, relative, lead):
    cells = improvement(columns, rows, value_fn, ours=delta_ours, relative=relative)
    head = rf"\multicolumn{{{lead}}}{{l}}{{{delta}}}" if lead > 1 else delta
    return " & ".join([head] + [cells[c.key] or "" for c in columns]) + r" \\"


def component_columns(components, codes, values=None, mark=r"\checkmark"):
    """The ✓ columns of a component ablation: `components` [(key, header)] in column order, `codes` {row key: "101"},
    one 0 or 1 per component. Returns (columns, value_fn): unranked text columns printing `mark` or nothing, and a
    value_fn that answers for them and hands every other column to `values`, so they build in one table with the
    metric columns. Refused: a code of the wrong length or with other characters, and two rows with one code, which
    the ✓ columns could not tell apart. The idea follows ImmunoStruct's decoded ablation codes in figures4papers; no
    code is taken from it."""
    n = len(components)
    for key, code in codes.items():
        if len(code) != n or set(code) - {"0", "1"}:
            raise ValueError(f"row {key!r}: code {code!r} needs one 0 or 1 for each of the {n} components")
    twice = sorted(c for c, k in Counter(codes.values()).items() if k > 1)
    if twice:
        raise ValueError(f"codes {twice} name more than one row: rows the ✓ columns cannot tell apart")
    index = {key: i for i, (key, _) in enumerate(components)}
    cols = [Column(key, header, None, None) for key, header in components]

    def value(row, col):
        if col in index:
            return mark if codes[row][index[col]] == "1" else ""
        if values is None:
            raise KeyError(f"{col}: not a component column and no values= given")
        return values(row, col)
    return cols, value


# ------------------------------------------------------------------------------------ reading the LaTeX source
_COND = re.compile(r"\\(newif\s*\\if[a-zA-Z@]*|if[a-zA-Z@]*|else|fi)(?![a-zA-Z@])")


def _uncomment(line: str) -> str:
    i = 0
    while (i := line.find("%", i)) >= 0:
        j = i
        while j > 0 and line[j - 1] == "\\":
            j -= 1
        if (i - j) % 2 == 0:                                         # an unescaped %: the rest of the line is gone
            return line[:i]
        i += 1
    return line


def live_lines(path) -> list[str]:
    """The lines of a .tex file as LaTeX reads them: % comments cut, \\iffalse ... \\fi blocks (\\else branches kept)
    and comment environments blanked, the line count kept so a position still names its line in the file. An \\if
    followed by a brace (\\ifthenelse, etoolbox's \\ifdef) is a macro, not a conditional."""
    stack, out, in_env = [], [], False
    dead = lambda: any(f == "F" for f in stack)
    for line in Path(path).read_text(errors="replace").splitlines():
        line = _uncomment(line)
        if in_env or re.match(r"\s*\\begin\{comment\}", line):
            in_env = not re.search(r"\\end\{comment\}", line)
            out.append("")
            continue
        parts, pos = [], 0
        for m in _COND.finditer(line):
            tok, was = m.group(1), dead()
            if tok.startswith("newif") or (tok.startswith("if") and line[m.end():].lstrip().startswith("{")):
                continue
            if tok == "iffalse":
                stack.append("F")
            elif tok == "iftrue":
                stack.append("T")
            elif tok.startswith("if"):
                stack.append("O")                                   # a condition we cannot evaluate: kept live
            elif tok == "else" and stack:
                stack[-1] = {"F": "T", "T": "F"}.get(stack[-1], stack[-1])
            elif tok == "fi" and stack:
                stack.pop()
            if not was and dead():
                parts.append(line[pos:m.start()])
            elif was and not dead():
                pos = m.end()
        if not dead():
            parts.append(line[pos:])
        out.append("".join(parts))
    return out


def _skip(s, i):
    while i < len(s) and s[i] in " \t\n":
        i += 1
    return i


def _group(s, i, pair="{}"):
    """(content, end) of the balanced group opening at s[i], or (None, i) when none opens there."""
    if i >= len(s) or s[i] != pair[0]:
        return None, i
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        depth += (c == "{") - (c == "}")
        if (pair == "{}" and depth == 0) or (pair != "{}" and depth == 0 and c == pair[1]):
            return s[i + 1:j], j + 1
        j += 1
    return s[i + 1:], len(s)


def _arg(s, i):
    """A mandatory argument: a braced group, a control sequence or one character."""
    i = _skip(s, i)
    if i < len(s) and s[i] == "{":
        return _group(s, i)
    m = re.match(r"\\[a-zA-Z@]+|\\.|.", s[i:], re.S)
    return (m.group(0), i + m.end()) if m else ("", i)


def _opt(s, i, pair="[]"):
    j = _skip(s, i)
    content, k = _group(s, j, pair)
    return (content, k) if content is not None else (None, i)


_SYM = {"times": "×", "pm": "±", "uparrow": "↑", "downarrow": "↓", "Uparrow": "↑", "Downarrow": "↓", "sigma": "σ",
        "ell": "ℓ", "circ": "°", "cdot": "·", "le": "≤", "ge": "≥", "leq": "≤", "geq": "≥", "infty": "∞",
        "approx": "≈", "dagger": "†", "ddagger": "‡", "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ",
        "Delta": "Δ", "eta": "η", "lambda": "λ", "mu": "μ", "psi": "ψ", "theta": "θ", "epsilon": "ε",
        "varepsilon": "ε", "tau": "τ", "phi": "φ", "in": "∈", "to": "→", "rightarrow": "→", "textendash": "–",
        "quad": " ", "qquad": " ", "enspace": " ", "textasciitilde": "~", "ast": "*", "checkmark": "✓"}
_BOLD = re.compile(r"\\(textbf|mathbf|boldsymbol|bm)\s*\{|\\(bf|bfseries)(?![a-zA-Z])")
_UNDER = re.compile(r"\\(underline|uline)\s*\{|\\ul(?![a-zA-Z])")
_UP = re.compile(r"\\[uU]parrow(?![a-zA-Z])|↑")
_DOWN = re.compile(r"\\[dD]ownarrow(?![a-zA-Z])|↓")
_NUM = re.compile(r"([+\-−]?)(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?:\s*±\s*[\d.]+)?\s*(?:%|[KMGB]|×)?")
_MISSING = {"--", "-", "–", "—", "---", "n/a", "N/A", "×", "✗"}


def plain(tex: str) -> str:
    """What a cell or a name prints, near enough to compare two spellings: colours and formatting dropped, the common
    symbols mapped, braces and dollars gone. Both sides of every comparison go through it."""
    s = tex.replace("\\\\", " ")
    s = re.sub(r"\\(cellcolor|rowcolor|color)\s*(\[[^\]]*\])?\s*\{[^{}]*\}", "", s)
    s = re.sub(r"\\(textcolor|colorbox)\s*(\[[^\]]*\])?\s*\{[^{}]*\}", "", s)       # keeps the coloured text
    s = re.sub(r"\\(label|vspace|hspace|phantom|hphantom|vphantom)\*?\s*\{[^{}]*\}", "", s)
    s = re.sub(r"\\(shortstack|makecell|parbox|raisebox)\s*\[[^\]]*\]", r"\\\1", s)
    s = re.sub(r"\\[td]?frac\s*\{?([^{}\s\\])\}?\s*\{?([^{}\s\\])\}?", r"\1/\2", s)
    s = re.sub(r"\^(?:\{2\}|2(?![0-9]))", "²", s)
    s = re.sub(r"\\([a-zA-Z@]+)\*?", lambda m: _SYM.get(m.group(1), ""), s)
    s = re.sub(r"\\[,;:! ]", " ", s)
    s = re.sub(r"\\([%&_#$])", r"\1", s)
    s = re.sub(r"[{}$^_]", "", s).replace("~", " ")
    return re.sub(r"\s+", " ", s).strip()


def _noarrow(text):
    return re.sub(r"\s*\(?[↑↓]\)?", "", text).strip()


def _cell(raw):
    t, span, rows = raw.strip(), 1, 0
    if (m := re.match(r"\\multicolumn\s*", t)):
        n, i = _arg(t, m.end())
        _, i = _arg(t, i)
        content, i = _arg(t, i)
        span, t = (int(n) if n.strip().isdigit() else 1), content + t[i:]
    if (k := t.find("\\multirow")) >= 0:
        _, i = _opt(t, k + 9)
        n, i = _arg(t, i)
        _, i = _opt(t, i)
        _, i = _arg(t, i)
        _, i = _opt(t, i)
        content, i = _arg(t, i)
        rows, t = (abs(int(n)) if re.fullmatch(r"\s*-?\d+\s*", n) else 0), t[:k] + content + t[i:]
    text = plain(t)
    num = _NUM.fullmatch(text)
    numtext = None
    if num:
        numtext = ("-" if num.group(1) in "-−" and num.group(1) else "") + num.group(2).replace(",", "")
        numtext += "." + num.group(3) if num.group(3) else ""
    return dict(raw=raw, text=text, span=span, multirow=rows, bold=bool(_BOLD.search(t)),
                under=bool(_UNDER.search(t)), num=Decimal(numtext) if num else None, numtext=numtext,
                dec=len(num.group(3) or "") if num else None)


_RULE = re.compile(r"\\(toprule|midrule|bottomrule|hline|cline|cmidrule|cdashline|hdashline|addlinespace|"
                   r"specialrule|morecmidrules|rowcolor|noalign|hhline|arrayrulecolor)(?![a-zA-Z@])")


def _lead_rules(text):
    """The rule commands at the start of a row, split off: (rules, the rest)."""
    rules, i = [], 0
    while (m := _RULE.match(text, _skip(text, i))):
        name, i = m.group(1), m.end()
        if name in ("toprule", "midrule", "bottomrule", "hdashline", "addlinespace"):
            _, i = _opt(text, i)
        elif name == "cmidrule":
            _, i = _opt(text, i)
            _, i = _opt(text, i, "()")
            _, i = _arg(text, i)
        elif name == "cdashline":
            _, i = _arg(text, i)
            _, i = _opt(text, i)
        elif name in ("cline", "hhline", "noalign"):
            _, i = _arg(text, i)
        elif name == "specialrule":
            for _ in range(3):
                _, i = _arg(text, i)
        elif name in ("rowcolor", "arrayrulecolor"):
            _, i = _opt(text, i)
            _, i = _arg(text, i)
        rules.append(name)
    return rules, text[i:]


def _scan(body):
    """Rows of a tabular body: [(start offset, [(cell text, offset)])], split at & and \\\\ outside braces and
    nested environments; the text after the last \\\\ is returned as the last row."""
    rows, cells, start, depth, env, i, n = [], [], 0, 0, 0, 0, len(body)
    while i < n:
        c = body[i]
        if c == "\\":
            if body.startswith("\\\\", i) or re.match(r"\\tabularnewline(?![a-zA-Z])", body[i:i + 16]):
                if depth == 0 and env == 0:
                    cells.append((body[start:i], start))
                    rows.append(cells)
                    cells = []
                    i += 2 if body.startswith("\\\\", i) else 15
                    if i < n and body[i] == "*":
                        i += 1
                    _, i = _opt(body, i)
                    start = i
                    continue
                i += 2
                continue
            m = re.match(r"\\(begin|end)(?=\s*\{)", body[i:i + 12])
            if m:
                env += 1 if m.group(1) == "begin" else -1
                i += len(m.group(0))
                continue
            m = re.match(r"\\[a-zA-Z@]+", body[i:])
            i += len(m.group(0)) if m else 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "&" and depth == 0 and env == 0:
            cells.append((body[start:i], start))
            start = i + 1
        i += 1
    cells.append((body[start:], start))
    rows.append(cells)
    return rows


_TABULAR = re.compile(r"\\begin\s*\{(tabular\*?|tabularx|tabulary)\}")


def _env_end(s, i, name):
    depth = 1
    for m in re.finditer(r"\\(begin|end)\s*\{" + re.escape(name) + r"\}", s[i:]):
        depth += 1 if m.group(1) == "begin" else -1
        if depth == 0:
            return i + m.start(), i + m.end()
    return len(s), len(s)


def _tabular(s, m, line_of):
    name = m.group(1)
    i = m.end()
    if name != "tabular":
        _, i = _arg(s, i)                                            # the width of tabular*, tabularx, tabulary
    _, i = _opt(s, i)
    spec, i = _arg(s, i)
    end, _ = _env_end(s, i, name)
    rows, trail = [], []
    for cells in _scan(s[i:end]):
        rules, first = _lead_rules(cells[0][0])
        cells = [(first, cells[0][1] + len(cells[0][0]) - len(first))] + cells[1:]
        if len(cells) == 1 and not cells[0][0].strip():
            trail += rules                                         # rules after the last row: \bottomrule
            continue
        off = i + cells[0][1] + len(cells[0][0]) - len(cells[0][0].lstrip())
        rows.append(dict(line=line_of(off), rules=rules, cells=[_cell(t) for t, _ in cells]))
    bare = re.sub(r"[@!<>]\s*\{(?:[^{}]|\{[^{}]*\})*\}|[pmbw]\s*\{[^{}]*\}", "", spec)
    vertical = "|" in bare or "\\vrule" in spec or "\\vline" in s[i:end]
    return dict(env=name, spec=spec, line=line_of(m.start()), end=line_of(end), rows=rows, trail=trail,
                vertical=vertical)


def parse_tables(path) -> list[dict]:
    """The table floats of one .tex file, live lines only: label(s), caption (raw), position, placement, the line
    span, and every tabular in it with its rows parsed into cells."""
    lines = live_lines(path)
    s = "\n".join(lines)
    nl = [k for k, ch in enumerate(s) if ch == "\n"]
    line_of = lambda k: bisect.bisect_left(nl, k) + 1
    out = []
    for m in re.finditer(r"\\begin\s*\{(table\*?|sidewaystable\*?)\}", s):
        env = m.group(1)
        place, _ = _opt(s, m.end())
        end, end2 = _env_end(s, m.end(), env)
        if any(t["start"] <= m.start() < t["stop"] for t in out):
            continue
        body = s[m.end():end]
        cap = re.search(r"\\caption(?![a-zA-Z@])\*?\s*", body)
        caption, cap_at = None, None
        if cap:
            _, k = _opt(body, cap.end())
            caption, _ = _arg(body, k)
            cap_at = cap.start()
        tabs, reach = [], -1
        for t in _TABULAR.finditer(body):
            if t.start() < reach:                                    # a tabular nested in a cell of another
                continue
            reach = _env_end(body, t.end(), t.group(1))[1]
            tabs.append(_tabular(body, t, lambda k, o=m.end(): line_of(o + k)))
        first_tab = _TABULAR.search(body)
        out.append(dict(path=str(path), env=env, placement=place or "", line=line_of(m.start()), end=line_of(end2),
                        start=m.start(), stop=end2, labels=re.findall(r"\\label\s*\{([^}]*)\}", body),
                        caption=caption, caption_line=line_of(m.end() + cap_at) if cap else None,
                        position=None if not (cap and first_tab) else ("above" if cap_at < first_tab.start() else "below"),
                        tabulars=[t for t in tabs if t["rows"]]))
    return out


# ------------------------------------------------------------------------------------- the structure of a tabular
def structure(tab) -> dict:
    """Header and data rows of a parsed tabular: each column's direction (from its header arrow), label and group;
    each data row's cells by column (a \\multicolumn's extra columns are None), its label with \\multirow cells carried
    down, and its block (rows between \\midrule or \\hline, or under a full-width heading row)."""
    rows = tab["rows"]
    first = next((i for i, r in enumerate(rows) if "midrule" in r["rules"] or ("hline" in r["rules"] and i > 0)), None)
    head, body = (rows[:first], rows[first:]) if first else (rows[:1], rows[1:])
    ncol = max(sum(c["span"] for c in r["cells"]) for r in rows)
    direction, label, group, heads = [None] * ncol, [""] * ncol, [""] * ncol, [""] * ncol
    for h in head:
        j = 0
        for c in h["cells"]:
            arrow = "+" if _UP.search(c["raw"]) else "-" if _DOWN.search(c["raw"]) else None
            for k in range(j, min(j + c["span"], ncol)):
                direction[k] = arrow or direction[k]
                if c["text"]:
                    if c["span"] > 1 and h is not head[-1]:
                        group[k] = _noarrow(c["text"])
                    else:
                        label[k], heads[k] = _noarrow(c["text"]), c["text"]
            j += c["span"]
    data, carry, block = [], {}, -1
    for i, r in enumerate(body):
        filled = [c for c in r["cells"] if c["text"]]
        heading = len(filled) == 1 and filled[0]["span"] > 1
        if i == 0 or heading or "midrule" in r["rules"] or "hline" in r["rules"]:
            block += 1
            if heading:
                carry = {}
        if heading:
            continue
        cols = []
        for c in r["cells"]:
            cols += [c] + [None] * (c["span"] - 1)
        cols += [None] * (ncol - len(cols))
        texts = []
        for j, c in enumerate(cols):
            text = c["text"] if c else ""
            if not text and carry.get(j, ("", 0))[1] > 0:
                text = carry[j][0]
            if c and c["multirow"] > 1:
                carry[j] = [c["text"], c["multirow"]]
            texts.append(text)
        for v in carry.values():
            v[1] -= 1
        stop = next((j for j, c in enumerate(cols) if c and c["num"] is not None), ncol)
        # data.append(dict(line=r["line"], cols=cols, texts=texts, block=block,
        #                  label=" / ".join(t for t in texts[:stop] if t)))
        label = " / ".join(t for t in texts[:stop] if t)
        data.append(dict(line=r["line"], cols=cols, texts=texts, block=block, label=label,
                         delta=label.startswith("Δ"), ours=any(c and "\\cellcolor" in c["raw"] for c in cols)))
    return dict(head=head, data=data, ncol=ncol, direction=direction, label=label, group=group, heads=heads)


def _mark_of(c):
    return ("b" if c["bold"] else "") + ("u" if c["under"] else "")


def _name(st, j):
    return f"{st['group'][j]} / {st['label'][j]}" if st["group"][j] else (st["label"][j] or f"column {j + 1}")


def _names(st, cols):
    """Column names, one entry per distinct header name: "NFE (2 columns), Time (s) (2 columns)"."""
    n = Counter(st["label"][j] or _name(st, j) for j in cols)
    return ", ".join(f"{k} ({v} columns)" if v > 1 else k for k, v in n.items())


def _label_columns(st):
    """The first column and every column holding a \\multirow: labels and settings, not results."""
    return {0} | {j for r in st["data"] for j, c in enumerate(r["cols"]) if c is not None and c["multirow"] > 1}


def _states_scope(caption):
    """Whether the sentence of the caption that names the marks also names their scope."""
    marks = [s for s in re.split(r"(?<=[.;])\s+", plain(caption or "")) if re.search(r"bold|best|underline", s, re.I)]
    return any(SCOPE_WORDS.search(s) for s in marks)


def _recompute(st, scope, second):
    """Expected marks {(row, column): "b" | "u"} under one scope: "table" (per column), "block" (per column within a
    block) or "row" (per row, across the columns that share a header name)."""
    groups = defaultdict(dict)
    for i, r in enumerate(st["data"]):
        for j, c in enumerate(r["cols"]):
            if c is not None and c["num"] is not None and st["direction"][j]:
                key = {"table": (j,), "block": (r["block"], j), "row": (i, st["label"][j], st["direction"][j])}[scope]
                groups[key][(i, j)] = c["numtext"]
    out = {}
    for key, cells in groups.items():
        out.update(rank(cells, st["direction"][next(iter(cells))[1]], second))
    return out


def audit_marks(st, caption=""):
    """[(severity, message)] for the marks of one tabular: recomputed on the printed values under the scope that
    explains them best, with the directions read from the header arrows. A Δ row is not a method and is left out."""
    st = dict(st, data=[r for r in st["data"] if not r.get("delta")])
    data, direction = st["data"], st["direction"]
    cells = [(i, j, c) for i, r in enumerate(data) for j, c in enumerate(r["cols"]) if c is not None]
    marked = [(i, j, c) for i, j, c in cells if c["num"] is not None and _mark_of(c)]
    numeric = sorted({j for _, j, c in cells if c["num"] is not None})
    undirected = [j for j in numeric if not direction[j] and j not in _label_columns(st)]
    out = []
    loose = [j for j in undirected if any(jj == j for _, jj, _ in marked)]
    if loose:
        n = sum(1 for _, j, _ in marked if j in loose)
        out.append(("WARN", f"{n} marks in columns with no arrow, so no direction to check them by: "
                            f"{_names(st, loose)}"))
    elif undirected:
        out.append(("INFO", f"not ranked, no arrow in the header: {_names(st, undirected)}"))
    if not marked:
        return out + [("PASS", "no marks")]
    ranked = [(i, j, c) for i, j, c in cells if c["num"] is not None and direction[j]]
    if not ranked:
        return out
    second = any(c["under"] for _, _, c in cells)
    scopes = ["table"] + (["block"] if len({r["block"] for r in data}) > 1 else [])
    rowkeys = Counter((i, st["label"][j], direction[j]) for i, j, _ in ranked)
    if any(v > 1 for v in rowkeys.values()):
        scopes.append("row")
    result = {}
    for sc in scopes:
        exp = _recompute(st, sc, second)
        result[sc] = [(i, j, exp.get((i, j), ""), _mark_of(c)) for i, j, c in ranked if exp.get((i, j), "") != _mark_of(c)]
    sc = min(scopes, key=lambda s: len(result[s]))
    words = {"table": "per column over the whole table", "block": "per column within each row block",
             "row": "per row, across the columns of one name"}[sc]
    bad = result[sc]
    show = {"b": "bold", "u": "underlined", "bu": "bold and underlined", "": "plain"}
    if bad:
        out.append(("FAIL", f"{len(bad)} of {len(ranked)} ranked cells carry a mark the printed values do not give "
                            f"them (best scope: {words}; ties at the printed precision marked equally)"))
        for i, j, e, f in bad:
            r = data[i]
            out.append(("", f"    {r['label']} · {_name(st, j)} = {r['cols'][j]['text']}: expected {show[e]}, "
                            f"found {show[f]} (line {r['line']})"))
    else:
        out.append(("PASS", f"{len([m for m in marked if direction[m[1]]])} marks match, {words}"))
    if sc != "table" and not _states_scope(caption):
        out.append(("WARN", f"the marks are {words}, and the caption's mark sentence does not say so"))
    share = sum(1 for _, j, c in marked if direction[j]) / len(ranked)
    if share > MARKED_MAX:
        out.append(("WARN", f"marks on {share:.0%} of the ranked cells (at most {MARKED_MAX:.0%}): with scopes of "
                            f"four rows or fewer, drop the second mark (build(second=False))"))
    return out


def audit_delta(st):
    """[(severity, message)] for a Δ row: each cell recomputed from the printed cells as a tinted row (ours) minus the
    best untinted row of its column, by the header arrow, at the Δ cell's own precision; a percentage cell as a share
    of that best row. With two tinted rows, a cell may follow either."""
    deltas = [r for r in st["data"] if r.get("delta")]
    if not deltas:
        return []
    rows = [r for r in st["data"] if not r.get("delta")]
    ours, others = [r for r in rows if r["ours"]], [r for r in rows if not r["ours"]]
    if not ours:
        return [("WARN", "a Δ row but no tinted row of ours to recompute it from")]
    out, bad, checked = [], [], 0
    for d in deltas:
        for j, cell in enumerate(d["cols"]):
            if cell is None or cell["num"] is None or not st["direction"][j]:
                continue
            base = [r["cols"][j]["num"] for r in others if r["cols"][j] is not None and r["cols"][j]["num"] is not None]
            if not base:
                continue
            best = max(base) if st["direction"][j] == "+" else min(base)
            q = Decimal(1).scaleb(-cell["dec"])
            got = []
            for r in ours:
                c = r["cols"][j]
                if c is None or c["num"] is None:
                    continue
                v = c["num"] - best
                if cell["text"].endswith("%"):
                    v = v / abs(best) * 100 if best else None
                if v is not None:
                    got.append(v.quantize(q, rounding=ROUND_HALF_UP))
            checked += 1
            if cell["num"] not in got:
                bad.append(f"{_name(st, j)} prints {cell['text']} where the printed cells give "
                           f"{' or '.join(_signed(g) for g in got) or 'nothing'} (line {d['line']})")
    if bad:
        out.append(("FAIL", f"{len(bad)} of {checked} Δ cells disagree with the printed cells: " + "; ".join(bad[:4])))
    elif checked:
        out.append(("PASS", f"Δ row recomputed from the printed cells, {checked} cells"))
    return out


def _signed(d):
    return f"{d:f}" if d == 0 else ("+" if d > 0 else "") + f"{d:f}"


def audit_decimals(st):
    st = dict(st, data=[r for r in st["data"] if not r.get("delta")])        # a Δ row may carry its own precision
    out, labels = [], _label_columns(st)
    for j in range(st["ncol"]):
        if j in labels:
            continue
        filled = [(r, r["cols"][j]) for r in st["data"] if r["cols"][j] is not None and r["cols"][j]["text"]
                  and r["cols"][j]["text"] not in _MISSING]
        nums = [(r, c) for r, c in filled if c["num"] is not None]
        if not nums or len(nums) < NUMERIC_COLUMN * len(filled):
            continue
        decs = Counter(c["dec"] for _, c in nums)
        if len(decs) > 1:
            odd = min(decs, key=decs.get)
            r, c = next((r, c) for r, c in nums if c["dec"] == odd)
            spread = ", ".join(f"{d} in {n}" for d, n in sorted(decs.items()))
            out.append(("WARN", f"{_name(st, j)}: decimals differ ({spread} cells; e.g. {c['text']}, line {r['line']})"))
    return out or [("PASS", "one precision per numeric column")]


# ------------------------------------------------------------------------------------------ captions and names
def caption_words(tex) -> int:
    """Words of a caption as they print, counted as the PDF survey counts them: a maths group is one word, \\cref
    two ("Tab. 1"), \\cite one per key, a macro one; formatting and colour commands none."""
    if not tex:
        return 0
    s = re.sub(r"(?<!\\)\$[^$]*\$|\\\(.*?\\\)", " M ", tex)
    s = re.sub(r"\\[cC]ref\s*\{([^}]*)\}", lambda m: " Tab. N " * len(m.group(1).split(",")), s)
    s = re.sub(r"\\(ref|eqref|autoref|pageref)\s*\{[^}]*\}", " N ", s)
    s = re.sub(r"\\cite[a-zA-Z]*\*?\s*(\[[^\]]*\])?\s*\{([^}]*)\}", lambda m: " [N] " * len(m.group(2).split(",")), s)
    s = re.sub(r"\\(textcolor|colorbox|cellcolor|rowcolor|color)\s*(\[[^\]]*\])?\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\(label|vspace|hspace)\*?\s*\{[^{}]*\}", " ", s)
    s = re.sub(r"\\(textbf|textit|emph|underline|textsc|texttt|textrm|textsf|mbox|text|small|footnotesize|"
               r"scriptsize|centering|noindent|newline|linebreak|hfill|quad|qquad|xspace)(?![a-zA-Z])", " ", s)
    s = re.sub(r"\\[a-zA-Z@]+", " W ", s).replace("\\\\", " ").replace("~", " ")
    return sum(1 for w in re.sub(r"[{}]", "", s).split() if any(ch.isalnum() for ch in w))


def caption_verdict(words):
    if words > CAPTION_FAIL:
        return "FAIL", f"caption {words} words (flagship main-text median 25; target at most {CAPTION_PASS}, " \
                       f"fail over {CAPTION_FAIL})"
    if words > CAPTION_PASS:
        return "WARN", f"caption {words} words (target at most {CAPTION_PASS}; the text carries the verdict)"
    return "PASS", f"caption {words} words"


def caption_report(tex_path) -> list[dict]:
    """Words per table caption in one or more .tex files and the verdict against the contract."""
    paths = [tex_path] if isinstance(tex_path, (str, Path)) else list(tex_path)
    out = []
    for p in paths:
        for t in parse_tables(p):
            w = caption_words(t["caption"])
            sev, msg = caption_verdict(w) if t["caption"] is not None else ("WARN", "no caption")
            out.append(dict(path=str(p), line=t["line"], label=", ".join(t["labels"]) or "(no label)", words=w,
                            verdict=sev, message=msg))
    return out


def load_canon(src) -> dict:
    """{key: {"name": display name, "forbid": [variants]}}. From a YAML file or a dict: an entry is a mapping with a
    `name` and an optional `forbid` list, or a bare string; entries may sit under category keys (methods:, metrics:,
    tasks:, datasets:). Variants are matched in the LaTeX source as written, case-sensitively; quote YAML names such
    as `yes` or `1.0` that would otherwise not be read as strings."""
    if isinstance(src, dict) and all(isinstance(v, dict) and set(v) == {"name", "forbid"} for v in src.values()):
        return src
    if not isinstance(src, dict):
        import yaml
        src = yaml.safe_load(Path(src).read_text()) or {}
    out = {}

    def walk(d):
        for k, v in d.items():
            if isinstance(v, str):
                out[k] = dict(name=v, forbid=[])
            elif isinstance(v, dict) and "name" in v:
                out[k] = dict(name=str(v["name"]), forbid=[str(x) for x in (v.get("forbid") or [])])
            elif isinstance(v, dict):
                walk(v)
            else:
                raise ValueError(f"canon entry {k!r}: a name, or a mapping with name and forbid")
    walk(src)
    return out


_REFS = re.compile(r"\\(label|ref|eqref|cref|Cref|autoref|pageref|cite[a-zA-Z]*|input|include|includegraphics|url|"
                   r"href|bibliography|bibliographystyle|usepackage|documentclass|graphicspath|definecolor|"
                   r"newcommand|renewcommand)\*?\s*(\[[^\]]*\])?\s*\{[^}]*\}")


def _bounded(s):
    return r"(?<![A-Za-z0-9])" + re.escape(s) + r"(?![A-Za-z0-9])"


def check_names(paths, canon, case=True) -> list[dict]:
    """Every off-canon spelling in the files: [{"path", "line", "found", "name", "key"}]. A forbidden variant is
    reported wherever it is not part of a canonical name ("Box" inside "Box inpainting" is not). With `case`, a name
    with a capital after its first letter (FlowDPS, CelebA-128) is also reported in any other casing (FLowDPS).
    .tex files are read live (comments and \\iffalse blocks skipped); any other file (a figure script) as it is.
    Arguments of \\label, \\ref, \\cite, \\includegraphics and the like are not read."""
    canon = load_canon(canon)
    paths = [paths] if isinstance(paths, (str, Path)) else list(paths)
    names = sorted({e["name"] for e in canon.values()}, key=len, reverse=True)
    variants = sorted(((v, e["name"], k) for k, e in canon.items() for v in e["forbid"]), key=lambda t: -len(t[0]))
    cased = [(e["name"], k) for k, e in canon.items() if any(ch.isupper() for ch in e["name"][1:])]
    hits = []
    for p in paths:
        p = Path(p)
        lines = live_lines(p) if p.suffix == ".tex" else p.read_text(errors="replace").splitlines()
        for n, line in enumerate(lines, 1):
            s = _REFS.sub(lambda m: " " * len(m.group(0)), line).replace("~", " ")
            taken = [m.span() for nm in names for m in re.finditer(_bounded(nm), s)]
            free = lambda a, b: not any(a < y and x < b for x, y in taken)
            for v, nm, k in variants:
                for m in re.finditer(_bounded(v), s):
                    if free(*m.span()):
                        hits.append(dict(path=str(p), line=n, found=m.group(0), name=nm, key=k))
                        taken.append(m.span())
            for nm, k in cased if case else []:
                for m in re.finditer(_bounded(nm), s, re.I):
                    if m.group(0) != nm and free(*m.span()):
                        hits.append(dict(path=str(p), line=n, found=m.group(0), name=nm, key=k))
                        taken.append(m.span())
    return sorted(hits, key=lambda h: (h["path"], h["line"]))


# ------------------------------------------------------------------------------------------------ verification
def verify(tex_path, label, columns, rows, value_fn, scope="table", second=True, delta=None, delta_ours=None,
           relative=False) -> list[dict]:
    """Every cell of the table labelled `label` whose number or mark differs from what build() computes from
    value_fn, every spec row missing from the table and every table row missing from the spec, and every header that
    is not the column's name with its arrow: [{"row", "column", "line", "expected", "found"}]. The table is read as
    build() lays it out: the class column when the rows have a class, the name, then the columns in order; with
    `delta`, the Δ row build() writes is checked against improvement()."""
    found = [t for t in parse_tables(tex_path) if label in t["labels"]]
    if not found or not found[0]["tabulars"]:
        raise ValueError(f"no table labelled {label} with a tabular in {tex_path}")
    st = structure(found[0]["tabulars"][0])
    printed, marks = _expected(columns, rows, value_fn, scope, second)
    lead = 2 if any(r.cls for r in rows) else 1
    show = lambda text, m: text + {"b": " bold", "u": " underlined", "bu": " bold and underlined"}.get(m, "")
    issues, used = [], set()
    for k, c in enumerate(columns):
        want = plain(c.header + ARROW.get(c.direction, ""))
        if lead + k < st["ncol"] and st["heads"][lead + k] != want:
            issues.append(dict(row=None, column=c.key, line=st["head"][-1]["line"] if st["head"] else None,
                               expected=f"header {want}", found=f"header {st['heads'][lead + k] or '(none)'}"))
    for r in rows:
        idx = next((i for i, d in enumerate(st["data"]) if i not in used and d["texts"][lead - 1] == plain(r.name)
                    and (lead == 1 or d["texts"][0] == plain(r.cls or ""))), None)
        if idx is None:
            issues.append(dict(row=r.key, column=None, line=None, expected=f"row {r.name}", found="not in the table"))
            continue
        used.add(idx)
        d = st["data"][idx]
        for k, c in enumerate(columns):
            cell = d["cols"][lead + k] if lead + k < len(d["cols"]) else None
            text, mark = printed[(r.key, c.key)], marks.get((r.key, c.key), "")
            if cell is None:
                issues.append(dict(row=r.key, column=c.key, line=d["line"], expected=show(text, mark), found="no cell"))
                continue
            got = cell["numtext"] if cell["num"] is not None else cell["text"]
            same = got == text if _isnum(text) else (cell["text"] in _MISSING if text == MISSING else cell["text"] == plain(text))
            if not same or _mark_of(cell) != mark:
                issues.append(dict(row=r.key, column=c.key, line=d["line"], expected=show(text, mark),
                                   found=show(got, _mark_of(cell))))
    if delta:
        want = improvement(columns, rows, value_fn, ours=delta_ours, relative=relative)
        idx = next((i for i, d in enumerate(st["data"]) if i not in used and d["label"] == plain(delta)), None)
        if idx is None:
            issues.append(dict(row="delta", column=None, line=None, expected=f"row {plain(delta)}", found="not in the table"))
        else:
            used.add(idx)
            d = st["data"][idx]
            for k, c in enumerate(columns):
                cell = d["cols"][lead + k] if lead + k < len(d["cols"]) else None
                text = plain(want[c.key] or "")
                got = "" if cell is None else cell["text"]
                if got != text:
                    issues.append(dict(row="delta", column=c.key, line=d["line"], expected=text or "(empty)",
                                       found=got or "(empty)"))
    for i, d in enumerate(st["data"]):
        if i not in used:
            issues.append(dict(row=None, column=None, line=d["line"], expected="no such row in the spec", found=d["label"]))
    return issues


# ------------------------------------------------------------------------------------------ the source audit
_SEV = {"FAIL": 3, "WARN": 2, "PASS": 1, "INFO": 0, "": 0}


def audit_tex(paths, canon=None) -> tuple[list[dict], list[dict]]:
    """The source audit of every table float in the files, no spec needed: (one report per table with its checks as
    (severity, check, message) and its worst severity as verdict, the off-canon names outside any table)."""
    paths = [paths] if isinstance(paths, (str, Path)) else list(paths)
    hits = check_names(paths, canon) if canon is not None else []
    reports, inside = [], set()
    for p in paths:
        for t in parse_tables(p):
            checks = []
            if t["caption"] is None:
                checks.append(("WARN", "caption", "no caption"))
            else:
                sev, msg = caption_verdict(caption_words(t["caption"]))
                checks.append((sev, "caption", msg))
            for n, tab in enumerate(t["tabulars"]):
                tag = f"tabular {n + 1}: " if len(t["tabulars"]) > 1 else ""
                allrules = [x for r in tab["rows"] for x in r["rules"]] + tab["trail"]
                bad = ([f"a vertical rule in the column spec {{{tab['spec']}}}"] if tab["vertical"] else []) + \
                      ([f"{allrules.count('hline')} \\hline, {allrules.count('cline')} \\cline"]
                       if "hline" in allrules or "cline" in allrules else [])
                if bad:
                    checks.append(("FAIL", "rules", tag + "; ".join(bad) + " (booktabs: \\toprule, \\midrule, "
                                   "\\cmidrule, \\bottomrule; no vertical rules)"))
                elif "toprule" not in allrules or "bottomrule" not in allrules:
                    checks.append(("WARN", "rules", tag + "no \\toprule or no \\bottomrule"))
                else:
                    checks.append(("PASS", "rules", tag + "booktabs, no vertical rule, no \\hline"))
                st = structure(tab)
                checks += [(sev, "marks" if sev else "", (tag + msg) if sev else msg)
                           for sev, msg in audit_marks(st, t["caption"])]
                checks += [(sev, "decimals", tag + msg) for sev, msg in audit_decimals(st)]
                checks += [(sev, "delta", tag + msg) for sev, msg in audit_delta(st)]
            if canon is not None:
                mine = [h for h in hits if h["path"] == t["path"] and t["line"] <= h["line"] <= t["end"]]
                inside |= {id(h) for h in mine}
                checks.append(("FAIL", "names", f"{len(mine)} off-canon: " + "; ".join(
                    f"'{h['found']}' for '{h['name']}' (line {h['line']})" for h in mine)) if mine
                              else ("PASS", "names", "every name on the canon"))
            verdict = max((c[0] for c in checks), key=lambda s: _SEV[s], default="PASS")
            reports.append(dict(path=t["path"], line=t["line"], end=t["end"], labels=t["labels"], env=t["env"],
                                placement=t["placement"], position=t["position"], checks=checks,
                                verdict=verdict if _SEV[verdict] else "PASS"))
    return reports, [h for h in hits if id(h) not in inside]
