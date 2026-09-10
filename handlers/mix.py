import random


def generate(quiz):
    quiz.a, quiz.b, quiz.c = random.randint(1, 20), random.randint(1, 20), random.randint(1, 20)
    quiz.solution = (quiz.a + quiz.b) * quiz.c
    quiz.question = f"({quiz.a} + {quiz.b}) * {quiz.c} = ?"
    quiz.clear_plot()
