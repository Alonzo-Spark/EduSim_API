from pydantic import BaseModel
from typing import List, Dict, Any

class QuizSubmitRequest(BaseModel):
    topic_id: int
    answers: List[Dict[str, Any]]
    score: float
    total: int
    time_taken_seconds: int = 0
    wrong_questions: List[Dict[str, Any]] = []
    simulation_count: int = 0
