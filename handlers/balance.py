"""Balance-scale hints for equations: solve one move at a time, doing the same thing to both sides.

Terms are plain dicts so hints can be saved with the rest of the quiz:
  {"t": "x", "n": 3}                      3x
  {"t": "k", "v": -5}                     the number −5
  {"t": "fr", "num": 7, "den": 3}         the fraction 7/3
  {"t": "fx", "p": 2, "q": 3}             (2/3)x
  {"t": "grp", "m": 4, "inner": [...]}    4(x + b): four identical bags
  {"t": "div", "d": 5, "inner": [...]}    (x + b) / 5
"""
from math import gcd


def X(n): return {"t": "x", "n": n}
def K(v): return {"t": "k", "v": v}
def FR(num, den): return {"t": "fr", "num": num, "den": den}
def FX(p, q): return {"t": "fx", "p": p, "q": q}
def G(m, inner): return {"t": "grp", "m": m, "inner": inner}
def D(d, inner): return {"t": "div", "d": d, "inner": inner}


def is_x(term):
    return term["t"] in ("x", "fx")


def _term_text(term):
    t = term["t"]
    if t == "x":
        return False, "x" if term["n"] == 1 else f"{term['n']}x"
    if t == "k":
        return term["v"] < 0, str(abs(term["v"]))
    if t == "fr":
        return term["num"] < 0, f"{abs(term['num'])}/{term['den']}"
    if t == "fx":
        return False, f"({term['p']}/{term['q']})x"
    if t == "grp":
        return False, f"{term['m']}({side_text(term['inner'])})"
    return False, f"({side_text(term['inner'])}) / {term['d']}"


def side_text(terms):
    if not terms:
        return "0"
    out = []
    for i, term in enumerate(terms):
        neg, s = _term_text(term)
        out.append(("−" if neg else "") + s if i == 0 else (" − " if neg else " + ") + s)
    return "".join(out)


def eq_text(left, right):
    return f"{side_text(left)} = {side_text(right)}"


def _x_count(side):
    return sum(t["n"] for t in side if t["t"] == "x")


def _k_sum(side):
    return sum(t["v"] for t in side if t["t"] == "k")


def _x_label(n):
    return "x" if n == 1 else f"{n}x"


def _or_zero(side):
    return side or [K(0)]


def _move_x(left, right):
    m = min(_x_count(left), _x_count(right))

    def take(side):
        kept = [X(t["n"] - m) if t["t"] == "x" else t for t in side]
        return _or_zero([t for t in kept if not (t["t"] == "x" and t["n"] == 0)])
    return {"L": take(left), "R": take(right), "take": m,
            "move": f"Take {_x_label(m)} off both sides (the smaller pile of x's)"}


def _move_const(left, right):
    x_left = any(is_x(t) for t in left)
    xs, other = (left, right) if x_left else (right, left)
    k = _k_sum(xs)
    new_xs = [t for t in xs if t["t"] != "k"]
    new_other = [K(_k_sum(other) - k)]
    move = f"Take {k} away from both sides" if k > 0 else f"Add {-k} to both sides (it cancels the −{-k})"
    left, right = (new_xs, new_other) if x_left else (new_other, new_xs)
    return {"L": left, "R": right, "move": move}


def _move_divide(left, right):
    x_left = any(is_x(t) for t in left)
    xs, other = (left, right) if x_left else (right, left)
    n, v = _x_count(xs), _k_sum(other)
    g = gcd(v, n)
    result = K(v // n) if v % n == 0 else FR(v // g, n // g)
    move = f"Split both sides into {n} equal groups (÷ {n})"
    return {"L": [X(1)], "R": [result], "move": move} if x_left else {"L": [result], "R": [X(1)], "move": move}


def _move_open(left, right):
    def open_side(side):
        out = []
        for t in side:
            out.extend([X(t["m"]), K(t["m"] * t["inner"][1]["v"])] if t["t"] == "grp" else [t])
        return out
    def describe(g):
        b = g["inner"][1]["v"]
        shown = f"(−{-b})" if b < 0 else str(b)
        return f"{g['m']} bags of ({side_text(g['inner'])}) = {_x_label(g['m'])} and {g['m']} × {shown}"
    groups = [t for t in left + right if t["t"] == "grp"]
    return {"L": open_side(left), "R": open_side(right),
            "move": "Open the parentheses: " + "; ".join(describe(g) for g in groups)}


def _move_times_div(left, right):
    d = left[0]["d"]
    return {"L": left[0]["inner"], "R": [K(_k_sum(right) * d)],
            "move": f"Multiply both sides by {d} (undoes the ÷ {d})"}


def _move_times_frac(left, right):
    f = next(t for t in left if t["t"] == "fx")
    return {"L": [X(f["p"])], "R": [K(_k_sum(right) * f["q"])],
            "move": f"Multiply both sides by {f['q']}: {f['q']} groups of ({f['p']}/{f['q']})x make {_x_label(f['p'])}"}


def solve(left, right):
    """Every state from the starting equation to x = answer; each later state records the move that made it."""
    states = [{"L": left, "R": right, "move": None}]
    for _ in range(8):
        cur = states[-1]
        everything = cur["L"] + cur["R"]
        x_side = cur["L"] if any(is_x(t) for t in cur["L"]) else cur["R"]
        if any(t["t"] == "grp" for t in everything):
            nxt = _move_open(cur["L"], cur["R"])
        elif any(t["t"] == "div" for t in everything):
            nxt = _move_times_div(cur["L"], cur["R"])
        elif any(is_x(t) for t in cur["L"]) and any(is_x(t) for t in cur["R"]):
            nxt = _move_x(cur["L"], cur["R"])
        elif any(t["t"] == "k" for t in x_side):
            nxt = _move_const(cur["L"], cur["R"])
        elif any(t["t"] == "fx" for t in everything):
            nxt = _move_times_frac(cur["L"], cur["R"])
        elif _x_count(x_side) > 1:
            nxt = _move_divide(cur["L"], cur["R"])
        else:
            break
        states.append(nxt)
    return states


def evaluate(terms, x):
    total = 0
    for t in terms:
        kind = t["t"]
        if kind == "x":
            total += t["n"] * x
        elif kind == "k":
            total += t["v"]
        elif kind == "fr":
            total += t["num"] / t["den"]
        elif kind == "fx":
            total += t["p"] * x / t["q"]
        elif kind == "grp":
            total += t["m"] * evaluate(t["inner"], x)
        else:
            total += evaluate(t["inner"], x) / t["d"]
    return total
