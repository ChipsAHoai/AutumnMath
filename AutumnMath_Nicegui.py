from nicegui import ui
import random
import time

# Global variables
wrong = 0
current_problem = {}
start_time = None
total_problems = 20
problem_index = 0

# Layout containers for easy updates
layout = None
problem_label = None
question_label = None
answer_input = None
submit_button = None
start_button = None

def generate_problem():
    global current_problem
    operator = ["%", "x", "alg", "mix", "multi_alg", "parens"]
    symbol = random.choice(operator)
    problem_data = {"symbol": symbol, "solution": None, "display": ""}

    if symbol == 'x':
        x = random.randint(3, 99)
        y = random.randint(11, 99)
        problem_data["solution"] = x * y
        problem_data["display"] = f"{x} * {y} = ?"
    elif symbol == "%":
        division = random.randint(2, 999)
        y = random.randint(2, 9)
        x = division * y
        problem_data["solution"] = division
        problem_data["display"] = f"{x} ÷ {y} = ?"
    elif symbol == 'alg':
        formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
        chosen = random.choice(formats)
        problem_data["format"] = chosen

        if chosen == "a*x+b=c":
            a = random.randint(1, 12)
            x_val = random.randint(1, 10)
            b = random.randint(1, 20)
            c = a * x_val + b
            problem_data["solution"] = x_val
            problem_data["display"] = f"{a} * __ + {b} = {c}"

        elif chosen == "a*x-b=c":
            a = random.randint(1, 12)
            x_val = random.randint(1, 10)
            b = random.randint(1, 20)
            c = a * x_val - b
            problem_data["solution"] = x_val
            problem_data["display"] = f"{a} * __ - {b} = {c}"

        elif chosen == "a+b*x=c":
            b = random.randint(1, 12)
            x_val = random.randint(1, 10)
            a = random.randint(1, 20)
            c = a + b * x_val
            problem_data["solution"] = x_val
            problem_data["display"] = f"{a} + {b} * __ = {c}"

    elif symbol == "mix":
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 10)
        problem_data["solution"] = (a + b) * c
        problem_data["display"] = f"({a} + {b}) * {c} = ?"

    elif symbol == "multi_alg":
        x_val = random.randint(1, 10)
        a = random.randint(1, 5)
        c = random.randint(a + 1, a + 4)
        b = random.randint(0, 10)

        left = a * x_val + b
        right = c * x_val
        d = right - left

        problem_data["solution"] = x_val
        problem_data["display"] = f"{a}x + {b} = {c}x - {d}"

    elif symbol == "parens":
        formats = ["(a + b) * c", "a * (b - c)", "(a + b) + (c + d)", "(a * b) - (c * d)"]
        chosen = random.choice(formats)

        if chosen == "(a + b) * c":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            c = random.randint(1, 10)
            problem_data["solution"] = (a + b) * c
            problem_data["display"] = f"({a} + {b}) * {c} = ?"

        elif chosen == "a * (b - c)":
            b = random.randint(5, 15)
            c = random.randint(1, b)
            a = random.randint(1, 10)
            problem_data["solution"] = a * (b - c)
            problem_data["display"] = f"{a} * ({b} - {c}) = ?"

        elif chosen == "(a + b) + (c + d)":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            c = random.randint(1, 10)
            d = random.randint(1, 10)
            problem_data["solution"] = (a + b) + (c + d)
            problem_data["display"] = f"({a} + {b}) + ({c} + {d}) = ?"

        elif chosen == "(a * b) - (c * d)":
            a = random.randint(1, 10)
            b = random.randint(1, 5)
            c = random.randint(1, 4)
            d = random.randint(1, 3)
            problem_data["solution"] = (a * b) - (c * d)
            problem_data["display"] = f"({a} * {b}) - ({c} * {d}) = ?"

    current_problem = problem_data

async def check_answer():
    global wrong, problem_index
    try:
        answer = int(answer_input.value.strip())  # Trimming spaces and converting to integer
    except ValueError:
        answer = None

    if answer == current_problem["solution"]:
        # Custom success notification
        ui.notify("Great Job Autumn Baby Peaccion!", color="green")
        
        problem_index += 1
        if problem_index < total_problems:
            generate_problem()
            update_ui()
        else:
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            layout.clear()
            ui.label(f"Great job! You've finished in {duration} seconds.")
            ui.label(f"You got {wrong} incorrect answers.")
    else:
        wrong += 1
        ui.notify("Wrong answer, try again!", color="red")

def update_ui():
    problem_label.text = f"Problem {problem_index + 1} out of {total_problems}"
    question_label.text = current_problem["display"]
    answer_input.value = ""  # Clear input field for next answer

    # Remove start button once quiz has started
    start_button.visible = False

    # Display the answer-related fields
    answer_input.visible = True
    submit_button.visible = True

async def main():
    global start_time, problem_index, wrong
    start_time = time.time()
    problem_index = 0
    wrong = 0
    generate_problem()
    update_ui()

# Layout and UI components
with ui.row().classes('items-center'):
    start_button = ui.button("Start Math Practice", on_click=main).classes('text-4xl')

# Layout container for the problem and input components
layout = ui.column()

with layout:
    problem_label = ui.label("").classes('text-4xl')  # Even bigger font size
    question_label = ui.label("").classes('text-4xl')  # Even bigger font size
    answer_input = ui.input(label="Your Answer").classes('text-4xl')  # Set bigger font size
    submit_button = ui.button("Submit", on_click=check_answer).classes('text-4xl')


# Event listener for Enter key
def handle_key(e):
    if e.event_type == "keydown" and e.key == "Enter":  # Check for keydown and Enter
        submit_button.click()  # Trigger submit button click

# Attach the event handler to the input field
answer_input.on("keydown", handle_key)
# Continue with the rest of your code as it is

# Run the app
ui.run()
