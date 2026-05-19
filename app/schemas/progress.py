from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProgressResponse(BaseModel):
    id: int
    user_id: str
    topic_id: int
    completion: float
    xp_earned: int
    quiz_score: Optional[float] = None
    quiz_attempts: int
    simulation_count: int
    explanation_viewed: bool
    formulas_viewed: bool
    last_studied: datetime

    class Config:
        from_attributes = True

class ProgressSummaryResponse(BaseModel):
    topics_learned: int
    simulations_run: int
    xp: int
    level: int
    streak: int
    badges: List[dict]
