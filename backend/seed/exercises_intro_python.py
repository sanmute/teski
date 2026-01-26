from __future__ import annotations

from sqlmodel import Session, select

from models_exercise import Exercise


def seed_intro_python_exercises(session: Session) -> None:
    """Seed a small set of intro Python exercises. No-op if exercises already exist."""
    existing = session.exec(select(Exercise)).first()
    if existing:
        return

    exercises = [
        Exercise(
            prompt="What is the output of: print(2 + 3 * 2)?",
            type="mcq",
            choices=["10", "8", "7", "12"],
            correct_answer="8",
            explanation="Multiplication has higher precedence: 3 * 2 = 6, then 2 + 6 = 8.",
            primary_skill_id="python_basics",
            skill_ids=["python_basics", "operators"],
            difficulty="intro",
        ),
        Exercise(
            prompt="Which of these is a valid Python variable name?",
            type="mcq",
            choices=["1variable", "my-var", "for", "user_name"],
            correct_answer="user_name",
            explanation="Python variables cannot start with a digit, cannot contain '-', and cannot be a keyword like 'for'.",
            primary_skill_id="python_variables",
            skill_ids=["python_variables"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is the type of the value 3.0 in Python?",
            type="mcq",
            choices=["int", "float", "str", "bool"],
            correct_answer="float",
            explanation="3.0 has a decimal point, so it is a float.",
            primary_skill_id="python_types",
            skill_ids=["python_types"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What does the expression len('Teski') return?",
            type="numeric",
            choices=None,
            correct_answer="5",
            explanation="The string 'Teski' has 5 characters.",
            primary_skill_id="python_strings",
            skill_ids=["python_strings"],
            difficulty="intro",
        ),
        Exercise(
            prompt="Fill in the blank to print 'Hello, LUT': print(____)",
            type="short_answer",
            choices=None,
            correct_answer="'Hello, LUT'",
            explanation="In Python, strings must be quoted: print('Hello, LUT').",
            primary_skill_id="python_strings",
            skill_ids=["python_strings"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is the result of: 5 // 2?",
            type="mcq",
            choices=["2.5", "2", "3", "4"],
            correct_answer="2",
            explanation="// is integer (floor) division in Python. 5 // 2 = 2.",
            primary_skill_id="python_operators",
            skill_ids=["python_basics", "operators"],
            difficulty="intro",
        ),
        Exercise(
            prompt="Which keyword is used to start a function definition in Python?",
            type="mcq",
            choices=["func", "define", "def", "function"],
            correct_answer="def",
            explanation="Functions in Python are defined using the 'def' keyword.",
            primary_skill_id="python_functions",
            skill_ids=["python_functions"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is printed by:\n\nx = 3\nif x > 5:\n    print('big')\nelse:\n    print('small')",
            type="mcq",
            choices=["big", "small", "3", "Nothing is printed"],
            correct_answer="small",
            explanation="x is 3, so x > 5 is False, and the else-branch runs.",
            primary_skill_id="python_conditionals",
            skill_ids=["python_conditionals"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is the value of x after this code?\n\nx = 0\nfor i in range(3):\n    x = x + 2\n\nprint(x)",
            type="numeric",
            choices=None,
            correct_answer="6",
            explanation="The loop runs 3 times, adding 2 each time: 0 → 2 → 4 → 6.",
            primary_skill_id="python_loops",
            skill_ids=["python_loops"],
            difficulty="intro",
        ),
        Exercise(
            prompt="Which of these lists contains 3 elements?",
            type="mcq",
            choices=["[1, 2, 3]", "[1, 2, 3, 4]", "[]", "[1]"],
            correct_answer="[1, 2, 3]",
            explanation="[1, 2, 3] has exactly 3 elements.",
            primary_skill_id="python_lists",
            skill_ids=["python_lists"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is the output of:\n\nx = [1, 2, 3]\nprint(x[0])",
            type="mcq",
            choices=["1", "2", "3", "0"],
            correct_answer="1",
            explanation="Python lists are zero-indexed: x[0] is the first element, 1.",
            primary_skill_id="python_lists",
            skill_ids=["python_lists"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What does the 'return' keyword do inside a function?",
            type="mcq",
            choices=[
                "Prints a value to the screen",
                "Stops the program",
                "Exits the function and optionally sends a value back",
                "Restarts the function",
            ],
            correct_answer="Exits the function and optionally sends a value back",
            explanation="return ends function execution and provides the result to the caller.",
            primary_skill_id="python_functions",
            skill_ids=["python_functions"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What is the boolean result of: (3 < 5) and (10 > 20)?",
            type="mcq",
            choices=["True", "False", "3", "20"],
            correct_answer="False",
            explanation="(3 < 5) is True, (10 > 20) is False; True and False = False.",
            primary_skill_id="python_booleans",
            skill_ids=["python_booleans", "operators"],
            difficulty="intro",
        ),
        Exercise(
            prompt="What will this code print?\n\nx = 'Teski'\nprint(x.upper())",
            type="mcq",
            choices=["teski", "TESKI", "Teski", "Error"],
            correct_answer="TESKI",
            explanation="The .upper() method returns an uppercase version of the string.",
            primary_skill_id="python_strings",
            skill_ids=["python_strings"],
            difficulty="intro",
        ),
        Exercise(
            prompt="Which operator is used for equality comparison in Python?",
            type="mcq",
            choices=["=", "==", "===", "!="],
            correct_answer="==",
            explanation="'==' compares equality. '=' assigns a value to a variable.",
            primary_skill_id="python_operators",
            skill_ids=["python_operators"],
            difficulty="intro",
        ),
    ]

    for ex in exercises:
        session.add(ex)
    session.commit()
