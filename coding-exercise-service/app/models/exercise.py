from datetime import datetime

# Exercise document structure
exercise_schema = {
    "title": str,
    "description": str,
    "difficulty": str,  # easy, medium, hard
    "topic": str,       # algorithms, data structures, etc.
    "created_at": datetime,
    "test_cases": [
        {
            "input": str,
            "expected_output": str,
            "is_hidden": bool  # Hidden test cases are not shown to users
        }
    ],
    "starter_code": {
        "python": str,
        "javascript": str,
        # Other languages
    },
    "solution_code": {
        "python": str,
        "javascript": str,
        # Other languages
    },
    "hints": [
        {
            "level": int,  # 1 for subtle hints, 3 for more direct hints
            "content": str
        }
    ]
}

def create_exercise_document(title, description, difficulty, topic, 
                           test_cases=None, starter_code=None, 
                           solution_code=None, hints=None):
    """Create a new exercise document."""
    return {
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "topic": topic,
        "created_at": datetime.utcnow(),
        "test_cases": test_cases or [],
        "starter_code": starter_code or {},
        "solution_code": solution_code or {},
        "hints": hints or []
    }