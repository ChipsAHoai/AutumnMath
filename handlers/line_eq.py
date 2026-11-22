"""Lines in y = mx + b form, answered in pieces: the slope first, then b (where the line crosses the y-axis).
Each piece is its own question, like the LCM follow-ups, and the finished equation is shown at the end."""
import random
from fractions import Fraction

# Slopes that are fractions; kept small so the points stay on the grid.
FRACTION_SLOPES = [Fraction(1, 2), Fraction(-1, 2), Fraction(3, 2), Fraction(-3, 2),
                   Fraction(1, 3), Fraction(-2, 3), Fraction(2, 3), Fraction(-1, 3)]
ANSWER_TIP = "Enter a whole number or a fraction, like -3 or 1/2."


def signed(n) -> str:
    """A number for display, with a real minus sign: −3, 1/2, −2/3."""
    n = Fraction(n)
    return f"−{-n}" if n < 0 else str(n)


def line_text(m, b) -> str:
    """y = 2x − 3, y = −x + 4, y = (1/2)x, written the way a textbook would."""
    m, b = Fraction(m), Fraction(b)
    if m == 1:
        mx = "x"
    elif m == -1:
        mx = "−x"
    else:
        mx = f"{signed(m)}x"
    rest = "" if b == 0 else f" + {b}" if b > 0 else f" − {-b}"
    return f"y = {mx}{rest}"


def _slope():
    if random.random() < 0.3:
        return random.choice(FRACTION_SLOPES)
    return Fraction(random.choice([n for n in range(-5, 6) if n != 0]))


def _as_answer(value):
    """Whole numbers stay ints; fractions are saved as text, the way follow-ups store them."""
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else str(value)


def read_line(quiz):
    """Read the slope and b straight off an equation."""
    m, b = _slope(), random.randint(-9, 9)
    eq = line_text(m, b)
    quiz.question = f"Look at the line {eq}. What is its slope (m)? {ANSWER_TIP}"
    quiz.solution = m if m.denominator > 1 else m.numerator
    quiz.hint = {"kind": "read_line", "m": str(m), "b": b, "ask": "m"}
    quiz.follow_up_questions = [{
        "question": f"The line {eq} has slope {signed(m)}. What is b, where it crosses the y-axis? {ANSWER_TIP}",
        "solution": _as_answer(b),
        "hint": {"kind": "read_line", "m": str(m), "b": b, "ask": "b"},
        "after": f"✅ Yes! {eq} has slope {signed(m)} and crosses the y-axis at {signed(b)}.",
    }]


def two_points(quiz):
    """Find the slope from two points, then b by putting one point into y = mx + b."""
    while True:
        m, b = _slope(), random.randint(-6, 6)
        # x a multiple of the slope's bottom number keeps every y whole; x = 0 would give b away.
        xs = [x for x in range(-8, 9) if x and x % m.denominator == 0 and abs(m * x + b) <= 9]
        if len(xs) >= 2:
            break
    x1, x2 = random.sample(xs, 2)
    y1, y2 = int(m * x1 + b), int(m * x2 + b)
    points = f"({x1}, {y1}) and ({x2}, {y2})"
    quiz.question = f"A line goes through {points}. What is its slope? {ANSWER_TIP}"
    quiz.solution = m if m.denominator > 1 else m.numerator
    quiz.hint = {"kind": "slope", "x1": x1, "y1": y1, "x2": x2, "y2": y2}
    quiz.follow_up_questions = [{
        "question": f"The line through {points} has slope {signed(m)}. "
                    f"In y = mx + b, what is b? {ANSWER_TIP}",
        "solution": _as_answer(b),
        "hint": {"kind": "intercept", "m": str(m), "px": x1, "py": y1},
        "after": f"✅ So the line is {line_text(m, b)}",
    }]


def generate(quiz):
    (read_line if random.random() < 0.35 else two_points)(quiz)
    quiz.clear_plot()
