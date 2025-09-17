import pygame
import random
import time
from art import *

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
FONT = pygame.font.SysFont("Arial", 32)
LARGE_FONT = pygame.font.SysFont("Arial", 48)

# Screen setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Math Quiz for Autumn")

class MathQuizGame:
    def __init__(self):
        self.total_problems = 20
        self.current_index = 0
        self.wrong = 0
        self.start_time = time.time()

        self.question = ""
        self.solution = 0
        self.symbol = ""
        self.algebra_format = ""

        self.input_text = ""
        self.feedback = ""
        self.feedback_color = GREEN

        self.generate_problem()

    def generate_problem(self):
        ops = ["x", "%", "alg"]
        self.symbol = random.choice(ops)

        if self.symbol == '+':
            x, y = random.randint(1, 100), random.randint(1, 100)
            self.solution = x + y
            self.question = f"{x} + {y} = ?"

        elif self.symbol == '-':
            x = random.randint(1, 100)
            y = random.randint(1, x)
            self.solution = x - y
            self.question = f"{x} - {y} = ?"

        elif self.symbol == 'x':
            x = random.randint(3, 12)
            y = random.randint(3, 12)
            self.solution = x * y
            self.question = f"{x} * {y} = ?"

        elif self.symbol == '%':
            divisor = random.randint(2, 12)
            y = random.randint(2, 9)
            x = divisor * y
            self.solution = divisor
            self.question = f"{x} ÷ {y} = ?"

        elif self.symbol == 'alg':
            formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
            self.algebra_format = random.choice(formats)

            if self.algebra_format == "a*x+b=c":
                a, x_val, b = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                c = a * x_val + b
                self.solution = x_val
                self.question = f"{a} * __ + {b} = {c}"

            elif self.algebra_format == "a*x-b=c":
                a, x_val, b = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                c = a * x_val - b
                self.solution = x_val
                self.question = f"{a} * __ - {b} = {c}"

            elif self.algebra_format == "a+b*x=c":
                b, x_val, a = random.randint(1, 12), random.randint(1, 10), random.randint(1, 20)
                c = a + b * x_val
                self.solution = x_val
                self.question = f"{a} + {b} * __ = {c}"

    def check_answer(self):
        try:
            answer = int(self.input_text)
        except ValueError:
            return

        if answer == self.solution:
            self.feedback = "✅ Correct!"
            self.feedback_color = GREEN
            self.current_index += 1
            self.input_text = ""
            if self.current_index < self.total_problems:
                self.generate_problem()
            else:
                self.end_game()
        else:
            self.feedback = "❌ Try again!"
            self.feedback_color = RED
            self.wrong += 1
            self.input_text = ""

    def end_game(self):
        total_time = round(time.time() - self.start_time, 2)
        print("\n" + "*" * 50)
        tprint(f"{total_time} sec")
        print(f"You got {self.wrong} incorrect answers.")
        print("*" * 50 + "\n")

    def draw(self):
        screen.fill(WHITE)

        if self.current_index < self.total_problems:
            question_surface = FONT.render(f"{self.current_index+1}. {self.question}", True, BLACK)
            screen.blit(question_surface, (50, 100))

            input_surface = FONT.render(self.input_text, True, BLACK)
            screen.blit(input_surface, (50, 180))

            feedback_surface = FONT.render(self.feedback, True, self.feedback_color)
            screen.blit(feedback_surface, (50, 250))

            score_surface = FONT.render(f"Score: {self.current_index - self.wrong} correct, {self.wrong} wrong", True, BLACK)
            screen.blit(score_surface, (50, 320))
        else:
            total_time = round(time.time() - self.start_time, 2)
            final_message = f"Great job Autumn Peacci\u00f3n! Time: {total_time}s, Wrong: {self.wrong}"
            final_surface = LARGE_FONT.render(final_message, True, BLACK)
            screen.blit(final_surface, (50, HEIGHT // 2 - 40))

        pygame.display.flip()

quiz = MathQuizGame()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                quiz.check_answer()
            elif event.key == pygame.K_BACKSPACE:
                quiz.input_text = quiz.input_text[:-1]
            elif event.unicode.isdigit():
                quiz.input_text += event.unicode

    quiz.draw()

pygame.quit()
