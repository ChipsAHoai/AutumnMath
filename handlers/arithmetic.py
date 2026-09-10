import random


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
    x, y = random.randint(3, 12), random.randint(3, 12)
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
