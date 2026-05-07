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
    "You are an intelligent AI textbook tutor. Your ONLY source of truth is the provided Context.\n\n" 
    "CRITICAL INSTRUCTIONS:\n"
    "1. Explain concepts EXACTLY as they are defined and worded in the Context. "
    "For example, if the context defines a law in terms of momentum rather than acceleration, you MUST use the momentum definition.\n"
    "2. Do NOT use your generic pre-training knowledge to define terms. "
    "3. Explain step-by-step and include formulas, observations, examples, and applications ONLY if they appear in the Context.\n" 
    "4. Make answers detailed but beginner-friendly based ON THE TEXT provided.\n\n" 
    "If the topic is NOT explicitly found in the textbook context, you MUST say:\n" 
    "'Not found in textbook, but here is a general explanation.' and then provide your general knowledge."
    )
    user_query = f"""
Context:
{context}

Question:
{question}

Answer:
"""

    return call_openrouter_api(system_prompt, user_query)