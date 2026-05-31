import sys
import os
import uuid

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


def test_history_endpoints():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No test user found for endpoint tests.")
            return

        # Create Bearer token
        token = create_access_token({"sub": str(user.id), "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}

        # 1. GET chat history
        print("Testing GET /api/persistence/history/chat...")
        response = client.get("/api/persistence/history/chat", headers=headers)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        print(f"Chat history response keys: {data.keys()}")
        print(f"Chat history length: {len(data.get('history', []))}")

        # 2. GET formula history
        print("Testing GET /api/persistence/history/formula...")
        response = client.get("/api/persistence/history/formula", headers=headers)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        print(f"Formula history length: {len(data.get('history', []))}")

        # 3. GET simulation history
        print("Testing GET /api/persistence/history/simulation...")
        response = client.get("/api/persistence/history/simulation", headers=headers)
        assert response.status_code == 200, f"Error: {response.text}"
        data = response.json()
        print(f"Simulation history length: {len(data.get('history', []))}")

        # Try to delete one chat session if it exists
        response = client.get("/api/persistence/history/chat", headers=headers)
        chat_list = response.json().get("history", [])
        if chat_list:
            session_id = chat_list[0]["session_id"]
            print(f"Testing DELETE /api/persistence/history/chat/{session_id}...")
            del_resp = client.delete(f"/api/persistence/history/chat/{session_id}", headers=headers)
            assert del_resp.status_code == 200, f"Error: {del_resp.text}"
            print(f"Deleted chat history response: {del_resp.json()}")

        # Try to delete one formula calculation
        response = client.get("/api/persistence/history/formula", headers=headers)
        formula_list = response.json().get("history", [])
        if formula_list:
            calc_id = formula_list[0]["id"]
            print(f"Testing DELETE /api/persistence/history/formula/{calc_id}...")
            del_resp = client.delete(f"/api/persistence/history/formula/{calc_id}", headers=headers)
            assert del_resp.status_code == 200, f"Error: {del_resp.text}"
            print(f"Deleted formula calculation response: {del_resp.json()}")

        # Try to delete one simulation record
        response = client.get("/api/persistence/history/simulation", headers=headers)
        sim_list = response.json().get("history", [])
        if sim_list:
            sim_id = sim_list[0]["simulation_id"]
            print(f"Testing DELETE /api/persistence/history/simulation/{sim_id}...")
            del_resp = client.delete(f"/api/persistence/history/simulation/{sim_id}", headers=headers)
            assert del_resp.status_code == 200, f"Error: {del_resp.text}"
            print(f"Deleted simulation response: {del_resp.json()}")

        print("\n=== ALL ENDPOINT HISTORY AND DELETE TESTS PASSED SUCCESSFULLY! ===")
    finally:
        db.close()


if __name__ == "__main__":
    test_history_endpoints()
