import math
import random
import re


LCM_STORIES = (
    "Two bells ring together now. One rings every {a} minutes and the other every {b} minutes. "
    "How many minutes will pass before they next ring together? Enter the number of minutes.",
    "Two lights flash together now. One flashes every {a} seconds and the other every {b} seconds. "
    "How many seconds will pass before they next flash together? Enter the number of seconds.",
    "Pencils come in packs of {a} and erasers come in packs of {b}. Autumn buys only full packs "
    "and wants the same number of pencils as erasers. What is the smallest positive number "
    "of pencils she can buy? Enter the number of pencils.",
)

GCF_STORIES = (
    "Autumn has {a} pencils and {b} erasers. She puts all of them into identical gift bags, "
    "with the same number of pencils in each bag and the same number of erasers in each bag. "
    "What is the greatest number of bags she can make with nothing left over? Enter the number of bags.",
    "A red ribbon is {a} centimeters long and a blue ribbon is {b} centimeters long. Autumn cuts "
    "both ribbons into pieces of the same whole-number length, with nothing left over. "
    "What is the greatest possible length of each piece? Enter the length in centimeters.",
    "A teacher has {a} apples and {b} oranges. She uses all the fruit to make identical baskets, "
    "with the same number of apples in each basket and the same number of oranges in each basket. "
    "What is the greatest number of baskets she can make? Enter the number of baskets.",
)


def lcm(quiz):
    a, b = random.randint(10, 100), random.randint(10, 100)
    quiz.solution = math.lcm(a, b)
    story = random.choice(LCM_STORIES)
    quiz.question = story.format(a=a, b=b)
    quiz.follow_up_questions = make_follow_ups('lcm', story, a, b)
    quiz.clear_plot()


def gcf(quiz):
    a, b = random.randint(10, 100), random.randint(10, 100)
    quiz.solution = math.gcd(a, b)
    story = random.choice(GCF_STORIES)
    quiz.question = story.format(a=a, b=b)
    quiz.follow_up_questions = make_follow_ups('gcf', story, a, b)
    quiz.clear_plot()


def make_follow_ups(symbol, story, a, b):
    if symbol == 'lcm':
        result = math.lcm(a, b)
        answers = (result // a, result // b)
        if story == LCM_STORIES[0]:
            context = f"The bells ring every {a} and {b} minutes and next ring together after {result} minutes. "
            prompts = (
                f"Not counting the ring at the start, how many times does the bell that rings every {a} minutes ring up to and including that time?",
                f"Not counting the ring at the start, how many times does the bell that rings every {b} minutes ring up to and including that time?",
            )
        elif story == LCM_STORIES[1]:
            context = f"The lights flash every {a} and {b} seconds and next flash together after {result} seconds. "
            prompts = (
                f"Not counting the flash at the start, how many times does the light that flashes every {a} seconds flash up to and including that time?",
                f"Not counting the flash at the start, how many times does the light that flashes every {b} seconds flash up to and including that time?",
            )
        else:
            context = f"Autumn buys {result} pencils and {result} erasers. Pencils come in packs of {a} and erasers in packs of {b}. "
            prompts = ("How many packs of pencils does she buy?", "How many packs of erasers does she buy?")
    else:
        result = math.gcd(a, b)
        answers = (a // result, b // result)
        if story == GCF_STORIES[0]:
            context = f"Autumn splits {a} pencils and {b} erasers equally among {result} identical gift bags, with nothing left over. "
            prompts = ("How many pencils are in each bag?", "How many erasers are in each bag?")
        elif story == GCF_STORIES[1]:
            context = f"Autumn cuts a {a}-centimeter red ribbon and a {b}-centimeter blue ribbon into {result}-centimeter pieces, with nothing left over. "
            prompts = ("How many red pieces does she get?", "How many blue pieces does she get?")
        else:
            context = f"The teacher splits {a} apples and {b} oranges equally among {result} identical baskets, with nothing left over. "
            prompts = ("How many apples are in each basket?", "How many oranges are in each basket?")
    return [
        {"question": context + prompt + " Enter a whole number.", "solution": answer}
        for prompt, answer in zip(prompts, answers)
    ]


def restore_follow_ups(quiz):
    """Upgrade saved primary stories without repeating already completed follow-ups."""
    stories = LCM_STORIES if quiz.symbol == 'lcm' else GCF_STORIES
    for story in stories:
        pattern = re.escape(story).replace(r'\{a\}', r'(?P<a>\d+)').replace(r'\{b\}', r'(?P<b>\d+)')
        match = re.fullmatch(pattern, quiz.question)
        if match:
            a, b = int(match['a']), int(match['b'])
            if 10 <= a <= 100 and 10 <= b <= 100:
                quiz.follow_up_questions = make_follow_ups(quiz.symbol, story, a, b)
            return
