import os
import random
import time
import math
from fractions import Fraction
import handlers
import matplotlib.pyplot as plt
from nicegui import ui, app


# ---------- BASE QUIZ CLASS ----------
class MathQuizGame:
    def __init__(self, total_problems=20, allowed_ops=None, name="player", multiplication_range=(3, 12)):
        self.total_problems = total_problems
        self.allowed_ops = allowed_ops or ["+"]
        self.name = name
        self.multiplication_range = multiplication_range

        self.current_index = 0
        self.wrong = 0
        self.start_time = None
        self.answer_pending = False
        self.follow_up_questions = []
        self.slope_points = None

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
        if self.start_time is None or self.current_index >= self.total_problems:
            self.current_index = 0
            self.wrong = 0
            self.start_time = time.time()
            self.answer_pending = False
            self.input_text = ""
            self.feedback = ""
            self.feedback_color = None
            self.generate_problem()
            self.save_progress()

        self.update_ui()
        if self.start_button and self.start_button.visible:
            self.start_button.visible = False
            self.start_button.update()

    def generate_problem(self):
        self.follow_up_questions = []
        self.symbol = random.choice(self.allowed_ops)
        self.solution = None
        self.question = ""
        self.question_svg = None
        self.slope_points = None

        handler = handlers.registry.get(self.symbol)
        if handler:
            try:
                handler(self)
            except Exception:
                self.question = "Error generating problem"
                self.clear_plot()
        else:
            self.question = "Unsupported operation"
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

    def check_answer(self):
        if self.answer_pending or self.start_time is None or self.current_index >= self.total_problems:
            return
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
            self.answer_pending = True
            self.save_progress()
            ui.notify(f"Great Job {self.name.capitalize()}!", type='positive')
            self.feedback = "✅ Correct!"
            self.input_text = ""
            self.update_ui()          # immediate visual feedback

            # small pause so user can see "Correct!" message before next problem
            ui.timer(0.6, self.advance_problem, once=True)

        else:
            ui.notify(f"Try Again {self.name.capitalize()}!", type='negative')
            self.feedback = "❌ Try again!"
            self.wrong += 1
            self.input_text = ""
            self.update_ui()
            self.save_progress()

    def advance_problem(self):
        if not self.answer_pending:
            return
        self.answer_pending = False
        self.input_text = ""
        self.feedback = ""
        if self.follow_up_questions:
            follow_up = self.follow_up_questions.pop(0)
            self.question = follow_up["question"]
            self.solution = follow_up["solution"]
            self.save_progress()
            self.update_ui()
            return
        self.current_index += 1
        if self.current_index < self.total_problems:
            self.generate_problem()
            self.save_progress()
        else:
            self.end_game()
        self.update_ui()

    def save_progress(self):
        app.storage.user[self.name] = {
            "current_index": self.current_index,
            "wrong": self.wrong,
            "question": self.question,
            "solution": str(self.solution),
            "symbol": self.symbol,
            "start_time": self.start_time,
            "answer_pending": self.answer_pending,
            "slope_points": self.slope_points,
            "follow_up_questions": list(self.follow_up_questions),
        }

    def restore_progress(self, saved):
        self.current_index = saved.get("current_index", 0)
        self.wrong = saved.get("wrong", 0)
        self.question = saved.get("question", "")
        sol = saved.get("solution", "")
        self.solution = Fraction(sol) if "/" in sol else int(sol)
        self.symbol = saved.get("symbol", "")
        self.start_time = saved.get("start_time") or time.time()
        self.answer_pending = saved.get("answer_pending", False)
        self.slope_points = saved.get("slope_points")
        self.follow_up_questions = list(saved.get("follow_up_questions", []))
        if self.symbol in ('lcm', 'gcf') and not self.follow_up_questions:
            handlers.common_multiples.restore_follow_ups(self)
        if self.answer_pending:
            self.advance_problem()
            return
        self.feedback = "⏪ Progress restored!"
        if self.symbol == "ruler":
            self.question_svg = handlers.ruler.build_ruler_svg(int(self.solution * 16))
        elif self.symbol == "cm_ruler":
            self.question_svg = handlers.cm_ruler.build_centimeter_svg(int(self.solution * 10))
        elif self.symbol == "slope":
            handlers.slope.restore(self)
        self.update_ui()

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        self.question = f"🎉 Finished! Time: {total_time}s, Wrong: {self.wrong}"
        self.feedback = ""
        self.solution = None
        self.question_svg = None
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
    if quiz.answer_pending:
        return
    quiz.input_text += ch
    if quiz.answer_label:
        quiz.answer_label.set_text(quiz.input_text)


def clear_input(quiz: MathQuizGame):
    quiz.input_text = ""
    if quiz.answer_label:
        quiz.answer_label.set_text("")


# ---------- PAGE FACTORY ----------
def make_quiz_page(total_problems: int, name: str, ops: list, multiplication_range=(3, 12)):
    @ui.page(f'/{name}', dark=True)
    def page():
        quiz = MathQuizGame(total_problems=total_problems,
                            allowed_ops=ops, name=name, multiplication_range=multiplication_range)

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
                try:
                    quiz.restore_progress(saved)
                except (ValueError, TypeError, ZeroDivisionError):
                    app.storage.user.pop(name, None)
                    quiz.current_index = 0
                    quiz.start_time = None
                    quiz.answer_pending = False
                    quiz.solution = None
                    quiz.question_svg = None
                    quiz.clear_plot()
                else:
                    if quiz.start_button:
                        quiz.start_button.visible = quiz.current_index >= quiz.total_problems
                        quiz.start_button.update()
                    return
            quiz.question = "Press ▶️ Start Quiz to begin"
            quiz.update_ui()

        with ui.row().classes("items-start justify-start w-full h-screen p-6 gap-12"):
            with ui.column().classes("items-start"):
                ui.label(f"Math Quiz for {name.capitalize()}").classes(
                    "text-3xl font-bold mb-6"
                )

                quiz.progress_label = ui.label("").classes("text-xl mb-2")
                quiz.feedback_label = ui.label("").classes("text-xl mb-2")
                quiz.question_label = ui.label("").classes("text-2xl mb-2 max-w-xl whitespace-normal")
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
                quiz.svg_container = ui.html("", sanitize=False).classes("w-[520px] h-[140px]")
                quiz.plot = ui.pyplot().classes("w-[500px] h-[400px]")

        ui.timer(0.1, restore_progress, once=True)
    return page


# ---------- REGISTER QUIZ PAGES ----------
# make_quiz_page(15, "autumn", ["multi_alg", "fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler"])
make_quiz_page(15, "autumn", ["slope", "lcm", "gcf"])
make_quiz_page(20, "molly", ["+", "-", "*"], multiplication_range=(1, 5))


# ---------- ROOT PAGE ----------
def root_page():
    with ui.column().classes("items-center justify-center h-screen gap-6"):
        ui.label("Welcome to Peaccion Math!").classes(
            "text-3xl font-bold mb-8")
        ui.button("Autumn's Quiz", on_click=lambda: ui.navigate.to('/autumn')).classes(
            "bg-blue-500 text-white text-xl p-6 rounded-xl w-64"
        )
        ui.button("Molly's Quiz", on_click=lambda: ui.navigate.to('/molly')).classes(
            "bg-green-500 text-white text-xl p-6 rounded-xl w-64"
        )

ui.page('/',dark=True)(root_page)
# Disable development file watching when running on the server.
ui.run(storage_secret='super-secret-key', reload=False, show=False)
