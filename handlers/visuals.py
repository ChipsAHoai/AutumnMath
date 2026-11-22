"""Picture hints: SVG drawings that show what a problem means without giving away the answer.

Colors and fonts match the Learn pages in learn/: orange and purple for the two numbers, yellow for
the part being asked about, red for anything that comes off.
"""
import re
import textwrap
from collections import Counter
from math import ceil, gcd
from xml.sax.saxutils import escape

from . import balance

INK, MUTED, LINE, PAPER = "#1b2737", "#5b6a7e", "#cfd9e6", "#f8fafd"
MARK, ORANGE, PURPLE = "#ffc83d", "#e8761f", "#7650d0"
COOL, GOOD, BAD, BAD_SOFT = "#1d6a86", "#2f8a57", "#c8394d", "#fbe3e7"
ROW_COLORS = (ORANGE, PURPLE)
ROD_COLOR, CUBE_COLOR, CROSS_COLOR = "#3b82c4", GOOD, BAD
PRIME_COLORS = {2: "#3b82c4", 3: "#2f8a57", 5: "#d9681a", 7: "#b0438a"}
OTHER_PRIME_COLOR = "#6b7787"
BODY_FONT = "font-family=\"'Atkinson Hyperlegible', 'Segoe UI', sans-serif\""
DISPLAY_FONT = "font-family=\"'Baloo 2', 'Trebuchet MS', sans-serif\" font-weight=\"800\""


def _svg(width, height, parts):
    return "".join([
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="16" fill="{PAPER}" stroke="{LINE}" stroke-width="2" />',
        *parts,
        "</svg>",
    ])


FRACTION = re.compile(r"(\d+)/(\d+)")


def _text(x, y, text, size=16, anchor="middle", fill=INK, bold=False, display=False, extra=""):
    text = str(text)
    if FRACTION.search(text):
        return _text_with_fractions(x, y, text, size, anchor, fill, bold, display, extra)
    font = DISPLAY_FONT if display else BODY_FONT + (' font-weight="700"' if bold else "")
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" {font} {extra}>'
            f'{escape(text)}</text>')


FIGURE_SPACE = " "  # as wide as a digit


def _text_with_fractions(x, y, text, size, anchor, fill, bold, display, extra):
    """One <text> where each fraction like 5/6 is drawn as 5 over a bar over 6: the top is raised and
    underlined, then the bottom steps back under it. Digits share one width, so only digits are measured."""
    small = size * 0.78
    raise_by = size * 0.42
    out, last = [], 0
    for match in FRACTION.finditer(text):
        before = escape(text[last:match.start()])
        # After a fraction the line is still down at the bottom number; step back up to the baseline.
        out.append(f'<tspan dx="2" dy="{-raise_by:.1f}">{before}</tspan>' if last else before)
        num, den = match.groups()
        width = max(len(num), len(den))
        pad = lambda s: FIGURE_SPACE * ((width - len(s)) // 2) + s + FIGURE_SPACE * ((width - len(s) + 1) // 2)
        out.append(f'<tspan dx="2" dy="{-raise_by:.1f}" font-size="{small:.1f}" text-decoration="underline">{pad(num)}</tspan>'
                   f'<tspan dx="{-width * small * 0.58:.1f}" dy="{2 * raise_by:.1f}" font-size="{small:.1f}">{pad(den)}</tspan>')
        last = match.end()
    out.append(f'<tspan dx="2" dy="{-raise_by:.1f}">{escape(text[last:])}</tspan>')
    font = DISPLAY_FONT if display else BODY_FONT + (' font-weight="700"' if bold else "")
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" {font} {extra} '
            f'xml:space="preserve" style="font-variant-numeric: tabular-nums">{"".join(out)}</text>')


def _captions(lines, top, width, size=15, chars=68, fill=INK):
    """Centered caption lines, wrapped to fit; returns (parts, bottom y). Lines with stacked fractions get more room."""
    parts, y = [], top
    for line in lines:
        for piece in textwrap.wrap(line, chars) or [""]:
            tall = bool(FRACTION.search(piece))
            y += 6 if tall else 0
            parts.append(_text(width / 2, y, piece, size=size, fill=fill))
            y += size + 8 + (8 if tall else 0)
    return parts, y


def _cross(x, y, w, h):
    return (f'<line x1="{x - 2}" y1="{y - 2}" x2="{x + w + 2}" y2="{y + h + 2}" stroke="{CROSS_COLOR}" stroke-width="3" />'
            f'<line x1="{x + w + 2}" y1="{y - 2}" x2="{x - 2}" y2="{y + h + 2}" stroke="{CROSS_COLOR}" stroke-width="3" />')


# ---------- MULTIPLICATION: DOT GRID, THEN THE TABLE'S TRICK ----------
# (what to say, rows in each part, whether the last row is taken away)
TIMES_TRICKS = {
    3: ("Split it: 2 rows, plus 1 more row.", [2, 1], False),
    4: ("Double, then double again: 2 rows and 2 rows.", [2, 2], False),
    5: ("5 rows is half of 10 rows.", [5], False),
    6: ("5 rows, plus 1 more row.", [5, 1], False),
    7: ("5 rows, plus 2 more rows.", [5, 2], False),
    8: ("Double the 4s: 4 rows and 4 rows.", [4, 4], False),
    9: ("10 rows, then take 1 row away.", [10], True),
    10: ("10 rows: put a 0 on the end.", [10], False),
    11: ("10 rows, plus 1 more row.", [10, 1], False),
    12: ("10 rows, plus 2 more rows.", [10, 2], False),
}


def times_trick(a: int, b: int):
    """(rows, cols) where the rows are a table with a trick, or None for tiny facts like 2 × 2."""
    for rows, cols in ((a, b), (b, a)):
        if rows in TIMES_TRICKS:
            return rows, cols
    return None


def dot_grid_svg(rows: int, cols: int, step: int = 1) -> str:
    """Step 1: rows of dots with skip-count labels, the last left for the kid to find.
    Step 2: the same dots split the way that times table's trick says."""
    trick = times_trick(rows, cols) if step >= 2 else None
    gap, radius, margin = 26, 9, 24
    if not trick:
        top = 48
        width = max(margin * 2 + cols * gap + 70, 220)
        height = top + rows * gap + margin
        parts = [_text(width / 2, 32, f"{rows} rows of {cols}", size=20, display=True)]
        for r in range(rows):
            cy = top + r * gap + gap / 2
            for c in range(cols):
                parts.append(f'<circle cx="{margin + c * gap + gap / 2}" cy="{cy}" r="{radius}" fill="{ROW_COLORS[r % 2]}" />')
            label = "?" if r == rows - 1 else str((r + 1) * cols)
            parts.append(_text(margin + cols * gap + 16, cy + 6, label, size=18, anchor="start", display=True))
        return _svg(width, height, parts)

    t_rows, t_cols = trick
    say, split, minus = TIMES_TRICKS[t_rows]
    width = max(margin * 2 + t_cols * gap + 120, 420)
    title = f"{t_rows} × {t_cols}" + ("  (turned around)" if (t_rows, t_cols) != (rows, cols) else "")
    parts = [_text(width / 2, 32, title, size=20, display=True), _text(width / 2, 56, say, size=15, bold=True)]
    y = 72
    for j, count in enumerate(split):
        start = y
        for r in range(count):
            ghost = minus and r == count - 1
            cy = y + gap / 2
            for c in range(t_cols):
                cx = margin + c * gap + gap / 2
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius - 1}" fill="none" stroke="{BAD}" '
                             f'stroke-width="2" stroke-dasharray="3 3" />' if ghost else
                             f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{ROW_COLORS[j % 2]}" />')
            if ghost:
                parts.append(_text(margin + t_cols * gap + 16, cy + 5, f"take away 1 × {t_cols}", size=14,
                                   anchor="start", fill=BAD, bold=True))
            y += gap
        label_y = (start + y - (gap if minus else 0)) / 2 + 6
        parts.append(_text(margin + t_cols * gap + 16, label_y, f"{count} × {t_cols}", size=18, anchor="start",
                           fill=ROW_COLORS[j % 2], display=True))
        y += 12
    if t_rows == 5:
        last = f"Find 10 × {t_cols} first, then take half."
    elif len(split) == 1 and not minus:
        last = f"Write {t_cols}, then put a 0 on the end."
    else:
        last = "Work out each part, then put them together."
    caption, bottom = _captions([last], y + 14, width)
    return _svg(width, bottom + 4, parts + caption)


# ---------- ADDITION / SUBTRACTION: BASE-TEN BLOCKS ----------
UNIT = 15  # side of one cube; a rod is 10 cubes tall


def _blocks(x0, top, tens, ones, crossed_tens=0, crossed_ones=0):
    """Draw tens rods then ones cubes (columns of 5). Crossed items are the last ones drawn."""
    parts = []
    x = x0
    for i in range(tens):
        parts.append(f'<rect x="{x}" y="{top}" width="{UNIT}" height="{UNIT * 10}" fill="{ROD_COLOR}" stroke="{INK}" />')
        for k in range(1, 10):
            parts.append(f'<line x1="{x}" y1="{top + k * UNIT}" x2="{x + UNIT}" y2="{top + k * UNIT}" stroke="{INK}" />')
        if i >= tens - crossed_tens:
            parts.append(_cross(x, top, UNIT, UNIT * 10))
        x += UNIT + 8
    if tens and ones:
        x += 6
    for i in range(ones):
        cx = x + (i // 5) * (UNIT + 4)
        cy = top + (i % 5) * (UNIT + 4)
        parts.append(f'<rect x="{cx}" y="{cy}" width="{UNIT}" height="{UNIT}" fill="{CUBE_COLOR}" stroke="{INK}" />')
        if i >= ones - crossed_ones:
            parts.append(_cross(cx, cy, UNIT, UNIT))
    if ones:
        x += ((ones - 1) // 5 + 1) * (UNIT + 4)
    return parts, max(x - x0, 40)


def base_ten_svg(a: int, b: int, op: str) -> str:
    top, margin = 50, 24
    parts, captions = [], []
    if op == "+":
        x = margin
        for i, n in enumerate((a, b)):
            if i:
                parts.append(_text(x + 14, top + 62, "+", size=32, display=True))
                x += 40
            group, w = _blocks(x, top, n // 10, n % 10)
            parts.append(_text(x + w / 2, 32, n, size=22, display=True))
            parts.append(_text(x + w / 2, top + UNIT * 10 + 22, f"{n // 10} tens {n % 10} ones", size=14, fill=MUTED))
            parts.extend(group)
            x += w + 16
        if a % 10 + b % 10 >= 10:
            captions.append("10 ones make 1 ten!")
        width = x + margin
    else:
        tens, ones = a // 10, a % 10
        if ones < b % 10:
            tens, ones = tens - 1, ones + 10
            captions.append("Not enough ones: trade 1 ten for 10 ones")
        group, w = _blocks(margin, top, tens, ones, b // 10, b % 10)
        parts.append(_text(margin, 32, f"Start with {a}, take away {b}", size=20, anchor="start", display=True))
        parts.append(_text(margin + w / 2, top + UNIT * 10 + 22, f"{tens} tens {ones} ones", size=14, fill=MUTED))
        parts.extend(group)
        width = max(margin * 2 + w, 420)
    height = top + UNIT * 10 + 36
    for i, caption in enumerate(captions):
        parts.append(_text(width / 2, height + 4 + i * 22, caption, size=16, bold=True, fill=ORANGE))
    height += 22 * len(captions) + (10 if captions else 0)
    return _svg(width, height, parts)


# ---------- GCF / LCM: PRIME BLOCKS IN THREE BINS ----------
def prime_factors(n: int) -> list:
    factors, p = [], 2
    while p * p <= n:
        while n % p == 0:
            factors.append(p)
            n //= p
        p += 1
    if n > 1:
        factors.append(n)
    return factors


def _factorization(n: int) -> str:
    factors = prime_factors(n)
    return f"{n} is prime" if len(factors) == 1 else f"{n} = {' × '.join(map(str, factors))}"


def _prime_block(x, y, p, size=30):
    color = PRIME_COLORS.get(p, OTHER_PRIME_COLOR)
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="7" fill="{color}" />'
            + _text(x + size / 2, y + size / 2 + 6, p, size=16 if p < 10 else 13, fill="white", display=True))


def factor_bins_svg(a: int, b: int, step: int = 3, goal=None) -> str:
    """Step 1: bigger or smaller, and what to do. Step 2: the prime factors. Step 3: sorted into bins."""
    width = 540
    fa, fb = Counter(prime_factors(a)), Counter(prime_factors(b))
    common = fa & fb
    bins = [sorted((fa - common).elements()), sorted(common.elements()), sorted((fb - common).elements())]
    if step == 1:
        # Follow-up questions keep this hint, so talk about the LCM or GCF, not "the answer".
        top = {
            "lcm": ["Lining up again means the LCM.",
                    f"The LCM of {a} and {b} is at least as big as {max(a, b)}."],
            "gcf": ["Equal pieces or groups means the GCF.",
                    f"The GCF of {a} and {b} is no bigger than {min(a, b)}."],
        }.get(goal, [f"LCM (lining up again): at least as big as {max(a, b)}.",
                     f"GCF (equal pieces or groups): no bigger than {min(a, b)}."])
        bottom = [f"Next: break {a} and {b} into prime blocks. Try a factor tree on the scratchpad!"]
    elif step == 2:
        top = [_factorization(a), _factorization(b)]
        bottom = ["Blocks that both numbers have go in the middle bin.", "The rest go in their own bins."]
    else:
        top = [_factorization(a), _factorization(b)]
        bottom = {
            "gcf": ["GCF: multiply the blocks in the middle bin."],
            "lcm": ["LCM: multiply every block, using the middle ones only once."],
        }.get(goal, ["GCF: multiply the blocks in the middle bin.",
                     "LCM: multiply every block, using the middle ones only once."])
    parts = [_text(width / 2, 34, top[0], size=18, display=True), _text(width / 2, 60, top[1], size=18, display=True)]

    per_row, size, gap = 4, 30, 6
    rows = max(1, ceil(max(len(group) for group in bins) / per_row)) if step >= 3 else 1
    bin_top, bin_w = 82, 156
    bin_h = 40 + rows * (size + gap) + 8
    labels = [(f"Only in {a}", ORANGE), ("In both", INK), (f"Only in {b}", PURPLE)]
    for i, (group, (label, color)) in enumerate(zip(bins, labels)):
        x = 18 + i * (bin_w + 15)
        middle = i == 1
        dashes = "" if middle else ' stroke-dasharray="6 5"'
        parts.append(f'<rect x="{x}" y="{bin_top}" width="{bin_w}" height="{bin_h}" rx="14" fill="white" '
                     f'stroke="{MARK if middle else LINE}" stroke-width="{3 if middle else 2}"{dashes} />')
        parts.append(_text(x + bin_w / 2, bin_top + 26, label, size=15, fill=color, bold=True))
        if step < 3:
            parts.append(_text(x + bin_w / 2, bin_top + 64, "?", size=28, fill=MUTED, display=True))
        elif not group:
            parts.append(_text(x + bin_w / 2, bin_top + 62, "none", size=14, fill=MUTED))
        else:
            for k, p in enumerate(group):
                row, col = divmod(k, per_row)
                in_row = min(per_row, len(group) - row * per_row)
                bx = x + (bin_w - (in_row * size + (in_row - 1) * gap)) / 2 + col * (size + gap)
                parts.append(_prime_block(bx, bin_top + 40 + row * (size + gap), p, size))
    caption, bottom_y = _captions(bottom, bin_top + bin_h + 28, width)
    return _svg(width, bottom_y + 2, parts + caption)


# Old saves and older code call it by its first name.
factor_venn_svg = factor_bins_svg


# ---------- PERCENT: MONEY BAR ----------
def _money(amount) -> str:
    cents = round(amount * 100)
    return f"${cents // 100}" if cents % 100 == 0 else f"${cents // 100}.{cents % 100:02d}"


def _swatch(x, y, fill, label, hatched=False):
    box = (f'<rect x="{x}" y="{y - 13}" width="16" height="16" rx="4" fill="url(#off)" stroke="{BAD}" stroke-width="2" />'
           if hatched else f'<rect x="{x}" y="{y - 13}" width="16" height="16" rx="4" fill="{fill}" stroke="{INK}" stroke-width="1.5" />')
    return box + _text(x + 24, y, label, size=14, anchor="start")


def percent_bar_svg(whole: int, pct=None, part=None, sign=1, step: int = 1) -> str:
    """The whole price is 100%. A sale cuts a piece off the start of the bar; tax or a fee adds a piece past 100%."""
    width, x0, length, top, bar_height = 540, 30, 400, 74, 54
    finding_percent = pct is None
    share = part / whole if finding_percent else pct / 100
    piece = length * share
    adds_on = not finding_percent and sign > 0
    # Hatching for the part that comes off; drawn with a path so the bar has no <line> tick marks.
    parts = [f'<defs><pattern id="off" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             f'<path d="M0 0 V9" stroke="{BAD}" stroke-width="4" /></pattern></defs>']
    if finding_percent:
        parts += [f'<rect x="{x0}" y="{top}" width="{length}" height="{bar_height}" rx="8" fill="white" stroke="{INK}" stroke-width="2" />',
                  f'<rect x="{x0}" y="{top}" width="{piece:.1f}" height="{bar_height}" rx="8" fill="{MARK}" stroke="{INK}" stroke-width="2" />']
    elif adds_on:
        parts += [f'<rect x="{x0}" y="{top}" width="{length}" height="{bar_height}" rx="8" fill="{MARK}" stroke="{INK}" stroke-width="2" />',
                  f'<rect x="{x0 + length}" y="{top}" width="{piece:.1f}" height="{bar_height}" rx="6" fill="{GOOD}" stroke="{INK}" stroke-width="2" />']
    else:
        parts += [f'<rect x="{x0}" y="{top}" width="{length}" height="{bar_height}" rx="8" fill="{MARK}" stroke="{INK}" stroke-width="2" />',
                  f'<rect x="{x0}" y="{top}" width="{piece:.1f}" height="{bar_height}" rx="8" fill="url(#off)" stroke="{BAD}" stroke-width="2" />']

    base = None
    if not finding_percent:
        # Build from 10% when that's not already the answer; otherwise from 1%.
        base = 10 if pct % 5 == 0 and pct != 10 else 1
        for tenth in range(1, 10):
            x = x0 + length * tenth / 10
            parts.append(f'<path d="M{x:.1f} {top + 3} V{top + bar_height - 3}" stroke="{INK}" stroke-opacity="0.35" '
                         f'stroke-dasharray="4 3" />')
        if step >= 2 and base == 10:
            box = _money(whole / 10)
            for tenth in range(10):
                parts.append(_text(x0 + length * (tenth + 0.5) / 10, top + bar_height - 10, box,
                                   size=12 if len(box) > 4 else 14, bold=True))
    marks = (("0%", 0), ("100%", 1)) if finding_percent else (("0%", 0), ("50%", 0.5), ("100%", 1))
    for label, frac in marks:
        parts.append(_text(x0 + length * frac, top + bar_height + 20, label, size=13, fill=MUTED))
    parts.append(_text(x0 + length, top - 14, f"100% = {_money(whole)}", size=17,
                       anchor="middle" if adds_on else "end", display=True, fill=COOL))
    label = f"{pct}% = ?" if not finding_percent else f"{_money(part)} = ?%"
    label_color = INK if finding_percent else GOOD if adds_on else BAD
    if adds_on:
        parts.append(_text(x0 + length + piece / 2, top - 38, label, size=17, display=True, fill=label_color))
    else:
        narrow = piece < 90
        parts.append(_text(x0 if narrow else x0 + piece / 2, top - 14, label, size=17,
                           anchor="start" if narrow else "middle", display=True, fill=label_color))

    legend_y = top + bar_height + 48
    if adds_on:
        parts += [_swatch(x0, legend_y, MARK, "the price (100%)"), _swatch(x0 + 200, legend_y, GOOD, "added on")]
    elif not finding_percent:
        parts += [_swatch(x0, legend_y, None, "comes off", hatched=True), _swatch(x0 + 200, legend_y, MARK, "what's left")]

    if not finding_percent:
        if base == 10:
            count = pct // 10
            build = f"{pct}% = {count} × 10%" if pct % 10 == 0 else (
                f"{pct}% = {count} × 10% + 5% (5% is half of 10%)" if count else "5% is half of 10%")
        else:
            build = f"{pct}% = {pct} × 1%"
        if step == 1:
            captions = [f"Find {pct}% of {_money(whole)}.",
                        "Start with an easy piece: 10% moves the decimal point one place left."
                        if base == 10 else "Start with an easy piece: 1% moves the decimal point two places left."]
        else:
            captions = [f"{base}% of {_money(whole)} = {_money(whole * base / 100)}", build]
        captions.append("For the total, add it to the price." if sign > 0
                        else "For what's left, take it away from the price.")
    elif step == 1:
        captions = [f"What part of {_money(whole)} is {_money(part)}?",
                    "Try finding 1% of the price first."]
    else:
        captions = [f"1% of {_money(whole)} = {_money(whole / 100)}",
                    f"How many of those make {_money(part)}? That's the percent."]
    caption, bottom = _captions(captions, legend_y + (36 if not finding_percent else 0), width)
    return _svg(width, bottom + 2, parts + caption)


# ---------- EQUATIONS: BALANCE SCALE ----------
TILE = 30


def _tile_items(term, leave=0):
    """Drawable pieces for one term: list of (width, height, draw(x, bottom))."""
    t = term["t"]
    if t == "x":
        items = []
        going = min(leave, term["n"])
        for _ in range(going):
            items.append((TILE, TILE, lambda x, b: (
                f'<rect x="{x}" y="{b - TILE}" width="{TILE}" height="{TILE}" rx="6" fill="{BAD_SOFT}" stroke="{BAD}" '
                f'stroke-width="2.5" stroke-dasharray="4 3" />'
                + _text(x + TILE / 2, b - 9, "x", size=18, fill=BAD, display=True)
                + f'<path d="M{x + 5} {b - TILE / 2} H{x + TILE - 5}" stroke="{BAD}" stroke-width="2.5" />')))
        rest = term["n"] - going
        if 0 < rest <= 6:
            items += [_x_tile("x")] * rest
        elif rest > 6:
            items.append(_x_tile(f"{rest}x", 46))
        return items
    if t == "fx":
        return [_x_tile(f"{term['p']}/{term['q']}x", 52, size=14)]
    if t in ("k", "fr"):
        value = term["v"] if t == "k" else term["num"]
        text = str(abs(value)) if t == "k" else f"{abs(term['num'])}/{term['den']}"
        label = ("−" if value < 0 else "") + text
        w = max(TILE, 14 + 9 * len(label))
        if value < 0:
            return [(w, TILE, lambda x, b, w=w, label=label: (
                f'<rect x="{x}" y="{b - TILE}" width="{w}" height="{TILE}" rx="15" fill="{BAD_SOFT}" stroke="{BAD}" '
                f'stroke-width="2" stroke-dasharray="4 3" />' + _text(x + w / 2, b - 9, label, size=16, fill=BAD, display=True)))]
        return [(w, TILE, lambda x, b, w=w, label=label: (
            f'<rect x="{x}" y="{b - TILE}" width="{w}" height="{TILE}" rx="15" fill="{MARK}" />'
            + _text(x + w / 2, b - 9, label, size=16, display=True)))]
    inner = [item for sub in term["inner"] for item in _tile_items(sub)]
    inner_w = sum(w for w, _, _ in inner) + 3 * (len(inner) - 1)
    if t == "grp":
        w, h = inner_w + 10, TILE + 10

        def bag(x, b):
            out = [f'<rect x="{x}" y="{b - h}" width="{w}" height="{h}" rx="9" fill="none" stroke="{PURPLE}" '
                   f'stroke-width="2" stroke-dasharray="5 4" />']
            cx = x + 5
            for iw, _, draw in inner:
                out.append(draw(cx, b - 5))
                cx += iw + 3
            return "".join(out)
        return [(w, h, bag)] * term["m"]
    w, h = inner_w + 10, TILE + 30

    def shared(x, b):
        out = [f'<rect x="{x}" y="{b - h}" width="{w}" height="{h}" rx="9" fill="none" stroke="{PURPLE}" stroke-width="2" />',
               f'<path d="M{x} {b - 22} H{x + w}" stroke="{PURPLE}" stroke-width="2" />',
               _text(x + w / 2, b - 6, f"÷ {term['d']}", size=14, fill=PURPLE, bold=True)]
        cx = x + 5
        for iw, _, draw in inner:
            out.append(draw(cx, b - 26))
            cx += iw + 3
        return "".join(out)
    return [(w, h, shared)]


def _x_tile(label, w=TILE, size=18):
    return (w, TILE, lambda x, b: (
        f'<rect x="{x}" y="{b - TILE}" width="{w}" height="{TILE}" rx="6" fill="{ORANGE}" />'
        + _text(x + w / 2, b - 9, label, size=size, fill="white", display=True)))


def _pan_rows(side, leave, pan_w):
    items = [item for term in side for item in _tile_items(term, leave)]
    rows, row, row_w = [], [], 0
    for item in items:
        if row and row_w + 5 + item[0] > pan_w:
            rows.append(row)
            row, row_w = [], 0
        row_w += (5 if row else 0) + item[0]
        row.append(item)
    if row:
        rows.append(row)
    return rows


def _pan_height(rows):
    return sum(max(h for _, h, _ in row) + 6 for row in rows)


def _draw_pan(rows, left, pan_w, base):
    out, b = [], base
    for row in rows:
        row_w = sum(w for w, _, _ in row) + 5 * (len(row) - 1)
        x = left + (pan_w - row_w) / 2
        for w, _, draw in row:
            out.append(draw(x, b))
            x += w + 5
        b -= max(h for _, h, _ in row) + 6
    return out


def balance_svg(left, right, step: int = 1) -> str:
    """Hint n shows the equation after n − 1 moves and names move n; it never shows x = answer."""
    states = balance.solve(left, right)
    moves = len(states) - 1
    step = max(1, min(step, moves))
    cur, nxt = states[step - 1], states[step]
    leave = nxt.get("take", 0)
    width, pan_w = 560, 240
    left_rows, right_rows = _pan_rows(cur["L"], leave, pan_w), _pan_rows(cur["R"], leave, pan_w)
    base = 64 + max(_pan_height(left_rows), _pan_height(right_rows), TILE + 6)
    parts = [_text(width / 2, 38, balance.eq_text(cur["L"], cur["R"]), size=24, display=True)]
    parts += _draw_pan(left_rows, 20, pan_w, base)
    parts += _draw_pan(right_rows, width - 20 - pan_w, pan_w, base)
    parts += [
        _text(width / 2, base - 8, "=", size=30, fill=MUTED, display=True),
        f'<rect x="16" y="{base + 2}" width="{width - 32}" height="7" rx="3" fill="{INK}" />',
        f'<rect x="{width / 2 - 4}" y="{base + 9}" width="8" height="34" fill="{INK}" />',
        f'<path d="M{width / 2 - 34} {base + 66} L{width / 2} {base + 40} L{width / 2 + 34} {base + 66} Z" fill="{INK}" />',
    ]
    lines = [f"Move {step} of {moves}: {nxt['move']}."]
    lines.append("The red dashed x's come off both sides together, so it stays balanced." if leave
                 else "Do the same thing to both sides so the scale stays level.")
    caption, bottom = _captions(lines, base + 96, width)
    return _svg(width, bottom + 2, parts + caption)


# ---------- SLOPE: RISE OVER RUN ON A GRID ----------
def slope_svg(x1, y1, x2, y2, step: int = 1) -> str:
    width, unit, gx, gy = 540, 15, 120, 20
    sx = lambda x: gx + (x + 10) * unit
    sy = lambda y: gy + (10 - y) * unit
    parts = [f'<defs><clipPath id="slope-grid"><rect x="{sx(-10)}" y="{sy(10)}" width="{20 * unit}" height="{20 * unit}" />'
             f'</clipPath></defs>']
    for i in range(-10, 11):
        color, w = (MUTED, 2) if i == 0 else (LINE, 1)
        parts.append(f'<path d="M{sx(i)} {sy(-10)} V{sy(10)}" stroke="{color}" stroke-width="{w}" />')
        parts.append(f'<path d="M{sx(-10)} {sy(i)} H{sx(10)}" stroke="{color}" stroke-width="{w}" />')
        if i and i % 5 == 0:
            parts.append(_text(sx(i), sy(0) + 14, i, size=11, fill=MUTED, bold=True))
            parts.append(_text(sx(0) - 5, sy(i) + 4, i, size=11, fill=MUTED, bold=True, anchor="end"))
    dx, dy, k = x2 - x1, y2 - y1, 40
    parts.append(f'<path d="M{sx(x1 - k * dx)} {sy(y1 - k * dy)} L{sx(x2 + k * dx)} {sy(y2 + k * dy)}" '
                 f'stroke="{COOL}" stroke-width="3" clip-path="url(#slope-grid)" />')
    if step >= 1 and dx:
        parts.append(f'<path d="M{sx(x1)} {sy(y1)} H{sx(x2)}" stroke="{ORANGE}" stroke-width="5" stroke-linecap="round" />')
        parts.append(_text((sx(x1) + sx(x2)) / 2, sy(y1) + (18 if dy > 0 else -8), "run", size=16, fill=ORANGE, display=True))
    if step >= 2 and dy:
        parts.append(f'<path d="M{sx(x2)} {sy(y1)} V{sy(y2)}" stroke="{PURPLE}" stroke-width="5" stroke-linecap="round" />')
        parts.append(_text(sx(x2) + (8 if dx > 0 else -8), (sy(y1) + sy(y2)) / 2 + 5, "rise", size=16, fill=PURPLE,
                           display=True, anchor="start" if dx > 0 else "end"))
    # Each point's label sits on the far side from the other point, clear of the run and rise.
    for name, x, y, other_x in (("1st", x1, y1, x2), ("2nd", x2, y2, x1)):
        outside = -1 if x < other_x else 1
        parts.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="6" fill="{INK}" stroke="white" stroke-width="2" />')
        parts.append(_text(sx(x) + 10 * outside, sy(y) + 4, f"{name} ({x}, {y})", size=12,
                           anchor="end" if outside < 0 else "start", bold=True,
                           extra='paint-order="stroke" stroke="white" stroke-width="4"'))
    neg = lambda n: f"({n})" if n < 0 else str(n)
    if step == 1:
        lines = ["Run: how far across from the 1st point to the 2nd.",
                 f"run = {x2} − {neg(x1)}", "Going left counts as negative."]
    else:
        lines = ["Rise: how far up or down from the 1st point to the 2nd.",
                 f"rise = {y2} − {neg(y1)}", "Slope = rise ÷ run. Going down counts as negative. Simplify at the end."]
    caption, bottom = _captions(lines, sy(-10) + 34, width)
    return _svg(width, bottom + 2, parts + caption)


# ---------- FRACTIONS: BARS CUT INTO PIECES ----------
def _frac_label(n, d):
    return str(n) if d == 1 else f"{n}/{d}"


def _fraction_bar(x0, y, unit_w, n, d, color, wholes_shown):
    """Whole bars side by side, each cut into d pieces, with n pieces colored."""
    out, h = [], 32
    cell = unit_w / d
    for w in range(wholes_shown):
        wx = x0 + w * unit_w
        out.append(f'<rect x="{wx:.1f}" y="{y}" width="{unit_w:.1f}" height="{h}" fill="white" stroke="{INK}" stroke-width="2" />')
        filled = max(0, min(d, n - w * d))
        if filled:
            out.append(f'<rect x="{wx:.1f}" y="{y}" width="{filled * cell:.1f}" height="{h}" fill="{color}" />')
        if cell >= 5:
            for i in range(1, d):
                out.append(f'<path d="M{wx + i * cell:.1f} {y} V{y + h}" stroke="{INK}" stroke-opacity="0.45" />')
        out.append(f'<rect x="{wx:.1f}" y="{y}" width="{unit_w:.1f}" height="{h}" fill="none" stroke="{INK}" stroke-width="2" />')
    return out


def fraction_svg(n1, d1, n2, d2, step: int = 1) -> str:
    """Step 1: the two fractions as bars, pieces of different sizes. Step 2: both cut into matching pieces."""
    width, x0, bar_w = 560, 92, 440
    lcd = d1 * d2 // gcd(d1, d2)
    wholes = max(1, ceil(max(n1 / d1, n2 / d2)))
    unit_w = bar_w / wholes
    renamed = step >= 2 and d1 != d2
    rows = ([(n1 * lcd // d1, lcd, ORANGE), (n2 * lcd // d2, lcd, PURPLE)] if renamed
            else [(n1, d1, ORANGE), (n2, d2, PURPLE)])
    title = f"{_frac_label(n1, d1)} + {_frac_label(n2, d2)}"
    parts = [_text(width / 2, 36, title, size=24, display=True)]
    y = 62
    for n, d, color in rows:
        parts.append(_text(x0 - 12, y + 23, _frac_label(n, d), size=18, anchor="end", fill=color, display=True))
        parts += _fraction_bar(x0, y, unit_w, n, d, color, max(1, ceil(n / d)))
        y += 48
    if d1 == d2:
        lines = [f"Both are already cut into {d1} pieces per whole, so the pieces match.",
                 "Add the tops, keep the bottom, then simplify if you can."]
    elif not renamed:
        lines = [f"The pieces are different sizes: 1/{d1} and 1/{d2}. You can only add matching pieces.",
                 f"Cut both into pieces that fit both bottoms: the LCM of {d1} and {d2}."]
    else:
        lines = [f"{_frac_label(n1, d1)} = {rows[0][0]}/{lcd} and {_frac_label(n2, d2)} = {rows[1][0]}/{lcd}",
                 f"Now the pieces match. Add the tops, keep the bottom {lcd}, then simplify."]
    caption, bottom = _captions(lines, y + 16, width)
    return _svg(width, bottom + 2, parts + caption)


# ---------- WHICH PICTURE, AND HOW MANY STEPS ----------
def hint_steps(hint) -> int:
    """How many hints a problem has; each one shows a bit more."""
    if not hint:
        return 1
    kind = hint.get("kind")
    if kind == "dots":
        return 2 if times_trick(hint["a"], hint["b"]) else 1
    if kind == "scale":
        return max(1, len(balance.solve(hint["L"], hint["R"])) - 1)
    if kind == "fraction":
        return 2 if hint["d1"] != hint["d2"] else 1
    return {"venn": 3, "percent": 2, "slope": 2}.get(kind, 1)


def build_svg(hint, step: int = 1) -> str:
    if not hint:
        return ""
    kind = hint.get("kind")
    if kind == "dots":
        return dot_grid_svg(hint["a"], hint["b"], step)
    if kind == "blocks":
        return base_ten_svg(hint["a"], hint["b"], hint["op"])
    if kind == "venn":
        return factor_bins_svg(hint["a"], hint["b"], step, hint.get("goal"))
    if kind == "percent":
        return percent_bar_svg(hint["whole"], hint.get("pct"), hint.get("part"), hint.get("sign", 1), step)
    if kind == "scale":
        return balance_svg(hint["L"], hint["R"], step)
    if kind == "slope":
        return slope_svg(hint["x1"], hint["y1"], hint["x2"], hint["y2"], step)
    if kind == "fraction":
        return fraction_svg(hint["n1"], hint["d1"], hint["n2"], hint["d2"], step)
    return ""
