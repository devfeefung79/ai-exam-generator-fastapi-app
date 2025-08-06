# AI Exam Generator App

This repository is a backend fastapi project for AI Exam Generator application. 

## Getting Started

### Clone the Repository

### Install the Required Dependencies

### Configure the Environment Variable(s)

Make sure you have a valid Google API key for the Gemini AI product.

```
# .env.example
GOOGLE_API_KEY=
```

### Run the Application

You could visit `/docs` to play around with the APIs.

## API Specifications

### `POST` /v1/exams/generate

Generate an exam based on input parameters.

Sample Response
```json
{
    "id": null,
    "exam_title": "Java Developer Core Competencies Exam",
    "total_questions": 10,
    "difficulty": "Mixed",
    "estimated_completion_minutes": 20,
    "question_types": [
        "Multiple Choice",
        "True/False"
    ],
    "questions": [
        {
            "id": 1,
            "type": "Multiple Choice",
            "difficulty": "Easy",
            "question": "Which of the following is NOT a core OOP principle?",
            "options": [
                "Encapsulation",
                "Abstraction",
                "Inheritance",
                "Debugging"
            ],
            "correct_answer": "Debugging",
            "explanation": "Debugging is a development process, not a core principle of Object-Oriented Programming. The core OOP principles typically include Encapsulation, Abstraction, Inheritance, and Polymorphism."
        },
        {
            "id": 2,
            "type": "True/False",
            "difficulty": "Medium",
            "question": "A race condition occurs when multiple threads access shared data concurrently and try to modify it, leading to unpredictable results.",
            "correct_answer": "True",
            "explanation": "A race condition is a common concurrency bug where the output of a concurrent program depends on the sequence or timing of events that cannot be controlled."
        },
        {
            "id": 3,
            "type": "Multiple Choice",
            "difficulty": "Medium",
            "question": "Which Java Stream API terminal operation is used to combine elements into a single result by applying a binary operator iteratively?",
            "options": [
                "map",
                "filter",
                "forEach",
                "reduce"
            ],
            "correct_answer": "reduce",
            "explanation": "The `reduce` operation applies a binary operator to each element in the stream to reduce the stream to a single value. `map` transforms elements, `filter` selects elements, and `forEach` performs an action for each element without returning a result."
        }
    ]
}
```

### `POST` /v1/exams/download

Download a previously generated exam file
