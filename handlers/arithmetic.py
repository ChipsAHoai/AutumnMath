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


def restore_hint(quiz):
    """Rebuild the picture hint for a question saved before hints existed."""
    match = re.fullmatch(r"(\d+) ([+×-]) (\d+) = \?", quiz.question)
    if not match:
        return
    x, operator, y = int(match[1]), match[2], int(match[3])
    if operator == "×":
        quiz.hint = {"kind": "dots", "a": x, "b": y}
    else:
        quiz.hint = {"kind": "blocks", "a": x, "b": y, "op": operator}


def plus(quiz):
    x, y = random.randint(1, 100), random.randint(1, 100)
    quiz.solution = x + y
    quiz.question = f"{x} + {y} = ?"
    quiz.hint = {"kind": "blocks", "a": x, "b": y, "op": "+"}
    quiz.clear_plot()


def minus(quiz):
    x = random.randint(1, 100)
    y = random.randint(1, x)
    quiz.solution = x - y
    quiz.question = f"{x} - {y} = ?"
    quiz.hint = {"kind": "blocks", "a": x, "b": y, "op": "-"}
    quiz.clear_plot()


def times(quiz):
    lower, upper = quiz.multiplication_range
    x, y = random.randint(lower, upper), random.randint(lower, upper)
    quiz.solution = x * y
    quiz.question = f"{x} × {y} = ?"
    quiz.hint = {"kind": "dots", "a": x, "b": y}
    quiz.clear_plot()


def divide(quiz):
    divisor = random.randint(2, 12)
    y = random.randint(2, 9)
    x = divisor * y
    quiz.solution = divisor
    quiz.question = f"{x} ÷ {y} = ?"
    quiz.clear_plot()
