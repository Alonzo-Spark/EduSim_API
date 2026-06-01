import asyncio
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))

from app.src.config.database import SessionLocal
from app.src.models.user import User
from app.src.api.tutor_router import analyze_query, TutorQueryRequest
from app.src.utils.auth import create_access_token
from app.src.models.persistence import ChatHistory

async def main():
    db = SessionLocal()
    user = db.query(User).filter_by(email="student@edusim.local").first()
    if not user:
        from app.src.utils.auth import hash_password
        user = User(
            name="Test Student",
            email="student@edusim.local",
            password_hash=hash_password("StudentPass123!"),
            role="student",
            is_email_verified=True,
            is_mobile_verified=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    headers = {"Authorization": f"Bearer {token}"}

    queries = ["What is collision?", "Explain Newton's Second Law"]
    
    for q in queries:
        print(f"\n--- Testing: {q} ---")
        req = TutorQueryRequest(query=q)
        res = await analyze_query(req, authorization=headers["Authorization"], db=db)
        print("Response received.")

    print("\n--- Checking Database ---")
    history = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(2).all()
    for h in history:
        print(f"Topic: {h.topic} | Content: {h.content} | Summary: {h.summary}")

if __name__ == "__main__":
    asyncio.run(main())
