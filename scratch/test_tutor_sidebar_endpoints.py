import sys
import os
from fastapi.testclient import TestClient

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from main import app
import json

client = TestClient(app)

print("1. Logging in as Admin...")
login_response = client.post("/api/auth/login", json={
    "email": "admin@gmail.com",
    "password": "Admin@123"
})
print(f"Login Status: {login_response.status_code}")
login_data = login_response.json()
token = login_data["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n2. Sending a Tutor query to generate some history...")
analyze_response = client.post("/api/tutor/analyze", headers=headers, json={
    "query": "What is Newton's First Law?",
    "class_name": "Class 11",
    "subject": "Physics",
    "chapter": "Laws of Motion",
    "topic": "Newton's First Law"
})
print(f"Analyze Status: {analyze_response.status_code}")
analyze_data = analyze_response.json()
session_id = analyze_data.get("session_id")
print(f"Generated Session ID: {session_id}")

print("\n3. Testing GET /api/persistence/tutor/sessions...")
sessions_response = client.get("/api/persistence/tutor/sessions", headers=headers)
print(f"Sessions Status: {sessions_response.status_code}")
sessions_data = sessions_response.json()
print("Sessions list:")
print(json.dumps(sessions_data, indent=2))

if session_id:
    print(f"\n4. Testing GET /api/persistence/tutor/session/{session_id}...")
    session_response = client.get(f"/api/persistence/tutor/session/{session_id}", headers=headers)
    print(f"Session Messages Status: {session_response.status_code}")
    session_data = session_response.json()
    print("Messages detail:")
    print(json.dumps(session_data, indent=2))

    print(f"\n5. Testing DELETE /api/persistence/tutor/session/{session_id}...")
    delete_response = client.delete(f"/api/persistence/tutor/session/{session_id}", headers=headers)
    print(f"Delete Status: {delete_response.status_code}")
    print(delete_response.json())
    
    print("\n6. Re-fetching sessions to verify deletion...")
    sessions_response = client.get("/api/persistence/tutor/sessions", headers=headers)
    print(f"Sessions count after delete: {len(sessions_response.json().get('sessions', []))}")
