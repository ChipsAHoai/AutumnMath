import random
import time
from fractions import Fraction
import matplotlib.pyplot as plt
from nicegui import ui


class MathQuizGame:
    def __init__(self):
        self.total_problems = 20
        self.current_index = 0
        self.wrong = 0
        self.start_time = None

        self.question = ""
        self.solution = None
        self.symbol = ""
        self.algebra_format = ""

        self.input_text = ""
        self.feedback = ""

        self.plot = None  # slope plot element

        # store variables for re-rendering
        self.a = self.b = self.c = self.d = 0
        self.f1 = self.f2 = None
        self.last_parens_problem = ""

    def start(self):
        self.current_index = 0
        self.wrong = 0
        self.start_time = time.time()
        self.generate_problem()
        self.update_ui()
        start_button.visible = False   # hide start button once clicked

    def generate_problem(self):
        operators = ["+", "-", "x", "÷", "alg", "mix", "multi_alg", "parens", "fraction", "slope"]
        operators = ["slope"]
        self.symbol = random.choice(operators)
        self.algebra_format = ""
        self.last_parens_problem = ""
        self.solution = None

        # ---- Basic arithmetic ----
        if self.symbol == "+":
            x, y = random.randint(1, 10000), random.randint(1, 10000)
            self.solution = x + y
            self.question = f"{x} + {y} = ?"
            self.clear_plot()

        elif self.symbol == "-":
            x = random.randint(1, 10000)
            y = random.randint(1, x)
            self.solution = x - y
            self.question = f"{x} - {y} = ?"
            self.clear_plot()

        elif self.symbol == "x":
            x, y = random.randint(3, 99), random.randint(11, 99)
            self.solution = x * y
            self.question = f"{x} × {y} = ?"
            self.clear_plot()

        elif self.symbol == "÷":
            divisor = random.randint(2, 999)
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

        # ---- Algebra (single step) ----
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
                self.last_parens_problem = f"({self.a} + {self.b}) * {self.c} = ?"

            elif chosen == "a * (b - c)":
                self.b, self.c, self.a = random.randint(5, 15), random.randint(1, 5), random.randint(1, 10)
                self.solution = self.a * (self.b - self.c)
                self.last_parens_problem = f"{self.a} * ({self.b} - {self.c}) = ?"

            elif chosen == "(a + b) + (c + d)":
                self.a, self.b, self.c, self.d = random.randint(1, 10), random.randint(1, 10), random.randint(1, 10), random.randint(1, 10)
                self.solution = (self.a + self.b) + (self.c + self.d)
                self.last_parens_problem = f"({self.a} + {self.b}) + ({self.c} + {self.d}) = ?"

            elif chosen == "(a * b) - (c * d)":
                self.a, self.b, self.c, self.d = random.randint(1, 10), random.randint(1, 5), random.randint(1, 4), random.randint(1, 3)
                self.solution = (self.a * self.b) - (self.c * self.d)
                self.last_parens_problem = f"({self.a} * {self.b}) - ({self.c} * {self.d}) = ?"

            self.question = self.last_parens_problem
            self.clear_plot()

        # ---- Slope between 2 points ----
        elif self.symbol == "slope":
            x1, y1 = random.randint(-10, 10), random.randint(-10, 10)
            x2, y2 = random.randint(-10, 10), random.randint(-10, 10)
            while x2 == x1:
                x2 = random.randint(-10, 10)

            delta_y, delta_x = y2 - y1, x2 - x1
            self.solution = Fraction(delta_y, delta_x)
            self.question = f"Slope through ({x1},{y1}) and ({x2},{y2}) = ? (fraction)"

            if not self.plot:
                self.plot = ui.pyplot().classes("w-96 h-72")

            with self.plot:
                plt.clf()
                plt.axhline(0, color='gray', linewidth=0.8)
                plt.axvline(0, color='gray', linewidth=0.8)
                plt.grid(True, linestyle='--', linewidth=0.5)
                plt.plot([x1, x2], [y1, y2], color='crimson', linewidth=2)
                plt.scatter([x1, x2], [y1, y2], color='dodgerblue', zorder=5)
                plt.text(x1, y1, f'({x1},{y1})', fontsize=9, ha='left', va='bottom')
                plt.text(x2, y2, f'({x2},{y2})', fontsize=9, ha='left', va='bottom')
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
            elif self.symbol == "alg":
                answer = int(user_input)
                if self.algebra_format == "a*x+b=c":
                    correct = (self.a * answer + self.b == self.c)
                elif self.algebra_format == "a*x-b=c":
                    correct = (self.a * answer - self.b == self.c)
                elif self.algebra_format == "a+b*x=c":
                    correct = (self.a + self.b * answer == self.c)
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

    def update_ui(self):
        progress_label.set_text(f"{self.current_index+1} out of {self.total_problems}")
        question_label.set_text(self.question)
        feedback_label.set_text(self.feedback)
        answer_label.set_text(self.input_text)


quiz = MathQuizGame()

# ----------- UI ------------
with ui.row().classes("items-start justify-center w-full h-screen p-6 gap-12"):

    # Left side: Quiz UI
    with ui.column().classes("items-center"):
        ui.label("Math Quiz for Autumn").classes("text-3xl font-bold mb-6")

        progress_label = ui.label("").classes("text-xl mb-2")
        feedback_label = ui.label("").classes("text-xl mb-2")   # moved here
        question_label = ui.label("").classes("text-2xl mb-2")
        answer_label = ui.label("").classes("text-2xl font-mono mb-4")

        keypad_row = ui.column().classes("items-center gap-3")
        with keypad_row:
            for row in [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["0", "/", "-"], ["C", "Enter"]]:
                with ui.row().classes("gap-3"):
                    for key in row:
                        if key == "C":
                            ui.button("Clear", on_click=lambda: clear_input()).classes("bg-red-500 text-white text-lg p-3 rounded-xl w-24")
                        elif key == "Enter":
                            ui.button("Enter", on_click=lambda: quiz.check_answer()).classes("bg-green-500 text-white text-lg p-3 rounded-xl w-80")
                        else:
                            ui.button(key, on_click=lambda _, k=key: add_char(k)).classes("bg-blue-500 text-white text-lg p-3 rounded-xl w-24")

        start_button = ui.button("▶️ Start Quiz", on_click=lambda: quiz.start()).classes("bg-green-600 text-white text-lg p-3 rounded-xl mt-6")

    # Right side: Graph
    with ui.column().classes("items-center justify-center"):
        quiz.plot = ui.pyplot().classes("w-[500px] h-[400px]")


# ------ keypad functions ------
def add_char(ch: str):
    quiz.input_text += ch
    answer_label.set_text(quiz.input_text)


def clear_input():
    quiz.input_text = ""
    answer_label.set_text("")


ui.run()
