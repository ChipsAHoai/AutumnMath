import random

from .balance import X, K


def generate(quiz):
    x_val = random.randint(1, 20)
    quiz.a = random.randint(1, 20)
    quiz.c = random.randint(quiz.a + 1, quiz.a + 4)
    quiz.b = random.randint(0, 20)
    left = quiz.a * x_val + quiz.b
    right = quiz.c * x_val
    quiz.d = right - left
    quiz.solution = x_val
    quiz.question = f"{quiz.a}x + {quiz.b} = {quiz.c}x - {quiz.d}"
    left = [X(quiz.a)] + ([K(quiz.b)] if quiz.b else [])
    right = [X(quiz.c)] + ([K(-quiz.d)] if quiz.d else [])
    quiz.hint = {"kind": "scale", "L": left, "R": right}
    quiz.clear_plot()
