import sys
import os
from fastapi.testclient import TestClient

# Align python path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "app", "src"))

from main import app

client = TestClient(app)

payload = {
    "query": "What is the formula?",
    "class_name": "Class 10",
    "subject": "physics",
    "chapter": "Electricity",
    "topic": "Ohm's Law"
}

print("Sending request with active topic metadata...")
try:
    with client:
        response = client.post("/api/tutor/analyze", json=payload)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        explanation = data.get("data", {}).get("explanation") or data.get("data", {}).get("ai_explanation") or ""
        
        # Safe printing for Windows command consoles
        safe_explanation = explanation.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        print(f"\nAI Explanation Snippet:\n{safe_explanation[:500]}...")
        
        # Verify it mentions Ohm's law or V = IR, and NOT chemistry/molecules
        lowered_explanation = explanation.lower()
        has_physics = "ohm" in lowered_explanation or "voltage" in lowered_explanation or "current" in lowered_explanation or "v = ir" in lowered_explanation
        has_chemistry = "chemistry" in lowered_explanation or "molecule" in lowered_explanation or "compound" in lowered_explanation
        
        if has_physics and not has_chemistry:
            print("\n[SUCCESS] Verification Successful: Generic query resolved to Ohm's Law based on metadata!")
        else:
            print("\n[FAILED] Verification Failed!")
            print(f"Physics terms found: {has_physics}")
            print(f"Chemistry terms found: {has_chemistry}")
            
except Exception as e:
    print(f"Error during request: {e}")
