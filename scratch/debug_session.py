import uuid
from app.src.config.database import SessionLocal
from app.src.models.persistence import ChatHistory

db = SessionLocal()
try:
    sid = uuid.UUID("50d97c63-c4e2-43de-9116-1b63ec5acd34")
    chats = db.query(ChatHistory).filter(ChatHistory.session_id == sid).order_by(ChatHistory.created_at.asc()).all()
    print(f"Total messages for session: {len(chats)}")
    for idx, c in enumerate(chats):
        print(f"--- Index {idx} | Role: {c.role} | Topic: {c.topic} ---")
        print(f"Content:\n{c.content}\n")
finally:
    db.close()
