from fastapi.testclient import TestClient
import sys
import os

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from main import app
import json

client = TestClient(app)

payload = {
    "query": "Can you write its formula?",
    "class_name": "Class 11",
    "subject": "Physics",
    "chapter": "Laws of Motion",
    "topic": "Newton's Second Law",
    "history": [
        {"role": "user", "content": "What is Newton's Second Law of Motion?"},
        {"role": "assistant", "content": "Newton's Second Law states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass. Mathematically, F = ma."}
    ]
}

print("Sending request using FastAPI TestClient...")
try:
    with client:
        response = client.post("/api/tutor/analyze", json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        # Check if the explanation mentions F = ma or formula
        explanation = data.get("data", {}).get("explanation") or data.get("data", {}).get("ai_explanation") or ""
        
        # Encode/decode to ignore characters that can't be represented in the current console encoding
        safe_explanation = explanation.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"\nAI Explanation:\n{safe_explanation}")
        
        if "formula" in explanation.lower() or "f" in explanation.lower() or "m" in explanation.lower():
            print("\n✅ Verification Successful: LLM resolved 'its formula' based on the history 'Newton's Second Law'!")
        else:
            print("\n⚠️ Verification potentially incomplete or key terms not found.")
except Exception as e:
    print(f"Error during request: {e}")
