import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to the project .env file.")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_database() -> dict[str, object]:
    with engine.connect() as connection:
        version = connection.execute(text("SELECT version();")).scalar_one()

    return {
        "success": True,
        "message": "Connected to PostgreSQL",
        "database_url": DATABASE_URL,
        "version": version,
    }