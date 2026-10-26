import os
import random
import time
import math
import inspect
from fractions import Fraction
import handlers
import matplotlib.pyplot as plt
from nicegui import ui, app
from scratchpad import Scratchpad


# ---------- KID-FRIENDLY HELPERS ----------
AVATARS = ["🦊", "🐼", "🦄", "🐸", "🐯", "🐙", "🚀", "🌟"]

# Each kid's default avatar and card colors on the welcome page.
KIDS = {
    "autumn": {"avatar": "🦊", "gradient": "from-orange-400 to-pink-500"},
    "molly": {"avatar": "🦄", "gradient": "from-purple-400 to-sky-500"},
}

AVATAR_DANCES = ("dance-wiggle", "dance-hop", "dance-spin")
AVATAR_DANCE_CSS = '''
@keyframes avatar-wiggle {
    0%, 100% { transform: rotate(0) scale(1); }
    20% { transform: rotate(-20deg) scale(1.25); }
    40% { transform: rotate(20deg) scale(1.25); }
    60% { transform: rotate(-14deg) scale(1.15); }
    80% { transform: rotate(10deg) scale(1.1); }
}
@keyframes avatar-hop {
    0%, 100% { transform: translateY(0) scale(1, 1); }
    15% { transform: translateY(0) scale(1.2, 0.8); }
    40% { transform: translateY(-36px) scale(0.9, 1.15); }
    60% { transform: translateY(0) scale(1.15, 0.85); }
    75% { transform: translateY(-14px) scale(1); }
}
@keyframes avatar-spin {
    0% { transform: rotate(0) scale(1); }
    50% { transform: rotate(200deg) scale(1.4); }
    100% { transform: rotate(360deg) scale(1); }
}
.dance-wiggle { animation: avatar-wiggle 0.9s ease-in-out; }
.dance-hop { animation: avatar-hop 0.9s ease-out; }
.dance-spin { animation: avatar-spin 0.8s ease-in-out; }
'''

# ---------- BATTLE GAME ----------
MAX_LIFE = 10
MISS_DAMAGE = 2
HINT_COST = 1
ENEMIES = ("👾", "👻", "🦖", "🐉", "🤖", "🦂", "🦇", "🐍", "🦈", "🕷️")
# Separate generator so picking enemies never disturbs the problem generators' random numbers.
enemy_random = random.Random()

BATTLE_ANIMATIONS = ("attack-right", "attack-left", "hit", "defeated", "pop-in")
BATTLE_CSS = '''
@keyframes lunge-right { 0%, 100% { transform: translateX(0); } 40% { transform: translateX(90px) scale(1.25); } }
@keyframes lunge-left { 0%, 100% { transform: translateX(0); } 40% { transform: translateX(-90px) scale(1.25); } }
@keyframes got-hit {
    0%, 100% { transform: translateX(0); filter: none; }
    20% { transform: translateX(-10px); filter: drop-shadow(0 0 10px red) brightness(1.6); }
    40% { transform: translateX(10px); }
    60% { transform: translateX(-8px); filter: drop-shadow(0 0 10px red); }
    80% { transform: translateX(6px); }
}
@keyframes knocked-out {
    0% { transform: scale(1) rotate(0); opacity: 1; filter: drop-shadow(0 0 10px red); }
    100% { transform: scale(0) rotate(540deg); opacity: 0; }
}
@keyframes pop-in { 0% { transform: scale(0.2); opacity: 0; } 70% { transform: scale(1.2); } 100% { transform: scale(1); opacity: 1; } }
.attack-right { animation: lunge-right 0.5s ease-in-out; }
.attack-left { animation: lunge-left 0.5s ease-in-out; }
.hit { animation: got-hit 0.5s ease-in-out 0.2s; }
.defeated { animation: knocked-out 0.6s ease-in 0.3s forwards; }
.pop-in { animation: pop-in 0.45s ease-out; }
'''

END_MESSAGES = {3: "Perfect! Not a single miss!", 2: "Awesome work!", 1: "Great practice! Keep going!"}


def get_avatar(name: str) -> str:
    default = KIDS.get(name, {}).get("avatar", "🌟")
    try:
        return app.storage.user.get(f"avatar_{name}", default)
    except RuntimeError:
        return default


def set_avatar(name: str, avatar: str):
    app.storage.user[f"avatar_{name}"] = avatar


def star_rating(wrong: int) -> int:
    if wrong == 0:
        return 3
    if wrong <= 3:
        return 2
    return 1


def format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


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
        self.hint = None  # picture hint data, drawn by handlers.visuals
        self.hint_level = 0  # how many hint steps are showing

        # battle game: each problem is an enemy that takes one hit per question it asks
        self.life = MAX_LIFE
        self.enemy = None
        self.enemy_hp = self.enemy_max_hp = 0
        self.defeated = 0

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
        self.progress_bar = None
        self.avatar_label = None
        self.life_label = None
        self.enemy_label = None
        self.enemy_hp_label = None
        self.battle_dialog = None
        self.battle_avatar_label = self.battle_enemy_label = None
        self.battle_caption_label = self.battle_status_label = None
        self.hint_button = None
        self.hint_container = None
        self.end_card = None
        self.end_title_label = None
        self.end_avatar_label = None
        self.end_stars_label = None
        self.end_details_label = None
        self.end_message_label = None

    def start(self):
        # Only reset if not continuing a restored quiz
        if self.start_time is None or self.current_index >= self.total_problems or self.life <= 0:
            self.current_index = 0
            self.wrong = 0
            self.life = MAX_LIFE
            self.defeated = 0
            self.animate(self.avatar_label, "pop-in")
            self.start_time = time.time()
            self.answer_pending = False
            self.input_text = ""
            self.feedback = ""
            self.feedback_color = None
            self.generate_problem()
            self.save_progress()

        if self.end_card:
            self.end_card.visible = False
        self.update_ui()
        if self.start_button and self.start_button.visible:
            self.start_button.visible = False
            self.start_button.update()

    def generate_problem(self):
        self.follow_up_questions = []
        self.hint = None
        self.hint_level = 0
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

        self.enemy = enemy_random.choice(ENEMIES)
        self.enemy_hp = self.enemy_max_hp = 1 + len(self.follow_up_questions)
        self.animate(self.enemy_label, "pop-in")

    @property
    def in_play(self):
        return self.start_time is not None and self.current_index < self.total_problems and self.life > 0

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
        if self.answer_pending or not self.in_play:
            return
        user_input = self.input_text.strip()
        if self.symbol == "percent":
            user_input = user_input.replace("$", "").replace("%", "").replace(",", "")
        correct = False
        self.feedback_color = None

        try:
            if self.symbol in ["fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler", "percent"]:
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
            # Your avatar attacks; each correct answer takes one 💚 off the enemy.
            self.enemy_hp = max(self.enemy_hp - 1, 0)
            knockout = self.enemy_hp == 0
            if knockout:
                self.defeated += 1
                self.feedback = f"✅ Correct! You beat the {self.enemy}!"
            else:
                self.feedback = f"✅ Correct! You hit the {self.enemy}! Keep going!"
            self.save_progress()
            self.input_text = ""
            self.update_ui()          # immediate visual feedback
            fight = self.show_battle(player_attacks=True, knockout=knockout,
                                     caption=f"You beat the {self.enemy}! 🎉" if knockout
                                     else f"You hit the {self.enemy}! 💥")

            # pause so the attack (and knockout) can play before the next question
            ui.timer(fight or (1.0 if knockout else 0.6), self.advance_problem, once=True)

        else:
            # The enemy attacks back.
            self.life = max(self.life - MISS_DAMAGE, 0)
            self.wrong += 1
            self.input_text = ""
            self.show_battle(player_attacks=False, knockout=self.life == 0,
                             caption=f"The {self.enemy} hit you! −{MISS_DAMAGE} ❤️")
            if self.life == 0:
                self.game_over()
                self.update_ui()
                return
            self.feedback = f"💥 The {self.enemy} hit you! −{MISS_DAMAGE} ❤️ Try again!"
            if self.hint:
                # The picture that opens after a miss is free; the miss already cost hearts.
                self.feedback += " Here's a hint 💡"
                self.hint_level = min(self.hint_level + 1, handlers.visuals.hint_steps(self.hint))
            self.update_ui()
            self.save_progress()

    def animate(self, element, animation, delay_ms=0):
        """Restart a CSS animation (from AVATAR_DANCE_CSS / BATTLE_CSS) on a label in the browser."""
        if not element:
            return
        ui.run_javascript(f'''
            const el = document.getElementById("c{element.id}");
            if (el) {{
                el.classList.remove(...{list(AVATAR_DANCES + BATTLE_ANIMATIONS)});
                void el.offsetWidth;  // restart the animation even if the same one repeats
                setTimeout(() => el.classList.add("{animation}"), {delay_ms});
            }}
        ''')

    def show_battle(self, player_attacks: bool, knockout: bool, caption: str) -> float:
        """Pop up the fight, play it, and close the pop-up. Returns how long it stays open."""
        if not self.battle_dialog:
            return 0
        self.battle_avatar_label.set_text(get_avatar(self.name))
        self.battle_enemy_label.set_text(self.enemy or "")
        self.battle_caption_label.set_text(caption)
        self.battle_status_label.set_text(
            "❤️" * self.life + "🖤" * (MAX_LIFE - self.life) + "    " +
            "💚" * self.enemy_hp + "🤍" * (self.enemy_max_hp - self.enemy_hp))
        self.battle_dialog.open()
        start = 300  # let the pop-up finish opening first
        if player_attacks:
            self.animate(self.battle_avatar_label, "attack-right", start)
            self.animate(self.battle_enemy_label, "defeated" if knockout else "hit", start)
        else:
            self.animate(self.battle_enemy_label, "attack-left", start)
            self.animate(self.battle_avatar_label, "defeated" if knockout else "hit", start)
        duration = 1.7 if knockout else 1.3
        ui.timer(duration, self.close_battle, once=True)
        return duration

    def close_battle(self):
        self.battle_dialog.close()
        if self.answer_label and self.in_play and not self.answer_pending:
            self.answer_label.run_method('focus')

    def celebrate(self):
        """Make the avatar do a random little dance."""
        if self.avatar_label:
            self.animate(self.avatar_label, random.choice(AVATAR_DANCES))

    def show_hint(self):
        if not self.hint or self.answer_pending or not self.in_play:
            return
        if self.hint_level >= handlers.visuals.hint_steps(self.hint):
            return
        self.hint_level += 1
        self.life = max(self.life - HINT_COST, 0)
        self.feedback = f"💡 Hint used: −{HINT_COST} ❤️"
        self.animate(self.avatar_label, "hit")
        if self.life == 0:
            self.animate(self.avatar_label, "defeated")
            self.game_over()
            self.update_ui()
            return
        self.save_progress()
        self.update_ui()

    def advance_problem(self):
        if not self.answer_pending:
            return
        self.answer_pending = False
        self.input_text = ""
        self.feedback = ""
        if self.follow_up_questions:
            follow_up = self.follow_up_questions.pop(0)
            self.question = follow_up["question"]
            solution = follow_up["solution"]
            self.solution = Fraction(solution) if isinstance(solution, str) else solution
            self.hint_level = 0
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
            "hint": self.hint,
            "hint_level": self.hint_level,
            "life": self.life,
            "enemy": self.enemy,
            "enemy_hp": self.enemy_hp,
            "enemy_max_hp": self.enemy_max_hp,
            "defeated": self.defeated,
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
        self.hint = saved.get("hint")
        self.hint_level = saved.get("hint_level", 1 if saved.get("hint_shown") else 0)
        if not self.hint:
            # Saved before picture hints existed: rebuild one from the question text.
            if self.symbol in ("+", "-", "*", "x"):
                handlers.arithmetic.restore_hint(self)
            elif self.symbol in ("lcm", "gcf"):
                handlers.common_multiples.restore_hint(self)
        if self.symbol in ('lcm', 'gcf') and not self.follow_up_questions:
            handlers.common_multiples.restore_follow_ups(self)
        # Saves from before the battle game start at full life with a fresh enemy.
        self.life = saved.get("life", MAX_LIFE)
        self.defeated = saved.get("defeated", self.current_index)
        self.enemy = saved.get("enemy") or enemy_random.choice(ENEMIES)
        self.enemy_max_hp = saved.get("enemy_max_hp", 1 + len(self.follow_up_questions))
        self.enemy_hp = saved.get("enemy_hp", self.enemy_max_hp)
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

    def finish(self, question: str, score_line: str):
        """Shared wrap-up for winning and game over: clear the problem, save the score."""
        self.question = question
        self.feedback = ""
        self.solution = None
        self.hint = None
        self.hint_level = 0
        self.question_svg = None
        self.clear_plot()
        app.storage.user.pop(self.name, None)

        os.makedirs("scores", exist_ok=True)
        with open(os.path.join("scores", f"{self.name}_scores.txt"), "a") as f:
            f.write(f"{time.ctime()}: {score_line}\n")

    def show_end_card(self, title, big, details, message, button):
        if self.end_card:
            if self.end_title_label:
                self.end_title_label.set_text(title)
            self.end_avatar_label.set_text(get_avatar(self.name))
            self.end_stars_label.set_text(big)
            self.end_details_label.set_text(details)
            self.end_message_label.set_text(message)
            self.end_card.visible = True
        if self.start_button:
            self.start_button.set_text(button)
            self.start_button.visible = True
            self.start_button.update()

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        self.enemy = None
        self.animate(self.enemy_label, "pop-in")  # the trophy replaces the knocked-out enemy
        self.celebrate()
        self.finish("🎉 Finished!", f"Time {total_time}s, Wrong {self.wrong}, Life {self.life}")
        stars = star_rating(self.wrong)
        self.show_end_card("🎉 You did it!", "⭐" * stars,
                           f"Time: {format_duration(total_time)} • Misses: {self.wrong} • ❤️ {self.life} left",
                           END_MESSAGES[stars], "🔁 Play again")

    def game_over(self):
        self.finish("💀 Game over!", f"Game over: beat {self.defeated} of {self.total_problems}, Wrong {self.wrong}")
        self.show_end_card("💀 Game over!", "😵",
                           f"You beat {self.defeated} of {self.total_problems} enemies. "
                           f"The {self.enemy} got you this time.",
                           "Try again! You've got this! 💪", "🔁 Try again")

    def update_ui(self):
        if self.progress_label:
            question_number = min(self.current_index + 1, self.total_problems)
            self.progress_label.set_text(
                f"Question {question_number} of {self.total_problems}")
        if self.progress_bar:
            self.progress_bar.set_value(self.current_index / self.total_problems)
        if self.life_label:
            self.life_label.set_text("❤️" * self.life + "🖤" * (MAX_LIFE - self.life))
        if self.enemy_label:
            started = self.start_time is not None
            finished = started and self.current_index >= self.total_problems and self.life > 0
            self.enemy_label.set_text("🏆" if finished else (self.enemy or "") if started else "")
            self.enemy_hp_label.set_text(
                "💚" * self.enemy_hp + "🤍" * (self.enemy_max_hp - self.enemy_hp) if started and self.enemy else "")
        if self.question_label:
            displayed_question = handlers.arithmetic.vertical_question(self.question)
            if displayed_question != self.question:
                self.question_label.classes(add='font-mono whitespace-pre text-4xl',
                                            remove='whitespace-normal text-2xl')
            else:
                self.question_label.classes(add='whitespace-normal text-2xl',
                                            remove='font-mono whitespace-pre text-4xl')
            self.question_label.set_text(displayed_question)
        if self.feedback_label:
            self.feedback_label.set_text(self.feedback)
            if self.feedback_color:
                self.feedback_label.style(f"color: {self.feedback_color}")
            else:
                self.feedback_label.style("")  # reset to default
        if self.answer_label:
            self.answer_label.set_value(self.input_text)
            active = self.in_play and not self.answer_pending
            self.answer_label.set_enabled(active)
            if active:
                self.answer_label.run_method('focus')
        if self.svg_container:
            self.svg_container.set_content(self.question_svg or "")
        if self.hint_container:
            self.hint_container.set_content(
                handlers.visuals.build_svg(self.hint, self.hint_level) if self.hint_level else "")
        if self.hint_button:
            self.hint_button.set_text("💡 Show me" if self.hint_level == 0 else "💡 Another hint")
            self.hint_button.visible = (bool(self.hint) and not self.answer_pending
                                        and self.hint_level < handlers.visuals.hint_steps(self.hint))


# keypad helpers
def add_char(quiz: MathQuizGame, ch: str):
    if quiz.answer_pending:
        return
    quiz.input_text += ch
    if quiz.answer_label:
        quiz.answer_label.set_value(quiz.input_text)


def clear_input(quiz: MathQuizGame):
    quiz.input_text = ""
    if quiz.answer_label:
        quiz.answer_label.set_value("")


def handle_quiz_key(quiz: MathQuizGame, key: str):
    if quiz.answer_pending or not quiz.in_play:
        return
    if key in "0123456789.-/" and len(key) == 1:
        add_char(quiz, key)
    elif key == "Enter":
        if quiz.input_text.strip():
            quiz.check_answer()
    elif key == "Backspace":
        quiz.input_text = quiz.input_text[:-1]
        if quiz.answer_label:
            quiz.answer_label.set_value(quiz.input_text)
    elif key in ("Escape", "Delete"):
        clear_input(quiz)


def handle_keyboard_event(quiz: MathQuizGame, event):
    if not event.action.keydown or event.action.repeat:
        return
    if event.modifiers.ctrl or event.modifiers.alt or event.modifiers.meta:
        return
    handle_quiz_key(quiz, event.key.name)


# ---------- PAGE FACTORY ----------
def create_svg_container(classes='w-[520px] h-[140px]'):
    # NiceGUI 2.x rejects sanitize; NiceGUI 3.x requires it.
    # This container only displays SVG generated by our ruler and visuals handlers.
    options = {'sanitize': False} if 'sanitize' in inspect.signature(ui.html).parameters else {}
    return ui.html('', **options).classes(classes)


def make_quiz_page(total_problems: int, name: str, ops: list, multiplication_range=(3, 12)):
    @ui.page(f'/{name}', dark=True)
    def page():
        quiz = MathQuizGame(total_problems=total_problems,
                            allowed_ops=ops, name=name, multiplication_range=multiplication_range)
        ui.add_css(AVATAR_DANCE_CSS)
        ui.add_css(BATTLE_CSS)
        ui.keyboard(on_key=lambda e: handle_keyboard_event(quiz, e), repeating=False,
                    ignore=['input', 'select', 'textarea'])

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

        with ui.row().classes("items-start justify-start w-full h-screen p-6 gap-12") as quiz_layout:
            # Capture Enter on focused keypad buttons before it can click them.
            # Elsewhere, ui.keyboard handles Enter normally.
            quiz_layout.on('keydown.capture', lambda e: handle_quiz_key(quiz, 'Enter'), js_handler='''(e) => {
                if (e.key === 'Enter' && e.target.closest('button') &&
                    e.target.closest('[data-quiz-keypad]')) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (!e.repeat && !e.ctrlKey && !e.altKey && !e.metaKey) emit({});
                }
            }''')
            quiz_layout.on('keyup.capture', js_handler='''(e) => {
                if (e.key === 'Enter' && e.target.closest('button') &&
                    e.target.closest('[data-quiz-keypad]')) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }''')
            with ui.column().classes("items-start"):
                ui.label(f"{name.capitalize()}'s Math Adventure").classes("text-3xl font-bold mb-4")

                # Battle arena: your avatar and hearts vs. this problem's enemy and its health.
                # Sticky so the fight stays in view when the page scrolls to the answer box.
                with ui.row().classes("items-end justify-between w-[440px] mb-4 px-6 py-4 rounded-2xl "
                                      "bg-gradient-to-r from-sky-900 to-indigo-900 sticky top-2 z-10 shadow-lg"):
                    with ui.column().classes("items-center gap-1"):
                        quiz.avatar_label = ui.label(get_avatar(name)).classes("text-6xl inline-block")
                        quiz.life_label = ui.label("❤️" * MAX_LIFE).classes("text-xs")
                    ui.label("⚔️").classes("text-3xl self-center")
                    with ui.column().classes("items-center gap-1"):
                        quiz.enemy_label = ui.label("").classes("text-6xl inline-block")
                        quiz.enemy_hp_label = ui.label("").classes("text-xs")

                def pick_avatar(avatar):
                    set_avatar(name, avatar)
                    quiz.avatar_label.set_text(avatar)
                    quiz.celebrate()

                quiz.progress_label = ui.label("").classes("text-xl")
                quiz.progress_bar = ui.linear_progress(value=0, show_value=False, size='24px',
                                                       color='orange').props('rounded').classes('w-96 mb-4')
                quiz.feedback_label = ui.label("").classes("text-xl mb-2")
                quiz.question_label = ui.label("").classes("text-2xl mb-2 max-w-xl whitespace-normal")
                quiz.hint_button = ui.button("💡 Show me", on_click=quiz.show_hint, color=None).classes(
                    "bg-yellow-400 text-gray-900 text-lg font-bold rounded-xl mb-2"
                )
                quiz.hint_button.visible = False
                quiz.hint_container = create_svg_container("mb-2")

                with ui.card().classes("items-center p-8 rounded-3xl bg-gradient-to-br from-yellow-300 "
                                       "to-orange-400 text-gray-900 w-96") as quiz.end_card:
                    quiz.end_avatar_label = ui.label("").classes("text-7xl")
                    quiz.end_title_label = ui.label("🎉 You did it!").classes("text-3xl font-bold")
                    quiz.end_stars_label = ui.label("").classes("text-5xl")
                    quiz.end_details_label = ui.label("").classes("text-xl")
                    quiz.end_message_label = ui.label("").classes("text-xl font-semibold")
                quiz.end_card.visible = False

                play_area = ui.column().classes("items-start gap-0")
                play_area.bind_visibility_from(quiz.end_card, 'visible', backward=lambda shown: not shown)
                with play_area:
                    quiz.answer_label = ui.input('Your answer').bind_value(quiz, 'input_text').props(
                        'outlined autocomplete=off'
                    ).classes('text-2xl font-mono mb-4 w-64')
                    quiz.answer_label.disable()
                    # Handle keys directly on the input; the global listener ignores inputs.
                    quiz.answer_label.on('keydown', lambda e: handle_quiz_key(quiz, e.args['key']),
                                         js_handler='''(e) => {
                        if (!e.ctrlKey && !e.altKey && !e.metaKey &&
                            ['Enter', 'Escape', 'Delete'].includes(e.key)) {
                            e.preventDefault();
                            e.stopPropagation();
                            if (!e.repeat) emit({key: e.key});
                        }
                    }''')
                    ui.label('Type your answer • Enter: submit • Backspace: erase • Esc: clear').classes('text-sm mb-2')

                    # ✅ Keypad now evenly aligned and centered
                    keypad_col = ui.column().classes("items-center gap-2 mt-4 scale-90").props('data-quiz-keypad')
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
                                            else (lambda _, k=key, q=quiz: add_char(q, k)),
                                            color=None
                                            ).classes(
                                                f"{btn_class} text-white text-lg font-bold p-3 rounded-xl w-20 h-16"
                                            )

                quiz.start_button = ui.button("▶️ Start Quiz", on_click=lambda q=quiz: q.start(), color=None).classes(
                    "bg-green-600 text-white text-lg p-3 rounded-xl mt-6"
                ).props('data-quiz-start')

                # Kids can pick their player whenever a quiz isn't in progress.
                with ui.column().classes("mt-4 gap-1") as avatar_picker:
                    ui.label("Pick your player:").classes("text-lg")
                    with ui.row().classes("gap-2"):
                        for avatar in AVATARS:
                            ui.button(avatar, on_click=lambda _, a=avatar: pick_avatar(a)).props(
                                'flat round'
                            ).classes("text-3xl")
                avatar_picker.bind_visibility_from(quiz.start_button, 'visible')

            # Scratch work stays visible while moving through follow-up questions.
            with ui.column().classes("items-start justify-start w-full min-w-0").style('flex: 1 1 520px; max-width: 900px'):
                Scratchpad().classes('w-full')
                quiz.svg_container = create_svg_container()
                quiz.plot = ui.pyplot().classes("w-[500px] h-[400px]")

        # The fight pops up over everything after each answer, then closes itself.
        with ui.dialog() as quiz.battle_dialog, ui.card().classes(
                "items-center gap-2 px-10 py-8 rounded-3xl bg-gradient-to-br from-sky-800 to-indigo-900 text-white"):
            with ui.row().classes("items-center gap-10"):
                quiz.battle_avatar_label = ui.label("").classes("text-8xl inline-block")
                ui.label("⚔️").classes("text-5xl")
                quiz.battle_enemy_label = ui.label("").classes("text-8xl inline-block")
            quiz.battle_caption_label = ui.label("").classes("text-2xl font-bold")
            quiz.battle_status_label = ui.label("").classes("text-sm whitespace-pre")

        ui.timer(0.1, restore_progress, once=True)
    return page


# ---------- REGISTER QUIZ PAGES ----------
# make_quiz_page(15, "autumn", ["multi_alg", "fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler"])
make_quiz_page(15, "autumn", ["lcm", "gcf", "percent"])
# Repeating multiplication gives it a 50% chance; addition and subtraction each get 25%.
make_quiz_page(15, "molly", ["*"], multiplication_range=(3, 7))


# ---------- ROOT PAGE ----------
def root_page():
    with ui.column().classes("items-center justify-center w-full h-screen gap-6"):
        ui.label("Welcome to Peaccion Math!").classes("text-4xl font-bold")
        ui.label("Pick your player").classes("text-2xl mb-6")
        with ui.row().classes("gap-8 justify-center"):
            for name, kid in KIDS.items():
                with ui.card().classes(
                    f"items-center p-8 rounded-3xl cursor-pointer bg-gradient-to-br {kid['gradient']} "
                    "text-white w-64 hover:scale-105 transition-transform"
                ).on('click', lambda _, n=name: ui.navigate.to(f'/{n}')):
                    ui.label(get_avatar(name)).classes("text-6xl")
                    ui.label(name.capitalize()).classes("text-2xl font-bold")
                    ui.label("Let's play! ▶️").classes("text-lg")

ui.page('/',dark=True)(root_page)
# Disable development file watching when running on the server.
ui.run(storage_secret='super-secret-key', reload=False, show=False)
