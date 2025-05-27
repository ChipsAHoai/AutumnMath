import random
import os
import time
from art import *
from fractions import Fraction

def main():
    global wrong
    global x 
    global y 
    global solution

    wrong = 0
    os.system('clear')
    start = time.time()
    totalProblems = 20

    for z in range(totalProblems):
        solution = 0
        os.system('clear')
        print(z + 1, ' out of ', totalProblems)
        math = problem()

        if math == '-':
            print(x, " - ", y, " = ", solution)
        elif math == '+':
            print(x, " + ", y, " = ", solution)
        elif math == 'x':
            print(x, " * ", y, " = ", solution)
        elif math == '%':
            print(x, " ÷ ", y, " = ", solution)
        elif math == 'alg':
            print("Nice work solving for the unknown!")
        elif math == 'mix':
            print("Well done solving the mixed-type expression!")
        elif math == 'multi_alg':
            print("Awesome job solving the multi-step equation!")
        elif math == 'parens':
            print("Parentheses master! Great job!")
        elif math == 'fraction':
            print("Fractions? Nailed it! Excellent work!")

        if z == (totalProblems - 1):
            print("Great job Autumn Peacción! You've finished in:")
            total = round((time.time() - start), 2)
            total = str(total) + ' seconds'
            tprint(total)
            print('You got', wrong, 'incorrect answers')
        else:
            print('Good job Autumn! Next problem')
        print('\n\n')

def problem():
    global wrong, x, y, solution, last_parens_problem, current_alg_format, a, b, c, d

    last_parens_problem = ""
    current_alg_format = ""
    a = b = c = d = 0

    operator = ["%", "x", "alg", "mix", "multi_alg", "parens", "fraction"]
    operator = ["fraction"]
    symbol = random.choice(operator)

    if symbol == '-':
        x = random.randint(1, 10000)
        y = random.randint(1, x)
        solution = x - y

    elif symbol == '+':
        x = random.randint(1, 10000)
        y = random.randint(1, x)
        solution = x + y

    elif symbol == 'x':
        x = random.randint(3, 99)
        y = random.randint(11, 99)
        solution = x * y

    elif symbol == "%":
        division = random.randint(2, 999)
        y = random.randint(2, 9)
        x = division * y
        solution = division

    elif symbol == "fraction":
        num1 = random.randint(1, 9)
        den1 = random.randint(1, 9)
        num2 = random.randint(1, 9)
        den2 = random.randint(1, 9)

        f1 = Fraction(num1, den1)
        f2 = Fraction(num2, den2)
        solution = f1 + f2

        x = str(f1)
        y = str(f2)

        print(f"{x} + {y} = ? (simplify if possible)")

    elif symbol == "alg":
        formats = ["a*x+b=c", "a*x-b=c", "a+b*x=c"]
        chosen = random.choice(formats)
        current_alg_format = chosen

        if chosen == "a*x+b=c":
            a = random.randint(1, 12)
            x_val = random.randint(1, 10)
            b = random.randint(1, 20)
            c = a * x_val + b
            solution = x_val
            print(f"{a} * __ + {b} = {c}")

        elif chosen == "a*x-b=c":
            a = random.randint(1, 12)
            x_val = random.randint(1, 10)
            b = random.randint(1, 20)
            c = a * x_val - b
            if c < 0:
                return problem()
            solution = x_val
            print(f"{a} * __ - {b} = {c}")

        elif chosen == "a+b*x=c":
            b = random.randint(1, 12)
            x_val = random.randint(1, 10)
            a = random.randint(1, 20)
            c = a + b * x_val
            solution = x_val
            print(f"{a} + {b} * __ = {c}")

    elif symbol == "mix":
        a = random.randint(1, 20)
        b = random.randint(1, 20)
        c = random.randint(1, 10)
        solution = (a + b) * c
        print(f"({a} + {b}) * {c} = ")

    elif symbol == "multi_alg":
        x_val = random.randint(1, 10)
        a = random.randint(1, 5)
        c = random.randint(a + 1, a + 4)
        b = random.randint(0, 10)

        left = a * x_val + b
        right = c * x_val
        d = right - left

        if d < 0:
            return problem()

        solution = x_val
        print(f"{a}x + {b} = {c}x - {d}")

    elif symbol == "parens":
        formats = ["(a + b) * c", "a * (b - c)", "(a + b) + (c + d)", "(a * b) - (c * d)"]
        chosen = random.choice(formats)

        if chosen == "(a + b) * c":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            c = random.randint(1, 10)
            solution = (a + b) * c
            last_parens_problem = f"({a} + {b}) * {c} = "

        elif chosen == "a * (b - c)":
            b = random.randint(5, 15)
            c = random.randint(1, b)
            a = random.randint(1, 10)
            solution = a * (b - c)
            last_parens_problem = f"{a} * ({b} - {c}) = "

        elif chosen == "(a + b) + (c + d)":
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            c = random.randint(1, 10)
            d = random.randint(1, 10)
            solution = (a + b) + (c + d)
            last_parens_problem = f"({a} + {b}) + ({c} + {d}) = ?"

        elif chosen == "(a * b) - (c * d)":
            a = random.randint(1, 10)
            b = random.randint(1, 5)
            c = random.randint(1, 4)
            d = random.randint(1, 3)
            solution = (a * b) - (c * d)
            if solution < 0:
                return problem()
            last_parens_problem = f"({a} * {b}) - ({c} * {d}) = ?"

        print(last_parens_problem)

    else:
        return symbol

    if symbol not in ["alg", "mix", "multi_alg", "parens", "fraction"]:
        x = str(x)
        y = str(y)
        for i in range(5 - len(x)):
            x = " " + x 
        for i in range(3 - len(y)):
            y = " " + y
        print(x)
        print(symbol, y)
        print("_____")

    answer_input = "= "
    for i in range(4 - len(str(solution))):
        answer_input += " "
    answer = input(answer_input)

    try:
        if symbol == "fraction":
            answer = Fraction(answer.strip())
        else:
            answer = int(answer)
    except:
        answer = Fraction(0, 1) if symbol == "fraction" else 0

    while True:
        correct = False

        if symbol == "alg":
            if current_alg_format == "a*x+b=c":
                correct = (a * answer + b == c)
            elif current_alg_format == "a*x-b=c":
                correct = (a * answer - b == c)
            elif current_alg_format == "a+b*x=c":
                correct = (a + b * answer == c)
        elif symbol == "fraction":
            correct = (answer == solution)
        else:
            correct = (answer == solution)

        if correct:
            break

        wrong += 1
        os.system('clear')
        print("Wrong answer Autumn Peacción, try again!")

        if symbol == "alg":
            if current_alg_format == "a*x+b=c":
                print(f"{a} * __ + {b} = {c}")
            elif current_alg_format == "a*x-b=c":
                print(f"{a} * __ - {b} = {c}")
            elif current_alg_format == "a+b*x=c":
                print(f"{a} + {b} * __ = {c}")
        elif symbol == "mix":
            print(f"({a} + {b}) * {c} = ")
        elif symbol == "multi_alg":
            print(f"{a}x + {b} = {c}x - {d}")
        elif symbol == "parens":
            print(last_parens_problem)
        elif symbol == "fraction":
            print(f"{x} + {y} = ? (simplify if possible)")
        else:
            print(x)
            print(symbol, y)
            print("_____")

        answer = input("= ")
        try:
            if symbol == "fraction":
                answer = Fraction(answer.strip())
            else:
                answer = int(answer)
        except:
            answer = Fraction(0, 1) if symbol == "fraction" else 0

    return symbol

if __name__ == "__main__":
    os.system('clear')
    main()
