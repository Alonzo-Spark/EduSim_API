"""
Quick script to inspect chat_history persistence in the EduSim database.
Run with: python inspect_db.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

from sqlalchemy import create_engine, text, inspect as sa_inspect
from datetime import datetime, timezone, timedelta

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Rith439@localhost:5432/edusim")
engine = create_engine(DATABASE_URL)

print(f"{'='*60}")
print(f"  EduSim Database Inspector")
print(f"  Database: {DATABASE_URL}")
print(f"  Time: {datetime.now()}")
print(f"{'='*60}\n")

with engine.connect() as conn:
    # 1. Total chat_history rows
    total = conn.execute(text("SELECT COUNT(*) FROM chat_history")).scalar()
    print(f"📊 Total chat_history records: {total}")

    # 2. Records in the last hour
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    recent = conn.execute(
        text("SELECT COUNT(*) FROM chat_history WHERE created_at >= :cutoff"),
        {"cutoff": one_hour_ago}
    ).scalar()
    print(f"🕐 Records in last 1 hour: {recent}")

    # 3. Unique users
    users = conn.execute(text("""
        SELECT ch.user_id, u.name, u.email, COUNT(*) as msg_count
        FROM chat_history ch
        JOIN users u ON u.id = ch.user_id
        GROUP BY ch.user_id, u.name, u.email
        ORDER BY msg_count DESC
    """)).fetchall()
    print(f"\n👥 Users with chat history:")
    for u in users:
        print(f"   {u[1]} ({u[2]}): {u[3]} messages")

    # 4. Latest 10 messages
    print(f"\n📝 Latest 10 messages:")
    latest = conn.execute(text("""
        SELECT ch.created_at, u.name, ch.role, ch.topic, 
               LEFT(ch.content, 60) as preview,
               ch.session_id
        FROM chat_history ch
        JOIN users u ON u.id = ch.user_id
        ORDER BY ch.created_at DESC
        LIMIT 10
    """)).fetchall()
    for r in latest:
        time_str = r[0].strftime("%H:%M:%S") if hasattr(r[0], 'strftime') else str(r[0])
        print(f"   [{time_str}] {r[1]:15s} | {r[2]:9s} | {r[3]:20s} | {r[4]}")

    # 5. Distinct sessions today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sessions_today = conn.execute(text("""
        SELECT COUNT(DISTINCT session_id) FROM chat_history WHERE created_at >= :today
    """), {"today": today_start}).scalar()
    print(f"\n📂 Distinct sessions today: {sessions_today}")

print(f"\n{'='*60}")
print(f"  ✅ Database inspection complete")
print(f"{'='*60}")
