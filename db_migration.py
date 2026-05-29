from sqlalchemy import text
from app.src.config.database import engine

def run_migration():
    queries = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(20);",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_mobile_verified BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_token TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code TEXT;",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;"
    ]
    
    with engine.connect() as connection:
        # Start a transaction block
        with connection.begin():
            for query in queries:
                print(f"Executing: {query}")
                connection.execute(text(query))
            print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
