import random
import re
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
    quiz.slope_points = [(x1, y1), (x2, y2)]
    draw_plot(quiz)


def restore(quiz):
    if not quiz.slope_points:
        # Older saved quizzes only stored the coordinates in the question text.
        points = re.findall(r"\((-?\d+),\s*(-?\d+)\)", quiz.question)
        if len(points) != 2:
            raise ValueError("Saved slope question has no coordinates")
        quiz.slope_points = [tuple(map(int, point)) for point in points]
    draw_plot(quiz)


def draw_plot(quiz):
    (x1, y1), (x2, y2) = quiz.slope_points

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
