from sqlalchemy import text, inspect
from app.src.config.database import engine

DEPRECATED_TABLES = [
    "roles",
    "profiles",
    "activity_logs",
    "app_session_state",
    "curriculum_progress",
    "curriculum_visits",
    "dashboard_state",
    "formula_lab_calculations",
    "formula_lab_sessions",
    "sandbox_simulations_state",
    "tutor_conversations",
    "tutor_messages",
]


def run_phase2_migration():
    print("[Migration] [Phase 2] Starting removal of deprecated tables...")
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    to_drop = [table for table in DEPRECATED_TABLES if table in existing_tables]
    
    if not to_drop:
        print("[Migration] [Phase 2] No deprecated tables found to remove.")
        return

    with engine.connect() as connection:
        with connection.begin():
            # Disable foreign key checks for SQLite during drop
            if "sqlite" in str(engine.url):
                connection.execute(text("PRAGMA foreign_keys = OFF;"))
                
            for table in to_drop:
                print(f"[Migration] [Phase 2] Dropping deprecated table: {table}")
                if "postgresql" in str(engine.url):
                    connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                else:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table};"))
                    
            if "sqlite" in str(engine.url):
                connection.execute(text("PRAGMA foreign_keys = ON;"))
                
    print("[Migration] [Phase 2] Deprecated tables removed successfully!")


if __name__ == "__main__":
    run_phase2_migration()
