import sys
import os
from fastapi.testclient import TestClient

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from main import app

client = TestClient(app)

payload = {
    "query": "what is its formula",
    "class_name": None,
    "subject": None,
    "chapter": None,
    "topic": None,
    "history": []
}

print("Sending pronoun request with empty history/context...")
try:
    with client:
        response = client.post("/api/tutor/analyze", json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        explanation = data.get("data", {}).get("explanation") or data.get("data", {}).get("ai_explanation") or ""
        title = data.get("data", {}).get("title") or ""
        
        print(f"Response Title: {title}")
        print(f"Response Explanation: {explanation}")
        
        if "Clarification Needed" in title and "physics concept" in explanation:
            print("\n[SUCCESS] Verification Successful: Pronoun query with no context correctly asked for clarification!")
        else:
            print("\n[FAILED] Verification Failed!")
            
except Exception as e:
    print(f"Error during request: {e}")
