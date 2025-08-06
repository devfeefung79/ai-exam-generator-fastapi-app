import enum
from datetime import datetime, timezone
from typing import List, Optional, Union, Literal

from pydantic import BaseModel, Field


class Difficulty(str, enum.Enum):
    Easy = "Easy"
    Medium = "Medium"
    Hard = "Hard"
    Mixed = "Mixed"

class QuestionType(str, enum.Enum):
    MCQ = "Multiple Choice"
    TrueFalse = "True/False"
    ShortAnswer = "Short Answer"
    Essay = "Essay"

class QuestionBase(BaseModel):
    id: int
    type: QuestionType
    difficulty: Literal[Difficulty.Easy, Difficulty.Medium, Difficulty.Hard]
    question: str

class MultipleChoiceQuestion(QuestionBase):
    type: Literal[QuestionType.MCQ]
    options: List[str]
    correct_answer: str
    explanation: str

class TrueFalseQuestion(QuestionBase):
    type: Literal[QuestionType.TrueFalse]
    correct_answer: str
    explanation: str

class ShortAnswerQuestion(QuestionBase):
    type: Literal[QuestionType.ShortAnswer]
    sample_answer: str

class EssayQuestion(QuestionBase):
    type: Literal[QuestionType.Essay]
    guidelines: str

# Union of all question types
Question = Union[
    MultipleChoiceQuestion,
    TrueFalseQuestion,
    ShortAnswerQuestion,
    EssayQuestion
]

class Exam(BaseModel):
    id: Optional[int] = None
    exam_title: str
    total_questions: int
    difficulty: str
    estimated_completion_minutes: int
    question_types: List[QuestionType]
    questions: List[Question]
