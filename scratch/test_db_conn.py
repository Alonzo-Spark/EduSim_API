import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def check_chat_columns():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    
    db_url = os.getenv("DATABASE_URL")
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check columns in chat_history table
            columns_res = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'chat_history'
            """)).fetchall()
            print("Columns in 'chat_history' table:")
            for col in columns_res:
                print(f" - {col[0]}: {col[1]}")
    except Exception as e:
        print(f"Failed to query columns: {e}")

if __name__ == "__main__":
    check_chat_columns()
