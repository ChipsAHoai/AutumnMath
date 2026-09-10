import random


def generate(quiz):
    formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
    quiz.algebra_format = random.choice(formats)

    if quiz.algebra_format == "a*x+b=c":
        quiz.a, x_val, quiz.b = random.randint(1, 20), random.randint(1, 20), random.randint(1, 20)
        quiz.c = quiz.a * x_val + quiz.b
        quiz.solution = x_val
        quiz.question = f"{quiz.a} * __ + {quiz.b} = {quiz.c}"

    elif quiz.algebra_format == "a*x-b=c":
        quiz.a, x_val, quiz.b = random.randint(1, 20), random.randint(1, 20), random.randint(1, 20)
        quiz.c = quiz.a * x_val - quiz.b
        quiz.solution = x_val
        quiz.question = f"{quiz.a} * __ - {quiz.b} = {quiz.c}"

    elif quiz.algebra_format == "a+b*x=c":
        quiz.b, x_val, quiz.a = random.randint(1, 20), random.randint(1, 20), random.randint(1, 20)
        quiz.c = quiz.a + quiz.b * x_val
        quiz.solution = x_val
        quiz.question = f"{quiz.a} + {quiz.b} * __ = {quiz.c}"

    quiz.clear_plot()
