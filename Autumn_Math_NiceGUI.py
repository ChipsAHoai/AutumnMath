import json
import os
import random
import time
import math
import inspect
import re
from fractions import Fraction
from html import escape
from pathlib import Path
import handlers
import matplotlib.pyplot as plt
from fastapi import FastAPI
from nicegui import ui, app
from scratchpad import Scratchpad
import notify


# ---------- KID-FRIENDLY HELPERS ----------
AVATARS = ["🦊", "🐼", "🦄", "🐸", "🐯", "🐙", "🚀", "🌟"]

# Each kid's default avatar and card colors on the welcome page.
KIDS = {
    "autumn": {"avatar": "🦊", "gradient": "from-orange-400 to-pink-500"},
    "molly": {"avatar": "🦄", "gradient": "from-purple-400 to-sky-500"},
}

# ---------- FONTS AND LEARN PAGES ----------
# Rounded display font for headings and buttons, a very readable one for everything else.
APP_FONTS_HTML = '''
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Atkinson+Hyperlegible:wght@400;700&display=swap">
<style>
/* "html body" outranks Quasar's own body font, whichever stylesheet loads last. */
html body, .q-field:not(.font-mono) { font-family: "Atkinson Hyperlegible", "Segoe UI", system-ui, sans-serif; }
/* Headings use the rounded font, like the h1/h2 on the Learn pages. */
html body .text-2xl, html body .text-3xl, html body .text-4xl, html body .text-5xl, .q-btn .q-btn__content {
  font-family: "Baloo 2", "Trebuchet MS", system-ui, sans-serif; font-weight: 700;
}
html body .am-story { font-family: "Atkinson Hyperlegible", "Segoe UI", system-ui, sans-serif; font-weight: 400; }
/* 5/6 drawn as 5 over a bar over 6. */
.am-frac {
  display: inline-flex; flex-direction: column; align-items: center; vertical-align: middle;
  line-height: 1; font-size: .85em; margin: 0 .12em;
}
.am-frac > span:first-child { border-bottom: .09em solid currentColor; padding: 0 .12em .08em; }
.am-frac > span:last-child { padding-top: .08em; }

/* Same look as the Learn pages (their dark colors): graph paper, cards, one yellow highlight. */
:root {
  --am-paper: #10161f; --am-grid: #1a2331; --am-surface: #172131; --am-ink: #e8eef6; --am-muted: #9babbf;
  --am-line: #2d3a4d; --am-mark: #f0b429; --am-on-mark: #1b2737; --am-cool: #1d6a86; --am-cool-light: #62b6d6;
  --am-good: #2f8a57; --am-bad: #c8394d;
}
body.body--dark, body {
  background-color: var(--am-paper);
  background-image: linear-gradient(var(--am-grid) 1px, transparent 1px),
                    linear-gradient(90deg, var(--am-grid) 1px, transparent 1px);
  background-size: 24px 24px;
  color: var(--am-ink);
}
.am-bench, .q-card.am-bench {
  background: var(--am-surface) !important; color: var(--am-ink);
  border: 1.5px solid var(--am-line); border-radius: 18px; box-shadow: none;
}
.am-end { border: 3px solid var(--am-mark) !important; }
.am-title { font-family: "Baloo 2", "Trebuchet MS", system-ui, sans-serif; font-weight: 800; line-height: 1.1; }
/* A thick underline pulled up behind the letters; a background would sit below Baloo's tall descent. */
.am-hl {
  text-decoration: underline; text-decoration-color: var(--am-mark); text-decoration-thickness: .38em;
  text-underline-offset: -.28em; text-decoration-skip-ink: none;
}
.am-muted { color: var(--am-muted); }
.q-btn.am-btn { border-radius: 12px; font-weight: 800; text-transform: none; }
.q-btn.am-mark { background: var(--am-mark) !important; color: var(--am-on-mark) !important; }
.q-btn.am-cool { background: var(--am-cool) !important; color: #fff !important; }
.q-btn.am-good { background: var(--am-good) !important; color: #fff !important; }
.q-btn.am-bad { background: var(--am-bad) !important; color: #fff !important; }
.q-btn.am-key { background: var(--am-surface) !important; color: var(--am-ink) !important; border: 1.5px solid var(--am-line); }
.q-btn.am-key:hover { border-color: var(--am-cool-light); }
.am-progress .q-linear-progress__model { background: var(--am-mark) !important; }
.am-progress .q-linear-progress__track { background: var(--am-line) !important; opacity: 1; }
.am-chip {
  border: 1.5px solid var(--am-line); border-radius: 999px; padding: 6px 16px; background: var(--am-surface);
  color: var(--am-ink); font-weight: 700; text-decoration: none;
}
.am-chip:hover { border-color: var(--am-cool-light); }

/* Big scratchpad: the same scratchpad fills the screen, with the problem pinned above the drawing. */
.am-scratch:not(.am-scratch-full) .am-scratch-only { display: none !important; }
.am-scratch-full .am-scratch-open { display: none !important; }
.am-scratch-full {
  position: fixed; inset: 0; z-index: 2000; background: var(--am-paper); flex-wrap: nowrap !important;
  padding: max(12px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right))
           max(12px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
}
.am-scratch-full section[aria-label="Scratchpad"] {
  max-width: none !important; flex: 1; min-height: 0; display: flex; flex-direction: column;
}
.am-scratch-full .sp-tip { display: none; }
/* Keep the 4:3 shape (strokes are stored as fractions of the size) and grow as big as fits. */
.am-scratch-full .sp-canvas-box { flex: 1; min-height: 0; container-type: size; display: grid; place-items: center; }
.am-scratch-full .sp-canvas-box canvas { width: min(100cqw, 133.33cqh) !important; }
.am-scratch-answer {
  min-width: 7em; min-height: 1.6em; line-height: 1.6em; padding: 4px 12px; border-radius: 10px; border: 1.5px solid var(--am-line);
  background: var(--am-surface); font-family: ui-monospace, monospace;
}
.q-btn.am-minikey { min-width: 48px; min-height: 48px; padding: 0 10px; }
body.am-noscroll { overflow: hidden; }

/* Quiz page: a rail for the fight, question and keypad; the scratchpad takes the rest. */
.am-quiz {
  display: grid; grid-template-columns: 380px minmax(0, 1fr); gap: 18px; align-items: start;
  width: 100%; max-width: 1400px;
}
@media (max-width: 900px) { .am-quiz { grid-template-columns: minmax(0, 1fr); } }
.am-face { font-size: 2.2rem; line-height: 1; }
.am-hearts { font-size: .75rem; letter-spacing: -1px; }
.am-mini-road { display: flex; align-items: center; gap: 3px; white-space: nowrap; font-weight: 700; }
.am-dot { width: 9px; height: 9px; border-radius: 50%; border: 2px solid #d6b07a; }
.am-dot.on { background: #fde68a; border-color: #fde68a; }
.am-keys { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; width: 100%; }
.am-keys .q-btn { min-height: 46px; }
.am-keys .am-key-wide { grid-column: span 2; }
.am-pin { background: #1d2a3d; border-radius: 12px; padding: 10px 14px; }
.am-pin-q { font-size: 1.05rem; }
.am-scratch-full .am-pin-q { font-size: 1.5rem; }
.am-scratch-full .am-scratch-hide { display: none !important; }
.am-scratch-full.am-bench { border-radius: 0; border: 0; }
.am-scratch .sp-tip { display: none; }
/* Stacked on a narrow screen, the question card sits right above, so the pin only keeps its button. */
@media (max-width: 900px) {
  .am-scratch:not(.am-scratch-full) .am-pin-q { display: none; }
  .am-scratch:not(.am-scratch-full) .am-pin { background: none; padding: 0; justify-content: flex-end; }
}
</style>
'''

# Picture walkthroughs in learn/, served at /learn. Free to open; they never cost a heart.
LEARN_DIR = Path(__file__).resolve().parent / "learn"
LEARN_TOPICS = {
    "multiplication.html": "Multiplication",
    "fractions.html": "Fractions",
    "percent.html": "Percents",
    "lcm-gcf.html": "LCM & GCF",
    "algebra.html": "Equations",
    "slope.html": "Slope",
}
LEARN_PAGES = {
    "*": "multiplication.html", "x": "multiplication.html",
    "fraction": "fractions.html",
    "percent": "percent.html",
    "lcm": "lcm-gcf.html", "gcf": "lcm-gcf.html",
    "alg": "algebra.html", "multi_alg": "algebra.html", "hard_alg": "algebra.html",
    "slope": "slope.html",
}


FRACTION = re.compile(r"(\d+)/(\d+)")


def stacked_fractions(text):
    """HTML for question text with fractions like 5/6 drawn as 5 over a bar over 6."""
    return FRACTION.sub(r'<span class="am-frac"><span>\1</span><span>\2</span></span>', escape(text))


def learn_url(symbol):
    page = LEARN_PAGES.get(symbol)
    return f"/learn/{page}" if page else None


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

# ---------- WIN STREAK & TREATS ----------
# Kept on the server (not in each browser) so every device counts toward the same streak.
# data/ is git-ignored, so deploys never overwrite it.
STATS_PATH = Path("data") / "stats.json"
WINS_FOR_TREAT = 7


def load_stats() -> dict:
    try:
        return json.loads(STATS_PATH.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def treat_dots_html(wins: int) -> str:
    """The castle road in one line for the quiz page: a dot per win toward the next treat."""
    wins = min(wins, WINS_FOR_TREAT)
    dots = "".join(f'<span class="am-dot{" on" if i < wins else ""}"></span>' for i in range(WINS_FOR_TREAT))
    return f"🏰 {dots} {wins} of {WINS_FOR_TREAT}"


def kid_stats(name: str) -> dict:
    return {"wins": 0, "streak": 0, "games_over": 0, "treats": 0, **load_stats().get(name, {})}


def record_result(name: str, won: bool) -> dict:
    """Count a finished quiz or a game over. Every WINS_FOR_TREAT wins earns a treat.
    Returns the kid's stats, with "treat" True when one was just earned. ("streak" is wins since the last treat.)"""
    stats = load_stats()
    kid = {"wins": 0, "streak": 0, "games_over": 0, "treats": 0, **stats.get(name, {})}
    earned = False
    if won:
        kid["wins"] += 1
        kid["streak"] += 1
        if kid["streak"] >= WINS_FOR_TREAT:
            earned = True
            kid["treats"] += 1
            kid["streak"] = 0
            kid["last_treat"] = time.strftime("%B %-d, %Y")
    else:
        kid["games_over"] += 1  # a game over only restarts that game; wins toward a treat are kept
    stats[name] = kid
    STATS_PATH.parent.mkdir(exist_ok=True)
    temp = STATS_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(stats, indent=2))
    temp.replace(STATS_PATH)  # never leave a half-written file behind
    return {**kid, "treat": earned}


def treat_progress(kid: dict) -> str:
    left = WINS_FOR_TREAT - kid["streak"]
    return f"{kid['streak']} of {WINS_FOR_TREAT} wins · {left} more to the castle 🎁"


def castle_road_svg(wins: int, avatar: str) -> str:
    """A winding road from the start flag to a treat castle; the avatar stands on the stone for each win."""
    width, height = 440, 130
    # Stop 0 is the start, stops 1-6 are stones, stop 7 is the castle.
    stops = [(36 + i * (370 / WINS_FOR_TREAT), 78 - 16 * math.sin(i * 1.1)) for i in range(WINS_FOR_TREAT + 1)]
    road = " ".join(f"{x:.0f},{y:.0f}" for x, y in stops)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg" role="img">',
        f'<title>{treat_progress({"streak": wins})}</title>',
        f'<rect width="{width}" height="{height}" rx="16" fill="#bae6fd" />',
        f'<rect y="{height * 0.45:.0f}" width="{width}" height="{height * 0.55:.0f}" rx="16" fill="#86efac" />',
        f'<polyline points="{road}" fill="none" stroke="#d6b37a" stroke-width="16" '
        'stroke-linecap="round" stroke-linejoin="round" />',
        f'<text x="{stops[0][0]:.0f}" y="{stops[0][1] + 8:.0f}" font-size="20" text-anchor="middle">🚩</text>',
    ]
    for i, (x, y) in enumerate(stops[1:WINS_FOR_TREAT], start=1):
        done = i <= wins
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="10" fill="{"#facc15" if done else "#f3f4f6"}" '
                     'stroke="#92400e" stroke-width="2" />')
        parts.append(f'<text x="{x:.0f}" y="{y + 4:.0f}" font-size="11" font-weight="bold" text-anchor="middle" '
                     f'font-family="sans-serif" fill="#78350f">{i}</text>')
    castle_x, castle_y = stops[-1]
    parts += [
        f'<text x="{castle_x:.0f}" y="{castle_y + 10:.0f}" font-size="44" text-anchor="middle">🏰</text>',
        f'<text x="{castle_x + 18:.0f}" y="{castle_y - 26:.0f}" font-size="20" text-anchor="middle">🎁</text>',
    ]
    avatar_x, avatar_y = stops[wins]
    parts += [
        f'<text x="{avatar_x:.0f}" y="{avatar_y - 14:.0f}" font-size="30" text-anchor="middle">{avatar}</text>',
        f'<text x="{width / 2:.0f}" y="{height - 10}" font-size="15" font-weight="bold" text-anchor="middle" '
        f'font-family="sans-serif" fill="#14532d">{treat_progress({"streak": wins})}</text>',
        "</svg>",
    ]
    return "".join(parts)


END_MESSAGES = {3: "Perfect! Not a single miss!", 2: "Awesome work!", 1: "Great practice! Keep going!"}
# How each kind of problem is named in the email to the parent.
TOPIC_NAMES = {
    "+": "adding", "-": "subtracting", "*": "times tables", "x": "times tables", "÷": "dividing",
    "fraction": "fractions", "alg": "equations", "multi_alg": "equations", "hard_alg": "harder equations",
    "mix": "mixed problems", "parens": "parentheses", "decimal_multi_div": "decimals", "slope": "slope",
    "ruler": "inch ruler", "cm_ruler": "centimeter ruler", "lcm": "LCM", "gcf": "GCF", "percent": "percents",
}


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
    def __init__(self, total_problems=20, allowed_ops=None, name="player", multiplication_range=(3, 12),
                 times_table=None):
        self.total_problems = total_problems
        self.allowed_ops = allowed_ops or ["+"]
        self.name = name
        self.multiplication_range = multiplication_range
        # e.g. 3: every × problem uses 3, the other number from multiplication_range; [3, 4]: 3 or 4 each time
        self.times_table = times_table

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
        self.treat_label = None
        self.battle_avatar_label = self.battle_enemy_label = None
        self.battle_caption_label = self.battle_status_label = None
        self.hint_button = None
        self.learn_button = None
        self.scratch_problem = None  # problem pinned above the big scratchpad
        self.scratch_full = False
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
            if self.symbol in ["fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler", "percent", "hard_alg"]:
                if self.symbol == "ruler":
                    if "/" not in user_input:
                        raise ValueError("Fraction required for ruler")
                    num_str, den_str = user_input.split("/", 1)
                    num, den = int(num_str), int(den_str)
                    if math.gcd(num, den) != 1:
                        self.feedback = "Use simplest form (e.g., 1/4 instead of 2/8)."
                        self.feedback_color = "#f07082"  # readable red on the dark page
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
                            self.feedback_color = "#f07082"  # readable red on the dark page
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
        if self.answer_label and self.in_play and not self.answer_pending and not self.scratch_full:
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
        self.feedback = ""  # pick up quietly where she left off
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

    def game_report(self, outcome: str, kid: dict) -> str:
        """The email body about one finished game: how it went and what was practiced."""
        topics = ", ".join(dict.fromkeys(TOPIC_NAMES.get(op, op) for op in self.allowed_ops))
        return (f"{outcome}\n\n"
                f"Practiced: {topics}\n"
                f"Time: {format_duration(time.time() - self.start_time)} • Misses: {self.wrong} • "
                f"Hearts left: {self.life} of {MAX_LIFE}\n"
                f"Wins toward the next treat: {kid['streak']} of {WINS_FOR_TREAT} ({kid['wins']} wins in total)")

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        self.enemy = None
        self.animate(self.enemy_label, "pop-in")  # the trophy replaces the knocked-out enemy
        self.celebrate()
        self.finish("🎉 Finished!", f"Time {total_time}s, Wrong {self.wrong}, Life {self.life}")
        kid = record_result(self.name, won=True)
        self.update_treat_label(kid)
        stars = star_rating(self.wrong)
        report = self.game_report(f"{self.name.capitalize()} won the math game: all {self.total_problems} "
                                  f"questions, {'⭐' * stars}.", kid)
        if kid["treat"]:
            # One email covers both the game and the treat.
            notify.send_in_background(
                f"🎁 {self.name.capitalize()} earned free treat #{kid['treats']}!",
                f"{self.name.capitalize()} reached the castle on {kid['last_treat']}: "
                f"{WINS_FOR_TREAT} more math games won ({kid['wins']} in total).\n\n"
                f"{report}\n\n"
                "They'll be showing you their treat screen soon! 🍦🧋🍩")
            self.show_end_card(
                "🎁 FREE TREAT! 🎁", "🍦🧋🍩",
                f"{WINS_FOR_TREAT} wins! Treat #{kid['treats']} earned {kid['last_treat']}.",
                "Show this screen to get any treat you want: ice cream, boba, anything yummy!",
                "🔁 Play again")
            return
        notify.send_in_background(f"✅ {self.name.capitalize()} finished a math game {'⭐' * stars}", report)
        self.show_end_card("🎉 You did it!", "⭐" * stars,
                           f"Time: {format_duration(total_time)} • Misses: {self.wrong} • ❤️ {self.life} left",
                           f"{END_MESSAGES[stars]} {WINS_FOR_TREAT - kid['streak']} more wins for a free treat! 🍦",
                           "🔁 Play again")

    def game_over(self):
        self.finish("💀 Game over!", f"Game over: beat {self.defeated} of {self.total_problems}, Wrong {self.wrong}")
        kid = record_result(self.name, won=False)
        self.update_treat_label(kid)
        notify.send_in_background(
            f"💀 {self.name.capitalize()}'s math game ended early",
            self.game_report(f"{self.name.capitalize()} ran out of hearts after beating {self.defeated} of "
                             f"{self.total_problems} questions. The {self.enemy} won this time.", kid))
        self.show_end_card("💀 Game over!", "😵",
                           f"You beat {self.defeated} of {self.total_problems} enemies. "
                           f"The {self.enemy} got you this time.",
                           f"Try again! Your {kid['streak']} of {WINS_FOR_TREAT} wins are safe. 💪", "🔁 Try again")

    def update_treat_label(self, kid=None):
        if self.treat_label:
            self.treat_label.set_content(treat_dots_html((kid or kid_stats(self.name))["streak"]))

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
                                            remove='whitespace-normal text-2xl text-lg am-story')
            else:
                # Word problems read better in the body font; short equations use the rounded one.
                if len(displayed_question) > 40:
                    self.question_label.classes(add='whitespace-normal text-lg am-story',
                                                remove='font-mono whitespace-pre text-4xl text-2xl')
                else:
                    self.question_label.classes(add='whitespace-normal text-2xl',
                                                remove='font-mono whitespace-pre text-4xl text-lg am-story')
            self.question_label.set_content(stacked_fractions(displayed_question))
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
            if active and not self.scratch_full:
                self.answer_label.run_method('focus')
        if self.scratch_problem:
            self.scratch_problem.set_content(stacked_fractions(self.question))
        if self.svg_container:
            self.svg_container.set_content(self.question_svg or "")
        if self.plot:
            self.plot.visible = self.symbol == "slope"  # the graph area is blank for everything else
        if self.hint_container:
            self.hint_container.set_content(
                handlers.visuals.build_svg(self.hint, self.hint_level) if self.hint_level else "")
        if self.hint_button:
            self.hint_button.set_text("💡 Show me" if self.hint_level == 0 else "💡 Another hint")
            self.hint_button.visible = (bool(self.hint) and not self.answer_pending
                                        and self.hint_level < handlers.visuals.hint_steps(self.hint))
        if self.learn_button:
            self.learn_button.visible = self.in_play and learn_url(self.symbol) is not None

    def open_learn_page(self):
        url = learn_url(self.symbol)
        if url:
            ui.navigate.to(url, new_tab=True)


# keypad helpers
def add_char(quiz: MathQuizGame, ch: str):
    if quiz.answer_pending:
        return
    quiz.input_text += ch
    if quiz.answer_label:
        quiz.answer_label.set_value(quiz.input_text)


def delete_char(quiz: MathQuizGame):
    """Erase the last character typed (the keypad's DELETE key and Backspace)."""
    quiz.input_text = quiz.input_text[:-1]
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
        delete_char(quiz)
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
    # This container only displays our own markup: SVG from the ruler and visuals handlers, and page titles.
    options = {'sanitize': False} if 'sanitize' in inspect.signature(ui.html).parameters else {}
    return ui.html('', **options).classes(classes)


def make_quiz_page(total_problems: int, name: str, ops: list, multiplication_range=(3, 12), times_table=None):
    @ui.page(f'/{name}', dark=True)
    def page():
        quiz = MathQuizGame(total_problems=total_problems,
                            allowed_ops=ops, name=name, multiplication_range=multiplication_range,
                            times_table=times_table)
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

        # Left rail: the fight, the question and the keypad together. Right: the scratchpad, problem pinned on top.
        with ui.element('div').classes("am-quiz") as quiz_layout:
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
            with ui.column().classes("am-rail gap-3 min-w-0"):
                with ui.row().classes("items-center gap-3 no-wrap"):
                    ui.link("🏠", "/").classes("text-2xl no-underline").props('aria-label="Home"')
                    create_svg_container("am-title text-2xl").set_content(
                        f'{name.capitalize()}\'s <span class="am-hl">Adventure</span>')

                # The fight, progress through the quiz, and wins toward the treat castle.
                with ui.column().classes("am-bench gap-2 px-4 py-3 w-full"):
                    with ui.row().classes("items-center justify-between w-full no-wrap gap-1"):
                        quiz.avatar_label = ui.label(get_avatar(name)).classes("am-face inline-block")
                        quiz.life_label = ui.label("❤️" * MAX_LIFE).classes("am-hearts")
                        ui.label("⚔️").classes("text-lg")
                        quiz.enemy_hp_label = ui.label("").classes("am-hearts")
                        quiz.enemy_label = ui.label("").classes("am-face inline-block")
                    with ui.row().classes("items-center justify-between w-full no-wrap text-sm am-muted"):
                        quiz.progress_label = ui.label("")
                        quiz.treat_label = create_svg_container("am-mini-road")
                        quiz.update_treat_label()
                    quiz.progress_bar = ui.linear_progress(value=0, show_value=False, size='12px',
                                                           color='orange').props('rounded').classes('am-progress w-full')

                def pick_avatar(avatar):
                    set_avatar(name, avatar)
                    quiz.avatar_label.set_text(avatar)
                    quiz.update_treat_label()
                    quiz.celebrate()

                with ui.column().classes("am-bench gap-3 px-4 py-4 w-full"):
                    quiz.feedback_label = ui.label("").classes("text-lg")
                    quiz.question_label = create_svg_container("text-lg whitespace-normal")
                    with ui.row().classes("gap-2"):
                        quiz.hint_button = ui.button("💡 Show me", on_click=quiz.show_hint, color=None).classes(
                            "am-btn am-mark text-lg"
                        )
                        quiz.hint_button.visible = False
                        # Opens the picture walkthrough for this kind of problem in a new tab; free, unlike hints.
                        quiz.learn_button = ui.button("📖 Learn", on_click=quiz.open_learn_page,
                                                      color=None).classes("am-btn am-cool text-lg")
                        quiz.learn_button.visible = False

                with ui.card().classes("am-bench am-end items-center p-8 w-full") as quiz.end_card:
                    quiz.end_avatar_label = ui.label("").classes("text-7xl")
                    quiz.end_title_label = ui.label("🎉 You did it!").classes("text-3xl font-bold")
                    quiz.end_stars_label = ui.label("").classes("text-5xl")
                    quiz.end_details_label = ui.label("").classes("text-xl")
                    quiz.end_message_label = ui.label("").classes("text-xl font-semibold")
                quiz.end_card.visible = False

                play_area = ui.column().classes("am-bench gap-3 px-4 py-4 w-full")
                play_area.bind_visibility_from(quiz.end_card, 'visible', backward=lambda shown: not shown)
                with play_area:
                    quiz.answer_label = ui.input('Your answer').bind_value(quiz, 'input_text').props(
                        'outlined autocomplete=off'
                    ).classes('text-2xl font-mono w-full')
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
                    with ui.element('div').classes("am-keys").props('data-quiz-keypad'):
                        for key in ["1", "2", "3", "Del", "4", "5", "6", ".", "7", "8", "9", "/", "-", "0", "Enter"]:
                            if key == "Del":
                                ui.button("DELETE", on_click=lambda q=quiz: delete_char(q), color=None).classes(
                                    "am-btn am-bad text-base")
                            elif key == "Enter":
                                ui.button("ENTER", on_click=lambda q=quiz: q.check_answer(), color=None).classes(
                                    "am-btn am-good text-lg am-key-wide")
                            else:
                                ui.button(key, on_click=lambda _, k=key, q=quiz: add_char(q, k), color=None).classes(
                                    "am-btn am-key text-xl")
                    ui.label('Enter: submit • Backspace: erase one • Esc: clear all').classes('text-xs am-muted')

                quiz.start_button = ui.button("▶️ Start Quiz", on_click=lambda q=quiz: q.start(), color=None).classes(
                    "am-btn am-good text-xl px-6 py-3"
                ).props('data-quiz-start')

                # Kids can pick their player whenever a quiz isn't in progress.
                with ui.column().classes("gap-1") as avatar_picker:
                    ui.label("Pick your player:").classes("text-lg")
                    with ui.row().classes("gap-1"):
                        for avatar in AVATARS:
                            ui.button(avatar, on_click=lambda _, a=avatar: pick_avatar(a)).props(
                                'flat round'
                            ).classes("text-3xl")
                avatar_picker.bind_visibility_from(quiz.start_button, 'visible')

            # Scratch work stays visible while moving through follow-up questions.
            with ui.column().classes("am-bench am-scratch gap-3 px-4 py-4 min-w-0") as scratch_area:
                def set_big_scratchpad(on):
                    quiz.scratch_full = on
                    if on:
                        scratch_area.classes(add="am-scratch-full")
                    else:
                        scratch_area.classes(remove="am-scratch-full")
                    ui.run_javascript(f"document.body.classList.toggle('am-noscroll', {str(on).lower()})")
                    quiz.update_ui()

                # Pinned above the drawing, so Undo, Clear and the pen can never touch the problem.
                with ui.row().classes("am-pin items-center gap-3 w-full no-wrap"):
                    with ui.column().classes("gap-0 flex-1 min-w-0"):
                        quiz.scratch_problem = create_svg_container("am-pin-q am-story whitespace-normal")
                        ui.label().bind_text_from(quiz, 'feedback').classes("am-scratch-only text-lg")
                    ui.button("✏️ Big", on_click=lambda: set_big_scratchpad(True), color=None).classes(
                        "am-scratch-open am-btn am-cool text-lg")
                    ui.button("✕ Done", on_click=lambda: set_big_scratchpad(False), color=None).classes(
                        "am-scratch-only am-btn am-cool text-lg")
                # Hint pictures are wide, so they show here, right where she's working.
                quiz.hint_container = create_svg_container("max-w-full overflow-x-auto")
                Scratchpad().classes('w-full')
                # Answer from the big scratchpad without the on-screen keyboard covering the work.
                with ui.row().classes("am-scratch-only items-center gap-2 w-full justify-center"):
                    ui.label().bind_text_from(quiz, 'input_text', backward=lambda t: t or " ").classes(
                        "am-scratch-answer text-2xl")
                    for key in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", ".", "/", "-"]:
                        ui.button(key, on_click=lambda _, k=key: add_char(quiz, k), color=None).classes(
                            "am-btn am-key am-minikey text-xl")
                    ui.button("DELETE", on_click=lambda: delete_char(quiz), color=None).classes(
                        "am-btn am-bad am-minikey text-lg")
                    ui.button("ENTER", on_click=quiz.check_answer, color=None).classes(
                        "am-btn am-good am-minikey text-lg")
                # Pictures that belong to the question itself (rulers, slope graphs).
                quiz.svg_container = create_svg_container("am-scratch-hide max-w-full overflow-x-auto")
                quiz.plot = ui.pyplot().classes("am-scratch-hide w-[500px] max-w-full h-[400px]")

        # The fight pops up over everything after each answer, then closes itself.
        with ui.dialog() as quiz.battle_dialog, ui.card().classes(
                "am-bench items-center gap-2 px-10 py-8"):
            with ui.row().classes("items-center gap-10"):
                quiz.battle_avatar_label = ui.label("").classes("text-8xl inline-block")
                ui.label("⚔️").classes("text-5xl")
                quiz.battle_enemy_label = ui.label("").classes("text-8xl inline-block")
            quiz.battle_caption_label = ui.label("").classes("text-2xl font-bold")
            quiz.battle_status_label = ui.label("").classes("text-sm whitespace-pre")

        ui.timer(0.1, restore_progress, once=True)
    return page


ui.add_head_html(APP_FONTS_HTML, shared=True)
app.add_static_files('/learn', LEARN_DIR)

# ---------- REGISTER QUIZ PAGES ----------
# make_quiz_page(15, "autumn", ["multi_alg", "fraction", "slope", "decimal_multi_div", "ruler", "cm_ruler"])
#(15, "autumn", ["lcm", "gcf", "percent"])
make_quiz_page(15, "autumn", ["lcm", "gcf", "percent", "hard_alg"])
# Molly practices the 3s and 4s: each problem picks one table, times 1 through 10, on either side.
make_quiz_page(100, "molly", ["*"], times_table=[3,4], multiplication_range=(1, 10))



# ---------- ROOT PAGE ----------
def root_page():
    with ui.column().classes("items-center justify-center w-full h-screen gap-6"):
        create_svg_container("am-title text-5xl").set_content('Welcome to Peaccion <span class="am-hl">Math!</span>')
        ui.label("Pick your player").classes("text-2xl mb-6")
        with ui.row().classes("gap-8 justify-center"):
            for name, kid in KIDS.items():
                with ui.card().classes(
                    f"items-center p-5 rounded-3xl cursor-pointer bg-gradient-to-br {kid['gradient']} "
                    "text-white w-96 max-w-full hover:scale-105 transition-transform"
                ).on('click', lambda _, n=name: ui.navigate.to(f'/{n}')):
                    ui.label(get_avatar(name)).classes("text-6xl")
                    ui.label(name.capitalize()).classes("text-2xl font-bold")
                    stats = kid_stats(name)
                    create_svg_container("w-full").set_content(castle_road_svg(stats["streak"], get_avatar(name)))
                    if stats["treats"]:
                        ui.label(f"🎁 {stats['treats']} treat{'s' if stats['treats'] > 1 else ''} earned").classes(
                            "text-sm font-bold")
                    ui.label("Let's play! ▶️").classes("text-lg")
        ui.label("📖 Learn with pictures").classes("text-2xl mt-6")
        with ui.row().classes("gap-3 justify-center"):
            for page, title in LEARN_TOPICS.items():
                ui.link(title, f"/learn/{page}", new_tab=True).classes("am-chip text-lg")

ui.page('/',dark=True)(root_page)
# Two ways to start:
#   python3 Autumn_Math_NiceGUI.py  -> NiceGUI's own server on port 8080 (what the server runs; nginx forwards to it)
#   uvicorn Autumn_Math_NiceGUI:fastapi_app --host 0.0.0.0 --port 8000 --reload  -> for local development
if __name__ == '__main__':
    # Disable development file watching when running on the server.
    ui.run(storage_secret='super-secret-key', reload=False, show=False)
elif __name__ == 'Autumn_Math_NiceGUI':  # imported by uvicorn (tests load the file under another name)
    fastapi_app = FastAPI()
    ui.run_with(fastapi_app, storage_secret='super-secret-key')
