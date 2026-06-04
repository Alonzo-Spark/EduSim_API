import asyncio
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))

from app.src.config.database import SessionLocal
from app.src.models.user import User
from app.src.models.persistence import StudentProfile
from app.src.repositories.student_repository import StudentRepository
from app.src.api.tutor_router import analyze_query, TutorQueryRequest
from app.src.utils.auth import create_access_token
from fastapi import BackgroundTasks

async def run_background_tasks(background_tasks: BackgroundTasks):
    """Executes the registered background tasks sequentially for testing."""
    print(f"[Test] Executing {len(background_tasks.tasks)} queued background tasks...")
    for task in background_tasks.tasks:
        try:
            if asyncio.iscoroutinefunction(task.func):
                await task.func(*task.args, **task.kwargs)
            else:
                task.func(*task.args, **task.kwargs)
        except Exception as e:
            print(f"[Test Background Tasks Error] Task failed: {e}")

async def main():
    db = SessionLocal()
    
    # 1. Ensure test student user exists
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

    # 2. Reset student profile to standard baseline
    profile = db.query(StudentProfile).filter_by(user_id=user.id).first()
    if profile:
        db.delete(profile)
        db.commit()
        
    print("\n=== Initializing student profile in DB ===")
    profile = StudentRepository.get_or_create_profile(db, user.id)
    print(f"Skill level: {profile.skill_level}")
    print(f"Mastered topics: {profile.mastered_topics}")
    print(f"Misconceptions: {profile.misconceptions}")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    authorization_header = f"Bearer {token}"

    # 3. Test Part 1: Long-term profile persistence & background analysis
    print("\n=== Test Part 1: Querying with misconception and trigger background analysis ===")
    
    # Question that introduces a misconception explicitly
    query = "Why does a 10kg mass fall faster than a 1kg mass under gravity? Is it because gravity pulls heavier things harder?"
    req = TutorQueryRequest(query=query)
    background_tasks = BackgroundTasks()
    
    res = await analyze_query(req, background_tasks=background_tasks, authorization=authorization_header, db=db)
    print("Response generated. RAG Explanation start:", res.get("data", {}).get("ai_explanation", "")[:120], "...")
    
    # Run the background LLM task which extracts the misconception
    await run_background_tasks(background_tasks)
    
    # Refresh DB session and verify if profile was updated
    db.expire_all()
    profile = StudentRepository.get_or_create_profile(db, user.id)
    print("\nUpdated student profile after background analysis:")
    print(f"Skill level: {profile.skill_level}")
    print(f"Mastered topics: {profile.mastered_topics}")
    print(f"Misconceptions: {profile.misconceptions}")
    
    # 4. Test Part 2: Dynamic history summarization
    print("\n=== Test Part 2: Querying with a very long history (>16 turns) ===")
    long_history = []
    # Generate 18 messages (9 user/assistant turns)
    for i in range(1, 10):
        long_history.append({"role": "user", "content": f"Physics question number {i}"})
        long_history.append({"role": "assistant", "content": f"Detailed explanation number {i} about general motion."})
        
    print(f"Constructed artificial history length: {len(long_history)} messages.")
    
    query_with_history = "Wait, let's go back to why acceleration due to gravity is independent of mass."
    req_history = TutorQueryRequest(
        query=query_with_history,
        history=long_history
    )
    
    background_tasks_2 = BackgroundTasks()
    res_history = await analyze_query(
        req_history,
        background_tasks=background_tasks_2,
        authorization=authorization_header,
        db=db
    )
    print("Response for history query generated successfully.")
    
    # Let's inspect that the final answer is complete
    explanation = res_history.get("data", {}).get("ai_explanation", "")
    print("Response length:", len(explanation))
    print("Snippet:", explanation[:150], "...")
    
    db.close()
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    asyncio.run(main())
