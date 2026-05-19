import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, Boolean, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"))
    completion = Column(Float, default=0.0)
    xp_earned = Column(Integer, default=0)
    quiz_score = Column(Float, nullable=True)
    quiz_attempts = Column(Integer, default=0)
    simulation_count = Column(Integer, default=0)
    explanation_viewed = Column(Boolean, default=False)
    formulas_viewed = Column(Boolean, default=False)
    last_studied = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True)
    messages = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
