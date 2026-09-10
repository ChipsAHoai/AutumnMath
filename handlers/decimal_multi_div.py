import random
from fractions import Fraction


def generate(quiz):
    multiplication_pool = [
        "0.05", "0.7", "0.08", "1.25", "2.40", "0.64", "3.5",
        "0.125", "2.05", "4.08", "0.500", "3.040", "5.020"
    ]
    divisor_pool = [
        "0.05", "0.1", "0.125", "0.2", "0.25", "0.4", "0.5",
        "0.8", "1.0", "1.25", "2.0", "2.5", "5.0"
    ]

    def pick_decimal(pool):
        base = random.choice(pool)
        if "." in base:
            decimals = base.split(".")[1]
            if len(decimals) < 3 and random.random() < 0.4:
                base = base + "0"
        return base, Fraction(base)

    op_symbol = random.choice(["×", "÷"])
    left_text, left_value = pick_decimal(multiplication_pool)
    if op_symbol == "×":
        right_text, right_value = pick_decimal(multiplication_pool)
        quiz.solution = left_value * right_value
    else:
        right_text, right_value = pick_decimal(divisor_pool)
        quiz.solution = left_value / right_value
    quiz.question = f"{left_text} {op_symbol} {right_text} = ? (enter decimal)"
    quiz.clear_plot()
