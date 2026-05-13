import requests
import json
import time

def test_api_generate():
    url = "http://localhost:8000/api/generate"
    payload = {
        "prompt": "Create a simulation of a block sliding down an inclined plane with friction."
    }
    headers = {
        "Content-Type": "application/json"
    }

    print(f"🚀 Sending request to: {url}")
    print(f"📝 Prompt: {payload['prompt']}")

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers)
        duration = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS ({duration:.2f}s)")
            
            # Verify structure
            keys = data.keys()
            print(f"📦 Response Keys: {list(keys)}")
            
            if all(k in data for k in ["dsl", "knowledge", "metadata"]):
                print("💎 Structure: VALID (dsl, knowledge, metadata found)")
            else:
                print("⚠️ Structure: INVALID (missing required keys)")

            # Save to file
            with open("api_test_output.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"💾 Result saved to api_test_output.json")
            
            # Print a snippet of the DSL
            title = data.get("dsl", {}).get("meta", {}).get("title", "Unknown")
            print(f"📌 Simulation Title: {title}")

        else:
            print(f"❌ FAILED (Status Code: {response.status_code})")
            print(f"Error Detail: {response.text}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("Note: Ensure your FastAPI server is running at http://localhost:8000")

if __name__ == "__main__":
    test_api_generate()
