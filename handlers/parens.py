import random


def generate(quiz):
    formats = ["(a + b) * c", "a * (b - c)", "(a + b) + (c + d)", "(a * b) - (c * d)"]
    chosen = random.choice(formats)
    if chosen == "(a + b) * c":
        quiz.a, quiz.b, quiz.c = random.randint(1, 20), random.randint(1, 20), random.randint(1, 20)
        quiz.solution = (quiz.a + quiz.b) * quiz.c
        quiz.question = f"({quiz.a} + {quiz.b}) * {quiz.c} = ?"
    elif chosen == "a * (b - c)":
        quiz.b, quiz.c, quiz.a = random.randint(5, 20), random.randint(1, 20), random.randint(1, 20)
        quiz.solution = quiz.a * (quiz.b - quiz.c)
        quiz.question = f"{quiz.a} * ({quiz.b} - {quiz.c}) = ?"
    elif chosen == "(a + b) + (c + d)":
        quiz.a, quiz.b, quiz.c, quiz.d = [random.randint(1, 10) for _ in range(4)]
        quiz.solution = (quiz.a + quiz.b) + (quiz.c + quiz.d)
        quiz.question = f"({quiz.a} + {quiz.b}) + ({quiz.c} + {quiz.d}) = ?"
    elif chosen == "(a * b) - (c * d)":
        quiz.a, quiz.b, quiz.c, quiz.d = random.randint(1, 20), random.randint(1, 2), random.randint(1, 2), random.randint(1, 20)
        quiz.solution = (quiz.a * quiz.b) - (quiz.c * quiz.d)
        quiz.question = f"({quiz.a} * {quiz.b}) - ({quiz.c} * {quiz.d}) = ?"
    quiz.clear_plot()
