import uuid
from app.src.config.database import SessionLocal
from app.src.models.persistence import ChatHistory
from app.src.models.user import User

db = SessionLocal()
try:
    # Get the student user
    user = db.query(User).filter(User.role == "student").first()
    if not user:
        print("No student user found in database.")
        exit(1)
        
    print(f"Testing for user ID: {user.id}")
    
    # Let's delete all existing tutor chat history for this user to start fresh
    db.query(ChatHistory).filter(ChatHistory.user_id == user.id, ChatHistory.session_type == "tutor").delete()
    db.commit()
    print("Cleaned up existing tutor history for test user.")
    
    # We will simulate the tutor_router POST /analyze logic for session 1
    # Turn 1
    session_id_1 = uuid.uuid4()
    user_rec_1 = ChatHistory(
        user_id=user.id,
        session_id=session_id_1,
        session_type="tutor",
        role="user",
        topic="Friction",
        content="explain friction",
        summary="Friction is...",
        metadata_json={}
    )
    assistant_rec_1 = ChatHistory(
        user_id=user.id,
        session_id=session_id_1,
        session_type="tutor",
        role="assistant",
        topic="Friction",
        content="Friction is a force...",
        summary=None,
        metadata_json={}
    )
    db.add(user_rec_1)
    db.add(assistant_rec_1)
    db.commit()
    print(f"Created Session 1: {session_id_1}")
    
    # Turn 2: Simulate starting a NEW chat (session 2)
    session_id_2 = uuid.uuid4()
    user_rec_2 = ChatHistory(
        user_id=user.id,
        session_id=session_id_2,
        session_type="tutor",
        role="user",
        topic="Gravity",
        content="explain gravity",
        summary="Gravity is...",
        metadata_json={}
    )
    assistant_rec_2 = ChatHistory(
        user_id=user.id,
        session_id=session_id_2,
        session_type="tutor",
        role="assistant",
        topic="Gravity",
        content="Gravity is a force...",
        summary=None,
        metadata_json={}
    )
    db.add(user_rec_2)
    db.add(assistant_rec_2)
    db.commit()
    print(f"Created Session 2: {session_id_2}")
    
    # Now let's list tutor sessions using the same PersistenceRepository logic
    from app.src.repositories.persistence_repository import PersistenceRepository
    repo = PersistenceRepository(db)
    sessions = repo.list_tutor_sessions(user.id)
    
    print(f"\nUnique tutor sessions retrieved: {len(sessions)}")
    for idx, s in enumerate(sessions):
        print(f"{idx+1}. ID: {s['id']} | Topic: {s['topic']}")
        
    assert len(sessions) == 2, f"Expected 2 sessions, got {len(sessions)}"
    print("\nAPI history logic verified successfully!")
    
finally:
    db.close()
