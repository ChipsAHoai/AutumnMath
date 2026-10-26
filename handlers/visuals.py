"""Picture hints: SVG drawings that show what a problem means without giving away the answer."""
from collections import Counter

ROW_COLORS = ("#f97316", "#8b5cf6")
ROD_COLOR, CUBE_COLOR, CROSS_COLOR = "#3b82f6", "#22c55e", "#dc2626"
TEXT = 'font-family="sans-serif"'


def _svg(width, height, parts):
    return "".join([
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="12" fill="white" />',
        *parts,
        "</svg>",
    ])


def _text(x, y, text, size=16, anchor="middle", extra="", fill="#222"):
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" {TEXT} {extra}>{text}</text>'


def _cross(x, y, w, h):
    return (f'<line x1="{x - 2}" y1="{y - 2}" x2="{x + w + 2}" y2="{y + h + 2}" stroke="{CROSS_COLOR}" stroke-width="3" />'
            f'<line x1="{x + w + 2}" y1="{y - 2}" x2="{x - 2}" y2="{y + h + 2}" stroke="{CROSS_COLOR}" stroke-width="3" />')


# ---------- MULTIPLICATION: DOT GRID ----------
def dot_grid_svg(rows: int, cols: int) -> str:
    """Rows of dots with skip-count labels; the last label is left for the kid to find."""
    gap, radius, margin, top = 26, 9, 24, 44
    width = margin * 2 + cols * gap + 70
    height = top + rows * gap + margin
    parts = [_text(width / 2, 28, f"{rows} rows of {cols}", size=18, extra='font-weight="bold"')]
    for r in range(rows):
        cy = top + r * gap + gap / 2
        color = ROW_COLORS[r % 2]
        for c in range(cols):
            cx = margin + c * gap + gap / 2
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{color}" />')
        label = "?" if r == rows - 1 else str((r + 1) * cols)
        parts.append(_text(margin + cols * gap + 16, cy + 6, label, size=18, anchor="start",
                           extra='font-weight="bold"'))
    return _svg(width, height, parts)


# ---------- ADDITION / SUBTRACTION: BASE-TEN BLOCKS ----------
UNIT = 15  # side of one cube; a rod is 10 cubes tall


def _blocks(x0, top, tens, ones, crossed_tens=0, crossed_ones=0):
    """Draw tens rods then ones cubes (columns of 5). Crossed items are the last ones drawn."""
    parts = []
    x = x0
    for i in range(tens):
        parts.append(f'<rect x="{x}" y="{top}" width="{UNIT}" height="{UNIT * 10}" fill="{ROD_COLOR}" stroke="#1e3a8a" />')
        for k in range(1, 10):
            parts.append(f'<line x1="{x}" y1="{top + k * UNIT}" x2="{x + UNIT}" y2="{top + k * UNIT}" stroke="#1e3a8a" />')
        if i >= tens - crossed_tens:
            parts.append(_cross(x, top, UNIT, UNIT * 10))
        x += UNIT + 8
    if tens and ones:
        x += 6
    for i in range(ones):
        cx = x + (i // 5) * (UNIT + 4)
        cy = top + (i % 5) * (UNIT + 4)
        parts.append(f'<rect x="{cx}" y="{cy}" width="{UNIT}" height="{UNIT}" fill="{CUBE_COLOR}" stroke="#14532d" />')
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
                parts.append(_text(x + 14, top + 62, "+", size=32, extra='font-weight="bold"'))
                x += 40
            group, w = _blocks(x, top, n // 10, n % 10)
            parts.append(_text(x + w / 2, 32, n, size=20, extra='font-weight="bold"'))
            parts.append(_text(x + w / 2, top + UNIT * 10 + 22, f"{n // 10} tens {n % 10} ones", size=14))
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
        parts.append(_text(margin, 32, f"Start with {a}, take away {b}", size=18, anchor="start",
                           extra='font-weight="bold"'))
        parts.append(_text(margin + w / 2, top + UNIT * 10 + 22, f"{tens} tens {ones} ones", size=14))
        parts.extend(group)
        width = max(margin * 2 + w, 420)
    height = top + UNIT * 10 + 36
    for i, caption in enumerate(captions):
        parts.append(_text(width / 2, height + 4 + i * 22, caption, size=16, extra='font-weight="bold"', fill="#b45309"))
    height += 22 * len(captions) + (10 if captions else 0)
    return _svg(width, height, parts)


# ---------- GCF / LCM: PRIME FACTOR VENN DIAGRAM ----------
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


def _factor_column(cx, cy, factors):
    if not factors:
        return [_text(cx, cy + 6, "only 1", size=15, fill="#666")]
    line_height = 24
    start = cy - (len(factors) - 1) * line_height / 2
    return [_text(cx, start + i * line_height + 7, f, size=20, extra='font-weight="bold"')
            for i, f in enumerate(factors)]


def _factorization(n: int) -> str:
    factors = prime_factors(n)
    return f"{n} is prime" if len(factors) == 1 else f"{n} = {' × '.join(map(str, factors))}"


def factor_venn_svg(a: int, b: int, step: int = 3) -> str:
    """Step 1: empty circles and what to do. Step 2: the prime factors to sort. Step 3: sorted."""
    width, height, radius, cy = 520, 360, 110, 200
    if step == 1:
        top = [f"Step 1: Break {a} and {b} into prime factors.",
               "Try a factor tree on the scratchpad!"]
        bottom = ["Step 2: Factors that both numbers share go in the middle.",
                  "The rest go on their own side."]
    else:
        top = [_factorization(a), _factorization(b)]
        if step == 2:
            bottom = ["Sort them: factors both numbers share go in the middle.",
                      "Then use the middle (GCF) or everything (LCM)."]
        else:
            bottom = ["GCF: multiply the factors in the middle",
                      "LCM: multiply every factor in both circles"]
    parts = [
        _text(width / 2, 26, top[0], size=16),
        _text(width / 2, 48, top[1], size=16),
        f'<circle cx="190" cy="{cy}" r="{radius}" fill="#f97316" fill-opacity="0.25" stroke="#f97316" stroke-width="3" />',
        f'<circle cx="330" cy="{cy}" r="{radius}" fill="#8b5cf6" fill-opacity="0.25" stroke="#8b5cf6" stroke-width="3" />',
        _text(120, cy - radius + 4, a, size=20, extra='font-weight="bold"', fill="#c2410c"),
        _text(400, cy - radius + 4, b, size=20, extra='font-weight="bold"', fill="#6d28d9"),
        _text(width / 2, height - 30, bottom[0], size=15),
        _text(width / 2, height - 10, bottom[1], size=15),
    ]
    if step >= 3:
        fa, fb = Counter(prime_factors(a)), Counter(prime_factors(b))
        common = fa & fb
        parts += [*_factor_column(130, cy, sorted((fa - common).elements())),
                  *_factor_column(260, cy, sorted(common.elements())),
                  *_factor_column(390, cy, sorted((fb - common).elements()))]
    else:
        parts += [_text(x, cy + 8, "?", size=28, extra='font-weight="bold"', fill="#888") for x in (130, 260, 390)]
    return _svg(width, height, parts)


# ---------- PERCENT: BAR MODEL ----------
def _money(amount) -> str:
    cents = round(amount * 100)
    return f"${cents // 100}" if cents % 100 == 0 else f"${cents // 100}.{cents % 100:02d}"


def percent_bar_svg(whole: int, pct=None, part=None, sign=1, step: int = 1) -> str:
    """The whole price is 100%; the shaded piece is the part being asked about."""
    width, x0, length, top, bar_height = 520, 30, 460, 70, 50
    share = pct / 100 if pct is not None else part / whole
    shaded = length * share
    parts = [
        f'<rect x="{x0}" y="{top}" width="{length}" height="{bar_height}" fill="#e0e7ff" stroke="#4338ca" stroke-width="2" />',
        f'<rect x="{x0}" y="{top}" width="{shaded:.1f}" height="{bar_height}" fill="#f97316" />',
    ]
    # When the percent is the answer, boxes or a 50% mark would let her count it off the bar.
    finding_percent = pct is None
    for tenth in range(1, 10) if not finding_percent else ():
        x = x0 + length * tenth / 10
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + bar_height}" stroke="#4338ca" stroke-opacity="0.35" />')
    for label, frac in (("0%", 0), ("100%", 1)) if finding_percent else (("0%", 0), ("50%", 0.5), ("100%", 1)):
        parts.append(_text(x0 + length * frac, top + bar_height + 20, label, size=13, fill="#555"))
    parts.append(_text(x0 + length, top - 12, f"100% = {_money(whole)}", size=16, anchor="end",
                       extra='font-weight="bold"', fill="#4338ca"))
    piece = f"{pct}% = ?" if pct is not None else f"{_money(part)} = ?%"
    narrow = shaded < 90
    parts.append(_text(x0 if narrow else x0 + shaded / 2, top - 12, piece, size=16,
                       anchor="start" if narrow else "middle", extra='font-weight="bold"', fill="#c2410c"))

    if pct is not None:
        # Build from 10% when that's not already the answer; otherwise from 1%.
        if pct % 5 == 0 and pct != 10:
            base, count = 10, pct // 10
            build = f"{pct}% = {count} × 10%" if pct % 10 == 0 else (
                f"{pct}% = {count} × 10% + 5% (5% is half of 10%)" if count else "5% is half of 10%")
        else:
            base, build = 1, f"{pct}% = {pct} × 1%"
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
    for i, caption in enumerate(captions):
        parts.append(_text(width / 2, top + bar_height + 56 + i * 24, caption, size=15))
    height = top + bar_height + 56 + len(captions) * 24
    return _svg(width, height, parts)


def hint_steps(hint) -> int:
    """How many hints a problem has; each one shows a bit more."""
    kind = hint.get("kind") if hint else None
    return {"venn": 3, "percent": 2}.get(kind, 1)


def build_svg(hint, step: int = 1) -> str:
    if not hint:
        return ""
    kind = hint.get("kind")
    if kind == "dots":
        return dot_grid_svg(hint["a"], hint["b"])
    if kind == "blocks":
        return base_ten_svg(hint["a"], hint["b"], hint["op"])
    if kind == "venn":
        return factor_venn_svg(hint["a"], hint["b"], step)
    if kind == "percent":
        return percent_bar_svg(hint["whole"], hint.get("pct"), hint.get("part"), hint.get("sign", 1), step)
    return ""
