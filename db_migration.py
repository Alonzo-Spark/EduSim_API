from sqlalchemy import text, inspect
from app.src.config.database import Base, engine, SessionLocal
from app.src.models.user import User
from app.src.models.persistence import (
    Subject,
    Chapter,
    Topic,
    ChatHistory,
    FormulaHistory,
    SimulationHistory,
    UserSetting,
    UserSession,
)
from app.src.utils.curriculum_loader import populate_curriculum


def run_migration():
    print("[Migration] [Phase 1] Starting database migration...")
    
    print("[Migration] Creating new tables (if not existing)...")
    Base.metadata.create_all(bind=engine)

    if "postgresql" in str(engine.url):
        print("[Migration] Adjusting user_sessions.session_key column type to support long JWT tokens...")
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("ALTER TABLE user_sessions ALTER COLUMN session_key TYPE VARCHAR(500);"))
    
    print("[Migration] Seeding curriculum data...")
    db = SessionLocal()
    try:
        populate_curriculum(db)
    finally:
        db.close()
        
    print("[Migration] [Phase 1] Database migration finished successfully!")


if __name__ == "__main__":
    run_migration()
