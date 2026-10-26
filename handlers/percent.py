import random
from fractions import Fraction

DOLLARS = "Enter the amount in dollars (like 4.50)."
PERCENT = "Enter the percent as a number (like 25)."

# (setup, name of the part, question for the part, question for the total, +1 adds / -1 takes away, percents)
PART_STORIES = (
    ("A jacket costs {price}. It is on sale for {pct}% off.",
     "discount", "How many dollars is the discount?", "What is the sale price?",
     -1, (10, 15, 20, 25, 30, 40, 50, 75)),
    ("Autumn buys a video game for {price}. Sales tax is {pct}%.",
     "sales tax", "How much is the sales tax?", "How much does she pay in total, with tax?",
     1, (5, 6, 8, 10)),
    ("A concert ticket costs {price}. The ticket website adds a {pct}% service fee.",
     "service fee", "How much is the service fee?", "What is the total cost of the ticket with the fee?",
     1, (5, 10, 12, 15, 20)),
    ("Autumn returns a scooter that cost {price}. The store keeps a {pct}% restocking fee.",
     "restocking fee", "How much does the store keep?", "How much money does Autumn get back as a refund?",
     -1, (10, 15, 20, 25)),
    ("A credit card has a balance of {price}. The card charges {pct}% interest for the month.",
     "interest", "How much interest is added?", "What is the new balance after the interest is added?",
     1, (2, 3, 5)),
)

# (story, percents); prices are multiples of 20 so the dollar amounts stay whole.
FIND_PERCENT_STORIES = (
    ("A backpack that costs {price} is on sale for {part} off. What percent is the discount?",
     (10, 15, 20, 25, 30, 40, 50, 75)),
    ("Autumn paid {part} in sales tax on a {price} purchase. What is the sales tax rate?",
     (5, 10)),
    ("Autumn returned a {price} order and got a {part} refund. What percent of her money did she get back?",
     (50, 75, 80, 90)),
)


def money(amount) -> str:
    cents = int(Fraction(amount) * 100)
    return f"${cents // 100}" if cents % 100 == 0 else f"${cents // 100}.{cents % 100:02d}"


def generate(quiz):
    if random.random() < 0.3:
        find_percent(quiz)
    else:
        find_part(quiz)
    quiz.clear_plot()


def find_part(quiz):
    setup, name, ask_part, ask_total, sign, percents = random.choice(PART_STORIES)
    price, pct = random.randint(12, 200), random.choice(percents)
    part = Fraction(price * pct, 100)
    intro = setup.format(price=money(price), pct=pct)
    quiz.question = f"{intro} {ask_part} {DOLLARS}"
    quiz.solution = part
    # Saved progress is JSON, so the follow-up keeps its answer as text.
    quiz.follow_up_questions = [{
        "question": f"{intro} The {name} is {money(part)}. {ask_total} {DOLLARS}",
        "solution": str(price + sign * part),
    }]
    quiz.hint = {"kind": "percent", "whole": price, "pct": pct, "sign": sign}


def find_percent(quiz):
    story, percents = random.choice(FIND_PERCENT_STORIES)
    price, pct = 20 * random.randint(2, 10), random.choice(percents)
    part = price * pct // 100
    quiz.question = f"{story.format(price=money(price), part=money(part))} {PERCENT}"
    quiz.solution = pct
    quiz.hint = {"kind": "percent", "whole": price, "part": part}
