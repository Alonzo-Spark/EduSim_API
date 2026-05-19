import httpx

from app.src.config.openrouter_config import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    MODEL_NAME
)

async def generate_tutor_response(
    topic: str,
    question: str
):
    prompt = f"""
You are an educational physics tutor.

Topic:
{topic}

Student Question:
{question}

Explain clearly and educationally.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
        data = response.json()
        return (
            data["choices"][0]
            ["message"]["content"]
            .strip()
        )
    except Exception:
        return "Tutor response is currently unavailable."
