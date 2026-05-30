# scratch/check_api.py
import requests
import json

def test():
    url = "http://127.0.0.1:8000/api/tutor/analyze"
    payload = {"query": "Create a pendulum simulation"}
    headers = {"Content-Type": "application/json"}
    
    print("Sending request to:", url)
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print("Status Code:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            print("Success:", data.get("success"))
            tutor_data = data.get("data", {})
            print("Response Keys:", tutor_data.keys())
            
            guide = tutor_data.get("simulation_guide", {})
            print("\nSimulation Guide:")
            print(json.dumps(guide, indent=2))
        else:
            print("Error Response:", response.text)
    except Exception as e:
        print("Connection failed:", e)

if __name__ == "__main__":
    test()
