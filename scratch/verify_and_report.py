import sys
import os
import uuid
from sqlalchemy import text

# Setup paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))

from app.src.config.database import engine, SessionLocal
from app.src.utils.auth import create_refresh_token
from app.src.models.user import User

def check_and_fix():
    print("[Report] Verifying PostgreSQL schema...")
    
    # Task 5: Verify PostgreSQL schema
    query = """
    SELECT character_maximum_length 
    FROM information_schema.columns 
    WHERE table_name='user_sessions' 
    AND column_name='session_key';
    """
    
    length = None
    with engine.connect() as connection:
        result = connection.execute(text(query)).fetchone()
        if result:
            length = result[0]
            print(f"[Report] Current character_maximum_length in database: {length}")
        else:
            print("[Report] Could not find session_key column in information_schema.columns")

    # Task 6: If length is still 120, generate and execute ALTER
    if length == 120:
        print("[Report] Column length is 120. Altering column to VARCHAR(500)...")
        alter_query = "ALTER TABLE user_sessions ALTER COLUMN session_key TYPE VARCHAR(500);"
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text(alter_query))
        print("[Report] ALTER executed successfully!")
        
        # Verify again
        with engine.connect() as connection:
            result = connection.execute(text(query)).fetchone()
            if result:
                length = result[0]
                print(f"[Report] New character_maximum_length in database: {length}")
    else:
        print("[Report] No alter needed. Column length is not 120.")

    # Calculate actual JWT refresh token length
    # A standard sub is UUID string (36 chars)
    sample_sub = str(uuid.uuid4())
    sample_token = create_refresh_token({"sub": sample_sub})
    token_length = len(sample_token)

    # Task 7: Print report
    model_path = os.path.abspath(os.path.join(root_dir, "app", "src", "models", "persistence.py"))
    
    print("\n" + "="*50)
    print("VERIFICATION REPORT:")
    print(f"- Model file path: {model_path}")
    print(f"- Actual column length in database: {length}")
    print(f"- Actual JWT refresh token length: {token_length}")
    print("="*50 + "\n")

if __name__ == "__main__":
    check_and_fix()
