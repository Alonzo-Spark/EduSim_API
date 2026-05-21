import os
import httpx
from dotenv import load_dotenv

from app.src.config.models import DEFAULT_MODEL, OPENROUTER_URL

load_dotenv()

def test_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"Key found: {api_key[:10]}...")
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        print(f"Headers: {headers}")
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                OPENROUTER_URL,
                headers=headers,
                json={
                    "model": DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "say hi"}],
                },
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openrouter()
