import httpx
import json

def test_tutor_api():
    url = "http://127.0.0.1:8000/api/tutor/analyze"
    payload = {
        "query": "What is Gravity?",
        "class_name": "Class 11",
        "subject": "Physics",
        "chapter": "Gravitation",
        "topic": "Gravity"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("Sending POST request to:", url)
    print("Payload:", json.dumps(payload, indent=2))
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=90.0)
        print("\nResponse Status Code:", response.status_code)
        
        if response.status_code == 200:
            print("\nResponse Data:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("\nError Response Text:")
            print(response.text)
    except Exception as e:
        print("\nFailed to connect to the server:", e)

if __name__ == "__main__":
    test_tutor_api()
