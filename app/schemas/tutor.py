from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any

class TutorRequest(BaseModel):
    step: Literal["explanation", "formulas", "quiz", "simulation", "feedback", "chat"]
    topic: str
    class_name: str
    subject: str
    chapter: Optional[str] = None
    subtopic: Optional[str] = None
    topic_id: Optional[int] = None
    message: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
    quiz_performance: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    topic: str
    class_name: str
    subject: str
    chapter: Optional[str] = None
    chat_history: Optional[List[Dict[str, Any]]] = None
