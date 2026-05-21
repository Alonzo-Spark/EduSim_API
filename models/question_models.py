from pydantic import BaseModel
from typing import List

class QuestionModel(BaseModel):
    question: str
    answer: str

class QuestionGenerationResponse(BaseModel):
    questions: List[QuestionModel]
