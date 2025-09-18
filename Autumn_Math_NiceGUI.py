import random
import time
from fractions import Fraction
import matplotlib.pyplot as plt
from nicegui import ui


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

        self.plot = None  # slope plot

        # store vars for algebra/parens
        self.a = self.b = self.c = self.d = 0
        self.f1 = self.f2 = None

    def start(self):
        self.current_index = 0
        self.wrong = 0
        self.start_time = time.time()
        self.generate_problem()
        self.update_ui()
        self.start_button.visible = False

    def generate_problem(self):
        self.symbol = random.choice(self.allowed_ops)
        self.solution = None
        self.question = ""

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
            num1, den1 = random.randint(1, 9), random.randint(1, 9)
            num2, den2 = random.randint(1, 9), random.randint(1, 9)
            self.f1, self.f2 = Fraction(num1, den1), Fraction(num2, den2)
            self.solution = self.f1 + self.f2
            self.question = f"{self.f1} + {self.f2} = ? (simplify if possible)"
            self.clear_plot()

        # ---- Algebra ----
        elif self.symbol == "alg":
            formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
            self.algebra_format = random.choice(formats)

            if self.algebra_format == "a*x+b=c":
                self.a, x_val, self.b = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                self.c = self.a * x_val + self.b
                self.solution = x_val
                self.question = f"{self.a} * __ + {self.b} = {self.c}"

            elif self.algebra_format == "a*x-b=c":
                self.a, x_val, self.b = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                self.c = self.a * x_val - self.b
                self.solution = x_val
                self.question = f"{self.a} * __ - {self.b} = {self.c}"

            elif self.algebra_format == "a+b*x=c":
                self.b, x_val, self.a = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                self.c = self.a + self.b * x_val
                self.solution = x_val
                self.question = f"{self.a} + {self.b} * __ = {self.c}"

            self.clear_plot()

        # ---- Mixed expression ----
        elif self.symbol == "mix":
            self.a, self.b, self.c = random.randint(1, 20), random.randint(1, 20), random.randint(1, 10)
            self.solution = (self.a + self.b) * self.c
            self.question = f"({self.a} + {self.b}) * {self.c} = ?"
            self.clear_plot()

        # ---- Multi-step algebra ----
        elif self.symbol == "multi_alg":
            x_val = random.randint(1, 10)
            self.a = random.randint(1, 5)
            self.c = random.randint(self.a + 1, self.a + 4)
            self.b = random.randint(0, 10)
            left = self.a * x_val + self.b
            right = self.c * x_val
            self.d = right - left
            self.solution = x_val
            self.question = f"{self.a}x + {self.b} = {self.c}x - {self.d}"
            self.clear_plot()

        # ---- Parentheses ----
        elif self.symbol == "parens":
            formats = ["(a + b) * c", "a * (b - c)", "(a + b) + (c + d)", "(a * b) - (c * d)"]
            chosen = random.choice(formats)
            if chosen == "(a + b) * c":
                self.a, self.b, self.c = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
                self.solution = (self.a + self.b) * self.c
                self.question = f"({self.a} + {self.b}) * {self.c} = ?"
            elif chosen == "a * (b - c)":
                self.b, self.c, self.a = random.randint(5, 15), random.randint(1, 5), random.randint(1, 10)
                self.solution = self.a * (self.b - self.c)
                self.question = f"{self.a} * ({self.b} - {self.c}) = ?"
            elif chosen == "(a + b) + (c + d)":
                self.a, self.b, self.c, self.d = [random.randint(1, 10) for _ in range(4)]
                self.solution = (self.a + self.b) + (self.c + self.d)
                self.question = f"({self.a} + {self.b}) + ({self.c} + {self.d}) = ?"
            elif chosen == "(a * b) - (c * d)":
                self.a, self.b, self.c, self.d = random.randint(1, 10), random.randint(1, 5), random.randint(1, 4), random.randint(1, 3)
                self.solution = (self.a * self.b) - (self.c * self.d)
                self.question = f"({self.a} * {self.b}) - ({self.c} * {self.d}) = ?"
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

            if not self.plot:
                self.plot = ui.pyplot().classes("w-[500px] h-[400px]")
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

    def clear_plot(self):
        if self.plot:
            self.plot.clear()

    def check_answer(self):
        user_input = self.input_text.strip()
        correct = False
        try:
            if self.symbol in ["fraction", "slope"]:
                answer = Fraction(user_input)
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
            self.feedback = "✅ Correct!"
            self.current_index += 1
            self.input_text = ""
            if self.current_index < self.total_problems:
                self.generate_problem()
            else:
                self.end_game()
        else:
            self.feedback = "❌ Try again!"
            self.wrong += 1
            self.input_text = ""

        self.update_ui()

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        self.question = f"🎉 Finished! Time: {total_time}s, Wrong: {self.wrong}"
        self.feedback = ""
        self.clear_plot()
        with open(f"{self.name}_scores.txt", "a") as f:
            f.write(f"{time.ctime()}: Time {total_time}s, Wrong {self.wrong}\n")

        # show Start Quiz button again so they can restart
        self.start_button.visible = True
        self.update_ui()

    def update_ui(self):
        self.progress_label.set_text(f"{self.current_index+1} out of {self.total_problems}")
        self.question_label.set_text(self.question)
        self.feedback_label.set_text(self.feedback)
        self.answer_label.set_text(self.input_text)


# ---------- PAGE FACTORY ----------
def make_quiz_page(name: str, ops: list):
    quiz = MathQuizGame(allowed_ops=ops, name=name)

    @ui.page(f'/{name}')
    def page():
        with ui.row().classes("items-start justify-center w-full h-screen p-6 gap-12"):
            with ui.column().classes("items-center"):
                ui.label(f"Math Quiz for {name.capitalize()}").classes("text-3xl font-bold mb-6")

                quiz.progress_label = ui.label("").classes("text-xl mb-2")
                quiz.feedback_label = ui.label("").classes("text-xl mb-2")
                quiz.question_label = ui.label("").classes("text-2xl mb-2")
                quiz.answer_label = ui.label("").classes("text-2xl font-mono mb-4")

                keypad_row = ui.column().classes("items-center gap-3")
                with keypad_row:
                    for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["0", "/", "-"], ["C", "Enter"]]:
                        with ui.row().classes("gap-3"):
                            for key in row:
                                if key == "C":
                                    ui.button("Clear", on_click=lambda q=quiz: clear_input(q)).classes("bg-red-500 text-white text-lg p-3 rounded-xl w-24")
                                elif key == "Enter":
                                    ui.button("Enter", on_click=lambda q=quiz: q.check_answer()).classes("bg-green-500 text-white text-lg p-3 rounded-xl w-80")
                                else:
                                    ui.button(key, on_click=lambda _, k=key, q=quiz: add_char(q, k)).classes("bg-blue-500 text-white text-lg p-3 rounded-xl w-24")

                quiz.start_button = ui.button("▶️ Start Quiz", on_click=lambda q=quiz: q.start()).classes("bg-green-600 text-white text-lg p-3 rounded-xl mt-6")

            with ui.column().classes("items-center justify-center"):
                quiz.plot = ui.pyplot().classes("w-[500px] h-[400px]")

    return quiz


# keypad helpers
def add_char(quiz: MathQuizGame, ch: str):
    quiz.input_text += ch
    quiz.answer_label.set_text(quiz.input_text)


def clear_input(quiz: MathQuizGame):
    quiz.input_text = ""
    quiz.answer_label.set_text("")


# ---------- SETUP PAGES ----------
autumn_quiz = make_quiz_page("autumn", ["+", "-", "x", "÷", "alg", "mix", "multi_alg", "parens", "fraction", "slope"])
molly_quiz = make_quiz_page("molly", ["+", "-"])

ui.run()
