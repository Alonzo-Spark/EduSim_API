from pydantic import BaseModel
from typing import Optional, List

class SubtopicResponse(BaseModel):
    id: int
    topic_id: int
    name: str
    content_summary: Optional[str] = None

    class Config:
        from_attributes = True

class TopicResponse(BaseModel):
    id: int
    chapter_id: int
    name: str
    slug: str
    has_simulation: bool
    simulation_type: Optional[str] = None

    class Config:
        from_attributes = True

class ChapterResponse(BaseModel):
    id: int
    subject_id: int
    name: str
    order_index: int

    class Config:
        from_attributes = True

class SubjectResponse(BaseModel):
    id: int
    class_id: int
    name: str
    icon: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class ClassResponse(BaseModel):
    id: int
    name: str
    display_order: int

    class Config:
        from_attributes = True
