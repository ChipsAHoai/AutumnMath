import random
from fractions import Fraction


def generate(quiz):
    num1, den1 = random.randint(1, 20), random.randint(1, 20)
    num2, den2 = random.randint(1, 20), random.randint(1, 20)
    quiz.f1, quiz.f2 = Fraction(num1, den1), Fraction(num2, den2)
    quiz.solution = quiz.f1 + quiz.f2
    quiz.question = f"{quiz.f1} + {quiz.f2} = ? (simplify if possible)"
    quiz.clear_plot()
