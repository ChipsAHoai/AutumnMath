import random
import re


def vertical_question(question):
    """Align place values in addition/subtraction, including restored questions."""
    match = re.fullmatch(r"(\d+) ([+-]) (\d+) = \?", question)
    if not match:
        return question
    first, operator, second = match.groups()
    if operator == '+' and len(second) > len(first):
        first, second = second, first
    width = max(len(first), len(second))
    return f"  {first:>{width}}\n{operator} {second:>{width}}\n{'─' * (width + 2)}"


def plus(quiz):
    x, y = random.randint(1, 100), random.randint(1, 100)
    quiz.solution = x + y
    quiz.question = f"{x} + {y} = ?"
    quiz.clear_plot()


def minus(quiz):
    x = random.randint(1, 100)
    y = random.randint(1, x)
    quiz.solution = x - y
    quiz.question = f"{x} - {y} = ?"
    quiz.clear_plot()


def times(quiz):
    lower, upper = quiz.multiplication_range
    x, y = random.randint(lower, upper), random.randint(lower, upper)
    quiz.solution = x * y
    quiz.question = f"{x} × {y} = ?"
    quiz.clear_plot()


def divide(quiz):
    divisor = random.randint(2, 12)
    y = random.randint(2, 9)
    x = divisor * y
    quiz.solution = divisor
    quiz.question = f"{x} ÷ {y} = ?"
    quiz.clear_plot()
