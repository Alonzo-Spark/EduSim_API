import sys
import os

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from app.src.config.database import SessionLocal
from app.src.models.persistence import ChatHistory

db = SessionLocal()
try:
    print("Fetching last 10 records from 'chat_history' table...\n")
    records = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(10).all()
    if not records:
        print("No records found in chat_history table.")
    else:
        for record in records:
            safe_content = record.content.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            print(f"[{record.created_at}] Session: {record.session_id}")
            print(f"Role: {record.role.upper()} | Topic: {record.topic}")
            print(f"Content: {safe_content[:150]}...")
            print("-" * 60)
except Exception as e:
    print(f"Error querying database: {e}")
finally:
    db.close()
