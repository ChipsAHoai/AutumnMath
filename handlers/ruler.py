import random
from fractions import Fraction


def build_ruler_svg(tick_index: int) -> str:
    width, height = 520, 120
    margin, usable = 20, 480
    base_y = 70
    ticks = []
    labels = []

    for i in range(17):
        x = margin + usable * i / 16
        if i % 16 == 0:
            top = base_y - 40
        elif i % 8 == 0:
            top = base_y - 30
        elif i % 4 == 0:
            top = base_y - 20
        elif i % 2 == 0:
            top = base_y - 15
        else:
            top = base_y - 10
        ticks.append(
            f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{base_y}" stroke="#222" stroke-width="2" />'
        )

        if i % 4 == 0:
            frac = Fraction(i, 16)
            label = "1" if frac == 1 else str(frac)
            labels.append(
                f'<text x="{x:.2f}" y="{base_y + 25}" font-size="14" text-anchor="middle" fill="#222">{label}</text>'
            )

    caret_x = margin + usable * tick_index / 16
    caret = f'<polygon points="{caret_x:.2f},{base_y + 10} {caret_x - 8:.2f},{base_y + 30} {caret_x + 8:.2f},{base_y + 30}" fill="crimson" />'

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="white" />',
        f'<text x="{width - 60}" y="20" font-size="14" text-anchor="end" fill="#444">inches</text>',
        f'<line x1="{margin}" y1="{base_y}" x2="{margin + usable}" y2="{base_y}" stroke="#222" stroke-width="3" />',
        *ticks,
        *labels,
        caret,
        "</svg>"
    ]
    return "".join(svg_parts)


def generate(quiz):
    tick_index = random.randint(1, 16)  # avoid 0 for a non-trivial question
    quiz.solution = Fraction(tick_index, 16)
    quiz.question = "What measurement is marked? (enter fraction)"
    try:
        quiz.question_svg = build_ruler_svg(tick_index)
    except Exception:
        quiz.question_svg = None
    quiz.clear_plot()
