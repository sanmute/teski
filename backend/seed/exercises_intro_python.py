from __future__ import annotations

from sqlmodel import Session, select

from models_exercise import Exercise


def seed_intro_python_exercises(session: Session) -> None:
    """Seed a small set of intro Python exercises. No-op if exercises already exist."""
    existing = session.exec(select(Exercise)).first()
    if existing:
        return

    raw = [
        {
            "question_text": "What is the output of: print(2 + 3 * 2)?",
            "type": "multiple_choice",
            "choices": ["10", "8", "7", "12"],
            "correct_answer": "8",
            "solution_explanation": "Multiplication has higher precedence: 3 * 2 = 6, then 2 + 6 = 8.",
            "skill_ids": ["python_basics", "operators"],
            "difficulty": 1,
        },
        {
            "question_text": "Which of these is a valid Python variable name?",
            "type": "multiple_choice",
            "choices": ["1variable", "my-var", "for", "user_name"],
            "correct_answer": "user_name",
            "solution_explanation": "Python variables cannot start with a digit, cannot contain '-', and cannot be a keyword like 'for'.",
            "skill_ids": ["python_variables"],
            "difficulty": 1,
        },
        {
            "question_text": "What is the type of the value 3.0 in Python?",
            "type": "multiple_choice",
            "choices": ["int", "float", "str", "bool"],
            "correct_answer": "float",
            "solution_explanation": "3.0 has a decimal point, so it is a float.",
            "skill_ids": ["python_types"],
            "difficulty": 1,
        },
        {
            "question_text": "What does the expression len('Teski') return?",
            "type": "multiple_choice",
            "choices": ["4", "5", "6", "Error"],
            "correct_answer": "5",
            "solution_explanation": "The string 'Teski' has 5 characters.",
            "skill_ids": ["python_strings"],
            "difficulty": 1,
        },
        {
            "question_text": "Fill in the blank to print 'Hello, LUT': print(____)",
            "type": "multiple_choice",
            "choices": ["Hello, LUT", "\"Hello, LUT\"", "'Hello, LUT'", "print('Hello, LUT')"],
            "correct_answer": "'Hello, LUT'",
            "solution_explanation": "In Python, strings must be quoted: print('Hello, LUT').",
            "skill_ids": ["python_strings"],
            "difficulty": 1,
        },
        {
            "question_text": "What is the result of: 5 // 2?",
            "type": "multiple_choice",
            "choices": ["2.5", "2", "3", "4"],
            "correct_answer": "2",
            "solution_explanation": "// is integer (floor) division in Python. 5 // 2 = 2.",
            "skill_ids": ["python_basics", "operators"],
            "difficulty": 1,
        },
        {
            "question_text": "Which keyword is used to start a function definition in Python?",
            "type": "multiple_choice",
            "choices": ["func", "define", "def", "function"],
            "correct_answer": "def",
            "solution_explanation": "Functions in Python are defined using the 'def' keyword.",
            "skill_ids": ["python_functions"],
            "difficulty": 1,
        },
        {
            "question_text": "What is printed by:\\n\\nx = 3\\nif x > 5:\\n    print('big')\\nelse:\\n    print('small')",
            "type": "multiple_choice",
            "choices": ["big", "small", "3", "Nothing is printed"],
            "correct_answer": "small",
            "solution_explanation": "x is 3, so x > 5 is False, and the else-branch runs.",
            "skill_ids": ["python_conditionals"],
            "difficulty": 1,
        },
        {
            "question_text": "What is the value of x after this code?\\n\\nx = 0\\nfor i in range(3):\\n    x = x + 2\\n\\nprint(x)",
            "type": "multiple_choice",
            "choices": ["2", "4", "6", "8"],
            "correct_answer": "6",
            "solution_explanation": "The loop runs 3 times, adding 2 each time: 0 → 2 → 4 → 6.",
            "skill_ids": ["python_loops"],
            "difficulty": 1,
        },
        {
            "question_text": "Which of these lists contains 3 elements?",
            "type": "multiple_choice",
            "choices": ["[1, 2, 3]", "[1, 2, 3, 4]", "[]", "[1]"],
            "correct_answer": "[1, 2, 3]",
            "solution_explanation": "[1, 2, 3] has exactly 3 elements.",
            "skill_ids": ["python_lists"],
            "difficulty": 1,
        },
        {
            "question_text": "What is the output of:\\n\\nx = [1, 2, 3]\\nprint(x[0])",
            "type": "multiple_choice",
            "choices": ["1", "2", "3", "0"],
            "correct_answer": "1",
            "solution_explanation": "Python lists are zero-indexed: x[0] is the first element, 1.",
            "skill_ids": ["python_lists"],
            "difficulty": 1,
        },
        {
            "question_text": "What does the 'return' keyword do inside a function?",
            "type": "multiple_choice",
            "choices": [
                "Prints a value to the screen",
                "Stops the program",
                "Exits the function and optionally sends a value back",
                "Restarts the function",
            ],
            "correct_answer": "Exits the function and optionally sends a value back",
            "solution_explanation": "return ends function execution and provides the result to the caller.",
            "skill_ids": ["python_functions"],
            "difficulty": 1,
        },
        {
            "question_text": "What is the boolean result of: (3 < 5) and (10 > 20)?",
            "type": "multiple_choice",
            "choices": ["True", "False", "3", "20"],
            "correct_answer": "False",
            "solution_explanation": "(3 < 5) is True, (10 > 20) is False; True and False = False.",
            "skill_ids": ["python_booleans", "operators"],
            "difficulty": 1,
        },
        {
            "question_text": "What will this code print?\\n\\nx = 'Teski'\\nprint(x.upper())",
            "type": "multiple_choice",
            "choices": ["teski", "TESKI", "Teski", "Error"],
            "correct_answer": "TESKI",
            "solution_explanation": "The .upper() method returns an uppercase version of the string.",
            "skill_ids": ["python_strings"],
            "difficulty": 1,
        },
        {
            "question_text": "Which operator is used for equality comparison in Python?",
            "type": "multiple_choice",
            "choices": ["=", "==", "===", "!="],
            "correct_answer": "==",
            "solution_explanation": "'==' compares equality. '=' assigns a value to a variable.",
            "skill_ids": ["python_operators"],
            "difficulty": 1,
        },
    ]

    exercises = []
    for idx, item in enumerate(raw):
        exercises.append(
            Exercise(
                id=f"python-intro-{idx+1}",
                question_text=item["question_text"],
                type=item["type"],
                choices=item["choices"],
                correct_answer=str(item["correct_answer"]),
                difficulty=int(item.get("difficulty", 1)),
                skill_ids=item.get("skill_ids", []),
                solution_explanation=item.get("solution_explanation"),
                hint=item.get("hint"),
                meta=item.get("metadata") or {},
            )
        )

    for ex in exercises:
        session.add(ex)
    session.commit()
