import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ✅ Use working model
MODEL = "openai/gpt-3.5-turbo"
# fallback if needed:
# MODEL = "mistralai/mistral-7b-instruct"

def call_openrouter_api(system_prompt: str, user_query: str, timeout=30):
    
    if not OPENROUTER_API_KEY:
        raise ValueError("❌ OPENROUTER_API_KEY not found in .env file")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "RAG-System",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
    }

    try:
        print(f"📡 Calling OpenRouter API ({MODEL})...")
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=timeout
        )

        # 🔥 DEBUG (very important)
        print("DEBUG STATUS:", response.status_code)
        print("DEBUG RESPONSE:", response.text[:500])

        response.raise_for_status()

        result = response.json()

        # ✅ Correct parsing (NO .content mistake)
        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.HTTPError:
        raise Exception(f"❌ API error: {response.text}")
    except Exception as e:
        raise Exception(f"❌ Unexpected error: {str(e)}")


def generate_response(context: str, question: str):

    system_prompt = (
    "You are an intelligent AI tutor.\n\n" 
    "Use the textbook context as the PRIMARY source.\n" "Explain concepts in detailed educational style.\n" 
    "Use all important information available in the context.\n" "Do not give very short answers.\n"
      "Explain step-by-step wherever possible.\n" "Include formulas, observations, examples, and applications if available.\n" 
      "Make answers beginner-friendly and descriptive.\n\n" "If the topic is NOT found in the textbook context,\n" 
      "then provide a general explanation using your own knowledge.\n" "In that case say:\n" 
      "'Not found in textbook, but here is a general explanation.'\n\n" 
      "Do not hallucinate incorrect formulas or facts."
    )
    user_query = f"""
Context:
{context}

Question:
{question}

Answer:
"""

    return call_openrouter_api(system_prompt, user_query)