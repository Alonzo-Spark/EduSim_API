from pydantic import BaseModel
from typing import List, Optional


class QuestionModel(BaseModel):
    question: str
    answer: str
    type: str = "conceptual"  # MCQ, numerical, conceptual
    options: Optional[List[str]] = None
    explanation: str = ""
    formula_used: str = ""
    related_concept: str = ""
    difficulty: str = "Medium"


class QuestionGenerationResponse(BaseModel):
    questions: List[QuestionModel]
