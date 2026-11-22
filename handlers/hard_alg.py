import random
from fractions import Fraction

from .balance import X, K, FX, G, D


def _term(n):
    """Format a constant that follows another term: '+ 5' or '- 5'."""
    return f"+ {n}" if n >= 0 else f"- {-n}"


def generate(quiz):
    formats = ["a(x+b)=cx+d", "a(x-b)+c=d(x+e)", "(x+b)/a=c", "p/q x+b=c", "ax+b=c frac"]
    quiz.algebra_format = random.choice(formats)

    if quiz.algebra_format == "a(x+b)=cx+d":
        # a(x + b) = cx + d  ->  distribute, then collect x on one side
        quiz.d = 0
        while quiz.d == 0:
            x_val = random.randint(-10, 12)
            quiz.a = random.randint(2, 9)
            quiz.b = random.choice([n for n in range(-9, 10) if n != 0])
            quiz.c = random.choice([n for n in range(1, 12) if n != quiz.a])
            quiz.d = quiz.a * (x_val + quiz.b) - quiz.c * x_val
        quiz.solution = x_val
        quiz.question = f"{quiz.a}(x {_term(quiz.b)}) = {quiz.c}x {_term(quiz.d)}"
        left, right = [G(quiz.a, [X(1), K(quiz.b)])], [X(quiz.c), K(quiz.d)]

    elif quiz.algebra_format == "a(x-b)+c=d(x+e)":
        quiz.c = 0
        while quiz.c == 0:
            x_val = random.randint(-8, 12)
            quiz.a = random.randint(2, 9)
            d = random.choice([n for n in range(2, 9) if n != quiz.a])
            quiz.b = random.randint(1, 9)
            e = random.randint(1, 9)
            quiz.c = d * (x_val + e) - quiz.a * (x_val - quiz.b)
        quiz.d = d
        quiz.solution = x_val
        quiz.question = f"{quiz.a}(x - {quiz.b}) {_term(quiz.c)} = {d}(x + {e})"
        left, right = [G(quiz.a, [X(1), K(-quiz.b)]), K(quiz.c)], [G(d, [X(1), K(e)])]

    elif quiz.algebra_format == "(x+b)/a=c":
        # (x + b) / a = c  ->  undo the division first
        quiz.a = random.randint(2, 9)
        quiz.c = random.randint(-6, 10)
        quiz.b = random.choice([n for n in range(-12, 13) if n != 0])
        quiz.solution = quiz.a * quiz.c - quiz.b
        quiz.question = f"(x {_term(quiz.b)}) / {quiz.a} = {quiz.c}"
        left, right = [D(quiz.a, [X(1), K(quiz.b)])], [K(quiz.c)]

    elif quiz.algebra_format == "p/q x+b=c":
        # (p/q)x + b = c with x a multiple of q, so the answer is a whole number
        q = random.randint(2, 8)
        p = random.choice([n for n in range(1, q * 2) if Fraction(n, q).denominator == q])
        x_val = q * random.randint(-4, 6)
        quiz.b = random.choice([n for n in range(-15, 16) if n != 0])
        quiz.c = int(Fraction(p, q) * x_val) + quiz.b
        quiz.solution = x_val
        quiz.question = f"({p}/{q})x {_term(quiz.b)} = {quiz.c}"
        left, right = [FX(p, q), K(quiz.b)], [K(quiz.c)]

    elif quiz.algebra_format == "ax+b=c frac":
        # a whole-number equation whose answer is a fraction, e.g. 4x + 3 = 6 -> 3/4
        quiz.a = random.randint(2, 9)
        num = random.choice([n for n in range(-20, 21) if n % quiz.a != 0])
        quiz.solution = Fraction(num, quiz.a)
        quiz.b = random.choice([n for n in range(-15, 16) if n != 0])
        quiz.c = num + quiz.b
        quiz.question = f"{quiz.a}x {_term(quiz.b)} = {quiz.c}"
        left, right = [X(quiz.a), K(quiz.b)], [K(quiz.c)]

    # The balance-scale hint walks through the moves one at a time.
    quiz.hint = {"kind": "scale", "L": left, "R": right}
    quiz.clear_plot()
