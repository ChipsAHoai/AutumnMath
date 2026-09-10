import random
from fractions import Fraction


def build_centimeter_svg(tick_tenth: int) -> str:
    width, height = 520, 120
    margin, usable = 20, 480
    base_y = 70
    ticks = []
    labels = []

    for tenth in range(0, 11):  # 0 to 1.0 cm in 0.1 steps
        x = margin + usable * tenth / 10
        if tenth in (0, 5, 10):
            top = base_y - 35
        else:
            top = base_y - 18
        ticks.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{base_y}" stroke="#222" stroke-width="2" />'
        )

        if tenth in (0, 5, 10):
            label = "1" if tenth == 10 else "1/2" if tenth == 5 else "0"
            labels.append(
                f'<text x="{x:.2f}" y="{base_y + 25}" font-size="14" text-anchor="middle" fill="#222">{label}</text>'
            )

    caret_x = margin + usable * tick_tenth / 10
    caret = f'<polygon points="{caret_x:.2f},{base_y + 10} {caret_x - 8:.2f},{base_y + 30} {caret_x + 8:.2f},{base_y + 30}" fill="crimson" />'

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />',
        f'<text x="{width - 60}" y="20" font-size="14" text-anchor="end" fill="#444">cm</text>',
        f'<line x1="{margin}" y1="{base_y}" x2="{margin + usable}" y2="{base_y}" stroke="#222" stroke-width="3" />',
        *ticks,
        *labels,
        caret,
        "</svg>"
    ]
    return "".join(svg_parts)


def generate(quiz):
    tick_tenth = random.randint(1, 10)  # 0.1 cm increments from 0 to 1 cm
    quiz.solution = Fraction(tick_tenth, 10)  # centimeters
    quiz.question = "What measurement in centimeters is marked? (enter decimal or fraction)"
    try:
        quiz.question_svg = build_centimeter_svg(tick_tenth)
    except Exception:
        quiz.question_svg = None
    quiz.clear_plot()
