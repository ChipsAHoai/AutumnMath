import os
import random
import time
import math
from fractions import Fraction

import matplotlib.pyplot as plt
from nicegui import ui, app


# ---------- BASE QUIZ CLASS ----------
class MathQuizGame:
    def __init__(self, total_problems=20, allowed_ops=None, name="player"):
        self.total_problems = total_problems
        self.allowed_ops = allowed_ops or ["+"]
        self.name = name

        self.current_index = 0
        self.wrong = 0
        self.start_time = None

        self.question = ""
        self.solution = None
        self.symbol = ""
        self.algebra_format = ""

        self.input_text = ""
        self.feedback = ""
        self.feedback_color = None
        self.question_svg = None

        self.plot = None  # slope plot
        self.svg_container = None  # ruler visualization

        # store vars for algebra/parens
        self.a = self.b = self.c = self.d = 0
        self.f1 = self.f2 = None

        # UI elements (initialized later in make_quiz_page)
        self.start_button = None
        self.progress_label = None
        self.question_label = None
        self.feedback_label = None
        self.answer_label = None

    def start(self):
        # Only reset if not continuing a restored quiz
        if self.current_index == 0:
            self.current_index = 0
            self.wrong = 0
            self.start_time = time.time()
            self.generate_problem()

        self.update_ui()
        if self.start_button and self.start_button.visible:
            self.start_button.visible = False
            self.start_button.update()

    def generate_problem(self):
        self.symbol = random.choice(self.allowed_ops)
        self.solution = None
        self.question = ""
        self.question_svg = None

        # ---- Arithmetic ----
        if self.symbol == "+":
            x, y = random.randint(1, 100), random.randint(1, 100)
            self.solution = x + y
            self.question = f"{x} + {y} = ?"
            self.clear_plot()

        elif self.symbol == "-":
            x = random.randint(1, 100)
            y = random.randint(1, x)
            self.solution = x - y
            self.question = f"{x} - {y} = ?"
            self.clear_plot()

        elif self.symbol == "x":
            x, y = random.randint(3, 12), random.randint(3, 12)
            self.solution = x * y
            self.question = f"{x} × {y} = ?"
            self.clear_plot()

        elif self.symbol == "÷":
            divisor = random.randint(2, 12)
            y = random.randint(2, 9)
            x = divisor * y
            self.solution = divisor
            self.question = f"{x} ÷ {y} = ?"
            self.clear_plot()

        # ---- Fractions ----
        elif self.symbol == "fraction":
            num1, den1 = random.randint(1, 20), random.randint(1, 20)
            num2, den2 = random.randint(1, 20), random.randint(1, 20)
            self.f1, self.f2 = Fraction(num1, den1), Fraction(num2, den2)
            self.solution = self.f1 + self.f2
            self.question = f"{self.f1} + {self.f2} = ? (simplify if possible)"
            self.clear_plot()

        # ---- Algebra ----
        elif self.symbol == "alg":
            formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
            self.algebra_format = random.choice(formats)

            if self.algebra_format == "a*x+b=c":
                self.a, x_val, self.b = random.randint(
                    1, 20), random.randint(1, 20), random.randint(1, 20)
                self.c = self.a * x_val + self.b
                self.solution = x_val
                self.question = f"{self.a} * __ + {self.b} = {self.c}"

            elif self.algebra_format == "a*x-b=c":
                self.a, x_val, self.b = random.randint(
                    1, 20), random.randint(1, 20), random.randint(1, 20)
                self.c = self.a * x_val - self.b
                self.solution = x_val
                self.question = f"{self.a} * __ - {self.b} = {self.c}"

            elif self.algebra_format == "a+b*x=c":
                self.b, x_val, self.a = random.randint(
                    1, 20), random.randint(1, 20), random.randint(1, 20)
                self.c = self.a + self.b * x_val
                self.solution = x_val
                self.question = f"{self.a} + {self.b} * __ = {self.c}"

            self.clear_plot()

        # ---- Mixed expression ----
        elif self.symbol == "mix":
            self.a, self.b, self.c = random.randint(
                1, 20), random.randint(1, 20), random.randint(1, 20)
            self.solution = (self.a + self.b) * self.c
            self.question = f"({self.a} + {self.b}) * {self.c} = ?"
            self.clear_plot()

        # ---- Multi-step algebra ----
        elif self.symbol == "multi_alg":
            x_val = random.randint(1, 20)
            self.a = random.randint(1, 20)
            self.c = random.randint(self.a + 1, self.a + 4)
            self.b = random.randint(0, 20)
            left = self.a * x_val + self.b
            right = self.c * x_val
            self.d = right - left
            self.solution = x_val
            self.question = f"{self.a}x + {self.b} = {self.c}x - {self.d}"
            self.clear_plot()

        # ---- Parentheses ----
        elif self.symbol == "parens":
            formats = ["(a + b) * c", "a * (b - c)",
                       "(a + b) + (c + d)", "(a * b) - (c * d)"]
            chosen = random.choice(formats)
            if chosen == "(a + b) * c":
                self.a, self.b, self.c = random.randint(
                    1, 20), random.randint(1, 20), random.randint(1, 20)
                self.solution = (self.a + self.b) * self.c
                self.question = f"({self.a} + {self.b}) * {self.c} = ?"
            elif chosen == "a * (b - c)":
                self.b, self.c, self.a = random.randint(
                    5, 20), random.randint(1, 20), random.randint(1, 20)
                self.solution = self.a * (self.b - self.c)
                self.question = f"{self.a} * ({self.b} - {self.c}) = ?"
            elif chosen == "(a + b) + (c + d)":
                self.a, self.b, self.c, self.d = [
                    random.randint(1, 10) for _ in range(4)]
                self.solution = (self.a + self.b) + (self.c + self.d)
                self.question = f"({self.a} + {self.b}) + ({self.c} + {self.d}) = ?"
            elif chosen == "(a * b) - (c * d)":
                self.a, self.b, self.c, self.d = random.randint(1, 20), random.randint(
                    1, 2), random.randint(1, 2), random.randint(1, 20)
                self.solution = (self.a * self.b) - (self.c * self.d)
                self.question = f"({self.a} * {self.b}) - ({self.c} * {self.d}) = ?"
            self.clear_plot()

        elif self.symbol == "decimal_multi_div":
            # curated pools keep decimal variety while avoiding repeating results on division
            multiplication_pool = [
                "0.05", "0.7", "0.08", "1.25", "2.40", "0.64", "3.5",
                "0.125", "2.05", "4.08", "0.500", "3.040", "5.020"
            ]
            divisor_pool = [
                "0.05", "0.1", "0.125", "0.2", "0.25", "0.4", "0.5",
                "0.8", "1.0", "1.25", "2.0", "2.5", "5.0"
            ]

            def pick_decimal(pool):
                base = random.choice(pool)
                if "." in base:
                    decimals = base.split(".")[1]
                    if len(decimals) < 3 and random.random() < 0.4:
                        base = base + "0"
                return base, Fraction(base)

            op_symbol = random.choice(["×", "÷"])
            left_text, left_value = pick_decimal(multiplication_pool)
            if op_symbol == "×":
                right_text, right_value = pick_decimal(multiplication_pool)
                self.solution = left_value * right_value
            else:
                right_text, right_value = pick_decimal(divisor_pool)
                self.solution = left_value / right_value
            self.question = f"{left_text} {op_symbol} {right_text} = ? (enter decimal)"
            self.clear_plot()

        # ---- Slope ----
        elif self.symbol == "slope":
            x1, y1 = random.randint(-10, 10), random.randint(-10, 10)
            x2, y2 = random.randint(-10, 10), random.randint(-10, 10)
            while x2 == x1:
                x2 = random.randint(-10, 10)
            delta_y, delta_x = y2 - y1, x2 - x1
            self.solution = Fraction(delta_y, delta_x)
            self.question = f"Slope through ({x1},{y1}) and ({x2},{y2}) = ? (fraction)"

            if self.plot:
                with self.plot:
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
                self.plot.update()

        # ---- Ruler measurement ----
        elif self.symbol == "ruler":
            tick_index = random.randint(1, 16)  # avoid 0 for a non-trivial question
            self.solution = Fraction(tick_index, 16)
            self.question = "What measurement is marked? (enter fraction)"
            self.question_svg = self.build_ruler_svg(tick_index)
            self.clear_plot()

        # ---- Centimeter ruler ----
        elif self.symbol == "cm_ruler":
            tick_tenth = random.randint(1, 10)  # 0.1 cm increments from 0 to 1 cm
            self.solution = Fraction(tick_tenth, 10)  # centimeters
            self.question = "What measurement in centimeters is marked? (enter decimal or fraction)"
            self.question_svg = self.build_centimeter_svg(tick_tenth)
            self.clear_plot()

    def clear_plot(self):
        if self.plot:
            with self.plot:
                plt.clf()
            self.plot.update()

    def build_ruler_svg(self, tick_index: int) -> str:
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

    def build_centimeter_svg(self, tick_tenth: int) -> str:
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
                label = "1" if tenth == 10 else "0.5" if tenth == 5 else "0"
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

    def check_answer(self):
        user_input = self.input_text.strip()
        correct = False
        self.feedback_color = None

        try:
            if self.symbol in ["fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler"]:
                if self.symbol == "ruler":
                    if "/" not in user_input:
                        raise ValueError("Fraction required for ruler")
                    num_str, den_str = user_input.split("/", 1)
                    num, den = int(num_str), int(den_str)
                    if math.gcd(num, den) != 1:
                        self.feedback = "Use simplest form (e.g., 1/4 instead of 2/8)."
                        self.feedback_color = "#8b0000"
                        self.input_text = ""
                        self.update_ui()
                        return
                    answer = Fraction(num, den)
                elif self.symbol == "cm_ruler":
                    if "/" in user_input:
                        num_str, den_str = user_input.split("/", 1)
                        num, den = int(num_str), int(den_str)
                        if math.gcd(num, den) != 1:
                            self.feedback = "Use simplest form (e.g., 1/2 instead of 5/10)."
                            self.feedback_color = "#8b0000"
                            self.input_text = ""
                            self.update_ui()
                            return
                        answer = Fraction(num, den)
                    else:
                        try:
                            answer = Fraction(user_input)
                        except ValueError:
                            answer = Fraction(float(user_input))
                else:
                    try:
                        answer = Fraction(user_input)
                    except ValueError:
                        answer = Fraction(float(user_input))
                correct = (answer == self.solution)
            else:
                answer = int(user_input)
                correct = (answer == self.solution)
        except Exception:
            self.feedback = "❌ Invalid input"
            self.input_text = ""
            self.update_ui()
            return

        if correct:
            ui.notify(f"Great Job {self.name.capitalize()}!", type='positive')
            self.feedback = "✅ Correct!"
            self.input_text = ""
            self.update_ui()          # immediate visual feedback

            # small pause so user can see "Correct!" message before next problem
            def next_problem():
                self.current_index += 1
                if self.current_index < self.total_problems:
                    self.feedback = ""  # clear old feedback
                    self.generate_problem()
                else:
                    self.end_game()
                self.update_ui()

            ui.timer(0.6, next_problem, once=True)  # wait 0.6s before next question

        else:
            ui.notify(f"Try Again {self.name.capitalize()}!", type='negative')
            self.feedback = "❌ Try again!"
            self.wrong += 1
            self.input_text = ""
            self.update_ui()

        # --- save progress ---
        app.storage.user[self.name] = {
            "current_index": self.current_index,
            "wrong": self.wrong,
            "question": self.question,
            "solution": str(self.solution),
            "symbol": self.symbol,
            "start_time": self.start_time,
        }

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        self.question = f"🎉 Finished! Time: {total_time}s, Wrong: {self.wrong}"
        self.feedback = ""
        self.clear_plot()
        app.storage.user.pop(self.name, None)

        os.makedirs("scores", exist_ok=True)
        with open(os.path.join("scores", f"{self.name}_scores.txt"), "a") as f:
            f.write(f"{time.ctime()}: Time {total_time}s, Wrong {self.wrong}\n")

        if self.start_button:
            self.start_button.visible = True
            self.start_button.update()

    def update_ui(self):
        if self.progress_label:
            self.progress_label.set_text(
                f"{self.current_index} out of {self.total_problems}")
        if self.question_label:
            self.question_label.set_text(self.question)
        if self.feedback_label:
            self.feedback_label.set_text(self.feedback)
            if self.feedback_color:
                self.feedback_label.style(f"color: {self.feedback_color}")
            else:
                self.feedback_label.style("")  # reset to default
        if self.answer_label:
            self.answer_label.set_text(self.input_text)
        if self.svg_container:
            self.svg_container.set_content(self.question_svg or "")


# keypad helpers
def add_char(quiz: MathQuizGame, ch: str):
    quiz.input_text += ch
    if quiz.answer_label:
        quiz.answer_label.set_text(quiz.input_text)


def clear_input(quiz: MathQuizGame):
    quiz.input_text = ""
    if quiz.answer_label:
        quiz.answer_label.set_text("")


# ---------- PAGE FACTORY ----------
def make_quiz_page(total_problems: int, name: str, ops: list):
    @ui.page(f'/{name}')
    def page():
        quiz = MathQuizGame(total_problems=total_problems,
                            allowed_ops=ops, name=name)

        # --- try to restore saved progress ---
        # placeholder until client connects
        quiz.question = "Loading..."
        quiz.update_ui()

        def restore_progress():
            try:
                saved = app.storage.user.get(name)
            except RuntimeError:
                saved = None

            if saved:
                quiz.current_index = saved.get("current_index", 0)
                quiz.wrong = saved.get("wrong", 0)
                quiz.question = saved.get("question", "")
                sol = saved.get("solution", "")
                quiz.solution = Fraction(sol) if "/" in sol else int(sol) if sol.isdigit() else None
                quiz.symbol = saved.get("symbol", "")
                quiz.start_time = saved.get("start_time", time.time())
                quiz.feedback = "⏪ Progress restored!"
                # rebuild SVGs for ruler questions on restore
                try:
                    if quiz.symbol == "ruler" and isinstance(quiz.solution, Fraction):
                        quiz.question_svg = quiz.build_ruler_svg(int(quiz.solution * 16))
                    elif quiz.symbol == "cm_ruler" and isinstance(quiz.solution, Fraction):
                        quiz.question_svg = quiz.build_centimeter_svg(int(quiz.solution * 10))
                except Exception:
                    quiz.question_svg = None
                quiz.update_ui()
                if quiz.start_button:
                    quiz.start_button.visible = False
                    quiz.start_button.update()
            else:
                quiz.question = "Press ▶️ Start Quiz to begin"
                quiz.update_ui()

        with ui.row().classes("items-start justify-start w-full h-screen p-6 gap-12"):
            with ui.column().classes("items-start"):
                ui.label(f"Math Quiz for {name.capitalize()}").classes(
                    "text-3xl font-bold mb-6"
                )

                quiz.progress_label = ui.label("").classes("text-xl mb-2")
                quiz.feedback_label = ui.label("").classes("text-xl mb-2")
                quiz.question_label = ui.label("").classes("text-2xl mb-2")
                quiz.answer_label = ui.label("").classes(
                    "text-2xl font-mono mb-4 h-8"
                )

                # ✅ Keypad now evenly aligned and centered
                keypad_col = ui.column().classes("items-center gap-2 mt-4 scale-90")
                with keypad_col:
                    for row in [
                        ["1", "2", "3"],
                        ["4", "5", "6"],
                        ["7", "8", "9"],
                        ["0", ".", "/"],
                        ["-", "C", "Enter"]
                    ]:
                        with ui.row().classes("gap-3 justify-center"):
                            for key in row:
                                label = "CLEAR" if key == "C" else "ENTER" if key == "Enter" else key
                                btn_class = (
                                    "bg-red-500" if key == "C"
                                    else "bg-green-500" if key == "Enter"
                                    else "bg-blue-500"
                                )
                                ui.button(label,
                                        on_click=(lambda q=quiz: clear_input(q))
                                        if key == "C"
                                        else (lambda q=quiz: q.check_answer())
                                        if key == "Enter"
                                        else (lambda _, k=key, q=quiz: add_char(q, k))
                                        ).classes(
                                            f"{btn_class} text-white text-lg font-bold p-3 rounded-xl w-20 h-16"
                                        )

                quiz.start_button = ui.button("▶️ Start Quiz", on_click=lambda q=quiz: q.start()).classes(
                    "bg-green-600 text-white text-lg p-3 rounded-xl mt-6"
                )

            # Right column for plot
            with ui.column().classes("items-start justify-start"):
                quiz.svg_container = ui.html("").classes("w-[520px] h-[140px]")
                quiz.plot = ui.pyplot().classes("w-[500px] h-[400px]")

        ui.timer(0.1, restore_progress, once=True)
    return page


# ---------- REGISTER QUIZ PAGES ----------
# make_quiz_page(15, "autumn", ["multi_alg", "fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler"])
make_quiz_page(15, "autumn", ["ruler", "cm_ruler"])
# make_quiz_page(15, "autumn", ["decimal_multi_div"])
make_quiz_page(20, "molly", ["+", "-"])


# ---------- ROOT PAGE ----------
@ui.page('/')
def index():
    with ui.column().classes("items-center justify-center h-screen gap-6"):
        ui.label("Welcome to Peaccion Math!").classes(
            "text-3xl font-bold mb-8")
        ui.button("Autumn's Quiz", on_click=lambda: ui.navigate.to('/autumn')).classes(
            "bg-blue-500 text-white text-xl p-6 rounded-xl w-64"
        )
        ui.button("Molly's Quiz", on_click=lambda: ui.navigate.to('/molly')).classes(
            "bg-green-500 text-white text-xl p-6 rounded-xl w-64"
        )


ui.run(storage_secret='super-secret-key')
