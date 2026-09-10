import random
from fractions import Fraction
import matplotlib.pyplot as plt


def generate(quiz):
    x1, y1 = random.randint(-10, 10), random.randint(-10, 10)
    x2, y2 = random.randint(-10, 10), random.randint(-10, 10)
    while x2 == x1:
        x2 = random.randint(-10, 10)
    delta_y, delta_x = y2 - y1, x2 - x1
    quiz.solution = Fraction(delta_y, delta_x)
    quiz.question = f"Slope through ({x1},{y1}) and ({x2},{y2}) = ? (fraction)"

    if quiz.plot:
        with quiz.plot:
            plt.clf()
            plt.axhline(0, color='gray', linewidth=0.8)
            plt.axvline(0, color='gray', linewidth=0.8)
            plt.grid(True, linestyle='--', linewidth=0.5)
            plt.plot([x1, x2], [y1, y2], color='crimson', linewidth=2)
            plt.scatter([x1, x2], [y1, y2], color='dodgerblue', zorder=5)
            plt.text(x1, y1, f'({x1},{y1})', fontsize=9)
            plt.text(x2, y2, f'({x2},{y2})', fontsize=9)
            plt.title("Slope Between Two Points")
            plt.tight_layout()
        quiz.plot.update()
