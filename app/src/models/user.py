import uuid

from sqlalchemy import Column, DateTime, String, Boolean, UUID
from sqlalchemy.sql import func

from app.src.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String(20), default="student")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # New columns for advanced authentication & verification
    mobile_number = Column(String(20), nullable=True)
    is_email_verified = Column(Boolean, default=False)
    is_mobile_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    otp_code = Column(String, nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)


