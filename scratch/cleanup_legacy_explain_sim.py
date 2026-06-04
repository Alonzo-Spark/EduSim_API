import sys
import os

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from app.src.config.database import SessionLocal
from app.src.models.persistence import ChatHistory

db = SessionLocal()
try:
    records = db.query(ChatHistory).filter(
        ChatHistory.session_type == "tutor",
        ChatHistory.topic.like("Explain the physics of%")
    ).all()
    
    if records:
        print(f"Found {len(records)} legacy simulation explanation records. Migrating...")
        for r in records:
            r.session_type = "explain_sim"
        db.commit()
        print("Successfully migrated legacy records to session_type='explain_sim'!")
    else:
        print("No legacy simulation explanation records found.")
except Exception as e:
    db.rollback()
    print(f"Error migrating records: {e}")
finally:
    db.close()
