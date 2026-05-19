from pydantic import BaseModel
from typing import Optional

class SimulationCreateRequest(BaseModel):
    topic: str
    class_name: str
    subject: str
    chapter: Optional[str] = None
    topic_id: Optional[int] = None
