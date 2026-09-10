import random


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
    quiz.clear_plot()
