import sys
import os

# Setup paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src"))

from fastapi.testclient import TestClient
from main import app
from app.src.config.database import SessionLocal
from app.src.models.user import User
from app.src.utils.auth import create_access_token

client = TestClient(app)

def verify_update_msg():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No test user found for verification.")
            return

        token = create_access_token({"sub": str(user.id), "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test POST /api/persistence/profile
        print("\n--- Testing POST /api/persistence/profile ---")
        profile_payload = {
            "bio": "Studying physics",
            "display_name": "Physics Student"
        }
        res = client.post("/api/persistence/profile", json=profile_payload, headers=headers)
        print("Status Code:", res.status_code)
        print("Response:", res.json())
        assert res.status_code == 200
        assert res.json().get("message") == "updated"

        # 2. Test POST /api/persistence/settings
        print("\n--- Testing POST /api/persistence/settings ---")
        settings_payload = {
            "key": "theme_preference",
            "value": "dark"
        }
        res = client.post("/api/persistence/settings", json=settings_payload, headers=headers)
        print("Status Code:", res.status_code)
        print("Response:", res.json())
        assert res.status_code == 200
        assert res.json().get("message") == "updated"

        # 3. Test POST /api/persistence/sandbox/state
        print("\n--- Testing POST /api/persistence/sandbox/state ---")
        sandbox_payload = {
            "simulation_id": "test-sim-verify-123",
            "prompt": "Friction test on block",
            "title": "Friction Lab"
        }
        res = client.post("/api/persistence/sandbox/state", json=sandbox_payload, headers=headers)
        print("Status Code:", res.status_code)
        print("Response:", res.json())
        assert res.status_code == 200
        assert res.json().get("message") == "updated"

        print("\n=== ALL POST SAVE VERIFICATION TESTS COMPLETED SUCCESSFULLY ===")
    finally:
        db.close()

if __name__ == "__main__":
    verify_update_msg()
